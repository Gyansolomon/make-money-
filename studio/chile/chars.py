"""Characters: mocap stickmen with props, countryballs with googly eyes, speech bubbles."""

import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import gfx as G

# Mocap clips come from the OpenMontage ink-theater (AGPL, CMU mocap data), so they are not copied here.
# Point INK_CLIPS at clips.js, or keep the OpenMontage repo cloned next to this one.
_src = Path(os.environ.get("INK_CLIPS", Path(__file__).resolve().parents[3] / "OpenMontage-video-creator-" / "ink-theater" / "mocap" / "clips.js")).read_text()
CLIPS = json.loads(_src[_src.index("{"): _src.rindex("}") + 1])
STAND = {"hips": [0, 0], "chest": [0, -88], "neck": [0, -150], "head": [0, -182],
         "shR": [52, -140], "elR": [64, -58], "haR": [72, 26], "shL": [-52, -140], "elL": [-64, -58], "haL": [-72, 26],
         "hipR": [26, -6], "knR": [32, 120], "ftR": [40, 262], "hipL": [-26, -6], "knL": [-32, 120], "ftL": [-40, 262],
         "rootY": 0}
STAND_GROUND = 262
AIM = dict(STAND, shR=[40, -140], elR=[130, -146], haR=[215, -150], shL=[-30, -140], elL=[60, -120], haL=[150, -146])
PLANT = dict(STAND, shR=[50, -140], elR=[110, -190], haR=[150, -250])


def clip_pose(name, t, loop=True):
    c = CLIPS[name]
    i = int(t * c["fps"])
    i = i % len(c["frames"]) if loop else min(i, len(c["frames"]) - 1)
    return c["frames"][i], c["groundY"]


# ------------------------------------------------------------------ stickman
def _ss_layer(w, h):
    return Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))


