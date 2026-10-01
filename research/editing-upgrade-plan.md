# Editing upgrade plan

## Where we are
Our renderer (`studio/chile/`) does: terrain globe with zooms, a tilted pseudo-3D view, glowing
countries, flags, labels, pins, arrows, photos with whip transitions, countryballs, stickmen,
speech bubbles, a ducked music bed, timed SFX and word-by-word captions.

The gap with GeoGlobeTales is the **look**: his objects are 3D and lit (e.g. a 3D chili lying on
Chile with a shadow); ours are flat cut-outs and simple characters.

## Closing the gap

| Option | How | Cost | Use for |
|---|---|---|---|
| **AI image + fake 3D** | Generate a realistic object (FLUX via fal.ai), warp it to the tilted map, add a contact shadow and lighting that matches the map | ~$0.01–0.03 per image (the $10 budget covers hundreds) | Most objects and props |
| **Real 3D in Blender** | Blender driven by Python on the VPS: a real 3D globe, free 3D models, real shadows, smooth camera moves | Free, but slow without a GPU | 3–5 hero shots per video |
| **AI image-to-video** (Kling, Runway, Veo) | Animate a still | ~$0.10–0.50 per second | One wow shot per video at most |
| **Jev** (TypeSafe AI) | Fast decisions inside the generator: which SFX, which camera move, QC checks | API cost | Later, during main production |

Planned first test: redo the chili scene both ways (AI image + fake 3D vs Blender) as a
10-second side-by-side.

## Studying his edits
- **YouTube Data API doesn't help:** it returns metadata (titles, views, thumbnails), never the video file.
- **Downloading from the cloud is blocked:** YouTube's bot wall returns 403 to data-center IPs. A workaround through a third-party token helper (bgutil) was blocked by the cloud environment's safety check, and we stopped there.
- **What works now:** `studio/tools/gemini_watch.py`. Google fetches the video, Gemini returns a timestamped shot-by-shot breakdown.
- **Better:** a 10–20 s phone screen recording shared via Google Drive. Frames can be pulled and looked at directly (shadows, lighting, angles, cut timing).
- **On a home PC:** yt-dlp usually works from a residential connection. Note that YouTube's terms don't allow downloading other people's videos. If used, it's only to study timing and technique; never reuse footage, sound or graphics, and delete the files afterwards.

## Not the whole story
Edits are only part of why he wins: he also has 2M subscribers and posts consistently. Story
quality still matters most.
