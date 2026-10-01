"""Narration: Kokoro 'am_liam' per scene + exact word timings via faster-whisper."""

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
SR = 24000

SCENES = [
    ("hook", "This country is over 4,000 kilometers long, but on average, just 177 kilometers wide."),
    ("europe", "Drop it onto Europe, and it would stretch from the Arctic Circle all the way to North Africa."),
    ("question", "So why is Chile shaped like a noodle?"),
    ("andes", "Look east. The Andes, the longest mountain range on land, run along Chile's entire border like a wall."),
    ("pacific", "Look west. Nothing but the Pacific. Chile is literally trapped between mountains and ocean."),
    ("treaty", "In 1881, Chile and Argentina signed a treaty. The border would follow the highest peaks of the Andes. "
               "Chile kept the coast. Argentina took the plains."),
    ("war", "Then came the War of the Pacific. Chile fought Peru and Bolivia over a desert full of valuable nitrates, and won."),
    ("landlocked", "Chile pushed its border north, and Bolivia lost its entire coastline."),
    ("navy", "But Bolivia still has a navy. And every year, it celebrates a Day of the Sea."),
    ("extremes", "So today, one country runs from the driest desert on Earth, to glaciers at the bottom of the world."),
    ("outro", "Follow for more maps that explain the world."),
]
GAP = 0.22  # pause between scenes (fast pacing)


def synth():
    from kokoro_onnx import Kokoro

    k = Kokoro(str(HERE.parent / "models" / "kokoro.onnx"), str(HERE.parent / "models" / "voices.bin"))
    pieces, timeline, t = [], [], 0.0
    for key, text in SCENES:
        audio, sr = k.create(text, voice="am_liam", speed=1.12, lang="en-us")
        assert sr == SR
        nz = np.where(np.abs(audio) > 0.01)[0]
        audio = audio[max(0, nz[0] - 300): nz[-1] + 900]
        dur = len(audio) / SR + GAP
        timeline.append({"key": key, "text": text, "start": round(t, 3), "end": round(t + dur, 3)})
        pieces += [audio, np.zeros(int(GAP * SR), dtype=audio.dtype)]
        t += dur
    sf.write(OUT / "voice.wav", np.concatenate(pieces), SR)
    return timeline


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def align(timeline):
    from faster_whisper import WhisperModel

    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(OUT / "voice.wav"), word_timestamps=True, language="en", beam_size=5)
    heard = [(w.word.strip(), float(w.start), float(w.end)) for s in segs for w in s.words if w.word.strip()]
    script = [(i, w) for i, sc in enumerate(timeline) for w in sc["text"].split()]
    a, b = [norm(w) for _, w in script], [norm(h[0]) for h in heard]
    times = [None] * len(script)
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = heard[j1 + k][1:]
        elif j2 > j1:
            s, e = heard[j1][1], heard[j2 - 1][2]
            n = i2 - i1
            for k in range(n):
                times[i1 + k] = (s + (e - s) * k / n, s + (e - s) * (k + 1) / n)
    for i, tm in enumerate(times):
        if tm is None:
            prev = times[i - 1][1] if i and times[i - 1] else 0.0
            times[i] = (prev, prev + 0.25)
    words = [{"scene": si, "text": w, "start": round(s, 3), "end": round(e, 3)} for (si, w), (s, e) in zip(script, times)]
    return words


if __name__ == "__main__":
    tl = synth()
    words = align(tl)
    json.dump({"timeline": tl, "words": words}, open(OUT / "voice.json", "w"), indent=1)
    print(f"total {tl[-1]['end']:.1f}s")
    for sc in tl:
        print(f"{sc['start']:6.2f}-{sc['end']:6.2f} {sc['key']}")
