from moneymaker.transcript import Segment, Transcript, Word


def make_segment(start: float, text: str, wps: float = 3.0) -> Segment:
    words, t = [], start
    for token in text.split():
        words.append(Word(round(t, 2), round(t + 1 / wps - 0.05, 2), token))
        t += 1 / wps
    return Segment(start, round(t, 2), text, words)


def make_transcript(texts: list[str], gap: float = 0.3) -> Transcript:
    segs, t = [], 0.0
    for text in texts:
        seg = make_segment(t, text)
        segs.append(seg)
        t = seg.end + gap
    return Transcript("en", segs)
