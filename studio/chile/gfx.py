"""Rendering primitives: terrain globe, vector overlays, labels, flags, arrows."""

import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import box, shape

HERE = Path(__file__).parent
A = HERE / "assets"
W, H = 1080, 1920
SS = 2

TEX = np.load(A / "world.npy", mmap_mode="r")
TH, TW = TEX.shape[:2]
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
SPACE_TOP, SPACE_BOT = np.array([4, 8, 18], np.float32), np.array([10, 18, 36], np.float32)
_g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
SPACE = (SPACE_TOP * (1 - _g) + SPACE_BOT * _g).repeat(W, axis=1)
_rng = np.random.default_rng(3)
for _ in range(260):
    x, y = _rng.integers(0, W), _rng.integers(0, H)
    SPACE[y, x] = _rng.integers(120, 255)

RED = (235, 64, 52)
BLUE = (52, 120, 235)
GREEN = (40, 185, 120)
GOLD = (255, 200, 40)
ORANGE = (255, 140, 30)
WHITE = (255, 255, 255)
BLACK = (15, 15, 20)

FONT_BOLD = str(A / "Poppins-ExtraBold.ttf")
FONT_BIG = str(A / "Anton-Regular.ttf")
_fonts = {}


def font(px, big=False):
    k = (px, big)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONT_BIG if big else FONT_BOLD, px)
    return _fonts[k]


# ---------------------------------------------------------------- geometry
def _rings(geom):
    polys = [geom] if geom.geom_type == "Polygon" else [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]
    return [np.radians(np.asarray(p.exterior.coords)) for p in polys if p.area > 0.002]


WORLD = {f["properties"]["ADMIN"]: shape(f["geometry"])
         for f in json.loads((A / "countries.geojson").read_text())["features"]}
RINGS = {n: _rings(g) for n, g in WORLD.items()}
BBOX = {n: g.bounds for n, g in WORLD.items()}


def clip_rings(name, bounds):
    return _rings(WORLD[name].intersection(box(*bounds)))


def transplant(rings, src, dst):
    """Move rings from center src=(lon,lat) to dst preserving distances and bearings (true size)."""
    lc, pc = map(math.radians, src)
    ln, pn = map(math.radians, dst)
    out = []
    for r in rings:
        lam, phi = r[:, 0], r[:, 1]
        dl = lam - lc
        c = np.arccos(np.clip(math.sin(pc) * np.sin(phi) + math.cos(pc) * np.cos(phi) * np.cos(dl), -1, 1))
        th = np.arctan2(np.sin(dl) * np.cos(phi), math.cos(pc) * np.sin(phi) - math.sin(pc) * np.cos(phi) * np.cos(dl))
        p2 = np.arcsin(math.sin(pn) * np.cos(c) + math.cos(pn) * np.sin(c) * np.cos(th))
        l2 = ln + np.arctan2(np.sin(th) * np.sin(c) * math.cos(pn), np.cos(c) - math.sin(pn) * np.sin(p2))
        out.append(np.stack([l2, p2], axis=1))
    return out


# ---------------------------------------------------------------- camera
def tilt_h(amount):
    """Homography flat->screen: the top of the frame sees a wider, farther strip (3D ground plane)."""
    e, f = 1.3 * amount, 1.1 * amount
    src = np.float32([[-e * W, -f * H], [W + e * W, -f * H], [W, H], [0, H]])
    dst = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    return cv2.getPerspectiveTransform(src, dst)


class Cam:
    def __init__(self, lon, lat, R, tilt=0.0):
        self.lon, self.lat, self.R, self.tilt = lon, lat, R, tilt

    def project(self, lonlat_rad, ss=1):
        pts, vis = self._flat(lonlat_rad)
        if self.tilt > 0.001:
            pts = cv2.perspectiveTransform(pts[None].astype(np.float32), tilt_h(self.tilt))[0].astype(np.float64)
        return pts * ss, vis

    def _flat(self, lonlat_rad):
        l0, p0 = math.radians(self.lon), math.radians(self.lat)
        lam, phi = lonlat_rad[:, 0], lonlat_rad[:, 1]
        cp, sp, dl = np.cos(phi), np.sin(phi), lonlat_rad[:, 0] - l0
        x = cp * np.sin(dl)
        y = math.cos(p0) * sp - math.sin(p0) * cp * np.cos(dl)
        vis = math.sin(p0) * sp + math.cos(p0) * cp * np.cos(dl) > 0
        return np.stack([W / 2 + self.R * x, H / 2 - self.R * y], axis=1), vis

    def pt(self, lon, lat):
        p, v = self.project(np.radians([[lon, lat]]))
        return (float(p[0, 0]), float(p[0, 1])), bool(v[0])


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ramp(t, t0, dur=0.3):
    return ease((t - t0) / dur) if dur > 0 else float(t >= t0)


