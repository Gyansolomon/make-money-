"""Command line entry point: python -m moneymaker clip <url-or-file> [options]"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from moneymaker import __version__
from moneymaker.captions import CaptionStyle
from moneymaker.media import MediaError


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="moneymaker", description="Turn long videos into captioned vertical clips.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("clip", help="cut a long video (URL or file) into short vertical clips")
    c.add_argument("sources", nargs="+", help="YouTube/other URL(s) or local video file(s)")
    c.add_argument("-n", "--count", type=int, default=8, help="clips per source (default 8)")
    c.add_argument("--min-len", type=float, default=20, help="minimum clip seconds (default 20)")
    c.add_argument("--max-len", type=float, default=60, help="maximum clip seconds (default 60)")
    c.add_argument("--layout", choices=["fit", "crop"], default="fit",
                   help="fit = full frame on blurred background; crop = fill 9:16 (single speaker)")
    c.add_argument("--whisper-model", default="small", help="tiny/base/small/medium (default small)")
    c.add_argument("--language", help="force transcript language, e.g. en")
    c.add_argument("--notes", default="", help="campaign requirements to steer clip choice")
    c.add_argument("--hashtags", default="", help="hashtags every clip must carry, e.g. '#brand #campaign'")
    c.add_argument("--no-llm", action="store_true", help="use the built-in heuristic instead of an LLM")
    c.add_argument("--no-captions", action="store_true")
    c.add_argument("--no-hook", action="store_true", help="skip the hook text at the top of the first 3s")
    c.add_argument("--font", default="DejaVu Sans", help="caption font installed on the system")
    c.add_argument("--caption-color", default="FFFFFF")
    c.add_argument("--highlight-color", default="FFE81F")
    c.add_argument("--cookies", help="cookies.txt for YouTube (see README)")
    c.add_argument("--proxy", help="proxy URL for downloads, e.g. http://user:pass@host:port")
    c.add_argument("-o", "--out", default="output", help="output folder (default ./output)")
    c.add_argument("--work", default="work", help="cache folder for downloads/transcripts (default ./work)")
    return p


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    if args.command == "clip":
        from moneymaker.clipper import ClipJob, run

        if args.min_len <= 0 or args.max_len <= args.min_len:
            print("--max-len must be greater than --min-len (> 0)", file=sys.stderr)
            return 2
        style = CaptionStyle(font=args.font, color=args.caption_color, highlight=args.highlight_color)
        failed = 0
        for source in args.sources:
            job = ClipJob(
                source=source, out_dir=Path(args.out), work_root=Path(args.work), count=args.count,
                min_len=args.min_len, max_len=args.max_len, layout=args.layout,
                whisper_model=args.whisper_model, language=args.language, notes=args.notes,
                hashtags=args.hashtags.split(), use_llm=not args.no_llm, captions=not args.no_captions,
                hook_text=not args.no_hook, cookies=args.cookies, proxy=args.proxy, style=style,
            )
            try:
                run(job)
            except MediaError as exc:
                failed += 1
                print(f"ERROR ({source}): {exc}", file=sys.stderr)
        return 1 if failed else 0
    return 2
