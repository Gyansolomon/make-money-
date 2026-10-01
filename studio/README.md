# Video studio: map and story Shorts

Code for the 9:16 story Shorts we prototyped (the Chile videos and the Niger narration). It sits
next to the clipper in `moneymaker/`, which it reuses for captions and ffmpeg.

The research behind it (style guide, formulas, topic lists, what worked and what didn't) is
in [`../research/`](../research/README.md).

## What's here

| Path | What it is |
|---|---|
| `chile/gfx.py` | Rendering primitives: orthographic terrain globe camera, tilted 3D-style ground plane, country fills and glowing borders, flags, labels, pins, arrows, dashed routes, photo panels, whip transitions |
| `chile/chars.py` | Characters: mocap-driven stickmen with props, countryballs (flag body, googly eyes that blink and dart), speech bubbles, smoke and flash |
| `chile/voice3.py` | **v3** narration: Kokoro TTS, narrator plus character voices, timed pauses for gags, word timings via faster-whisper |
| `chile/scenes3.py` | **v3** scene timeline: chili gag, stickman skit, countryballs, Chile growing south and north |
| `chile/render3.py` | **v3** render: frames in 4 parallel chunks, music bed ducked under speech, SFX cue sheet, captions, loudnorm to -14 LUFS |
| `chile/voice.py`, `scenes.py`, `render_all.py` | **v2** (narrator only, terrain maps and photos). `voice3.py` reuses `align()` from `voice.py` |
| `chile/assets/` | Fonts (OFL), CC0 music bed and sound effects from Freesound, rawpixel CC0 chili cut-out, sound catalogues (`sounds*.json`) and Gemini's ratings of them |
| `chile/imgs/` | Wikimedia photos used in v2 (CC BY-SA, credits in `../research/credits/chile-v2.txt`) |
| `niger/voice.py` | "The Trees Nobody Planted" narration, open-loop version |
| `niger/mix.py` | ~60 s audio track: Liam narration, ducked music, SFX on key lines (the approved audio) |
| `tools/gemini_watch.py` | Gemini watches a YouTube URL and writes a timestamped style breakdown |
| `tools/rate_music.py` | Gemini listens to music excerpts and rates them as a bed under narration |
| `tools/freesound_search.py` | Finds CC0 sounds on Freesound without an API key |
| `setup_assets.py` | Downloads the big files kept out of git (Kokoro model, world texture, country borders) |

## Setup

```bash
pip install -r ../requirements.txt kokoro-onnx soundfile opencv-python-headless shapely numpy pillow requests
python setup_assets.py            # ~1 GB of downloads, once
export GEMINI_API_KEY=...         # only for the tools/ scripts
```

The stickmen read mocap clips from the OpenMontage ink-theater (`ink-theater/mocap/clips.js`).
That repo is AGPL, so the file isn't copied here. Clone `OpenMontage-video-creator-` next to this
repo, or set `INK_CLIPS=/path/to/clips.js`.

## Render the Chile v3 Short

```bash
cd chile
python voice3.py     # narration + word timings -> out3/
python render3.py    # ~8 min on 4 cores -> ../output/why-chile-is-so-thin-v3.mp4
```

## Make the Niger audio

```bash
cd niger
python mix.py        # writes trees-nobody-planted-LIAM.mp3 / -PUCK.mp3
```

## Known gaps

- Characters are simple stickmen and balls, and objects like the chili are flat cut-outs. The
  upgrade plan (Blender for 3–5 hero shots, AI images with fake-3D lighting for the rest) is in
  `../research/editing-upgrade-plan.md`.
- Scenes are hand-written per video. The next step is a generator that takes a script and a
  scene plan and builds the timeline.
- `assets/sfx/pop_1.mp3` is actually a gunshot (Freesound title "Door slam - Gun shot"). v2
  used it as a pop by mistake; v3 uses the clean pops in `sfx2/`. Don't use `sfx/pop_1.mp3`
  for pops.
