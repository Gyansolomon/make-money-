"""Transcript data model and faster-whisper transcription (cached as JSON)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Word:
    start: float
    end: float
    text: str


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word] = field(default_factory=list)


@dataclass
class Transcript:
    language: str
    segments: list[Segment]

    def words_between(self, start: float, end: float) -> list[Word]:
        return [w for s in self.segments for w in s.words if w.start >= start - 0.05 and w.end <= end + 0.05]

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), ensure_ascii=False))

    @classmethod
    def load(cls, path: Path) -> "Transcript":
        data = json.loads(path.read_text())
        return cls(
            language=data["language"],
            segments=[
                Segment(s["start"], s["end"], s["text"], [Word(**w) for w in s["words"]])
                for s in data["segments"]
            ],
        )


def transcribe(audio: Path, cache: Path, model_size: str = "small", language: str | None = None) -> Transcript:
    if cache.exists():
        return Transcript.load(cache)

    from faster_whisper import WhisperModel

    # int8 on CPU: "small" transcribes ~1h of audio in ~10-20 min on a 4 vCPU VPS.
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    raw_segments, info = model.transcribe(
        str(audio), language=language, word_timestamps=True, vad_filter=True, beam_size=5
    )
    segments = []
    for s in raw_segments:
        words = [Word(round(w.start, 2), round(w.end, 2), w.word.strip()) for w in (s.words or []) if w.word.strip()]
        segments.append(Segment(round(s.start, 2), round(s.end, 2), s.text.strip(), words))
    transcript = Transcript(language=info.language, segments=segments)
    transcript.save(cache)
    return transcript
