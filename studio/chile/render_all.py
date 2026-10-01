"""Render frames in parallel, mix audio (voice + ducked music + SFX), burn captions, mux."""

import json
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from moneymaker.captions import CaptionStyle, build_ass  # noqa: E402
from moneymaker.media import ffmpeg_bin, run_ffmpeg  # noqa: E402
from moneymaker.transcript import Word  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "out"
A = HERE / "assets"
FPS = 30
SR = 48000

SFX_FILES = {
    "whoosh": "sfx/whoosh_1.mp3", "whoosh_b": "sfx/swoosh_1.mp3", "whoosh_c": "sfx/whoosh_2.mp3",
    "pop": "sfx/pop_2.mp3", "pop_b": "sfx/pop_1.mp3", "impact": "sfx/impact_2.mp3", "riser": "sfx/riser_0.mp3",
    "wind": "sfx/wind_0.mp3", "drums": "sfx/drums_1.mp3", "scratch": "sfx/scratch_0.mp3", "paper": "sfx/paper_0.mp3",
    "ding": "sfx/ding_0.mp3",
}
MAX_LEN = {"wind": 4.5, "drums": 5.5, "riser": 1.2, "impact": 2.5}
MUSIC = A / "music" / "music_cine_2.mp3"


def render_chunk(args):
    i0, i1, path = args
    import scenes as S

    proc = subprocess.Popen(
        [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", str(path)],
        stdin=subprocess.PIPE)
    for i in range(i0, i1):
        proc.stdin.write(S.frame(i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    return str(path)


def decode(path, sr=SR):
    raw = subprocess.run([ffmpeg_bin(), "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def db(x):
    return 10 ** (x / 20)


def mix(total, sfx_events):
    n = int((total + 0.3) * SR)
    voice = decode(OUT / "voice.wav")[:n]
    voice = np.pad(voice, (0, n - len(voice)))
    out = voice * db(1.5)
    # music bed, ducked under speech
    m = decode(MUSIC)
    start = int(8 * SR)  # skip the intro swell so energy starts immediately
    m = m[start:]
    if len(m) < n:
        m = np.tile(m, n // len(m) + 1)
    m = m[:n]
    env = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")
    speaking = np.clip(env / (env.max() * 0.08), 0, 1)
    gain = db(-17) * (1 - speaking) + db(-25) * speaking
    gain = np.convolve(gain, np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
    fade = np.ones(n)
    fade[: int(0.6 * SR)] = np.linspace(0, 1, int(0.6 * SR))
    fade[-int(1.5 * SR):] = np.linspace(1, 0, int(1.5 * SR))
    out += m * gain * fade
    cache = {}
    for t, name, g in sfx_events:
        if name not in cache:
            cache[name] = decode(A / SFX_FILES[name])
        s = cache[name]
        if name in MAX_LEN:
            s = s[: int(MAX_LEN[name] * SR)].copy()
            tail = min(len(s), int(0.4 * SR))
            s[-tail:] *= np.linspace(1, 0, tail)
        s = s / (np.abs(s).max() + 1e-9) * db(-6 + g)
        i = int(t * SR)
        j = min(n, i + len(s))
        out[i:j] += s[: j - i]
    sf.write(OUT / "mix.wav", out, SR)


def main():
    import scenes as S

    total = S.TOTAL
    nframes = int(total * FPS)
    k = 4
    bounds = [nframes * j // k for j in range(k + 1)]
    jobs = [(bounds[j], bounds[j + 1], OUT / f"part{j}.mp4") for j in range(k)]
    with Pool(k) as pool:
        parts = pool.map(render_chunk, jobs)
    (OUT / "parts.txt").write_text("".join(f"file '{p}'\n" for p in parts))
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(OUT / "parts.txt"), "-c", "copy", str(OUT / "visuals.mp4")])
    print("frames done")

    mix(total, S.SFX)
    print("audio mixed")

    words = [Word(w["start"], w["end"], w["text"]) for w in S.WORDS]
    style = CaptionStyle(font="Poppins ExtraBold", size=88, margin_v=470, outline=7, max_words=3, max_chars=18)
    (OUT / "captions.ass").write_text(build_ass(words, 0.0, total, style), encoding="utf-8")
    final = HERE.parent / "output" / "why-chile-is-so-thin-v2.mp4"
    final.parent.mkdir(exist_ok=True)
    run_ffmpeg([
        "-i", str(OUT / "visuals.mp4"), "-i", str(OUT / "mix.wav"),
        "-filter_complex", f"[0:v]ass='{OUT / 'captions.ass'}':fontsdir='{A}'[v];[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(final),
    ])
    print("done", final)


if __name__ == "__main__":
    main()
