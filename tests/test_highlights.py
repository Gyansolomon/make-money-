import json

from moneymaker import highlights, llm
from moneymaker.highlights import Clip, candidate_windows, heuristic_clips, select_non_overlapping
from tests.helpers import make_transcript

FILLER = "and then we talked about some other things for a while over there"
STRONG = "Why do most people stay broke? The biggest mistake is spending money before they save it."


def long_transcript():
    texts = [FILLER] * 12 + [STRONG, "Here is the rule I follow every single month without fail.",
                             "Save twenty percent first, then spend what is left over."] + [FILLER] * 12
    return make_transcript(texts)


def test_windows_respect_length_bounds():
    t = long_transcript()
    for i, j in candidate_windows(t, 10, 20):
        dur = t.segments[j].end - t.segments[i].start
        assert 10 <= dur <= 20


def test_heuristic_prefers_hooky_window():
    t = long_transcript()
    clips = heuristic_clips(t, 1, 10, 25)
    assert len(clips) == 1
    strong_start = t.segments[12].start
    assert clips[0].start <= strong_start + 0.01 < clips[0].end
    assert clips[0].title


def test_select_non_overlapping():
    clips = [Clip(0, 30, "a", score=5), Clip(10, 40, "b", score=9), Clip(45, 70, "c", score=1)]
    chosen = select_non_overlapping(clips, 3)
    assert [c.title for c in chosen] == ["b", "c"]


def test_llm_clips_snaps_to_segments_and_validates(monkeypatch):
    t = long_transcript()
    reply = {"clips": [
        {"start_line": 12, "end_line": 14, "title": "Why you stay broke", "hook": "Stop doing this",
         "hashtags": ["money", "#finance"], "score": 9, "reason": "strong hook"},
        {"start_line": 3, "end_line": 3, "title": "too short"},
        {"start_line": 999, "end_line": 1000, "title": "out of range"},
        {"title": "missing lines"},
    ]}
    monkeypatch.setattr(llm, "complete", lambda prompt, **kw: "```json\n" + json.dumps(reply) + "\n```")
    clips = highlights.llm_clips(t, 3, 8, 30, hashtags=["#campaign"])
    assert len(clips) == 1
    c = clips[0]
    assert c.start == t.segments[12].start and c.end == t.segments[14].end
    assert c.hashtags == ["#money", "#finance", "#campaign"]


def test_find_clips_falls_back_when_llm_fails(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "x")

    def boom(*a, **k):
        raise llm.LLMError("down")

    monkeypatch.setattr(llm, "complete", boom)
    clips = highlights.find_clips(long_transcript(), 2, 10, 25, log=lambda *_: None)
    assert clips and all(c.reason == "heuristic" for c in clips)


def test_parse_json_variants():
    assert llm.parse_json('{"a": 1}') == {"a": 1}
    assert llm.parse_json('Sure! Here you go: {"a": [1, 2]} hope it helps') == {"a": [1, 2]}
    assert llm.parse_json("```\n[1, 2]\n```") == [1, 2]
