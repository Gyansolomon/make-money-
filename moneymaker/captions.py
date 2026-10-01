"""Word-by-word burned-in captions as an ASS subtitle file (rendered by ffmpeg/libass)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from moneymaker.transcript import Word

WIDTH, HEIGHT = 1080, 1920


@dataclass
class CaptionStyle:
    font: str = "DejaVu Sans"
    size: int = 84
    color: str = "FFFFFF"      # RRGGBB
    highlight: str = "FFE81F"  # active word
    outline: int = 6
    max_words: int = 3
    max_chars: int = 16
    margin_v: int = 620        # distance from bottom; keeps text above platform UI
    uppercase: bool = True


def _ass_color(rgb: str) -> str:
    rgb = rgb.lstrip("#")
    return f"&H00{rgb[4:6]}{rgb[2:4]}{rgb[0:2]}".upper()


def _ts(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def chunk_words(words: list[Word], max_words: int = 3, max_chars: int = 16, pause: float = 0.45) -> list[list[Word]]:
    chunks: list[list[Word]] = []
    cur: list[Word] = []
    for w in words:
        if cur:
            too_long = len(cur) >= max_words or len(" ".join(x.text for x in cur + [w])) > max_chars
            gap = w.start - cur[-1].end > pause
            punct = cur[-1].text.rstrip()[-1:] in ".!?,;:"
            if too_long or gap or punct:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def build_ass(words: list[Word], offset: float, duration: float, style: CaptionStyle | None = None,
              hook: str = "", hook_seconds: float = 3.0) -> str:
    """Build an ASS script for words (absolute times), shifted so `offset` becomes 0."""
    st = style or CaptionStyle()
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{st.font},{st.size},{_ass_color(st.color)},{_ass_color(st.highlight)},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{st.outline},2,2,60,60,{st.margin_v},1
Style: Hook,{st.font},64,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0,8,80,80,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    if hook:
        lines.append(f"Dialogue: 1,{_ts(0)},{_ts(min(hook_seconds, duration))},Hook,,0,0,0,,{_escape(hook)}")

    shifted = [Word(w.start - offset, w.end - offset, w.text) for w in words]
    shifted = [w for w in shifted if w.end > 0 and w.start < duration]
    chunks = chunk_words(shifted, st.max_words, st.max_chars)
    hl = _ass_color(st.highlight)
    base = _ass_color(st.color)
    for ci, chunk in enumerate(chunks):
        chunk_end = chunks[ci + 1][0].start if ci + 1 < len(chunks) else min(duration, chunk[-1].end + 0.3)
        texts = [_escape(w.text.upper() if st.uppercase else w.text) for w in chunk]
        for wi, w in enumerate(chunk):
            start = w.start
            end = chunk[wi + 1].start if wi + 1 < len(chunk) else chunk_end
            if end <= start:
                continue
            parts = [f"{{\\c{hl}}}{t}{{\\c{base}}}" if k == wi else t for k, t in enumerate(texts)]
            pop = "{\\fscx108\\fscy108\\t(0,80,\\fscx100\\fscy100)}" if wi == 0 else ""
            lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Caption,,0,0,0,,{pop}{' '.join(parts)}")
    return header + "\n".join(lines) + "\n"


def write_ass(path: Path, *args, **kwargs) -> Path:
    path.write_text(build_ass(*args, **kwargs), encoding="utf-8")
    return path