def stickman(canvas, pose, ground_y_units, x, y_feet, height=300, facing=1, role="spanish",
             tilt=0.0, alpha=1.0, gun=False, gun_aim=False, flag_carry=None):
    """Draw a stick figure whose feet stand at (x, y_feet). tilt in radians rotates about the feet."""
    s = height / 540.0
    box = int(height * 2.4)
    lay = _ss_layer(box, box)
    d = ImageDraw.Draw(lay)
    ox, oy = box, box * 1.7  # feet anchor inside the 2x layer
    rootY = pose.get("rootY", 0) or 0

    def P(pt):
        px = pt[0] * facing * s * 2
        py = (pt[1] - ground_y_units + rootY) * s * 2
        c, sn = math.cos(tilt), math.sin(tilt)
        return (ox + px * c - py * sn, oy + px * sn + py * c)

    ink, halo = (20, 20, 25), (255, 255, 255)
    lw = max(10, int(24 * s * 2))
    HR = 78  # big chibi head (clip units)
    head_r = HR * s * 2
    nk, hd = pose["neck"], pose["head"]
    dx, dy = hd[0] - nk[0], hd[1] - nk[1]
    n = math.hypot(dx, dy) or 1.0
    hc = P([nk[0] + dx / n * HR * 0.95, nk[1] + dy / n * HR * 0.95])
    limbs = [["hips", "chest", "neck"], ["shR", "elR", "haR"], ["shL", "elL", "haL"], ["hipR", "knR", "ftR"], ["hipL", "knL", "ftL"]]
    for colr, wdt in ((halo, lw + 10), (ink, lw)):
        for chain in limbs:
            d.line([P(pose[j]) for j in chain], fill=colr, width=wdt, joint="curve")
            for j in (chain[0], chain[-1]):
                q = P(pose[j]); r = wdt / 2
                d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=colr)
        d.line([P(pose["neck"]), hc], fill=colr, width=wdt)
    skin = (255, 224, 189) if role == "spanish" else (196, 140, 98)
    d.ellipse((hc[0] - head_r - 5, hc[1] - head_r - 5, hc[0] + head_r + 5, hc[1] + head_r + 5), fill=halo)
    d.ellipse((hc[0] - head_r, hc[1] - head_r, hc[0] + head_r, hc[1] + head_r), fill=skin, outline=ink, width=lw // 2)
    # eyes (look in facing direction)
    for ex in (-0.28, 0.28):
        cx = hc[0] + (ex + 0.18 * facing) * head_r
        d.ellipse((cx - head_r * 0.1, hc[1] - head_r * 0.2, cx + head_r * 0.1, hc[1] + head_r * 0.05), fill=ink)
    if role == "spanish":  # morion helmet: dome + brim + crest
        top = hc[1] - head_r * 0.25
        d.chord((hc[0] - head_r * 1.05, top - head_r * 1.1, hc[0] + head_r * 1.05, top + head_r * 0.9), 180, 360, fill=(190, 195, 205), outline=ink, width=lw // 2)
        d.polygon([(hc[0] - head_r * 1.5, top - head_r * 0.05), (hc[0] + head_r * 1.5, top - head_r * 0.05),
                   (hc[0] + head_r * 1.2, top + head_r * 0.22), (hc[0] - head_r * 1.2, top + head_r * 0.22)], fill=(170, 175, 185), outline=ink)
        d.chord((hc[0] - head_r * 0.35, top - head_r * 1.55, hc[0] + head_r * 0.35, top - head_r * 0.2), 180, 360, fill=(170, 175, 185), outline=ink, width=lw // 3)
    else:  # Mapuche trarilonko headband
        d.line([(hc[0] - head_r, hc[1] - head_r * 0.35), (hc[0] + head_r, hc[1] - head_r * 0.35)], fill=(200, 30, 40), width=int(lw * 0.9))
        d.ellipse((hc[0] - head_r * 0.14, hc[1] - head_r * 0.5, hc[0] + head_r * 0.14, hc[1] - head_r * 0.2), fill=(230, 230, 235))
    if gun:
        h1, e1 = P(pose["haR"]), P(pose["elR"])
        ang = math.atan2(h1[1] - e1[1], h1[0] - e1[0]) if gun_aim else math.atan2(-1, 0.25 * facing)
        L = 300 * s * 2
        start = (h1[0] - math.cos(ang) * L * 0.35, h1[1] - math.sin(ang) * L * 0.35)
        end = (h1[0] + math.cos(ang) * L * 0.65, h1[1] + math.sin(ang) * L * 0.65)
        d.line([start, end], fill=(90, 55, 30), width=int(lw * 1.2))
        d.line([((start[0] + end[0]) / 2, (start[1] + end[1]) / 2), end], fill=(40, 40, 45), width=int(lw * 0.8))
        lay.info["muzzle"] = end
    if flag_carry:
        h1 = P(pose["haL"])
        pole_top = (h1[0], h1[1] - 560 * s * 2)
        d.line([(h1[0], h1[1] + 40 * s), pole_top], fill=(90, 55, 30), width=int(lw * 0.8))
        fl = G.flag(flag_carry, int(170 * s * 2), int(115 * s * 2))
        lay.alpha_composite(fl, (int(pole_top[0]), int(pole_top[1])))
    small = lay.resize((box, box), Image.LANCZOS)
    if alpha < 1:
        small.putalpha(small.getchannel("A").point(lambda v: int(v * alpha)))
    pos = (int(x - box / 2), int(y_feet - box * 0.85))
    G.safe_composite(canvas, small, pos)
    if "muzzle" in lay.info:
        m = lay.info["muzzle"]
        return (pos[0] + m[0] / 2, pos[1] + m[1] / 2)
    return None


def smoke(canvas, xy, t_since, scale=1.0, seed=0):
    if t_since < 0 or t_since > 1.4:
        return
    d = ImageDraw.Draw(canvas)
    rng = np.random.default_rng(seed)
    a = int(230 * max(0, 1 - t_since / 1.4))
    for i in range(7):
        ang = rng.uniform(0, 2 * math.pi)
        dist = (20 + 70 * t_since) * scale * rng.uniform(0.5, 1.2)
        r = (22 + 40 * t_since) * scale * rng.uniform(0.7, 1.2)
        cx, cy = xy[0] + math.cos(ang) * dist, xy[1] + math.sin(ang) * dist - 40 * t_since * scale
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(235, 235, 235, a))


def flash(canvas, xy, t_since, scale=1.0):
    if t_since < 0 or t_since > 0.12:
        return
    d = ImageDraw.Draw(canvas)
    r = 60 * scale
    pts = [(xy[0] + math.cos(i * math.pi / 6) * (r if i % 2 == 0 else r * 0.45), xy[1] + math.sin(i * math.pi / 6) * (r if i % 2 == 0 else r * 0.45)) for i in range(12)]
    d.polygon(pts, fill=(255, 210, 60, 255))


# ------------------------------------------------------------------ countryball
def _smooth_targets(t, seed, period=0.55):
    """Eyes dart between random targets; seek-safe (pure function of t)."""
    k = int(t / period)
    f = (t / period) - k
    rng_a, rng_b = np.random.default_rng(seed * 1000 + k), np.random.default_rng(seed * 1000 + k + 1)
    a, b = rng_a.uniform(-1, 1, 2), rng_b.uniform(-1, 1, 2)
    e = min(1.0, f * 4)  # quick dart then hold
    e = e * e * (3 - 2 * e)
    return a + (b - a) * e


def countryball(canvas, name, center, R, t, seed=1, mood="normal", squash=0.0, look=None, alpha=1.0):
    box = int(R * 2.6)
    lay = Image.new("RGBA", (box * 2, box * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = box
    rx, ry = R * 2 * (1 + squash), R * 2 * (1 - squash)
    # shadow
    d.ellipse((c - rx * 0.9, c + ry * 0.85, c + rx * 0.9, c + ry * 1.1), fill=(0, 0, 0, 90))
    fl = G.flag(name, int(rx * 2), int(ry * 2)).convert("RGBA")
    mask = Image.new("L", fl.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, fl.width - 1, fl.height - 1), fill=255)
    lay.paste(fl, (int(c - rx), int(c - ry)), mask)
    d.ellipse((c - rx, c - ry, c + rx, c + ry), outline=(15, 15, 20), width=int(R * 0.14))
    # eyes
    lk = np.array(look) if look is not None else _smooth_targets(t, seed)
    blink = 1.0
    bp = (t + seed * 0.37) % 3.1
    if bp < 0.12:
        blink = 0.15
    for ex in (-0.36, 0.36):
        ecx, ecy = c + ex * rx, c - 0.12 * ry
        er = 0.3 * R * 2
        d.ellipse((ecx - er, ecy - er * blink, ecx + er, ecy + er * blink), fill=(255, 255, 255), outline=(15, 15, 20), width=int(R * 0.08))
        if blink > 0.5:
            pr = er * 0.42
            px, py = ecx + lk[0] * er * 0.5, ecy + lk[1] * er * 0.5
            d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=(15, 15, 20))
        if mood == "angry":
            sgn = 1 if ex < 0 else -1
            d.line([(ecx - er * 1.1, ecy - er * (1.3 if sgn > 0 else 0.7)), (ecx + er * 1.1, ecy - er * (0.7 if sgn > 0 else 1.3))], fill=(15, 15, 20), width=int(R * 0.16))
        if mood == "sad":
            d.chord((ecx - er, ecy - er, ecx + er, ecy + er), 180, 360, fill=(15, 15, 20))
    small = lay.resize((box, box), Image.LANCZOS)
    if alpha < 1:
        small.putalpha(small.getchannel("A").point(lambda v: int(v * alpha)))
    G.safe_composite(canvas, small, (center[0] - box / 2, center[1] - box / 2))


# ------------------------------------------------------------------ speech bubble
def bubble(canvas, t_since, text, anchor, box_center, width=520, size=46, t_now=None, end=None):
    if t_since < 0 or (end is not None and t_now is not None and t_now > end + 0.2):
        return
    scale = G._pop_scale(t_since)
    if end is not None and t_now is not None and t_now > end:
        scale *= max(0, 1 - (t_now - end) / 0.2)
    if scale <= 0.02:
        return
    f = G.font(size)
    words, lines, cur = text.split(), [], ""
    dm = ImageDraw.Draw(Image.new("L", (1, 1)))
    for w in words:
        test = (cur + " " + w).strip()
        if dm.textlength(test, font=f) > width - 60 and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    lines.append(cur)
    lh = int(size * 1.2)
    bw = int(max(dm.textlength(l, font=f) for l in lines) + 70)
    bh = lh * len(lines) + 50
    pad = 60
    spr = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    bx, by = pad, pad
    # tail toward anchor (in sprite coords)
    ax = anchor[0] - (box_center[0] - spr.width / 2)
    ay = anchor[1] - (box_center[1] - spr.height / 2)
    ax, ay = min(max(ax, 0), spr.width), min(max(ay, 0), spr.height)
    base = (bx + bw / 2, by + bh / 2)
    for col, grow in (((15, 15, 20), 5), ((255, 255, 255), 0)):
        d.polygon([(base[0] - 30 - grow, base[1]), (base[0] + 30 + grow, base[1]), (ax, ay)], fill=col)
        d.rounded_rectangle((bx - grow, by - grow, bx + bw + grow, by + bh + grow), 40, fill=col)
    for i, l in enumerate(lines):
        d.text((bx + bw / 2, by + 25 + lh * i + lh / 2), l, font=f, fill=(15, 15, 20), anchor="mm")
    G.paste_scaled(canvas, spr, box_center, scale)
