"""Have Gemini watch a YouTube video and write a timestamped style breakdown.

Usage: python gemini_watch.py <youtube_url> <out.md> [model]

Needs GEMINI_API_KEY in the environment (or a proxy that injects the key).
Uses the streaming endpoint because some proxies cut plain requests after ~30 s.
Models that worked in Sept 2026: gemini-3-flash-preview, gemini-3.5-flash
(gemini-2.5-flash is retired for new keys). 503 "overloaded" errors are common:
wait a minute and retry, they don't use quota.
"""

import json
import os
import sys
import time

import requests

PROMPT = """You are analysing a YouTube Short so a video editor can recreate its STYLE (not copy it).
Give a precise, timestamped breakdown:
1. Every shot/scene with start-end time (mm:ss.s): exactly what is on screen (map type: flat/3D/satellite/terrain, colours, which countries highlighted, zoom/pan/rotation camera moves, borders drawn, arrows, icons, photos, archival images, text overlays and their font style/position/animation).
2. Transitions between shots (cut, zoom-through, whip, fade) and how often cuts happen.
3. On-screen text/captions: style, size, colour, position, word-by-word or phrase.
4. Audio: narrator voice (gender, tone, pace, AI or human), background music (genre, mood, volume), sound effects (whooshes, pops, booms) and when they hit.
5. The first 3 seconds hook exactly (visual + words).
6. Full transcript of the narration with timestamps.
7. The 10 most important production techniques that make this video engaging, ranked.
Be concrete and factual; say "unclear" if you cannot tell."""


def watch(url, model="gemini-3-flash-preview", prompt=PROMPT):
    body = {
        "contents": [{"parts": [{"fileData": {"fileUri": url}}, {"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "mediaResolution": "MEDIA_RESOLUTION_LOW"},
    }
    headers = {}
    if os.environ.get("GEMINI_API_KEY"):
        headers["x-goog-api-key"] = os.environ["GEMINI_API_KEY"]
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse",
        json=body, headers=headers, stream=True, timeout=(30, 600))
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
    text, usage = [], None
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        d = json.loads(line[5:])
        usage = d.get("usageMetadata", usage)
        for c in d.get("candidates", []):
            for p in c.get("content", {}).get("parts", []):
                text.append(p.get("text", ""))
    return "".join(text), usage


if __name__ == "__main__":
    url, out = sys.argv[1], sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "gemini-3-flash-preview"
    t0 = time.time()
    text, usage = watch(url, model)
    open(out, "w").write(text)
    print(f"{len(text)} chars saved in {time.time() - t0:.0f}s, usage {usage}")
