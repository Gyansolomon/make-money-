# Why Chile is so thin

Three versions were rendered. v3 is the one to build on; its script lives in
`studio/chile/voice3.py` and its scenes in `studio/chile/scenes3.py`.

## What changed between versions

| Version | Story | Feedback |
|---|---|---|
| v1 | First test: spinning globe and flat maps, no music | Led to studying the reference Shorts with Gemini |
| v2 | Number hook, Chile over Europe, terrain maps, photos, music and 43 SFX | "The sound was off and the story is also off" |
| v3 | The reference's growth story, with characters and jokes | Script: "best, I like it", plus asks for stickmen, countryballs with moving eyes, a Spanish voice and fewer out-of-line sounds. Render: "our edits are very poor compared to his" (flat chili vs his 3D chili) |

**Why v2's story felt off:** the reference is a **growth story** (Chile starts as a small strip,
can't grow east because of the Andes, grows south, then north through war). v2 was a list of
facts, told partly out of order.

**v2 sound problems** (found by Gemini, fixed in v3): a "pop" that was really a gunshot, a
second music track playing under the war scene, music ~16 dB under the voice (too quiet), and 6
heavy booms in 54 seconds.

## v3 beats
1. "Let's talk about Chile." A chili drops onto the map with a slide whistle and a thud. "No, not that chili. This Chile." The chili is yanked away, "NOT THAT CHILI" pops up, the country lights up red.
2. "Ever wondered why it's so ridiculously long?" "LOOOOONG" stretches along the country with a boing. Chile laid over Europe: Arctic Circle to North Africa, yet 177 km wide on average.
3. "So how does a country end up shaped like a noodle?"
4. Mapuche and Spanish: stickman skit. The captain (Spanish-accented voice): "Ah! What beautiful, empty land!" Mapuche: "Hello! We live here." Bang, smoke, they fall. "Now, we live here." The narrator adds that the Mapuche fought back for centuries.
5. 1818: only the central valley lights up. "Tiny."
6. A tiny Chile countryball: "Time to grow! Let's go east!" It bonks off the Andes. "Okay. South it is." (sad trombone)
7. Chile grows south (the 1881 treaty with Argentina follows the highest peaks), then north (War of the Pacific, nitrates). Tada fanfare.
8. An angry Bolivia ball: "Hey! Where did my ocean go?" Bolivia still has a navy and a Day of the Sea.
9. "Trapped between mountains and ocean, Chile could only grow one way. Longer."

Voices (Kokoro): narrator am_liam, Spanish captain em_alex, Mapuche am_onyx, Chile am_puck,
Bolivia am_fenrir. Gemini rated each 9–10/10 for its role.

Gemini's review of the first v3 render: 9/10 overall, 8/10 humor, 10/10 story clarity. Five
fixes were then applied (a loud gunshot, a missing chili sound, a thin Arctic line, a too-strong
blue on Argentina, a speech bubble that vanished too fast).

## Facts checked
- Over 4,000 km long, about 177 km wide on average.
- Laid over Europe it runs from above the Arctic Circle to the Libyan coast (measured on our map).
- Santiago founded 1541 by Pedro de Valdivia; independence 1818; boundary treaty with Argentina 1881; War of the Pacific 1879–1884.
- Bolivia kept its navy and celebrates Día del Mar every year.

## Still weak
Simple stickmen and balls; the chili is a flat cut-out where the reference used a 3D chili lying
on the country. See `../editing-upgrade-plan.md`.
