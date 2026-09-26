from moneymaker.captions import CaptionStyle, _ts, build_ass, chunk_words
from moneymaker.transcript import Word


def words(texts, start=10.0, step=0.4):
    return [Word(start + i * step, start + i * step + 0.35, t) for i, t in enumerate(texts)]


def test_timestamp_format():
    assert _ts(0) == "0:00:00.00"
    assert _ts(61.235) == "0:01:01.24"
    assert _ts(3725.5) == "1:02:05.50"


def test_chunking_breaks_on_size_punctuation_and_pause():
    ws = words(["one", "two", "three", "four", "five."]) + [Word(20.0, 20.3, "later")]
    chunks = [[w.text for w in c] for c in chunk_words(ws, max_words=3, max_chars=40)]
    assert chunks == [["one", "two", "three"], ["four", "five."], ["later"]]


def test_ass_is_shifted_highlighted_and_escaped():
    ws = words(["hello", "{bad}", "world"])
    ass = build_ass(ws, offset=10.0, duration=5.0, style=CaptionStyle(max_words=3, max_chars=40), hook="Watch this")
    events = [l for l in ass.splitlines() if l.startswith("Dialogue:")]
    assert events[0].startswith("Dialogue: 1,0:00:00.00,0:00:03.00,Hook")
    captions = events[1:]
    assert len(captions) == 3  # one event per word, active word highlighted
    assert captions[0].startswith("Dialogue: 0,0:00:00.00,")
    assert "{bad}" not in ass and "(BAD)" in ass
    assert "&H001FE8FF" in captions[1]  # highlight colour in ASS BGR order


def test_words_outside_clip_are_dropped():
    ws = words(["before"], start=0) + words(["inside"], start=12) + words(["after"], start=30)
    ass = build_ass(ws, offset=10.0, duration=5.0)
    assert "INSIDE" in ass and "BEFORE" not in ass and "AFTER" not in ass
