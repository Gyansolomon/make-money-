"""Pick the best moments of a transcript to turn into short clips."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from moneymaker import llm
from moneymaker.transcript import Segment, Transcript


@dataclass
class Clip:
    start: float
    end: float
    title: str
    hook: str = ""
    description: str = ""
    hashtags: list[str] = field(default_factory=list)
    score: float = 0.0
    reason: str = ""

    @property
    def duration(self) -> float:
        return self.end - self.start


HOOK_WORDS = {
    "never", "always", "secret", "mistake", "mistakes", "truth", "why", "how", "nobody", "everyone",
    "money", "million", "billion", "rich", "broke", "crazy", "insane", "shocking", "worst", "best",
    "biggest", "stop", "wrong", "lie", "lied", "fired", "quit", "dead", "died", "hate", "love",
    "actually", "honestly", "real", "reason", "problem", "rule", "trick", "hack", "free", "first",
}
WEAK_OPENERS = {"and", "but", "so", "because", "or", "which", "that", "then", "also", "um", "uh", "like"}
SENTENCE_END = re.compile(r"[.!?][\"')\]]*$")


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def score_window(segs: list[Segment], target: float) -> float:
    text = " ".join(s.text for s in segs)
    words = _tokens(text)
    if not words:
        return 0.0
    duration = segs[-1].end - segs[0].start
    opener = _tokens(segs[0].text)
    score = 0.0
    # Hook: the first ~2 segments decide whether people keep watching.
    head = _tokens(" ".join(s.text for s in segs[:2]))
    score += 1.5 * min(3, sum(w in HOOK_WORDS for w in head))
    score += 1.5 if "?" in segs[0].text else 0.0
    score += 1.0 if any(re.search(r"\d", s.text) for s in segs[:2]) else 0.0
    score += 1.0 if opener and opener[0] in {"you", "your", "if", "what", "why", "how", "the"} else 0.0
    # Starting mid-thought or ending mid-sentence feels broken.
    score -= 2.0 if opener and opener[0] in WEAK_OPENERS else 0.0
    score += 1.5 if SENTENCE_END.search(segs[-1].text.strip()) else -1.5
    # Overall intensity and pace.
    score += 0.5 * min(6, sum(w in HOOK_WORDS for w in words))
    wps = len(words) / max(duration, 1.0)
    score += 1.0 if 2.2 <= wps <= 4.0 else 0.0
    score -= 0.08 * abs(duration - target)
    return round(score, 3)


def candidate_windows(transcript: Transcript, min_len: float, max_len: float) -> list[tuple[int, int]]:
    segs = transcript.segments
    windows = []
    for i in range(len(segs)):
        for j in range(i, len(segs)):
            dur = segs[j].end - segs[i].start
            if dur > max_len:
                break
            if dur >= min_len:
                windows.append((i, j))
    return windows


def select_non_overlapping(clips: list[Clip], count: int, gap: float = 2.0) -> list[Clip]:
    if count <= 0:
        return []
    chosen: list[Clip] = []
    for clip in sorted(clips, key=lambda c: c.score, reverse=True):
        if all(clip.end + gap <= c.start or clip.start >= c.end + gap for c in chosen):
            chosen.append(clip)
        if len(chosen) == count:
            break
    return sorted(chosen, key=lambda c: c.start)


def _fallback_title(text: str, limit: int = 70) -> str:
    first = re.split(r"(?<=[.!?])\s+", text.strip())[0]
    return first if len(first) <= limit else first[: limit - 1].rsplit(" ", 1)[0] + "…"


def heuristic_clips(transcript: Transcript, count: int, min_len: float, max_len: float,
                    hashtags: list[str] | None = None) -> list[Clip]:
    target = (min_len + max_len) / 2
    segs = transcript.segments
    clips = []
    for i, j in candidate_windows(transcript, min_len, max_len):
        window = segs[i : j + 1]
        text = " ".join(s.text for s in window)
        clips.append(Clip(
            start=window[0].start, end=window[-1].end, title=_fallback_title(text),
            hook=_fallback_title(window[0].text, 50), description=text[:280],
            hashtags=list(hashtags or []), score=score_window(window, target), reason="heuristic",
        ))
    return select_non_overlapping(clips, count)


PROMPT = """You are a top short-form video editor. Below is a numbered transcript of a long video.
Pick the {n} best moments to post as standalone vertical clips on TikTok, Instagram Reels and YouTube Shorts.

