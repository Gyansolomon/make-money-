"""Synthesize the instrumental, mix it with the vocal, and write the analysis the renderer reads.

Everything is generated here (no samples), so the beat grid, sections and drum onsets are exact.
Outputs: audio/song.mp3, data/audio.json, work/stems/*.wav
Run after vocals.py and align.py:  python tools/music.py
"""

import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
SR = 44100
rng = np.random.default_rng(7)

sched = json.load(open(WORK / "schedule.json"))
BPM = sched["bpm"]
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = sched["duration"]
N = int(DUR * SR)

# --------------------------------------------------------------------------- arrangement
# sections start on the bar of the line that opens them; the outro is the last two bars
marks = [(s["section"], round(s["grid"] / BAR)) for s in sched["lines"] if s["section"]]
marks[0] = ("intro", 0)
marks.append(("outro", sched["bars"] - 2))
SECTIONS = []
for (name, b0), (_, b1) in zip(marks, marks[1:] + [("end", sched["bars"])]):
    SECTIONS.append({"name": name, "start": round(b0 * BAR, 3), "end": round(b1 * BAR, 3), "b0": b0, "b1": b1})
SEC_AT = {}
for s in SECTIONS:
    for b in range(s["b0"], s["b1"]):
        SEC_AT[b] = s["name"]
print(" | ".join(f"{s['name']} {s['b0']}-{s['b1']}" for s in SECTIONS))

# D minor: i VI III VII, and a tenser loop for the dry parts
NOTE = lambda m: 440.0 * 2 ** ((m - 69) / 12)
PROG_MAIN = [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]]  # Dm Bb F C
PROG_DRY = [[50, 53, 57], [43, 46, 50], [46, 50, 53], [45, 49, 52]]   # Dm Gm Bb A
PROG_LIFT = [[46, 50, 53], [53, 57, 60], [48, 52, 55], [50, 53, 57]]  # Bb F C Dm


def chord(bar):
    s = SEC_AT.get(bar, "outro")
    prog = PROG_DRY if s in ("break", "verse3", "bridge", "riser") else PROG_LIFT if s in ("drop", "regrow", "hook2") else PROG_MAIN
    return prog[bar % 4]


# --------------------------------------------------------------------------- instruments
def env_exp(n, decay):
    return np.exp(-np.arange(n) / SR * decay)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def kick(v=1.0):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 7.5)
    click = hp(rng.standard_normal(n), 2000) * env_exp(n, 220) * 0.25
    return np.tanh(1.6 * (body + click)) * v


def clap(v=1.0):
    n = int(0.3 * SR)
    x = bp(rng.standard_normal(n), 900, 3200)
    e = np.zeros(n)
    for d in (0.0, 0.011, 0.022):
        i = int(d * SR)
        e[i:] += env_exp(n - i, 70 if d < 0.02 else 18)
    return x * e * 0.55 * v


def shaker(v=1.0):
    n = int(0.07 * SR)
    a = np.minimum(1, np.arange(n) / (0.006 * SR))
    return lp(hp(rng.standard_normal(n), 6000), 9000) * a * env_exp(n, 70) * 0.13 * v


def bell(f, v=1.0):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    x = sum(w * np.sin(2 * np.pi * f * r * t) for r, w in ((1, 1), (2.76, 0.45), (5.4, 0.2), (8.9, 0.08)))
    return x * env_exp(n, 9) * 0.16 * v


def tom(f0, v=1.0):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.5 * np.exp(-t * 18))  # talking-drum style bend
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 9) * 0.5 * v


