# The Trees Nobody Planted: music video

A 98-second spoken-word track with code-rendered visuals and word-synced karaoke type, made in
the style of [pdoom-video](https://github.com/mexicat/pdoom-video) by Giacomo Magnanini. The
engine in `app/src/engine` and the render script come from that repo (MIT, see
`LICENSE-pdoom-video`). The song, the words and the scenes are ours.

## Pipeline

1. `tools/script.py`: the words, how Kokoro says them, and where each line sits in the song.
2. `python tools/vocals.py`: Kokoro (Liam) reads each line, snapped to the 100 BPM grid. Writes `work/`.
3. `python tools/align.py`: faster-whisper word timings, written to `data/lyrics.json`.
4. `python tools/music.py`: synthesizes and mixes the beat. Writes `audio/song.mp3` and `data/audio.json`.
5. `python tools/listen.py`: optional. Asks Gemini to review the mix.
6. Visuals: `app/src/timeline.ts` sets eight plates, one per section. They live in `app/src/scenes/`.

## Render

```
cd app && bun install
# no GPU: point at a Chromium and SwiftShader is used
export CHROME_PATH=/path/to/chrome
bun scripts/render.ts stills --t 12.5,70 --out ../out/wip
bun scripts/render.ts video --fps 30 --samples 1 --out ../out/trees.mp4
```

A frame takes about 0.65 s under SwiftShader. On a Mac with Chrome, leave out `CHROME_PATH` and
use `--fps 60 --samples auto` for motion blur.
