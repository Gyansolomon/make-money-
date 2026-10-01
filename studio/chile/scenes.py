"""Chile v2: scene timeline, frame rendering, SFX cue sheet."""

import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import gfx as G

HERE = Path(__file__).parent
V = json.loads((HERE / "out" / "voice.json").read_text())
TL, WORDS = V["timeline"], V["words"]
TOTAL = TL[-1]["end"] + 0.5
SC = {s["key"]: s for s in TL}
KEYS = [s["key"] for s in TL]
IMG = HERE / "imgs"


def _n(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def cue(scene, token, nth=0, end=False):
    si = KEYS.index(scene)
    hits = [w for w in WORDS if w["scene"] == si and _n(w["text"]).startswith(_n(token))]
    w = hits[min(nth, len(hits) - 1)]
    return w["end"] if end else w["start"]


# ------------------------------------------------------------------ cameras
C_G0 = G.Cam(15, 8, 430)
C_G1 = G.Cam(-64, -24, 430)
C_CHILE = G.Cam(-69.6, -37.4, 2330)
EU_DST = (19.0, 50.3)
C_EU = G.Cam(19.0, 50.4, 2150)
C_Q = G.Cam(-69.6, -37.4, 2550)
C_ANDES = G.Cam(-70.3, -33.0, 5600, tilt=0.28)
C_PAC = G.Cam(-74.0, -31.5, 2900, tilt=0.12)
C_TREATY = G.Cam(-66.0, -39.0, 1700)
C_WAR = G.Cam(-67.8, -20.8, 3000)
C_NAVY = G.Cam(-66.5, -17.8, 3300)

CHILE_SRC = (-70.0, -36.7)
CHILE_EU = G.transplant(G.RINGS["Chile"], CHILE_SRC, EU_DST)
BOLIVIA_COAST = G.clip_rings("Chile", (-75, -24.0, -66, -21.4))
PERU_SOUTH = G.clip_rings("Chile", (-75, -21.4, -66, -17.0))
_b = G.WORLD["Chile"].boundary.intersection(G.WORLD["Argentina"].boundary)
_ls = [_b] if _b.geom_type == "LineString" else [g for g in getattr(_b, "geoms", []) if g.geom_type == "LineString"]
BORDER = np.radians(np.array(sorted([p for ln in _ls for p in ln.coords], key=lambda p: -p[1])))

SFX = []  # (time, name, gain_db)


def sfx(t, name, gain=0.0):
    SFX.append((round(t, 3), name, gain))


# ------------------------------------------------------------------ helpers
def title(canvas, t_since, text, t_now=None, fade_at=None, y=250, size=52):
    G.pop(canvas, t_since, G.sprite("label", text, size=size, fg=G.WHITE, bg=(18, 18, 26)), (540, y), fade_at, t_now)


def map_frame(cam, fills=None, outline=None, extra=None, dim=0.72):
    return G.compose(G.terrain(cam, dim), G.overlay(cam, fills, outline, extra))


def P(cam, lon, lat):
    return cam.pt(lon, lat)[0]


# ------------------------------------------------------------------ scenes (t = absolute seconds)
def s_hook(t, canvas, d):
    s = SC["hook"]["start"]
    c_country = cue("hook", "country")
    c_4000, c_long, c_177 = cue("hook", "4000"), cue("hook", "long", end=True), cue("hook", "177")
    cam = G.cam_path(t, [(s, C_G0, 0), (s + 0.8, C_G1, 0), (s + 1.5, C_CHILE, 0), (SC["hook"]["end"], G.Cam(-69.6, -37.4, 2420), 0)])
    a = G.ramp(t, c_country - 0.1, 0.35)
    img = map_frame(cam, {"Chile": (G.RED, a)}, ["Chile"] if a > 0.5 else None)
    # length bracket + number
    q = G.ramp(t, max(c_4000 - 0.15, s + 1.45), 0.6)
    if q > 0:
        x = P(cam, -64.3, -30)[0]
        y0, y1 = P(cam, -64.3, -17.5)[1], P(cam, -64.3, -55.9)[1]
        yb = y0 + (y1 - y0) * q
        d.line([(x, y0), (x, yb)], fill=G.GOLD + (255,), width=7)
        d.line([(x - 20, y0), (x + 20, y0)], fill=G.GOLD + (255,), width=7)
        if q >= 1:
            d.line([(x - 20, y1), (x + 20, y1)], fill=G.GOLD + (255,), width=7)
        G.pop(canvas, t - max(c_4000 + 0.35, s + 1.9), G.sprite("big", "4,300 KM", size=120, fill=G.GOLD), (x + 175, (y0 + y1) / 2 + 120))
    if t > c_177 - 0.1:
        y = P(cam, -71, -33.4)[1]
        xl, xr = P(cam, -71.7, -33.4)[0], P(cam, -69.9, -33.4)[0]
        d.line([(xl - 4, y), (xr + 4, y)], fill=G.WHITE + (255,), width=6)
        for xx in (xl - 4, xr + 4):
            d.line([(xx, y - 16), (xx, y + 16)], fill=G.WHITE + (255,), width=6)
        G.pop(canvas, t - c_177, G.sprite("label", "177 KM WIDE", size=40), (xl - 170, y))
    return img


def ev_hook():
    s = SC["hook"]["start"]
    sfx(s, "whoosh", -2)
    sfx(s + 0.8, "whoosh_b", -3)
    sfx(cue("hook", "country"), "pop")
    sfx(max(cue("hook", "4000") - 0.2, SC["hook"]["start"] + 1.3), "riser", -6)
    sfx(max(cue("hook", "4000") + 0.35, SC["hook"]["start"] + 1.9), "impact", -3)
    sfx(cue("hook", "177"), "ding", -6)


def s_europe(t, canvas, d):
    s, e = SC["europe"]["start"], SC["europe"]["end"]
    c_eu, c_arc, c_afr = cue("europe", "europe"), cue("europe", "arctic"), cue("europe", "africa")
    cam = G.cam_path(t, [(s, G.Cam(-69.6, -37.4, 2420), 0), (s + 1.1, C_EU, 0.72), (e, G.Cam(19.0, 50.4, 2250), 0)])
    drop = G.ramp(t, c_eu + 0.05, 0.3)
    dst = (EU_DST[0], EU_DST[1] + 4 * (1 - drop))
    rings = G.transplant(G.RINGS["Chile"], CHILE_SRC, dst)
    img = map_frame(cam, extra=[(rings, G.RED, drop * 0.95, G.WHITE)])
    if t > c_arc - 0.1:
        pts = [P(cam, lon, 66.56) for lon in range(-30, 70, 2)]
        G.dashed_line(d, [(x + 3, y + 3) for x, y in pts], (0, 0, 0), 9, progress=G.ramp(t, c_arc - 0.1, 0.5))
        G.dashed_line(d, pts, G.GOLD, 7, progress=G.ramp(t, c_arc - 0.1, 0.5))
        G.pop(canvas, t - c_arc, G.sprite("label", "ARCTIC CIRCLE", size=38), (P(cam, 36, 66.56)[0], P(cam, 36, 66.56)[1] - 50))
    if t > c_afr - 0.1:
        xy = P(cam, 20.1, 31.8)
        G.pin(d, xy, G.GOLD, t_since=t - c_afr)
        G.pop(canvas, t - c_afr, G.sprite("label", "NORTH AFRICA", size=38), (xy[0] + 140, xy[1] + 60))
    G.pop(canvas, t - (c_eu + 0.2), G.sprite("label", "CHILE", size=40, flag_name="Chile"), (P(cam, 25, 58)[0] + 190, P(cam, 25, 58)[1]))
    return img


def ev_europe():
    s = SC["europe"]["start"]
    sfx(s, "whoosh", -1)
    sfx(cue("europe", "europe") + 0.3, "impact", -5)
    sfx(cue("europe", "arctic"), "pop")
    sfx(cue("europe", "africa"), "pop_b")


def s_question(t, canvas, d):
    s, e = SC["question"]["start"], SC["question"]["end"]
    cam = G.cam_path(t, [(s, G.Cam(19.0, 50.4, 2250), 0), (s + 1.0, C_Q, 0.72), (e, G.Cam(-69.6, -37.4, 2650), 0)])
    img = map_frame(cam, {"Chile": (G.RED, 1)}, ["Chile"], dim=0.6)
    c = cue("question", "noodle")
    G.pop(canvas, t - (c - 0.05), G.sprite("big", "SHAPED LIKE", size=110), (540, 820))
    G.pop(canvas, t - (c + 0.05), G.sprite("big", "A NOODLE?", size=170, fill=G.GOLD), (540, 960))
    return img


def ev_question():
    sfx(SC["question"]["start"], "whoosh_c", -2)
    sfx(cue("question", "noodle"), "scratch", -4)


def s_andes(t, canvas, d):
    s, e = SC["andes"]["start"], SC["andes"]["end"]
    c_andes, c_long, c_wall = cue("andes", "andes"), cue("andes", "longest"), cue("andes", "like")
    if t >= c_wall - 0.05:  # cut to real photo of the Andes
        ts = t - (c_wall - 0.05)
        img = G.photo(IMG / "aconcagua.jpg", ts, e - c_wall + 0.05, zoom_in=True, focus=(0.5, 0.45))
        img = G.whip(img, ts)
        G.pop(canvas, ts - 0.1, G.sprite("label", "THE ANDES", size=46), (540, 300))
        G.pop(canvas, ts - 0.35, G.sprite("label", "~7,000 KM LONG", size=38, fg=G.WHITE, bg=(200, 80, 20)), (540, 390))
        return img
    cam = G.cam_path(t, [(s, G.Cam(-69.6, -37.4, 2650), 0), (s + 1.3, C_ANDES, 0), (c_wall, G.Cam(-70.1, -33.6, 6200, 0.3), 0)])
    border_p = G.ramp(t, c_andes - 0.1, 1.2)
    img = map_frame(cam, {"Chile": (G.RED, 0.35)})
    pts, vis = cam.project(BORDER)
    pts = [tuple(p) for p, v in zip(pts, vis) if v]
    n = max(2, int(len(pts) * border_p))
    if border_p > 0:
        d.line(pts[:n], fill=G.ORANGE + (255,), width=9, joint="curve")
    if t > c_andes - 0.1:
        xy = P(cam, -69.3, -31.0)
        G.pop(canvas, t - c_andes, G.sprite("label", "THE ANDES", size=46, fg=G.WHITE, bg=(200, 80, 20)), (xy[0] + 120, xy[1]))
    G.pop(canvas, t - (s + 0.15), G.sprite("label", "LOOK EAST", size=44), (500, 250))
    G.arrow(d, (660, 250), (760, 250), G.WHITE, 12, G.ramp(t, s + 0.25, 0.25))
    return img


def ev_andes():
    s = SC["andes"]["start"]
    sfx(s, "whoosh_b", -2)
    sfx(s + 0.1, "wind", -14)
    sfx(cue("andes", "andes"), "pop")
    sfx(cue("andes", "like") - 0.05, "whoosh", -3)
    sfx(cue("andes", "wall"), "impact", -7)


def s_pacific(t, canvas, d):
    s, e = SC["pacific"]["start"], SC["pacific"]["end"]
    c_pac, c_trap = cue("pacific", "pacific"), cue("pacific", "trapped")
    cam = G.cam_path(t, [(s, G.Cam(-70.1, -33.6, 6200, 0.3), 0), (s + 1.0, C_PAC, 0), (e, G.Cam(-73.5, -31.5, 3100, 0.12), 0)])
    flash = 0.5 + 0.5 * math.sin((t - c_trap) * 18) if t > c_trap else 0
    img = map_frame(cam, {"Chile": (G.RED, 0.75 + 0.25 * flash)}, ["Chile"])
    G.pop(canvas, t - (s + 0.1), G.sprite("label", "LOOK WEST", size=44), (580, 250))
    G.arrow(d, (420, 250), (320, 250), G.WHITE, 12, G.ramp(t, s + 0.2, 0.25))
    if t > c_pac - 0.1:
        xy = P(cam, -78.5, -25.5)
        G.pop(canvas, t - c_pac, G.sprite("label", "PACIFIC OCEAN", size=44, fg=G.WHITE, bg=(30, 90, 180)), xy)
    if t > c_trap - 0.15:
        p = G.ramp(t, c_trap - 0.15, 0.35)
        yl = P(cam, -71, -29)[1]
        xw, xc, xe = P(cam, -79, -29)[0], P(cam, -71, -29)[0], P(cam, -64, -29)[0]
        G.arrow(d, (xw, yl + 90), (xc - 60, yl + 90), G.WHITE, 16, p)
        G.arrow(d, (xe, yl + 90), (xc + 60, yl + 90), G.WHITE, 16, p)
        G.pop(canvas, t - (c_trap + 0.2), G.sprite("big", "TRAPPED", size=130, fill=G.RED), (540, 1180))
    return img


def ev_pacific():
    s = SC["pacific"]["start"]
    sfx(s, "whoosh", -2)
    sfx(cue("pacific", "pacific"), "pop")
    sfx(cue("pacific", "trapped"), "impact", -2)


def s_treaty(t, canvas, d):
    s, e = SC["treaty"]["start"], SC["treaty"]["end"]
    c_1881, c_border, c_coast, c_arg2 = cue("treaty", "1881"), cue("treaty", "border"), cue("treaty", "coast"), cue("treaty", "plains")
    c_arg1 = cue("treaty", "argentina")
    cam = G.cam_path(t, [(s, G.Cam(-73.5, -31.5, 3100, 0.12), 0), (s + 1.0, C_TREATY, 0), (e, G.Cam(-66.5, -39.5, 1780), 0)])
    arg_a = G.ramp(t, c_arg2 - 0.2, 0.4)
    img = map_frame(cam, {"Chile": (G.RED, 1), "Argentina": (G.BLUE, arg_a)}, ["Chile"] + (["Argentina"] if arg_a > 0.5 else []))
    title(canvas, t - c_1881, "1881  ·  BORDER TREATY", t, e - 0.3)
    bp = G.ramp(t, c_border - 0.1, 1.6)
    if bp > 0:
        pts, vis = cam.project(BORDER)
        pts = [tuple(p) for p, v in zip(pts, vis) if v]
        d.line(pts[: max(2, int(len(pts) * bp))], fill=G.GOLD + (255,), width=8, joint="curve")
        if bp < 1:
            G.pin(d, pts[max(0, int(len(pts) * bp) - 1)], G.GOLD, 10)
    G.pop(canvas, t - c_arg1, G.sprite("label", "ARGENTINA", size=40, flag_name="Argentina"), P(cam, -64.5, -35))
    G.pop(canvas, t - c_coast, G.sprite("label", "COAST", size=38, fg=G.WHITE, bg=G.RED), (P(cam, -75.8, -36)[0] - 20, P(cam, -75.8, -36)[1]))
    G.pop(canvas, t - c_arg2, G.sprite("label", "PLAINS", size=38, fg=G.WHITE, bg=G.BLUE), P(cam, -64, -40))
    return img


def ev_treaty():
    s = SC["treaty"]["start"]
    sfx(s, "whoosh_c", -3)
    sfx(cue("treaty", "1881"), "paper", -3)
    sfx(cue("treaty", "argentina"), "pop")
    sfx(cue("treaty", "border") - 0.1, "riser", -9)
    sfx(cue("treaty", "coast"), "pop_b")
    sfx(cue("treaty", "plains"), "pop")


def s_war(t, canvas, d):
    s, e = SC["war"]["start"], SC["war"]["end"]
    c_war, c_peru, c_bol, c_des, c_nit, c_won = (cue("war", "war"), cue("war", "peru"), cue("war", "bolivia"),
                                                 cue("war", "desert"), cue("war", "nitrates"), cue("war", "won"))
    cam = G.cam_path(t, [(s, G.Cam(-66.5, -39.5, 1780), 0), (s + 1.0, C_WAR, 0), (e, G.Cam(-67.8, -20.8, 3150), 0)])
    pa, ba = G.ramp(t, c_peru - 0.1), G.ramp(t, c_bol - 0.1)
    pulse = 0.5 + 0.5 * math.sin((t - c_des) * 10) if t > c_des else 0
    extra = [(BOLIVIA_COAST, G.BLUE, ba, None), (PERU_SOUTH, G.GREEN, pa, None)]
    if t > c_des:
        extra += [(BOLIVIA_COAST + PERU_SOUTH, G.GOLD, 0.25 + 0.4 * pulse, G.GOLD)]
    img = map_frame(cam, {"Chile": (G.RED, 1), "Peru": (G.GREEN, pa), "Bolivia": (G.BLUE, ba)}, ["Chile"], extra)
    title(canvas, t - c_war, "WAR OF THE PACIFIC", t, e - 0.2)
    G.pop(canvas, t - (c_war + 0.25), G.sprite("label", "1879 – 1884", size=36, fg=G.BLACK, bg=G.GOLD), (540, 335))
    G.pop(canvas, t - c_peru, G.sprite("label", "PERU", size=40, flag_name="Peru"), P(cam, -74.5, -12.5))
    G.pop(canvas, t - c_bol, G.sprite("label", "BOLIVIA", size=40, flag_name="Bolivia"), P(cam, -64.2, -16.5))
    G.pop(canvas, t - c_nit, G.sprite("label", "NITRATES", size=40, fg=G.BLACK, bg=G.GOLD), (P(cam, -74.6, -22.5)[0] - 30, P(cam, -74.6, -22.5)[1]))
    G.pop(canvas, t - (c_won - 0.05), G.sprite("big", "CHILE WINS", size=120, fill=G.WHITE, stroke=(120, 10, 10)), (540, 1180))
    return img


def ev_war():
    s = SC["war"]["start"]
    sfx(s, "whoosh", -3)
    sfx(s + 0.3, "drums", -10)
    sfx(cue("war", "peru"), "pop")
    sfx(cue("war", "bolivia"), "pop")
    sfx(cue("war", "nitrates"), "ding", -8)
    sfx(cue("war", "won") - 0.05, "impact", -1)


def s_landlocked(t, canvas, d):
    s, e = SC["landlocked"]["start"], SC["landlocked"]["end"]
    c_push, c_lost = cue("landlocked", "pushed"), cue("landlocked", "coastline")
    cam = G.cam_path(t, [(s, G.Cam(-67.8, -20.8, 3150), 0), (e, G.Cam(-67.0, -19.5, 3400), 0)])
    conv = G.ramp(t, c_push, 0.8)
    col_b = tuple(int(G.BLUE[i] * (1 - conv) + G.RED[i] * conv) for i in range(3))
    col_p = tuple(int(G.GREEN[i] * (1 - conv) + G.RED[i] * conv) for i in range(3))
    shake = 7 * math.sin(t * 90) * max(0, 1 - (t - c_lost) / 0.4) if t > c_lost else 0
    img = map_frame(cam, {"Chile": (G.RED, 1), "Peru": (G.GREEN, 0.9), "Bolivia": (G.BLUE, 1)}, ["Chile", "Bolivia"],
                    [(BOLIVIA_COAST, col_b, 1, G.WHITE if conv < 1 else None), (PERU_SOUTH, col_p, 1, None)])
    if shake:
        img = np.roll(img, int(shake), axis=1)
    p = G.ramp(t, c_push - 0.05, 0.6)
    G.arrow(d, P(cam, -71.3, -25.5), P(cam, -71.2, -19.5), G.WHITE, 12, p, dotted=True)
    G.pop(canvas, t - (c_lost + 0.05), G.sprite("big", "LANDLOCKED", size=120, fill=G.WHITE, stroke=(20, 50, 140)), P(cam, -64.5, -16.2))
    return img


def ev_landlocked():
    sfx(cue("landlocked", "pushed"), "whoosh_c", -6)
    sfx(cue("landlocked", "coastline"), "impact", -2)


def s_navy(t, canvas, d):
    s, e = SC["navy"]["start"], SC["navy"]["end"]
    c_navy, c_sea = cue("navy", "navy"), cue("navy", "sea")
    cam = G.cam_path(t, [(s, G.Cam(-67.0, -19.5, 3400), 0), (s + 0.9, C_NAVY, 0), (e, G.Cam(-67.5, -17.2, 3900), 0)])
    img = map_frame(cam, {"Chile": (G.RED, 1), "Bolivia": (G.BLUE, 1), "Peru": (G.GREEN, 0.6)}, ["Bolivia"], dim=0.6)
    G.pop(canvas, t - (c_navy - 0.05), G.sprite("big", "BOLIVIA STILL", size=100), (540, 1080))
    G.pop(canvas, t - (c_navy + 0.1), G.sprite("big", "HAS A NAVY", size=150, fill=G.GOLD), (540, 1210))
    tl = P(cam, -69.3, -15.8)
    G.pin(d, tl, (30, 90, 180), 14, t - (c_navy + 0.5))
    G.pop(canvas, t - (c_navy + 0.5), G.sprite("label", "LAKE TITICACA", size=34), (tl[0] - 20, tl[1] - 60))
    G.pop(canvas, t - c_sea, G.sprite("label", "DAY OF THE SEA  ·  MARCH 23", size=40, fg=G.WHITE, bg=(30, 90, 180)), (540, 260))
    return img


def ev_navy():
    s = SC["navy"]["start"]
    sfx(s, "whoosh_b", -3)
    sfx(cue("navy", "navy"), "scratch", -3)
    sfx(cue("navy", "navy") + 0.5, "pop_b")
    sfx(cue("navy", "sea"), "ding", -5)


def s_extremes(t, canvas, d):
    s, e = SC["extremes"]["start"], SC["extremes"]["end"]
    c_gl = cue("extremes", "glaciers")
    if t < c_gl - 0.05:
        ts = t - s
        img = G.photo(IMG / "atacama.jpg", ts, c_gl - s, zoom_in=True, focus=(0.55, 0.5))
        img = G.whip(img, ts)
        G.pop(canvas, ts - 0.15, G.sprite("label", "ATACAMA DESERT", size=46, fg=G.BLACK, bg=G.GOLD), (540, 300))
        G.pop(canvas, ts - 0.4, G.sprite("label", "DRIEST NON-POLAR DESERT", size=34), (540, 385))
    else:
        ts = t - (c_gl - 0.05)
        img = G.photo(IMG / "glacier.jpg", ts, e - c_gl + 0.05, zoom_in=False, focus=(0.5, 0.5))
        img = G.whip(img, ts, direction=-1)
        G.pop(canvas, ts - 0.1, G.sprite("label", "PATAGONIAN ICE FIELD", size=44, fg=G.WHITE, bg=(30, 110, 190)), (540, 300))
    return img


def ev_extremes():
    s = SC["extremes"]["start"]
    sfx(s, "whoosh", -2)
    sfx(cue("extremes", "glaciers") - 0.05, "whoosh_b", -2)
    sfx(cue("extremes", "glaciers"), "wind", -13)


def s_outro(t, canvas, d):
    s, e = SC["outro"]["start"], TOTAL
    cam = G.cam_path(t, [(s, G.Cam(-69.6, -37.4, 3300), 0), (s + 0.9, C_CHILE, 0), (e, G.Cam(-69.6, -37.4, 2200), 0)])
    img = G.whip(map_frame(cam, {"Chile": (G.RED, 1)}, ["Chile"]), t - s)
    G.pop(canvas, t - (cue("outro", "follow") + 0.05), G.sprite("label", "FOLLOW FOR MORE", size=54, fg=G.WHITE, bg=G.RED), (540, 300))
    G.pop(canvas, t - (cue("outro", "maps")), G.sprite("label", "MAPS THAT EXPLAIN THE WORLD", size=34), (540, 395))
    return img


def ev_outro():
    sfx(SC["outro"]["start"], "whoosh", -2)
    sfx(cue("outro", "follow"), "ding", -4)


SCENE_FN = {"hook": s_hook, "europe": s_europe, "question": s_question, "andes": s_andes, "pacific": s_pacific,
            "treaty": s_treaty, "war": s_war, "landlocked": s_landlocked, "navy": s_navy, "extremes": s_extremes, "outro": s_outro}
for fn in (ev_hook, ev_europe, ev_question, ev_andes, ev_pacific, ev_treaty, ev_war, ev_landlocked, ev_navy, ev_extremes, ev_outro):
    fn()


def frame(t):
    key = next((s["key"] for s in TL if s["start"] <= t < s["end"]), "outro")
    canvas = Image.new("RGBA", (G.W, G.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    img = SCENE_FN[key](t, canvas, d)
    img = G.vignette(img, 0.4)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    out.alpha_composite(canvas)
    return out.convert("RGB")
