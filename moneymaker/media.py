"""ffmpeg/ffprobe helpers and source download."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path


class MediaError(RuntimeError):
    pass


@lru_cache(maxsize=None)
def ffmpeg_bin() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:  # dev/test fallback when system ffmpeg is missing
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise MediaError("ffmpeg not found. Install it: sudo apt install ffmpeg") from exc


def run_ffmpeg(args: list[str]) -> None:
    cmd = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise MediaError(f"ffmpeg failed: {proc.stderr.strip()[-2000:]}")


def probe(path: str | Path) -> dict:
    """Return duration (s), width and height. Uses ffprobe when available, else parses ffmpeg -i."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
            capture_output=True, text=True,
        )
        if out.returncode != 0:
            raise MediaError(f"ffprobe failed on {path}: {out.stderr.strip()}")
        data = json.loads(out.stdout)
        video = next((s for s in data["streams"] if s.get("codec_type") == "video"), None)
        return {
            "duration": float(data["format"].get("duration", 0.0)),
            "width": int(video["width"]) if video else 0,
            "height": int(video["height"]) if video else 0,
            "has_audio": any(s.get("codec_type") == "audio" for s in data["streams"]),
        }
    proc = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    err = proc.stderr
    dur = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", err)
    size = re.search(r"Video: .*?, (\d{2,5})x(\d{2,5})", err)
    if not dur:
        raise MediaError(f"Could not read media info for {path}")
    h, m, s = dur.groups()
    return {
        "duration": int(h) * 3600 + int(m) * 60 + float(s),
        "width": int(size.group(1)) if size else 0,
        "height": int(size.group(2)) if size else 0,
        "has_audio": "Audio:" in err,
    }


def extract_audio(video: Path, wav: Path) -> Path:
    if not wav.exists():
        run_ffmpeg(["-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)])
    return wav


def is_url(source: str) -> bool:
    return bool(re.match(r"^https?://", source))


def fetch_source(source: str, work_dir: Path, cookies: str | None = None, proxy: str | None = None) -> Path:
    """Return a local video file for `source` (a path or a URL), downloading with yt-dlp if needed."""
    if not is_url(source):
        path = Path(source).expanduser()
        if not path.exists():
            raise MediaError(f"Source file not found: {path}")
        return path

    import yt_dlp

    work_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        # 1080p max keeps downloads small; vertical output is 1080 wide anyway.
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(work_dir / "source.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # Datacenter IPv6 ranges are hit hardest by YouTube's bot check.
        "source_address": "0.0.0.0",
        "retries": 5,
    }
    cookies = cookies or os.environ.get("YTDLP_COOKIES") or None
    proxy = proxy or os.environ.get("YTDLP_PROXY") or None
    if cookies:
        opts["cookiefile"] = cookies
    if proxy:
        opts["proxy"] = proxy

    existing = sorted(work_dir.glob("source.*"))
    if existing and existing[0].suffix in {".mp4", ".mkv", ".webm"}:
        return existing[0]
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(source, download=True)
            path = Path(ydl.prepare_filename(info)).with_suffix(".mp4")
    except Exception as exc:  # yt-dlp raises many types
        msg = str(exc)
        if "not a bot" in msg or "Sign in" in msg:
            msg += (
                "\nYouTube is blocking this server. Pass --cookies cookies.txt (exported from a "
                "logged-in browser) or --proxy with a residential proxy. See README."
            )
        raise MediaError(f"Download failed: {msg}") from exc
    if not path.exists():
        matches = sorted(work_dir.glob("source.*"))
        if not matches:
            raise MediaError("Download finished but no file was found")
        path = matches[0]
    return path
