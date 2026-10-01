"""Word timings for every line (faster-whisper on each isolated line), written as data/lyrics.json.

Run after vocals.py:  python tools/align.py
"""

import difflib
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

from script import LINES, SR

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def whisper_words(model, path):
    a, _ = sf.read(path, dtype="float32")
    pad = np.zeros(int(0.3 * SR), np.float32)
    a = np.concatenate([pad, a, pad])
    # whisper wants 16 kHz
    x = np.interp(np.arange(0, len(a), SR / 16000), np.arange(len(a)), a).astype(np.float32)
    segs, _ = model.transcribe(x, language="en", word_timestamps=True, beam_size=5)
    out = []
    for s in segs:
        for w in s.words:
            out.append((w.word.strip(), max(0.0, w.start - 0.3), max(0.0, w.end - 0.3)))
    return out, len(a) / SR - 0.6


def fit(say_tokens, heard, dur):
    """Times for each spoken token: matched to whisper words, gaps filled by character share."""
    times = [None] * len(say_tokens)
    a, b = [norm(t) for t in say_tokens], [norm(w) for w, _, _ in heard]
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            _, s, e = heard[blk.b + k]
            times[blk.a + k] = [s, e]
    # fill unmatched tokens between their known neighbours, proportional to length
    i = 0
    while i < len(times):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(times) and times[j] is None:
            j += 1
        t0 = times[i - 1][1] if i > 0 else 0.0
        t1 = times[j][0] if j < len(times) else dur
        lens = [max(1, len(a[k])) for k in range(i, j)]
        tot, acc = sum(lens), t0
        for k, n in zip(range(i, j), lens):
            d = (t1 - t0) * n / tot
            times[k] = [acc, acc + d]
            acc += d
        i = j
    # monotonic, no overlaps
    for k in range(1, len(times)):
        times[k][0] = max(times[k][0], times[k - 1][0] + 0.02)
        times[k - 1][1] = min(max(times[k - 1][1], times[k - 1][0] + 0.05), times[k][0] + 0.15)
    return times


def main():
    sched = json.load(open(WORK / "schedule.json"))
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    lines = []
    for ln, s in zip(LINES, sched["lines"]):
        disp, say = ln["text"].split(), ln["say"].split()
        heard, dur = whisper_words(model, WORK / "lines" / f"{s['i']:02d}.wav")
        st = fit(say, heard, dur)
        # map display tokens onto spoken tokens (a numeral like "1970s." covers two spoken words)
        extra, groups, k = len(say) - len(disp), [], 0
        for tok in disp:
            n = 1 + extra if (extra > 0 and re.search(r"\d", tok)) else 1
            groups.append((k, k + n))
            k += n
        assert k == len(say), (ln["text"], disp, say)
        words = [{"w": tok, "start": round(s["start"] + st[a][0], 3), "end": round(s["start"] + st[b - 1][1], 3), "conf": 1.0}
                 for tok, (a, b) in zip(disp, groups)]
        lines.append({"i": s["i"], "text": ln["text"], "start": words[0]["start"], "end": words[-1]["end"], "words": words})
        print(f"{s['i']:2d} {' '.join(w for w, _, _ in heard)}")
    (ROOT / "data").mkdir(exist_ok=True)
    json.dump({"lines": lines}, open(ROOT / "data" / "lyrics.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