def lerp_cam(a, b, p, dip=0.0):
    p = ease(p)
    R = math.exp(math.log(a.R) + (math.log(b.R) - math.log(a.R)) * p) * (1 - dip * math.sin(math.pi * p))
    dlon = ((b.lon - a.lon + 180) % 360) - 180
    return Cam(a.lon + dlon * p, a.lat + (b.lat - a.lat) * p, R, a.tilt + (b.tilt - a.tilt) * p)


def cam_path(t, keys):
    """keys: [(time, Cam, dip)] -> Cam at t."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, c0, _), (t1, c1, dip) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp_cam(c0, c1, (t - t0) / max(t1 - t0, 1e-6), dip)
    return keys[-1][1]


# ---------------------------------------------------------------- base layers
def terrain(cam, dim=0.72):
    gx, gy = XX, YY
    if cam.tilt > 0.001:
        inv = np.linalg.inv(tilt_h(cam.tilt))
        den = inv[2, 0] * XX + inv[2, 1] * YY + inv[2, 2]
        gx = (inv[0, 0] * XX + inv[0, 1] * YY + inv[0, 2]) / den
        gy = (inv[1, 0] * XX + inv[1, 1] * YY + inv[1, 2]) / den
    x = (gx - W / 2) / cam.R
    y = (H / 2 - gy) / cam.R
    rho = np.sqrt(x * x + y * y)
    inside = rho < 1.0
    c = np.arcsin(np.clip(rho, 0, 1))
    sc, cc = np.sin(c), np.cos(c)
    p0, l0 = math.radians(cam.lat), math.radians(cam.lon)
    rs = np.where(rho == 0, 1e-9, rho)
    lat = np.arcsin(np.clip(cc * math.sin(p0) + y * sc * math.cos(p0) / rs, -1, 1))
    lon = l0 + np.arctan2(x * sc, rs * math.cos(p0) * cc - y * math.sin(p0) * sc)
    u = (((np.degrees(lon) + 180) % 360) / 360 * TW).astype(np.float32)
    v = ((90 - np.degrees(lat)) / 180 * TH).astype(np.float32)
    img = cv2.remap(np.asarray(TEX), u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP).astype(np.float32)
    img *= dim
    out = np.where(inside[..., None], img, SPACE)
    if cam.tilt > 0.001:  # distance haze toward the horizon
        fog = (np.clip(1 - YY / (H * 0.55), 0, 1) ** 1.6)[..., None] * min(1.0, cam.tilt * 2.2)
        out = out * (1 - fog) + np.array([150, 185, 225], np.float32) * 0.55 * fog
    if cam.R < 1.2 * max(W, H):  # atmosphere glow at the limb
        g = np.clip(1 - (rho - 1) * cam.R / 40, 0, 1) * (rho >= 1)
        out += g[..., None] * np.array([60, 120, 220], np.float32) * 0.8
    return out


def overlay(cam, fills=None, outline=None, extra=None, borders=True):
    """Draw vector layer at 2x and return RGBA float (H,W,4) at 1x.
    fills: {name: (rgb, alpha)}; outline: [names] get white outline + glow; extra: [(rings, rgb, alpha, outline_rgb)]"""
    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    glow = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)

    def rings_px(rings):
        for r in rings:
            p, v = cam.project(r, SS)
            if v.sum() < 3:
                continue
            p = p[v]
            if p[:, 0].max() < -50 or p[:, 0].min() > W * SS + 50 or p[:, 1].max() < -50 or p[:, 1].min() > H * SS + 50:
                continue
            yield [tuple(q) for q in p]

    fills = fills or {}
    if borders:
        for name, rings in RINGS.items():
            for poly in rings_px(rings):
                d.line(poly + [poly[0]], fill=(255, 255, 255, 70), width=SS)
    for name, (rgb, a) in fills.items():
        if a <= 0.01:
            continue
        for poly in rings_px(RINGS[name]):
            d.polygon(poly, fill=rgb + (int(170 * a),))
    for rings, rgb, a, orgb in extra or []:
        if a <= 0.01:
            continue
        for poly in rings_px(rings):
            d.polygon(poly, fill=rgb + (int(200 * a),))
            if orgb:
                d.line(poly + [poly[0]], fill=orgb + (int(255 * a),), width=3 * SS)
                gd.line(poly + [poly[0]], fill=orgb + (int(255 * a),), width=10 * SS)
    for name in outline or []:
        col = fills.get(name, (WHITE, 1))[0]
        for poly in rings_px(RINGS[name]):
            d.line(poly + [poly[0]], fill=(255, 255, 255, 255), width=3 * SS)
            gd.line(poly + [poly[0]], fill=col + (255,), width=12 * SS)
    small = cv2.resize(np.asarray(lay, np.float32), (W, H), interpolation=cv2.INTER_AREA)
    if outline or any(e[3] for e in extra or []):
        g = cv2.resize(np.asarray(glow, np.float32), (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        g = cv2.GaussianBlur(g, (0, 0), 9)
        g = cv2.resize(g, (W, H))
        return small, g
    return small, None


def compose(base, lay):
    small, glow = lay
    a = small[..., 3:4] / 255.0
    out = base * (1 - a) + small[..., :3] * a
    if glow is not None:
        out += glow[..., :3] * (glow[..., 3:4] / 255.0) * 0.9
    return out


def vignette(img, strength=0.35):
    r = np.sqrt(((XX - W / 2) / (W / 2)) ** 2 + ((YY - H / 2) / (H / 2)) ** 2)
    return img * (1 - strength * np.clip(r - 0.6, 0, 1)[..., None])


# ---------------------------------------------------------------- flags
def flag(name, w=84, h=56):
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    if name == "Chile":
        d.rectangle((0, h // 2, w, h), fill=(213, 43, 30))
        d.rectangle((0, 0, h // 2, h // 2), fill=(0, 57, 166))
        cx, cy, r = h // 4, h // 4, h * 0.16
        pts = [(cx + (r if i % 2 == 0 else r * 0.4) * math.sin(i * math.pi / 5), cy - (r if i % 2 == 0 else r * 0.4) * math.cos(i * math.pi / 5)) for i in range(10)]
        d.polygon(pts, fill=WHITE)
    elif name == "Argentina":
        d.rectangle((0, 0, w, h // 3), fill=(116, 172, 223))
        d.rectangle((0, 2 * h // 3, w, h), fill=(116, 172, 223))
        d.ellipse((w / 2 - h * 0.1, h / 2 - h * 0.1, w / 2 + h * 0.1, h / 2 + h * 0.1), fill=(246, 180, 14))
    elif name == "Bolivia":
        for i, c in enumerate([(213, 43, 30), (249, 228, 0), (0, 122, 51)]):
            d.rectangle((0, i * h / 3, w, (i + 1) * h / 3), fill=c)
    elif name == "Spain":
        d.rectangle((0, 0, w, h), fill=(198, 11, 30))
        d.rectangle((0, h / 4, w, 3 * h / 4), fill=(255, 196, 0))
    elif name == "Peru":
        d.rectangle((0, 0, w / 3, h), fill=(217, 16, 35))
        d.rectangle((2 * w / 3, 0, w, h), fill=(217, 16, 35))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 8, fill=255)
    out = Image.new("RGBA", (w, h))
    out.paste(img, (0, 0), m)
    return out


# ---------------------------------------------------------------- 2D elements on final frame (PIL, 1x)
def _pop_scale(t):
    """0->1.12->1 over 0.28s."""
    if t <= 0:
        return 0.0
    if t < 0.18:
        return 1.12 * ease(t / 0.18)
    return 1.12 - 0.12 * ease((t - 0.18) / 0.1)


def safe_composite(canvas, img, pos):
    x, y = int(pos[0]), int(pos[1])
    l, t = max(0, -x), max(0, -y)
    r, b = min(img.width, canvas.width - x), min(img.height, canvas.height - y)
    if r <= l or b <= t:
        return
    canvas.alpha_composite(img.crop((l, t, r, b)), (x + l, y + t))


def paste_scaled(canvas, sprite, center, scale, alpha=1.0):
    if scale <= 0.02 or alpha <= 0.01:
        return
    w, h = max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale))
    fw, fh = sprite.width, sprite.height  # clamp on final size so pop-in never jumps
    center = (min(max(center[0], fw / 2 + 14), W - fw / 2 - 14), min(max(center[1], fh / 2 + 14), H - fh / 2 - 14))
    s = sprite.resize((w, h), Image.LANCZOS)
    if alpha < 1:
        s.putalpha(s.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(s, (int(center[0] - w / 2), int(center[1] - h / 2)))


def label_sprite(text, size=44, fg=BLACK, bg=WHITE, flag_name=None, pad=(26, 14)):
    f = font(size)
    tw = int(ImageDraw.Draw(Image.new("L", (1, 1))).textlength(text, font=f))
    fw = 0
    fl = flag(flag_name, int(size * 1.35), int(size * 0.9)) if flag_name else None
    if fl:
        fw = fl.width + 16
    w, h = tw + fw + pad[0] * 2, int(size * 1.35) + pad[1] * 2
    img = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((8, 12, w + 8, h + 12), 16, fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, w + 8, h + 8), 16, fill=bg + (255,))
    x = 8 + pad[0]
    if fl:
        img.alpha_composite(fl, (x, 8 + (h - fl.height) // 2))
        x += fw
    d.text((x, 8 + h / 2), text, font=f, fill=fg, anchor="lm")
    return img


def big_text_sprite(text, size=150, fill=WHITE, stroke=BLACK, sw=10):
    f = font(size, big=True)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    l, t, r, b = d0.textbbox((0, 0), text, font=f, stroke_width=sw)
    img = Image.new("RGBA", (r - l + 40, b - t + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((20 - l, 20 - t), text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    return img


_sprite_cache = {}


def sprite(kind, *args, **kw):
    key = (kind, args, tuple(sorted(kw.items())))
    if key not in _sprite_cache:
        _sprite_cache[key] = {"label": label_sprite, "big": big_text_sprite, "flag": flag}[kind](*args, **kw)
    return _sprite_cache[key]


def pop(canvas, t_since, spr, center, fade_out_at=None, t_now=None):
    if t_since < 0:
        return
    a = 1.0
    if fade_out_at is not None and t_now is not None and t_now > fade_out_at:
        a = 1 - ease((t_now - fade_out_at) / 0.25)
    paste_scaled(canvas, spr, center, _pop_scale(t_since), a)


def pin(d, xy, color, r=16, t_since=1.0):
    if t_since < 0:
        return
    s = _pop_scale(t_since)
    r *= s
    x, y = xy
    d.ellipse((x - r - 6, y - r - 6, x + r + 6, y + r + 6), fill=(255, 255, 255, 255))
    d.ellipse((x - r, y - r, x + r, y + r), fill=color + (255,))


def arrow(d, p0, p1, color, width=12, progress=1.0, dotted=False, head=34):
    if progress <= 0:
        return
    x0, y0 = p0
    x1, y1 = p0[0] + (p1[0] - p0[0]) * progress, p0[1] + (p1[1] - p0[1]) * progress
    ang = math.atan2(y1 - y0, x1 - x0)
    tail_end = (x1 - head * 0.8 * math.cos(ang), y1 - head * 0.8 * math.sin(ang))
    if dotted:
        n = int(math.hypot(tail_end[0] - x0, tail_end[1] - y0) // 26)
        for i in range(n):
            cx, cy = x0 + (tail_end[0] - x0) * (i + 0.5) / max(n, 1), y0 + (tail_end[1] - y0) * (i + 0.5) / max(n, 1)
            d.ellipse((cx - width / 2, cy - width / 2, cx + width / 2, cy + width / 2), fill=color + (255,))
    else:
        d.line([(x0, y0), tail_end], fill=color + (255,), width=width)
    pts = [(x1, y1), (x1 - head * math.cos(ang - 0.45), y1 - head * math.sin(ang - 0.45)),
           (x1 - head * math.cos(ang + 0.45), y1 - head * math.sin(ang + 0.45))]
    d.polygon(pts, fill=color + (255,))


def dashed_line(d, pts, color, width=5, dash=22, gap=14, progress=1.0):
    total = [0.0]
    for a, b in zip(pts, pts[1:]):
        total.append(total[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    limit = total[-1] * progress
    pos, on = 0.0, True
    for (a, b), s0 in zip(zip(pts, pts[1:]), total):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        u = 0.0
        while u < seg and s0 + u < limit:
            step = min(dash if on else gap, seg - u, limit - s0 - u)
            if on:
                p = (a[0] + (b[0] - a[0]) * u / seg, a[1] + (b[1] - a[1]) * u / seg)
                q = (a[0] + (b[0] - a[0]) * (u + step) / seg, a[1] + (b[1] - a[1]) * (u + step) / seg)
                d.line([p, q], fill=color + (255,), width=width)
            u += step
            on = not on if step == (dash if on else gap) else on


# ---------------------------------------------------------------- photos
_photo_cache = {}


def photo(path, t, dur, zoom_in=True, focus=(0.5, 0.5)):
    if path not in _photo_cache:
        im = cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB).astype(np.float32)
        _photo_cache[path] = im
    im = _photo_cache[path]
    ih, iw = im.shape[:2]
    base = max(W / iw, H / ih)
    z = 1 + 0.14 * (t / dur if zoom_in else 1 - t / dur)
    s = base * z
    cw, ch = W / s, H / s
    cx = min(max(iw * focus[0], cw / 2), iw - cw / 2)
    cy = min(max(ih * focus[1], ch / 2), ih - ch / 2)
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def whip(img, t_since, dur=0.18, direction=1):
    """Directional motion blur at the start of a shot (whip-pan in)."""
    if t_since < 0 or t_since > dur:
        return img
    k = int(90 * (1 - t_since / dur)) | 1
    if k < 3:
        return img
    shift = int(direction * 120 * (1 - t_since / dur))
    img = np.roll(img, shift, axis=1)
    return cv2.blur(img, (k, 1))
