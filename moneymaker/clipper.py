"""Clipping pipeline: long video -> N captioned vertical clips + posting metadata."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from moneymaker import media
from moneymaker.captions import CaptionStyle, write_ass
from moneymaker.highlights import Clip, find_clips
from moneymaker.render import render_clip
from moneymaker.transcript import Transcript, transcribe


@dataclass
class ClipJob:
    source: str
    out_dir: Path = Path("output")
    work_root: Path = Path("work")
    count: int = 8
    min_len: float = 20.0
    max_len: float = 60.0
    layout: str = "fit"
    whisper_model: str = "small"
    language: str | None = None
    notes: str = ""
    hashtags: list[str] = field(default_factory=list)
    use_llm: bool = True
    captions: bool = True
    hook_text: bool = True
    cookies: str | None = None
    proxy: str | None = None
    style: CaptionStyle = field(default_factory=CaptionStyle)


def slugify(text: str, limit: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:limit].rstrip("-") or "clip"


def job_id(source: str) -> str:
    """Cache key for a source. Local files include size and mtime so an in-place replacement
    gets a fresh cache instead of reusing the old audio and transcript."""
    key = source
    if not media.is_url(source):
        path = Path(source).expanduser()
        if path.exists():
            st = path.stat()
            key = f"{path.resolve()}|{st.st_size}|{st.st_mtime_ns}"
    return hashlib.sha1(key.encode()).hexdigest()[:10]


def post_text(clip: Clip) -> str:
    parts = [clip.title]
    if clip.description and clip.description != clip.title:
        parts.append(clip.description)
    if clip.hashtags:
        parts.append(" ".join(clip.hashtags))
    return "\n\n".join(parts) + "\n"


def run(job: ClipJob, log=print) -> list[dict]:
    work = job.work_root / job_id(job.source)
    work.mkdir(parents=True, exist_ok=True)

    log(f"[1/4] Getting source: {job.source}")
    video = media.fetch_source(job.source, work, job.cookies, job.proxy)
    info = media.probe(video)
    if not info["has_audio"]:
        raise media.MediaError("Source has no audio track; nothing to transcribe")
    log(f"      {info['width']}x{info['height']}, {info['duration'] / 60:.1f} min")

    log(f"[2/4] Transcribing with whisper '{job.whisper_model}' (cached after first run)")
    audio = media.extract_audio(video, work / "audio.wav")
    transcript: Transcript = transcribe(audio, work / f"transcript-{job.whisper_model}-{job.language or 'auto'}.json",
                                        job.whisper_model, job.language)
    log(f"      {len(transcript.segments)} segments, language={transcript.language}")

    log(f"[3/4] Finding the best {job.count} moments")
    clips = find_clips(transcript, job.count, job.min_len, job.max_len, job.notes, job.hashtags, job.use_llm, log)
    if not clips:
        log("      No clip-worthy windows found (video too short for --min-len?)")
        return []

    out = job.out_dir / f"{slugify(Path(video).stem if not media.is_url(job.source) else job.source.split('/')[-1])}-{work.name}"
    out.mkdir(parents=True, exist_ok=True)
    log(f"[4/4] Rendering {len(clips)} clips -> {out}")
    results = []
    for n, clip in enumerate(clips, 1):
        name = f"{n:02d}-{slugify(clip.title)}"
        ass = None
        if job.captions:
            words = transcript.words_between(clip.start, clip.end)
            ass = write_ass(work / f"{name}.ass", words, clip.start, clip.duration, job.style,
                            hook=clip.hook if job.hook_text else "")
        mp4 = render_clip(video, clip.start, clip.end, out / f"{name}.mp4", ass, job.layout)
        (out / f"{name}.txt").write_text(post_text(clip), encoding="utf-8")
        results.append({"file": mp4.name, **asdict(clip), "duration": round(clip.duration, 2)})
        log(f"      {n:02d}. {clip.duration:4.0f}s  score {clip.score:<5}  {clip.title}")

    (out / "clips.json").write_text(json.dumps({"source": job.source, "clips": results}, indent=2, ensure_ascii=False))
    with open(out / "clips.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["file", "start", "end", "duration", "score", "title", "hashtags", "posted_tiktok",
                         "posted_reels", "posted_shorts", "views", "earned_usd"])
        for r in results:
            writer.writerow([r["file"], r["start"], r["end"], r["duration"], r["score"], r["title"],
                             " ".join(r["hashtags"]), "", "", "", "", ""])
    return results
