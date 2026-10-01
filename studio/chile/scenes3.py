"""Chile v3: story + humor (chili gag, stickman skit, countryballs)."""

import json
import math
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import box as sbox

import chars as C
import gfx as G

HERE = Path(__file__).parent
V = json.loads((HERE / "out3" / "voice.json").read_text())
TL, WORDS = V["timeline"], V["words"]
TOTAL = TL[-1]["end"] + 0.4
SEG = {s["key"]: s for s in TL}
KEYS = [s["key"] for s in TL]
IMG = HERE / "imgs"
CHILI = Image.open(HERE / "assets" / "chili.png").convert("RGBA")


def st(k):
    return SEG[k]["start"]


def se(k):
    return SEG[k]["speech_end"]


def en(k):
    return SEG[k]["end"]


def _n(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def cue(k, token, nth=0, end=False):
    si = KEYS.index(k)
    hits = [w for w in WORDS if w["scene"] == si and _n(w["text"]).startswith(_n(token))]
    w = hits[min(nth, len(hits) - 1)]
    return w["end"] if end else w["start"]


SFX = []


def sfx(t, name, gain=0.0):
    SFX.append((round(t, 3), name, gain))


# ------------------------------------------------------------------ geography
C_G0 = G.Cam(10, 5, 430)
C_SA = G.Cam(-64, -24, 900)
C_CHILE = G.Cam(-69.6, -37.4, 2330)
C_EU = G.Cam(19.0, 50.4, 2150)
C_BEFORE = G.Cam(-71.2, -36.0, 3900)
C_SKIT = G.Cam(-72.3, -36.4, 16000)
C_RESIST = G.Cam(-70.8, -35.5, 3600)
C_TINY = G.Cam(-69.5, -31.5, 2300)
C_ANDES = G.Cam(-70.5, -32.0, 6000, tilt=0.26)
C_SOUTH = G.Cam(-68.5, -40.0, 1750)
C_WAR = G.Cam(-67.5, -20.8, 2900)
C_BOL = G.Cam(-66.0, -18.2, 3600)

CHILE_SRC, EU_DST = (-70.0, -36.7), (19.0, 50.3)
CHILE_EU = G.transplant(G.RINGS["Chile"], CHILE_SRC, EU_DST)
CENTRAL = G.clip_rings("Chile", (-80, -37.6, -60, -25.3))
MAPUCHE = G.clip_rings("Chile", (-80, -42.0, -60, -37.6))
SPAIN_VALLEY = G.clip_rings("Chile", (-80, -37.6, -60, -30.0))
_b = G.WORLD["Chile"].boundary.intersection(G.WORLD["Argentina"].boundary)
_ls = [_b] if _b.geom_type == "LineString" else [g for g in getattr(_b, "geoms", []) if g.geom_type == "LineString"]
BORDER = np.radians(np.array(sorted([p for ln in _ls for p in ln.coords], key=lambda p: -p[1])))
SPAIN_RED = (198, 11, 30)
YELLOW = (250, 205, 40)


@lru_cache(maxsize=256)
def chile_band(lat_top, lat_bot):
    return G.clip_rings("Chile", (-80, lat_bot, -60, lat_top))


def map_frame(cam, fills=None, outline=None, extra=None, dim=0.72):
    return G.compose(G.terrain(cam, dim), G.overlay(cam, fills, outline, extra))


def P(cam, lon, lat):
    return cam.pt(lon, lat)[0]


def title(canvas, t_since, text, y=250, size=52, bg=(18, 18, 26), fg=G.WHITE):
    G.pop(canvas, t_since, G.sprite("label", text, size=size, fg=fg, bg=bg), (540, y))


def big(canvas, t_since, text, xy, size=150, fill=G.WHITE, stroke=G.BLACK):
    G.pop(canvas, t_since, G.sprite("big", text, size=size, fill=fill, stroke=stroke), xy)


# ------------------------------------------------------------------ scenes
def s_hook(t, cv, d):
    cam = G.cam_path(t, [(0, C_G0, 0), (1.1, C_SA, 0), (st("hook_b") + 0.4, C_SA, 0), (en("hook_b"), G.Cam(-66, -30, 1350), 0)])
    c_this = cue("hook_b", "this")
    a = G.ramp(t, c_this, 0.3)
    img = map_frame(cam, {"Chile": (G.RED, a)}, ["Chile"] if a > 0.5 else None)
    # giant chili drops on Chile, then gets yanked away
    t_drop, t_yank = cue("hook_a", "chile") - 0.1, cue("hook_b", "no")
    if t_drop <= t < t_yank + 0.6:
        target = P(cam, -71.0, -36.0)
        H = 1150
        spr = CHILI.resize((int(CHILI.width * H / CHILI.height), H), Image.LANCZOS).rotate(-28, expand=True, resample=Image.BICUBIC)
        if t < t_drop + 0.35:  # fall with gravity, then bounce
            y = -700 + (target[1] + 700) * ((t - t_drop) / 0.35) ** 2
        elif t < t_yank:
            b = t - (t_drop + 0.35)
            y = target[1] - 60 * abs(math.sin(b * 9)) * math.exp(-b * 5)
        else:
            y = target[1] - (t - t_yank) ** 2 * 9000
        G.safe_composite(cv, spr, (target[0] - spr.width / 2 + 40, y - spr.height / 2))
    if t >= c_this:
        G.pop(cv, t - c_this, G.sprite("label", "CHILE", size=48, flag_name="Chile"), (P(cam, -64.5, -34)[0] + 60, P(cam, -64.5, -34)[1]))
    if t_yank <= t < c_this:
        big(cv, t - t_yank, "NOT THAT CHILI", (540, 330), 110, G.WHITE, (150, 10, 10))
    return img


def ev_hook():
    sfx(0.0, "whoosh", -2)
    sfx(cue("hook_a", "chile") - 0.12, "slide_down", -7)
    sfx(cue("hook_a", "chile") + 0.25, "thud", -2)
    sfx(cue("hook_b", "no"), "slide", -3)
    sfx(cue("hook_b", "this"), "pop", -2)


def s_long(t, cv, d):
    cam = G.cam_path(t, [(st("long"), G.Cam(-66, -30, 1350), 0), (st("long") + 0.9, C_CHILE, 0), (en("long"), G.Cam(-69.6, -37.4, 2420), 0)])
    img = map_frame(cam, {"Chile": (G.RED, 1)}, ["Chile"])
    c_long = cue("long", "long")
    if t > c_long - 0.1:
        k = G.ramp(t, c_long - 0.1, 0.45)
        spr = G.sprite("big", "LOOOOONG", size=150, fill=G.GOLD)
        rot = spr.rotate(90, expand=True)
        h = max(2, int(rot.height * (0.25 + 0.75 * k)))
        s2 = rot.resize((rot.width, h), Image.LANCZOS)
        x = P(cam, -64.5, -37)[0] + 60
        G.safe_composite(cv, s2, (x - s2.width / 2, 960 - h / 2))
    return img


def ev_long():
    sfx(st("long"), "whoosh_b", -3)
    sfx(cue("long", "long") - 0.1, "boing", -3)


def s_europe(t, cv, d):
    s, e = st("europe"), en("europe")
    c_eu, c_arc, c_afr, c_177 = cue("europe", "europe"), cue("europe", "arctic"), cue("europe", "africa"), cue("europe", "177")
    cam = G.cam_path(t, [(s, G.Cam(-69.6, -37.4, 2420), 0), (s + 1.0, C_EU, 0.72), (e, G.Cam(19.0, 50.4, 2250), 0)])
    drop = G.ramp(t, c_eu + 0.05, 0.3)
    rings = G.transplant(G.RINGS["Chile"], CHILE_SRC, (EU_DST[0], EU_DST[1] + 4 * (1 - drop)))
    img = map_frame(cam, extra=[(rings, G.RED, drop * 0.95, G.WHITE)])
    if t > c_arc - 0.1:
        pts = [P(cam, lon, 66.56) for lon in range(-30, 70, 2)]
        pr = G.ramp(t, c_arc - 0.1, 0.5)
        G.dashed_line(d, [(x + 3, y + 3) for x, y in pts], (0, 0, 0), 14, progress=pr)
        G.dashed_line(d, pts, G.GOLD, 11, progress=pr)
        G.pop(cv, t - c_arc, G.sprite("label", "ARCTIC CIRCLE", size=46), (P(cam, 36, 66.56)[0], P(cam, 36, 66.56)[1] - 50))
    if t > c_afr - 0.1:
        xy = P(cam, 20.1, 31.8)
        G.pin(d, xy, G.GOLD, t_since=t - c_afr)
        G.pop(cv, t - c_afr, G.sprite("label", "NORTH AFRICA", size=38), (xy[0] + 140, xy[1] + 60))
    if t > c_177 - 0.1:
        a, b = G.transplant([np.radians([[-71.7, -33.4], [-69.9, -33.4]])], CHILE_SRC, EU_DST)[0]
        pa, pb = cam.project(np.array([a, b]))[0]
        y = (pa[1] + pb[1]) / 2
        d.line([(pa[0] - 4, y), (pb[0] + 4, y)], fill=G.WHITE + (255,), width=6)
        G.pop(cv, t - c_177, G.sprite("label", "177 KM WIDE", size=40), (pa[0] - 170, y))
    return img


def ev_europe():
    sfx(st("europe"), "whoosh", -2)
    sfx(cue("europe", "europe") + 0.3, "thud", -4)
    sfx(cue("europe", "arctic"), "pop", -3)
    sfx(cue("europe", "africa"), "pop2", -3)
    sfx(cue("europe", "177"), "ding", -8)


def s_noodle(t, cv, d):
    s, e = st("noodle"), en("noodle")
    cam = G.cam_path(t, [(s, G.Cam(19.0, 50.4, 2250), 0), (s + 0.9, C_CHILE, 0.72), (e, G.Cam(-69.6, -37.4, 2600), 0)])
    img = map_frame(cam, {"Chile": (G.RED, 1)}, ["Chile"], dim=0.6)
    c = cue("noodle", "noodle")
    big(cv, t - (c - 0.1), "SHAPED LIKE", (540, 820), 110)
    big(cv, t - c, "A NOODLE?", (540, 960), 170, G.GOLD)
    return img


def ev_noodle():
    sfx(st("noodle"), "whoosh_c", -3)
    sfx(cue("noodle", "noodle"), "boing2", -4)


def s_before(t, cv, d):
    s = st("before")
    c_map, c_sp = cue("before", "mapuche"), cue("before", "spanish")
    cam = G.cam_path(t, [(s, G.Cam(-69.6, -37.4, 2600), 0), (s + 1.0, C_BEFORE, 0), (se("before"), G.Cam(-71.4, -36.2, 4300), 0),
                         (se("before") + 0.45, C_SKIT, 0)])
    ma = G.ramp(t, c_map - 0.1, 0.35)
    img = map_frame(cam, extra=[(MAPUCHE, YELLOW, 0.7 * ma, YELLOW if ma > 0.5 else None)])
    if t < se("before") + 0.1:
        title(cv, t - (s + 0.2), "500 YEARS AGO", 250)
        if t > c_map:
            xy = P(cam, -72.5, -39.8)
            G.pop(cv, t - c_map, G.sprite("label", "MAPUCHE", size=44, fg=G.BLACK, bg=YELLOW), (xy[0] + 40, xy[1] - 260))
            for i, lon in enumerate((-72.9, -72.3, -71.7)):
                p, gy = C.clip_pose("twist", t * 0.4 + i)
                C.stickman(cv, p, gy, P(cam, lon, -40)[0], P(cam, lon, -40)[1], 150, -1, "mapuche", alpha=ma)
        if t > c_sp - 0.1:
            p0, p1 = P(cam, -71.0, -27.5), P(cam, -70.8, -33.4)
            G.arrow(d, p0, p1, SPAIN_RED, 14, G.ramp(t, c_sp - 0.1, 0.6), dotted=True)
            G.pop(cv, t - c_sp, G.sprite("label", "SPAIN", size=44, fg=G.WHITE, bg=SPAIN_RED, flag_name="Spain"), (p0[0] + 120, p0[1] + 60))
    return img


def ev_before():
    sfx(st("before"), "whoosh_b", -3)
    sfx(cue("before", "mapuche"), "pop", -3)
    sfx(cue("before", "spanish"), "whoosh_c", -5)
    sfx(se("before") + 0.2, "whoosh", -2)


GROUND = 1330


def s_skit(t, cv, d):
    cam = C_SKIT
    img = map_frame(cam, dim=0.8)
    t0 = se("before") + 0.45                      # Spanish march in
    arrive = t0 + 1.0
    m_in0, m_in1 = se("sp1") + 0.05, se("sp1") + 0.9  # Mapuche walk in
    t_aim, t_bang = se("ma1") + 0.15, se("ma1") + 0.5
    t_plant = cue("sp2", "we") - 0.1
    # Spanish
    for i, (x_end, role_flag) in enumerate(((170, "Spain"), (420, None))):
        x = x_end - 420 * (1 - G.ease((t - t0) / (arrive - t0)))
        if t < arrive:
            p, gy = C.clip_pose("march", t - t0 + i * 0.3)
        elif role_flag and t >= t_plant:
            p, gy = C.PLANT, C.STAND_GROUND
        elif not role_flag and t_aim <= t < t_bang + 0.9:
            p, gy = C.AIM, C.STAND_GROUND
        else:
            p, gy = C.STAND, C.STAND_GROUND
        muzzle = C.stickman(cv, p, gy, x, GROUND, 430, 1, "spanish", flag_carry=role_flag,
                            gun=not role_flag, gun_aim=(not role_flag and t_aim <= t < t_bang + 0.9))
        if muzzle and t >= t_bang:
            C.flash(cv, muzzle, t - t_bang, 1.2)
            C.smoke(cv, muzzle, t - t_bang, 1.3, seed=4)
    # Mapuche
    for i, x_end in enumerate((730, 930)):
        if t < m_in0:
            continue
        k = G.ease((t - m_in0) / (m_in1 - m_in0))
        x = x_end + 420 * (1 - k)
        if t < m_in1:
            p, gy = C.clip_pose("walk", t - m_in0 + i * 0.4)
            tilt, alpha = 0.0, 1.0
        elif t < t_bang + 0.05:
            p, gy = C.clip_pose("wave", t - m_in1 + i * 0.5)
            tilt, alpha = 0.0, 1.0
        else:
            p, gy = C.STAND, C.STAND_GROUND
            tilt = -1.45 * G.ease((t - t_bang - 0.05) / 0.25)
            alpha = 1 - G.ramp(t, t_bang + 1.2, 0.4)
        C.stickman(cv, p, gy, x, GROUND, 430, -1, "mapuche", tilt=tilt, alpha=alpha)
        if t > t_bang + 1.1:
            C.smoke(cv, (x - 90, GROUND - 40), t - (t_bang + 1.1), 1.0, seed=10 + i)
    C.bubble(cv, t - (st("sp1") - 0.05), "Ah! What beautiful, EMPTY land!", (430, 830), (400, 560), 620, 58, t, se("sp1") + 0.4)
    C.bubble(cv, t - (st("ma1") - 0.05), "Hello! We live here.", (760, 830), (680, 560), 560, 58, t, se("ma1") + 0.2)
    C.bubble(cv, t - (st("sp2") - 0.05), "Now, WE live here.", (430, 830), (420, 560), 580, 64, t, en("sp2") + 0.3)
    if t_bang <= t < t_bang + 0.7:
        big(cv, t - t_bang, "BANG!", (600, 1500), 170, G.GOLD, (120, 20, 10))
    return img


def ev_skit():
    t0 = se("before") + 0.45
    sfx(t0, "footsteps", -10)
    sfx(se("sp1") + 0.05, "footsteps", -12)
    sfx(se("ma1") + 0.5, "musket", -9)
    sfx(se("ma1") + 0.6, "thud2", -6)
    sfx(cue("sp2", "we") - 0.1, "pop", -3)


def s_resist(t, cv, d):
    s, e = st("resist"), en("resist")
    c_sp = cue("resist", "spain")
    cam = G.cam_path(t, [(s, C_SKIT, 0), (s + 1.0, C_RESIST, 0), (e, G.Cam(-70.8, -35.5, 3300), 0)])
    pulse = 0.55 + 0.25 * math.sin((t - s) * 8)
    sa = G.ramp(t, c_sp - 0.1, 0.35)
    img = map_frame(cam, extra=[(MAPUCHE, YELLOW, pulse, YELLOW), (SPAIN_VALLEY, SPAIN_RED, 0.8 * sa, G.WHITE if sa > 0.5 else None)])
    xy = P(cam, -72.6, -40.2)
    G.pop(cv, t - (s + 0.3), G.sprite("label", "MAPUCHE", size=44, fg=G.BLACK, bg=YELLOW), (xy[0], xy[1] + 70))
    G.pop(cv, t - (cue("resist", "centuries")), G.sprite("label", "FOUGHT BACK FOR CENTURIES", size=34), (540, 250))
    if t > c_sp:
        xy2 = P(cam, -73.8, -33.5)
        G.pop(cv, t - c_sp, G.sprite("label", "SPAIN", size=44, fg=G.WHITE, bg=SPAIN_RED, flag_name="Spain"), (xy2[0] - 40, xy2[1]))
    return img


def ev_resist():
    sfx(st("resist"), "whoosh", -2)
    sfx(cue("resist", "centuries"), "pop2", -4)
    sfx(cue("resist", "spain"), "pop", -3)


def s_tiny(t, cv, d):
    s, e = st("tiny"), en("tiny")
    cam = G.cam_path(t, [(s, G.Cam(-70.8, -35.5, 3300), 0), (s + 1.0, C_TINY, 0), (e, G.Cam(-69.5, -31.5, 2450), 0)])
    a = G.ramp(t, cue("tiny", "chile") - 0.1, 0.35)
    img = map_frame(cam, extra=[(CENTRAL, G.RED, a, G.WHITE if a > 0.5 else None)])
    title(cv, t - cue("tiny", "independence"), "CHILE  ·  1818", 250)
    big(cv, t - cue("tiny", "tiny"), "TINY.", (760, 1180), 160, G.GOLD)
    return img


def ev_tiny():
    sfx(st("tiny"), "whoosh_c", -3)
    sfx(cue("tiny", "chile") - 0.1, "pop", -3)
    sfx(cue("tiny", "tiny"), "boing2", -5)


def _ball_pos_east(t, cam):
    """Chile ball: appears, rolls east, bonks into the Andes, bounces back."""
    home = np.array(P(cam, -71.3, -31.2))
    wall = np.array(P(cam, -70.2, -31.2))
    t_roll, t_bonk = se("ch1") + 0.15, se("ch1") + 0.75
    if t < t_roll:
        return home, 0.0
    if t < t_bonk:
        return home + (wall - home) * G.ease((t - t_roll) / (t_bonk - t_roll)), 0.0
    b = t - t_bonk
    back = min(1.0, b / 0.35)
    sq = 0.35 * math.exp(-b * 9) * math.cos(b * 30)
    return wall + (home - wall) * 0.45 * math.sin(back * math.pi / 2), sq


def s_ch1(t, cv, d):
    cam = G.Cam(-69.5, -31.5, 2450 + 0 * t)
    img = map_frame(cam, extra=[(CENTRAL, G.RED, 1, G.WHITE)])
    pos, sq = _ball_pos_east(t, cam)
    C.countryball(cv, "Chile", pos, 95, t, seed=3, squash=sq)
    C.bubble(cv, t - (st("ch1") - 0.05), "Time to grow! Let's go EAST!", (pos[0] + 40, pos[1] - 90), (560, 560), 560, 50, t, se("ch1") + 0.95)
    return img


def ev_ch1():
    sfx(st("ch1") - 0.05, "pop2", -4)
    sfx(se("ch1") + 0.15, "slide_up", -6)
    sfx(se("ch1") + 0.75, "boing", -1)


def s_andes(t, cv, d):
    s = st("andes")
    cam = G.cam_path(t, [(s, G.Cam(-69.5, -31.5, 2450), 0), (s + 1.1, C_ANDES, 0), (en("andes"), G.Cam(-70.4, -32.3, 6400, 0.28), 0)])
    img = map_frame(cam, extra=[(CENTRAL, G.RED, 0.45, None)])
    bp = G.ramp(t, cue("andes", "andes") - 0.2, 1.0)
    pts, vis = cam.project(BORDER)
    pts = [tuple(p) for p, v in zip(pts, vis) if v]
    if bp > 0:
        d.line(pts[: max(2, int(len(pts) * bp))], fill=G.ORANGE + (255,), width=10, joint="curve")
    xy = P(cam, -69.5, -30.0)
    G.pop(cv, t - cue("andes", "andes"), G.sprite("label", "THE ANDES", size=48, fg=G.WHITE, bg=(200, 80, 20)), (xy[0] + 130, xy[1]))
    G.pop(cv, t - cue("andes", "longest"), G.sprite("label", "LONGEST RANGE ON LAND", size=34), (540, 250))
    bpos = P(cam, -71.0, -31.8)
    C.countryball(cv, "Chile", bpos, 80, t, seed=3)
    return img


def ev_andes():
    sfx(st("andes"), "whoosh_b", -3)
    sfx(cue("andes", "andes"), "pop", -3)


def s_ch2(t, cv, d):
    cam = G.Cam(-70.4, -32.3, 6400, 0.28)
    img = map_frame(cam, extra=[(CENTRAL, G.RED, 0.45, None)])
    pts, vis = cam.project(BORDER)
    d.line([tuple(p) for p, v in zip(pts, vis) if v], fill=G.ORANGE + (255,), width=10, joint="curve")
    bpos = P(cam, -71.0, -31.8)
    C.countryball(cv, "Chile", bpos, 80 + 20 * G.ramp(t, st("ch2"), 0.3), t, seed=3, mood="sad", look=(0.0, 0.8))
    C.bubble(cv, t - (st("ch2") - 0.05), "Okay. South it is...", (bpos[0] + 30, bpos[1] - 90), (560, 600), 500, 50, t, en("ch2"))
    return img


def ev_ch2():
    sfx(st("ch2") + 0.15, "sadtrombone", -6)


def s_south(t, cv, d):
    s, e = st("south"), en("south")
    c_1881 = cue("south", "1881")
    cam = G.cam_path(t, [(s, G.Cam(-70.4, -32.3, 6400, 0.28), 0), (s + 1.0, C_SOUTH, 0), (e, G.Cam(-67.5, -41, 1700), 0)])
    grow = G.ramp(t, s + 0.8, 2.8)
    lat_bot = -37.6 - 18.5 * grow
    arg = G.ramp(t, c_1881 + 0.3, 0.5)
    img = map_frame(cam, {"Argentina": (G.BLUE, 0.6 * arg)}, None,
                    [(CENTRAL, G.RED, 1, None), (chile_band(-37.6, round(lat_bot, 1)), G.RED, 1, G.WHITE)])
    ball_lat = -33 + (lat_bot + 3 + 33) * 1.0 if grow < 1 else -50
    C.countryball(cv, "Chile", P(cam, -73.8, max(ball_lat, -50)), 65, t, seed=3, squash=0.08 * math.sin(t * 20) if grow < 1 else 0)
    if t > c_1881 - 0.1:
        bp = G.ramp(t, c_1881, 1.4)
        pts, vis = cam.project(BORDER)
        pts = [tuple(p) for p, v in zip(pts, vis) if v]
        d.line(pts[: max(2, int(len(pts) * bp))], fill=G.GOLD + (255,), width=8, joint="curve")
        title(cv, t - c_1881, "1881  ·  BORDER TREATY", 250)
        xy = P(cam, -64.5, -36)
        G.pop(cv, t - (c_1881 + 0.3), G.sprite("label", "ARGENTINA", size=40, flag_name="Argentina"), xy)
    return img


def ev_south():
    sfx(st("south"), "whoosh", -2)
    sfx(st("south") + 0.8, "slide_down", -6)
    sfx(cue("south", "1881"), "paper", -3)
    sfx(cue("south", "argentina"), "pop", -3)


def s_north(t, cv, d):
    s, e = st("north"), en("north")
    c_peru, c_bol, c_won, c_des = cue("north", "peru"), cue("north", "bolivia"), cue("north", "won"), cue("north", "desert")
    cam = G.cam_path(t, [(s, G.Cam(-67.5, -41, 1700), 0), (s + 1.0, C_WAR, 0), (e, G.Cam(-67.5, -21.2, 3050), 0)])
    grow = G.ramp(t, c_won, 0.7)
    lat_top = -25.3 + 7.9 * grow
    img = map_frame(cam, {"Peru": (G.GREEN, G.ramp(t, c_peru - 0.1)), "Bolivia": (G.BLUE, G.ramp(t, c_bol - 0.1))}, None,
                    [(chile_band(-25.3, -60), G.RED, 1, None), (chile_band(round(lat_top, 1), -25.3), G.RED, 1, G.WHITE),
                     (G.clip_rings("Chile", (-80, -24.0, -60, -21.4)), G.BLUE, (1 - grow) * G.ramp(t, c_bol), None),
                     (G.clip_rings("Chile", (-80, -21.4, -60, -17.0)), G.GREEN, (1 - grow) * G.ramp(t, c_peru), None)])
    title(cv, t - (s + 0.4), "WAR OF THE PACIFIC", 250)
    G.pop(cv, t - (s + 0.6), G.sprite("label", "1879 – 1884", size=36, fg=G.BLACK, bg=G.GOLD), (540, 335))
    if t > c_des:
        xy = P(cam, -74.0, -22.4)
        G.pop(cv, t - c_des, G.sprite("label", "NITRATES", size=38, fg=G.BLACK, bg=G.GOLD), (xy[0] - 10, xy[1]))
    C.countryball(cv, "Peru", P(cam, -73.0, -12.2), 75, t, seed=8, alpha=G.ramp(t, c_peru - 0.1, 0.2)) if t > c_peru - 0.1 else None
    C.countryball(cv, "Bolivia", P(cam, -64.8, -16.8), 80, t, seed=5, alpha=G.ramp(t, c_bol - 0.1, 0.2),
                  mood="angry" if t > c_won else "normal") if t > c_bol - 0.1 else None
    if t > c_won:
        jump = abs(math.sin((t - c_won) * 9)) * 40 * math.exp(-(t - c_won) * 2)
        xy = P(cam, -70.3, -27.0)
        C.countryball(cv, "Chile", (xy[0], xy[1] - jump), 70, t, seed=3)
        big(cv, t - c_won, "CHILE WINS", (540, 1180), 120, G.WHITE, (120, 10, 10))
    return img


def ev_north():
    sfx(st("north"), "whoosh_c", -3)
    sfx(cue("north", "peru"), "pop", -3)
    sfx(cue("north", "bolivia"), "pop2", -3)
    sfx(cue("north", "won"), "tada", -4)


def s_bo1(t, cv, d):
    cam = G.cam_path(t, [(st("bo1") - 0.1, G.Cam(-67.5, -21.2, 3050), 0), (st("bo1") + 0.5, C_BOL, 0)])
    img = map_frame(cam, {"Bolivia": (G.BLUE, 1), "Peru": (G.GREEN, 0.6)}, None, [(chile_band(-17.4, -60), G.RED, 1, None)], dim=0.6)
    xy = P(cam, -65.0, -17.0)
    R = 80 + 70 * G.ramp(t, st("bo1") - 0.1, 0.35)
    look = (-0.9, 0.5) if t < st("bo1") + 0.6 else None
    C.countryball(cv, "Bolivia", xy, R, t, seed=5, mood="angry", look=look, squash=0.1 * math.sin(t * 25) * (t < se("bo1")))
    C.bubble(cv, t - st("bo1"), "Hey! Where did my OCEAN go?!", (xy[0] - 60, xy[1] - R * 1.1), (520, 560), 560, 52, t, en("bo1") + 0.2)
    return img


def ev_bo1():
    sfx(st("bo1") - 0.1, "scratch", -4)


def s_navy(t, cv, d):
    s, e = st("navy"), en("navy")
    c_navy, c_sea = cue("navy", "navy"), cue("navy", "sea")
    cam = G.cam_path(t, [(s, C_BOL, 0), (e, G.Cam(-67.0, -17.0, 3900), 0)])
    img = map_frame(cam, {"Bolivia": (G.BLUE, 1), "Peru": (G.GREEN, 0.6)}, ["Bolivia"], [(chile_band(-17.4, -60), G.RED, 1, None)], dim=0.6)
    big(cv, t - (c_navy - 0.25), "BOLIVIA STILL", (540, 1060), 100)
    big(cv, t - (c_navy - 0.05), "HAS A NAVY", (540, 1190), 150, G.GOLD)
    tl = P(cam, -69.3, -15.8)
    G.pin(d, tl, (30, 90, 180), 14, t - (c_navy + 0.4))
    G.pop(cv, t - (c_navy + 0.4), G.sprite("label", "LAKE TITICACA", size=34), (tl[0] - 20, tl[1] - 60))
    G.pop(cv, t - c_sea, G.sprite("label", "DAY OF THE SEA  ·  MARCH 23", size=40, fg=G.WHITE, bg=(30, 90, 180)), (540, 260))
    C.countryball(cv, "Bolivia", (860, 1640), 95, t, seed=5, mood="sad" if t > c_sea else "angry")
    return img


def ev_navy():
    sfx(cue("navy", "navy") - 0.05, "impact", -6)
    sfx(cue("navy", "navy") + 0.4, "pop", -4)
    sfx(cue("navy", "sea"), "ding", -6)


def s_outro(t, cv, d):
    s, e = st("outro"), TOTAL
    cam = G.cam_path(t, [(s, G.Cam(-67.0, -17.0, 3900), 0), (s + 1.0, C_CHILE, 0.5), (e, G.Cam(-69.6, -37.4, 2200), 0)])
    img = map_frame(cam, {"Chile": (G.RED, 1)}, ["Chile"])
    c_long = cue("outro", "longer")
    if t > c_long - 0.1:
        k = G.ramp(t, c_long - 0.1, 0.45)
        spr = G.sprite("big", "LONGER.", size=150, fill=G.GOLD).rotate(90, expand=True)
        h = max(2, int(spr.height * (0.25 + 0.75 * k)))
        G.safe_composite(cv, spr.resize((spr.width, h), Image.LANCZOS), (P(cam, -64.5, -37)[0] - 20, 960 - h / 2))
    C.countryball(cv, "Chile", P(cam, -77.5, -30), 85, t, seed=3, look=(0.7, -0.2) if t > c_long else None)
    G.pop(cv, t - cue("outro", "follow"), G.sprite("label", "FOLLOW FOR MORE", size=54, fg=G.WHITE, bg=G.RED), (540, 260))
    return img


def ev_outro():
    sfx(st("outro"), "whoosh", -2)
    sfx(cue("outro", "longer") - 0.1, "boing", -4)
    sfx(cue("outro", "follow"), "ding", -5)


SCENES = [("hook_a", s_hook), ("hook_b", s_hook), ("long", s_long), ("europe", s_europe), ("noodle", s_noodle),
          ("before", s_before), ("sp1", s_skit), ("ma1", s_skit), ("sp2", s_skit), ("resist", s_resist), ("tiny", s_tiny),
          ("ch1", s_ch1), ("andes", s_andes), ("ch2", s_ch2), ("south", s_south), ("north", s_north), ("bo1", s_bo1),
          ("navy", s_navy), ("outro", s_outro)]
SCENE_FN = dict(SCENES)
for fn in (ev_hook, ev_long, ev_europe, ev_noodle, ev_before, ev_skit, ev_resist, ev_tiny, ev_ch1, ev_andes, ev_ch2,
           ev_south, ev_north, ev_bo1, ev_navy, ev_outro):
    fn()


def frame(t):
    key = next((s["key"] for s in TL if s["start"] <= t < s["end"]), "outro")
    fn = SCENE_FN[key]
    if key == "before" and t >= se("before") + 0.45:
        fn = s_skit
    cv = Image.new("RGBA", (G.W, G.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    img = G.vignette(fn(t, cv, d), 0.4)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    out.alpha_composite(cv)
    return out.convert("RGB")