Rules:
- Each clip must be {min_len:.0f}-{max_len:.0f} seconds long (use the timestamps).
- It must make sense with zero context: a strong hook in the first 3 seconds, a complete thought, and a satisfying ending or payoff.
- Prefer: bold claims, surprising facts, stories with a twist, emotional moments, practical advice, funny moments, controversy.
- Avoid: intros/outros, sponsor reads, moments that depend on something shown on screen, clips that start mid-sentence.
- Clips must not overlap.
{notes}
Return JSON only, in this shape:
{{"clips": [{{"start_line": 12, "end_line": 19, "title": "short punchy title under 60 chars",
  "hook": "on-screen hook text, max 8 words", "description": "1-2 sentence post caption",
  "hashtags": ["#tag1", "#tag2", "#tag3"], "score": 1-10, "reason": "why this will perform"}}]}}

Transcript:
{lines}
"""

MAX_LINES_PER_CALL = 1200


def _fmt(t: float) -> str:
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def _llm_chunk(segs: list[Segment], offset: int, n: int, min_len: float, max_len: float, notes: str) -> list[dict]:
    lines = "\n".join(f"[{offset + k}] {_fmt(s.start)}-{_fmt(s.end)} {s.text}" for k, s in enumerate(segs))
    prompt = PROMPT.format(
        n=n, min_len=min_len, max_len=max_len, lines=lines,
        notes=f"- Campaign requirements from the client: {notes}\n" if notes else "",
    )
    data = llm.parse_json(llm.complete(prompt))
    clips = data.get("clips") if isinstance(data, dict) else data
    if not isinstance(clips, list):
        raise llm.LLMError(f"Expected a list of clips, got {type(clips).__name__}")
    return clips


def _to_clip(raw: dict, segs: list[Segment], min_len: float, max_len: float, hashtags: list[str]) -> Clip | None:
    try:
        i, j = int(raw["start_line"]), int(raw["end_line"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (0 <= i <= j < len(segs)):
        return None
    # Trim from the end if the model overshot the max length; drop clips far too short.
    while j > i and segs[j].end - segs[i].start > max_len * 1.1:
        j -= 1
    if segs[j].end - segs[i].start < min_len * 0.7:
        return None
    tags = [t if t.startswith("#") else f"#{t}" for t in raw.get("hashtags", []) if isinstance(t, str) and t.strip()]
    for t in hashtags:
        if t not in tags:
            tags.append(t)
    try:
        score = float(raw.get("score", 5))
    except (TypeError, ValueError):
        score = 5.0
    return Clip(
        start=segs[i].start, end=segs[j].end,
        title=str(raw.get("title") or _fallback_title(segs[i].text))[:100],
        hook=str(raw.get("hook") or "")[:80], description=str(raw.get("description") or "")[:500],
        hashtags=tags[:8], score=score, reason=str(raw.get("reason") or ""),
    )


def llm_clips(transcript: Transcript, count: int, min_len: float, max_len: float,
              notes: str = "", hashtags: list[str] | None = None) -> list[Clip]:
    segs = transcript.segments
    chunks = [(k, segs[k : k + MAX_LINES_PER_CALL]) for k in range(0, len(segs), MAX_LINES_PER_CALL)]
    per_chunk = max(2, -(-count * 3 // (2 * len(chunks))))  # ask for extra, keep the best
    clips = []
    for offset, chunk in chunks:
        for raw in _llm_chunk(chunk, offset, per_chunk, min_len, max_len, notes):
            if isinstance(raw, dict) and (clip := _to_clip(raw, segs, min_len, max_len, hashtags or [])):
                clips.append(clip)
    return select_non_overlapping(clips, count)


def find_clips(transcript: Transcript, count: int, min_len: float, max_len: float,
               notes: str = "", hashtags: list[str] | None = None, use_llm: bool = True,
               log=print) -> list[Clip]:
    if not transcript.segments:
        return []
    if use_llm and llm.available():
        try:
            clips = llm_clips(transcript, count, min_len, max_len, notes, hashtags)
            if clips:
                return clips
            log("LLM returned no usable clips; falling back to heuristic picker")
        except llm.LLMError as exc:
            log(f"LLM unavailable ({exc}); falling back to heuristic picker")
    return heuristic_clips(transcript, count, min_len, max_len, hashtags)
