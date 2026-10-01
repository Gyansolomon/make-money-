"""Record the spoken-word vocal (Kokoro, Liam) and place every line on the beat grid.

Writes work/lines/*.wav, work/vocal.wav and work/schedule.json (line start/end, section marks).
Run from studio/musicvideo:  python tools/vocals.py
"""

import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

from script import BPM, LINES, PRONOUNCE, SR

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
MODELS = ROOT.parent / "models"
BEAT = 60 / BPM
BAR = 4 * BEAT
LEAD_IN = 0.08  # speech starts this long after the grid point (consonant attack lands on the beat)


def synth(k, text, speed):
    ph = k.tokenizer.phonemize(text, "en-us")
    for a, b in PRONOUNCE.items():
        ph = ph.replace(a, b)
    a, sr = k.create(ph, voice="am_liam", speed=speed, lang="en-us", is_phonemes=True)
    assert sr == SR
    nz = np.where(np.abs(a) > 0.008)[0]
    return a[max(0, nz[0] - 200): nz[-1] + 600].astype(np.float32)


def main():
    (WORK / "lines").mkdir(parents=True, exist_ok=True)
    k = Kokoro(str(MODELS / "kokoro.onnx"), str(MODELS / "voices.bin"))
    sched, t_free = [], 0.0
    for i, ln in enumerate(LINES):
        a = synth(k, ln["say"], ln.get("speed", 1.1))
        dur = len(a) / SR
        # earliest grid point allowed: the requested bar, or right after the previous line + rest
        want = ln.get("bar")
        # sections start on a downbeat; other lines on the next half bar (or beat, if asked)
        on = ln.get("on", "bar" if ln.get("section") else "half")
        snap = {"bar": BAR, "half": BAR / 2, "beat": BEAT}[on]
        earliest = t_free + ln.get("rest", 0.5) * BEAT
        t = math.ceil(earliest / snap - 1e-6) * snap
        if want is not None:
            t = max(t, want * BAR)
        start = t + LEAD_IN
        sf.write(WORK / "lines" / f"{i:02d}.wav", a, SR)
        sched.append({"i": i, "text": ln["text"], "start": round(start, 3), "end": round(start + dur, 3),
                      "grid": round(t, 3), "section": ln.get("section")})
        t_free = start + dur
        print(f"{i:2d} bar {t / BAR:5.2f}  {dur:4.2f}s  {ln['text']}")
    total_bars = math.ceil((t_free + 2 * BEAT) / BAR) + 2  # two bars of outro after the last line
    duration = total_bars * BAR
    vocal = np.zeros(int(duration * SR) + SR, np.float32)
    for s in sched:
        a, _ = sf.read(WORK / "lines" / f"{s['i']:02d}.wav", dtype="float32")
        i0 = int(s["start"] * SR)
        vocal[i0: i0 + len(a)] += a
    sf.write(WORK / "vocal.wav", vocal[: int(duration * SR)], SR)
    json.dump({"bpm": BPM, "duration": round(duration, 3), "bars": total_bars, "lines": sched},
              open(WORK / "schedule.json", "w"), indent=1)
    print(f"{total_bars} bars, {duration:.1f}s")


if __name__ == "__main__":
    main()
