import sys, subprocess, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from moneymaker.media import ffmpeg_bin
SR = 48000
A = "../chile/assets/"
# (text, pause_after, sfx_at_start, sfx_at_end)
LINES = [
 ("Two hundred million trees. In one of the driest places on Earth.", 0.15, "whoosh", None),
 ("And not a single one was planted.", 0.55, None, "impact"),
 ("Fifty years ago, this land was dying.", 0.3, "whoosh_b", None),
 ("South of the Sahara lies the Sahel. For centuries, farmers grew their crops right next to the trees. Until they made one small decision.", 0.35, None, None),
 ("They cut them down. For farmland. For firewood. Nobody thought it mattered.", 0.35, "chop", None),
 ("Then, in the early nineteen seventies, the rain stopped.", 0.25, None, None),
 ("And suddenly, everyone found out what those trees had been doing all along.", 0.3, None, None),
 ("The wind ripped the soil right off the fields. Crops died. Cattle died. Millions went hungry. And the desert kept coming.", 0.75, "wind", None),
 ("Then an Australian named Tony Rinaudo showed up with a plan. Plant new trees. He planted thousands.", 0.4, "pop", None),
 ("Almost all of them died.", 0.7, None, "sad"),
 ("He was about to give up. Until one day, he looked down at a scruffy little bush,", 0.2, None, "riser"),
 ("and realized it wasn't a bush.", 0.6, None, None),
 ("It was a tree. Cut down years ago. With its roots still alive underground.", 0.45, "impact", None),
 ("The forest had never left. It was hiding under the dirt, waiting.", 0.45, None, None),
 ("So farmers stopped planting, and started protecting. And twenty years later, two hundred million trees were back.", 0.3, "whoosh", None),
 ("Enough to feed two and a half million more people.", 1.0, None, "ding"),
]
SFX = {"whoosh": ("sfx/whoosh_1.mp3", -8), "whoosh_b": ("sfx/swoosh_1.mp3", -9), "impact": ("sfx/impact_2.mp3", -7),
       "wind": ("sfx/wind_0.mp3", -15), "pop": ("sfx2/pop_0.mp3", -9), "sad": ("sfx2/sadtrombone_0.mp3", -18),
       "riser": ("sfx/riser_0.mp3", -8), "ding": ("sfx/ding_0.mp3", -10), "chop": ("sfx2/thud_0.mp3", -10)}

def dec(p):
    raw = subprocess.run([ffmpeg_bin(), "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def db(x): return 10 ** (x / 20)

def build(voice, speed, out):
    k = Kokoro("../models/kokoro.onnx", "../models/voices.bin")
    segs, events, t = [], [], 0.0
    for text, pause, s0, s1 in LINES:
        a, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
        nz = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, nz[0] - 300): nz[-1] + 900]
        a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a).astype(np.float32)
        if s0: events.append((max(0, t - 0.1), s0))
        if s1: events.append((t + len(a) / SR - (0.9 if s1 == "riser" else 0.0), s1))
        segs += [a, np.zeros(int(pause * SR), np.float32)]; t += len(a) / SR + pause
    v = np.concatenate(segs); n = len(v) + SR
    v = np.pad(v, (0, n - len(v)))
    m = dec(A + "music/music_cine_2.mp3")[8 * SR:]
    m = np.tile(m, n // len(m) + 1)[:n]
    env = np.convolve(np.abs(v), np.ones(SR // 4) / (SR // 4), mode="same")
    speak = np.clip(env / (env.max() * 0.08), 0, 1)
    g = np.convolve(db(-12) * (1 - speak) + db(-19) * speak, np.ones(SR // 6) / (SR // 6), mode="same")
    fade = np.ones(n); fade[: SR // 2] = np.linspace(0, 1, SR // 2); fade[-2 * SR:] = np.linspace(1, 0, 2 * SR)
    out_sig = v * db(1) + m * g * fade
    for t0, name in events:
        f, gain = SFX[name]
        s = dec(A + f)[: int((4 if name in ("wind", "sad") else 2.2) * SR)].copy()
        tail = min(len(s), SR // 3); s[-tail:] *= np.linspace(1, 0, tail)
        s = s / (np.abs(s).max() + 1e-9) * db(gain)
        i = int(t0 * SR); j = min(n, i + len(s)); out_sig[i:j] += s[: j - i]
    sf.write("tmp_mix.wav", out_sig, SR)
    subprocess.run([ffmpeg_bin(), "-v", "error", "-y", "-i", "tmp_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-b:a", "192k", out], check=True)
    print(out, f"{t:.1f}s")

build("am_liam", 1.2, "trees-nobody-planted-LIAM.mp3")
build("am_puck", 1.12, "trees-nobody-planted-PUCK.mp3")