def bass_note(m, length, v=1.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = NOTE(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)
    a = np.minimum(1, t / 0.008) * np.exp(-t * 2.2)
    rel = np.minimum(1, (length - t) / 0.03)
    return np.tanh(1.4 * x * a * rel) * 0.5 * v


def pad_chord(notes, length, bright=1200):
    n = int(length * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in notes:
        for det in (-0.12, 0.12):
            f = NOTE(m + 12) * 2 ** (det / 12)
            x += 2 * ((t * f) % 1) - 1  # saw
    x = lp(x, bright, 2) / (len(notes) * 2)
    a = np.minimum(1, t / 0.35) * np.minimum(1, (length - t) / 0.3)
    return x * a * 0.5


def pluck(m, v=1.0):
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    f = NOTE(m)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 20)
    return x * env_exp(n, 7) * 0.18 * v


def noise_sweep(length, f0, f1, v=1.0):
    n = int(length * SR)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    k = 24
    for j in range(k):  # piecewise band-pass sweep
        a, b = j * n // k, (j + 1) * n // k
        fc = f0 * (f1 / f0) ** (j / (k - 1))
        out[a:b] = bp(x[max(0, a - 2000):b], fc * 0.7, min(fc * 1.4, SR / 2 - 100))[-(b - a):]
    return out * np.linspace(0, 1, n) ** 2 * v


def wind(length, v=1.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * t) * np.sin(2 * np.pi * 0.07 * t + 1)
    return bp(rng.standard_normal(n), 300, 1400) * lfo * 0.18 * v


# --------------------------------------------------------------------------- render stems
stems = {k: np.zeros(N + SR) for k in ("drums", "bass", "other")}
onsets = {"kick": [], "snare": [], "hat": []}


def put(stem, x, t, kind=None, strength=1.0):
    i = int(t * SR)
    if i >= N:
        return
    j = min(N + SR, i + len(x))
    stems[stem][i:j] += x[: j - i]
    if kind:
        onsets[kind].append([round(t, 3), round(float(strength), 3)])


# 12/8-flavoured bell over 4/4 (16th grid positions): the classic West African standard pattern
BELL16 = [0, 2, 5, 7, 9, 12, 14]
BASS16 = [(0, 3, 0), (3, 2, 0), (6, 2, 7), (10, 2, 0), (12, 2, 5), (14, 2, 7)]  # (pos, len16, interval)
S16 = BEAT / 4

for bar in range(sched["bars"]):
    t0 = bar * BAR
    sec = SEC_AT.get(bar, "outro")
    ch = chord(bar)
    root = ch[0] - 12
    last_bar_of_sec = SEC_AT.get(bar + 1) != sec
    rain_stops = sec == "verse2" and last_bar_of_sec  # "Then the rain stops": the beat cuts out
    groove = sec in ("verse1", "verse2", "drop", "regrow", "hook2") and not rain_stops
    half = sec == "verse3"
    # pads everywhere except the riser's last bar and the hook1 hit
    bright = {"break": 700, "bridge": 900, "drop": 2200, "regrow": 2600, "hook2": 2600, "outro": 1500}.get(sec, 1300)
    if not (sec == "riser"):
        put("other", pad_chord(ch, BAR + 0.25, bright) * (1.1 if sec in ("break", "verse3", "bridge") else 0.8 if sec in ("intro", "outro") else 0.6), t0)
    # bell: intro softly from bar 1, grooves, outro
    if sec in ("intro", "verse1", "verse2", "drop", "regrow", "hook2", "outro") and not (sec == "intro" and bar == 0):
        for p in BELL16:
            hi = p in (0, 7, 12)
            put("other", bell(NOTE(81 if hi else 76), 0.9 if hi else 0.6) * (0.6 if sec in ("intro", "outro") else 1), t0 + p * S16)
    # shaker
    if (groove or sec in ("intro", "verse3", "bridge") and bar > 0) and not rain_stops:
        for p in range(16):
            acc = 1.0 if p % 4 == 2 else 0.55 if p % 2 == 0 else 0.35
            if sec == "bridge" and p % 4 != 2:
                continue
            put("drums", shaker(acc), t0 + p * S16 + (0.008 if p % 2 else 0), "hat", acc)
    # kick + clap
    if groove:
        for p in (0, 6, 8, 11) if sec in ("drop", "regrow") else (0, 6, 8):
            put("drums", kick(1.0 if p in (0, 8) else 0.75), t0 + p * S16, "kick", 1.0 if p in (0, 8) else 0.7)
        for p in (4, 12):
            put("drums", clap(), t0 + p * S16, "snare", 0.9)
    elif half:
        put("drums", kick(), t0, "kick", 1.0)
        put("drums", clap(0.8), t0 + 8 * S16, "snare", 0.8)
    elif sec == "bridge":  # heartbeat
        put("drums", kick(0.55), t0, "kick", 0.5)
        put("drums", kick(0.4), t0 + 3 * S16, "kick", 0.35)
    # talking drum fills on the last bar of a groove section, and through the drop
    if (groove and last_bar_of_sec) or sec == "drop":
        for p, f in ((10, 180), (12, 150), (13, 130), (14, 210), (15, 160)):
            put("drums", tom(f, 0.8), t0 + p * S16, "snare", 0.5)
    # bass
    if (groove or half or sec == "outro") and not rain_stops:
        for p, ln, iv in BASS16:
            if half and p not in (0, 6, 10):
                continue
            push = (0.012 if p in (3, 10) else -0.004) + rng.uniform(-0.004, 0.004)
            put("bass", bass_note(root + iv, ln * S16 * 0.95, (1.0 if p == 0 else 0.78) * rng.uniform(0.9, 1.0)), t0 + p * S16 + push)
    elif sec in ("break", "bridge", "intro", "hook1"):
        put("bass", bass_note(root, BAR * 0.95, 0.5), t0)
    # plucked arpeggio when the forest comes back
    if sec in ("regrow", "hook2"):
        arp = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24]
        for p in range(0, 16, 2):
            put("other", pluck(arp[(p // 2) % 4], 0.9 if p % 4 == 0 else 0.6), t0 + p * S16)
    # wind in the break
    if sec == "break":
        put("other", wind(BAR + 0.3, 1.0), t0)

# hits and transitions
first_line = sched["lines"][0]
hook1 = next(s for s in sched["lines"] if s["section"] == "hook1")
riser = next(s for s in SECTIONS if s["name"] == "riser")
drop = next(s for s in SECTIONS if s["name"] == "drop")
brk = next(s for s in SECTIONS if s["name"] == "break")
v1 = next(s for s in SECTIONS if s["name"] == "verse1")
put("other", noise_sweep(v1["start"] - hook1["grid"] - BAR, 800, 6000, 0.35), hook1["grid"] + BAR)  # lift into the groove
put("other", noise_sweep(riser["end"] - riser["start"] + BAR - BEAT, 400, 9000, 0.45), riser["start"] - BAR)
for p in range(12):  # snare roll, silent on the last beat before the drop
    v = 0.25 + 0.6 * p / 11
    put("drums", clap(v * 0.5), riser["start"] + p * S16, "snare", v * 0.6)
def crash(length, v=1.0):
    n = int(length * SR)
    return hp(rng.standard_normal(n), 4000) * env_exp(n, 1.6) * 0.25 * v
rain_t = brk["start"] - BAR
put("other", crash(2.0, 0.8)[::-1][int(0.6 * SR):], rain_t - 1.4)  # reverse swell
put("drums", crash(3.0, 0.9), rain_t, "hat", 0.6)
end_t = SECTIONS[-1]["start"]
put("other", pad_chord([50, 53, 57, 62], 2 * BAR, 1500) * 0.9, end_t)
for d, m in ((0, 81), (0.15, 76), (0.3, 74)):
    put("other", bell(NOTE(m), 1.0), end_t + d)

# impacts: the drop, the break (the rain stops), the final hook
for t, v in ((drop["start"], 1.0), (brk["start"], 0.7)):
    boom = np.sin(2 * np.pi * 38 * np.arange(int(1.6 * SR)) / SR) * env_exp(int(1.6 * SR), 2.5)
    put("drums", (boom + hp(rng.standard_normal(len(boom)), 3000) * env_exp(len(boom), 12) * 0.3) * 0.8 * v, t, "kick", v)

# --------------------------------------------------------------------------- mix
voc, vsr = sf.read(WORK / "vocal.wav", dtype="float64")
voc = np.interp(np.arange(0, len(voc), vsr / SR), np.arange(len(voc)), voc)
vocal = np.zeros(N + SR)
vocal[: min(len(voc), N + SR)] = voc[: N + SR]
vocal = hp(vocal, 90)
# de-esser: compress the 5-9 kHz band when it spikes
ess = bp(vocal, 4500, 10000)
eenv = np.convolve(np.abs(ess), np.ones(int(0.004 * SR)) / int(0.004 * SR), mode="same")
thr = np.percentile(eenv[eenv > 1e-5], 60)
vocal = vocal - ess * (1 - np.minimum(1, thr / (eenv + 1e-9)))
vocal = vocal - bp(vocal, 6000, 12000) * 0.3  # gentle high shelf
# short plate-ish reverb, low in the mix
ir_n = int(0.8 * SR)
ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR * 7.5)
ir = lp(hp(ir, 300), 6000)
wet = fftconvolve(vocal, ir)[: len(vocal)]
vocal = vocal + wet / (np.abs(wet).max() + 1e-9) * np.abs(vocal).max() * 0.12

venv = np.convolve(np.abs(vocal), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
duck = 1 - 0.35 * np.clip(venv / (venv.max() * 0.15), 0, 1)
kenv = np.zeros(N + SR)
for t, s in onsets["kick"]:
    i = int(t * SR)
    n = int(0.18 * SR)
    kenv[i:i + n] = np.maximum(kenv[i:i + n], s * np.linspace(1, 0, min(n, len(kenv) - i)))
side = 1 - 0.35 * kenv

drums = stems["drums"] * 0.9
bass = stems["bass"] * 0.8 * side
bass = bass - bp(bass, 95, 150) * 0.4  # less boom where the voice's chest sits
other = stems["other"] * 0.9 * side
# stereo: Haas-widened pads/bells, decorrelated room on the music, a long throw where the rain stops
def room(x, decay, seed):
    r = np.random.default_rng(seed)
    n = int(decay * 1.2 * SR)
    ir = lp(hp(r.standard_normal(n) * np.exp(-np.arange(n) / SR * (6.9 / decay)), 250), 7000)
    w = fftconvolve(x, ir)[: len(x)]
    return w / (np.abs(w).max() + 1e-9)
haas = int(0.011 * SR)
otherR = np.concatenate([np.zeros(haas), other[:-haas]])
dry = drums + bass
throw = np.zeros(N + SR)
rain = next(s for s in SECTIONS if s["name"] == "break")["start"] - BAR  # the dry bar starts here
i0, i1 = int((rain - BEAT) * SR), int(rain * SR)
throw[i0:i1] = (drums + other)[i0:i1]
mus_mono = dry + other
lvl = np.abs(mus_mono).max()
chans = []
for k, oth in enumerate((other, otherR)):
    m = dry + oth
    m = m + room(m, 1.4, 11 + k) * lvl * 0.10 + room(throw, 2.4, 21 + k) * lvl * 0.35
    m = m - bp(m, 200, 500) * 0.3  # about -3 dB where the voice's warmth sits
    chans.append(m * duck + vocal * 1.6)
mix = np.stack(chans, axis=1)
fade = np.ones(N + SR)
fade[N - int(1.5 * SR):N] = np.linspace(1, 0, int(1.5 * SR))
fade[N:] = 0
mix *= fade[:, None]
mix = mix[:N]
mix /= np.abs(mix).max() + 1e-9

(WORK / "stems").mkdir(exist_ok=True)
for k, x in (("drums", drums), ("bass", bass), ("other", other), ("vocal", vocal)):
    sf.write(WORK / "stems" / f"{k}.wav", (x[:N] / (np.abs(x).max() + 1e-9) * 0.9).astype(np.float32), SR)
sf.write(WORK / "mix.wav", (mix * 0.95).astype(np.float32), SR)
(ROOT / "audio").mkdir(exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(WORK / "mix.wav"), "-af", "loudnorm=I=-14:TP=-1.0:LRA=11",
                "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "256k", str(ROOT / "audio" / "song.mp3")], check=True)

# --------------------------------------------------------------------------- analysis for the renderer
FPS = 100
hop = SR // FPS


def envelope(x):
    n = len(x) // hop
    r = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    r = np.convolve(r, np.ones(3) / 3, mode="same")
    return np.round(r / (np.percentile(r, 99) + 1e-9), 3).clip(0, 1.2).tolist()


lyr = json.load(open(ROOT / "data" / "lyrics.json"))
mono = mix.mean(axis=1)
beats = [round(i * BEAT, 3) for i in range(int(DUR / BEAT) + 1)]
analysis = {
    "duration": round(DUR, 3), "bpm": BPM, "beat_period": round(BEAT, 5), "time_signature": 4,
    "beats": beats, "downbeats": beats[::4],
    "sections": [{k: s[k] for k in ("name", "start", "end")} for s in SECTIONS],
    "fps": FPS,
    "rms": envelope(mono), "low": envelope(lp(mono, 150)), "mid": envelope(bp(mono, 150, 2500)), "high": envelope(hp(mono, 2500)),
    "vocal": envelope(vocal[:N]), "drums": envelope(drums[:N]), "bass": envelope(bass[:N]), "other": envelope(other[:N]),
    "onsets": {**{k: sorted(v) for k, v in onsets.items()},
               "vocal": [[w["start"], 1.0] for l in lyr["lines"] for w in l["words"]]},
    "notes": "Generated by tools/music.py: exact grid at 100 BPM, onsets are the synthesized hits.",
}
json.dump(analysis, open(ROOT / "data" / "audio.json", "w"))
print(f"song.mp3 {DUR:.1f}s, {len(onsets['kick'])} kicks, {len(onsets['snare'])} snares")
