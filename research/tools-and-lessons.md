# Tools and lessons

## Gemini: our eyes and ears
Claude can't watch video or hear audio, so Gemini (free tier) does it:
- **Watch YouTube Shorts** by URL and return timestamped breakdowns (`studio/tools/gemini_watch.py`).
- **Rate music and SFX** as a bed under narration (`studio/tools/rate_music.py`).
- **Review our renders and audio:** pronunciation, humor, pacing, sound problems. It found the gunshot "pop", the double music track and the too-quiet music in Chile v2.

Practical notes:
- Key in the environment as `GEMINI_API_KEY`, sent as the `x-goog-api-key` header. Never paste keys into chat.
- Use `streamGenerateContent?alt=sse`; plain requests were cut by the cloud proxy after ~30 s.
- Models that worked: `gemini-3-flash-preview`, `gemini-3.5-flash`. `gemini-2.5-flash` is retired for new keys.
- 503 "overloaded" is common. Wait and retry; it doesn't use quota.
- One Short analysis is ~1 request and ~14k tokens.

## Voice: Kokoro TTS (free, Apache-2.0)
- **Narrator: `am_liam`** (chosen by the user over Puck, Fenrir, Onyx, Michael, George), speed ~1.05–1.15.
- Character voices: `em_alex` (Spanish accent), `am_onyx` (deep, deadpan), `am_puck` (cheerful), `am_fenrir` (annoyed).
- Spell out decades: "nineteen seventies", not "1970s".
- Have Gemini listen to each narration for mispronunciations before rendering.
- Upgrade path if needed: ElevenLabs, ~$5/month.

## Audio mix that works (`render3.py`, `niger/mix.py`)
- One music track only. Music ~-13 dB between lines, ducked to ~-20 dB under speech (RMS envelope of the voice). v2 used -17/-25 and the music was nearly inaudible.
- Skip the music's intro swell so energy starts immediately; fade in ~0.5 s, out 1.5–2 s.
- Cap long SFX (impact 2 s, footsteps 1.2 s, musket 1.6 s, tada 1.8 s) and fade their tails.
- 2–3 big booms per video at most; comedy stings (record scratch, sad trombone, boing) on jokes.
- Final loudness: `loudnorm=I=-14:TP=-1.5:LRA=11`.

## Asset sources

| Source | Status | Notes |
|---|---|---|
| Natural Earth (naciscdn.org) | ✅ | Shaded-relief raster and country borders, public domain |
| Freesound | ✅ | CC0 SFX and music; search page scraped, no API key (`tools/freesound_search.py`) |
| rawpixel | ✅ | CC0 illustrations (the chili) |
| Openverse API | ✅ | Image search |
| Wikimedia Commons | ⚠️ | Works but rate-limits (429); retry slowly. Photos are CC BY-SA, credit in the description |
| Google Fonts | ✅ | Poppins ExtraBold (captions), Anton (big text) |
| Pixabay | ❌ | 403 bot protection from the cloud |
| NASA Blue Marble | ❌ | Links were dead |
| YouTube video files | ❌ | 403 from cloud IPs; see `editing-upgrade-plan.md` |

## Jev (TypeSafe AI)
Released 15 Sept 2026. A "System-1" decision model: give it a question with fixed options and it
picks one with a confidence score, claimed 40–200× faster and much cheaper than chat models. It
can't write scripts or speed up rendering.

Plan: Claude is the brain (story, script, scene plan, code); Jev makes the thousands of small
choices inside the generator (which SFX per cue, which camera move, clip-worthiness scores,
caption/label QC). Add its key as an environment credential when main production starts.

Sources: [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/typesafe-ais-jev-offers-an-alternative-to-llms-that-claims-to-be-193x-faster-and-445x-cheaper-system-one-type-model-is-bespoke-for-probabilistic-decision-making),
[Forbes](https://www.forbes.com/sites/ronschmelzer/2026/09/22/why-everyone-is-talking-about-jev-the-ai-that-doesnt-chat/).

## Other lessons
- **Render time:** ~8 minutes for a 74 s Short on 4 cores (drawing ~2,200 frames). A bigger VPS or smarter rendering fixes that, not a faster model.
- **File size:** the chat upload limit is 30 MB; re-encode to send (v2 went from 59 MB to 24 MB with no visible loss on a phone).
- **Check every repo before running it.** `short-video-generator-AI` turned out to be malware posing as an OpusClip alternative; it was deleted without being run.
- **Video types status:** clipper (working), map/history Shorts (working, look needs upgrading), curiosity Shorts (partly; needs picture scenes), stock-footage faceless Shorts (not built), premium 3D shots (not built).
