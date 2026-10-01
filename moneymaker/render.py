"""Cut a clip from the source and render it as a 1080x1920 vertical video with captions."""

from __future__ import annotations

from pathlib import Path

from moneymaker.captions import HEIGHT, WIDTH
from moneymaker.media import run_ffmpeg

LAYOUTS = ("fit", "crop")


def _filter_escape(path: Path) -> str:
    # Paths inside a filtergraph need ':' ',' '\' and quotes escaped.
    return str(path).replace("\\", "/").replace(":", r"\:").replace("'", r"\'").replace(",", r"\,")


def video_filter(layout: str, ass_path: Path | None) -> str:
    if layout == "crop":
        # Fill the frame; best for single-speaker, centered footage.
        chain = f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},setsar=1[v]"
    elif layout == "fit":
        # Whole frame visible on a blurred copy of itself; safe for podcasts and wide shots.
        chain = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},gblur=sigma=30,eq=brightness=-0.08[bgb];"
            f"[fg]scale={WIDTH}:-2[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1[v]"
        )
    else:
        raise ValueError(f"layout must be one of {LAYOUTS}")
    if ass_path:
        chain = chain[: -len("[v]")] + f"[pre];[pre]ass='{_filter_escape(ass_path)}'[v]"
    return chain


def render_clip(source: Path, start: float, end: float, out: Path, ass_path: Path | None = None,
                layout: str = "fit", has_audio: bool = True, preset: str = "veryfast") -> Path:
    duration = end - start
    args = [
        "-ss", f"{start:.3f}", "-i", str(source), "-t", f"{duration:.3f}",
        "-filter_complex", video_filter(layout, ass_path), "-map", "[v]",
    ]
    if has_audio:
        # Platforms normalise loudness; hitting ~-14 LUFS avoids being turned down or sounding quiet.
        args += ["-map", "0:a:0", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "48000"]
    args += [
        "-c:v", "libx264", "-preset", preset, "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
        "-movflags", "+faststart", str(out),
    ]
    run_ffmpeg(args)
    return out
