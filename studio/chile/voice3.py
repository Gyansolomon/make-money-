"""v3 narration: narrator + character voices, with timed pauses for gags."""

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent))
from voice import align  # noqa: E402  (word alignment, reused)

HERE = Path(__file__).parent
OUT = HERE / "out3"
OUT.mkdir(exist_ok=True)
SR = 24000
VOICES = {"N": ("am_liam", 1.1), "SP": ("em_alex", 1.0), "MA": ("am_onyx", 1.0), "CH": ("am_puck", 1.05), "BO": ("am_fenrir", 1.05)}

# (key, speaker, text, pause_after_seconds)
SEGMENTS = [
    ("hook_a", "N", "Let's talk about Chile.", 1.0),
    ("hook_b", "N", "No, not that chili. This Chile.", 0.25),
    ("long", "N", "Ever wondered why it's so ridiculously long?", 0.3),
    ("europe", "N", "Put it on Europe, and it stretches from the Arctic Circle to North Africa. Yet on average, it's just 177 kilometers wide.", 0.25),
    ("noodle", "N", "So how does a country end up shaped like a noodle?", 0.3),
    ("before", "N", "Five hundred years ago, this land belonged to Indigenous peoples, like the Mapuche. Then, the Spanish showed up.", 1.1),
    ("sp1", "SP", "Ah! What beautiful, empty land!", 1.0),
    ("ma1", "MA", "Hello! We live here.", 1.5),
    ("sp2", "SP", "Now, we live here.", 0.4),
    ("resist", "N", "The Mapuche fought back for centuries. But Spain still grabbed the central valley.", 0.25),
    ("tiny", "N", "So after independence in 1818, Chile looked something like this. Tiny.", 0.3),
    ("ch1", "CH", "Time to grow! Let's go east!", 1.3),
    ("andes", "N", "Except east was the Andes, the longest mountain range on land.", 0.2),
    ("ch2", "CH", "Okay. South it is.", 0.6),
    ("south", "N", "So Chile marched south, all the way to the bottom of the continent. In 1881, Argentina agreed the border would follow the Andes' highest peaks.", 0.25),
    ("north", "N", "Then Chile looked north, at a desert full of valuable nitrates. It went to war with Peru and Bolivia, and won.", 0.5),
    ("bo1", "BO", "Hey! Where did my ocean go?", 0.6),
    ("navy", "N", "To this day, Bolivia still has a navy. And it celebrates a Day of the Sea every year.", 0.25),
    ("outro", "N", "Trapped between mountains and ocean, Chile could only grow one way. Longer. Follow for more.", 0.6),
]


def synth():
    from kokoro_onnx import Kokoro

    k = Kokoro(str(HERE.parent / "models" / "kokoro.onnx"), str(HERE.parent / "models" / "voices.bin"))
    pieces, timeline, t = [], [], 0.0
    for key, spk, text, pause in SEGMENTS:
        voice, speed = VOICES[spk]
        audio, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
        nz = np.where(np.abs(audio) > 0.01)[0]
        audio = audio[max(0, nz[0] - 300): nz[-1] + 900]
        speech = len(audio) / SR
        timeline.append({"key": key, "speaker": spk, "text": text, "start": round(t, 3),
                         "speech_end": round(t + speech, 3), "end": round(t + speech + pause, 3)})
        pieces += [audio, np.zeros(int(pause * SR), dtype=audio.dtype)]
        t += speech + pause
    sf.write(OUT / "voice.wav", np.concatenate(pieces), SR)
    return timeline


if __name__ == "__main__":
    import voice as V
    V.OUT = OUT
    tl = synth()
    words = align(tl)
    json.dump({"timeline": tl, "words": words}, open(OUT / "voice.json", "w"), indent=1)
    print(f"total {tl[-1]['end']:.1f}s")
    for s in tl:
        print(f"{s['start']:6.2f}-{s['end']:6.2f} {s['speaker']:2s} {s['key']}")
