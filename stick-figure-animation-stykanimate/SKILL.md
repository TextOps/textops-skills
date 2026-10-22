---
name: stick-figure-animation-stykanimate
description: Create stick-figure animations (MP4, GIF and an editable .styk project) with the open-source StykAnimate app (github.com/filippocalippo/StykAnimate-App). Use when the user asks for a stick-figure / Pivot-style animation, an animated explainer or social-media clip with stick figures (LinkedIn, Reels, Shorts), or wants to edit a .styk project. Also trigger on "אנימציית מקלות", "איש מקלות", "תעשה לי אנימציה".
license: MIT
compatibility: "Designed for Claude Code. Requires git, Node.js 22+, Python 3.10+ with Pillow, FFmpeg, and Playwright with Chromium."
metadata:
  version: "1.0.0"
  author: "TextOps"
---

# StykAnimate animations

You build the animation **as code**: a Node script writes a native StykAnimate document (JSON) using the app's
own helpers, StykAnimate's renderer draws every frame in headless Chromium, ffmpeg encodes it, and the app's
local service converts it to a `.styk` project the user can open and edit at https://app.stykanimate.com.

Nothing here needs a GPU or the Electron app. Read `references/document-model.md` before writing a scene —
the coordinate and angle conventions are not obvious and getting them wrong wastes a render cycle.

## Workflow

Follow these steps in order. Do not skip the concept and contact-sheet steps: they are where quality comes from.

1. **Brief.** Find out where it will be posted (sets the format), the message or joke, the language of any
   on-screen text, and whether it must loop. If the user gives a reference image, match its palette, font
   and composition.
2. **Concepts.** When the brief is open-ended ("make something for my post"), propose 2–4 short concepts,
   each with a one-line beat sheet, recommend one, and let the user choose. A good concept:
   - reads with the sound off, in 3 seconds, for someone scrolling;
   - has one visual metaphor and a punchline beat (a reveal, a reversal, a failed attempt);
   - lasts 8–15 s; for a loop, starts and ends on the same state (an empty stage is the easiest seam).
3. **Setup.** Run `scripts/setup.sh` once per environment (clones the app, installs dependencies, starts the
   local service in the background). Re-run it if a render fails with `ERR_CONNECTION_REFUSED`: the service
   does not survive the shell that started it unless it runs as a background task.
4. **Background.** Draw static scenery and on-screen text into a PNG with Pillow (see
   `examples/who-monitors-the-monitor-bg.py`). Anything that must move or change per frame is a figure, not
   background. For text that appears later, make a second background PNG and switch `frame.background_id`.
5. **Scene script.** Copy `examples/who-monitors-the-monitor.mjs` as the starting point. Define figures,
   key poses on a frame timeline, and generate **one keyframe per output frame** (`duration_raw: 1`).
   Use `scripts/rig.mjs` for two-bone IK, eased key tracks and figure helpers.
6. **Contact sheet.** Render 8–12 frames at the story beats (`scripts/render.mjs doc.json 0,40,80,... out/`),
   tile them with `scripts/contact_sheet.py`, and **look at the image**. Crop and zoom into any pose that
   looks off. Typical problems: elbows or knees bending the wrong way (fix the IK `pick`), a hand that
   misses its target (out of reach — move the body), limbs hidden behind the head, a camera zoom that
   crops the action. Fix and re-check only the changed frames.
7. **Full render and encode.** `scripts/render.mjs doc.json all frames/`, then `scripts/encode.sh`.
8. **Editable project.** `scripts/export_styk.sh doc.json out.styk` imports the JSON through the app's
   service, exports `.styk`, and re-imports it to verify the frame count. Pivot `.piv` export rejects
   image backgrounds — offer `.styk` only unless the scene has none.
9. **Deliver.** Send the MP4, GIF and `.styk`, plus a cover/thumbnail PNG of the punchline frame for
   social posts. State what each file is for. Say plainly that the `.styk` was verified by re-import, not
   by opening it in the app's UI.

## Formats

| Destination | Size | Notes |
| --- | --- | --- |
| LinkedIn / Instagram feed | 1080×1350 (4:5) | Largest size the feed shows uncropped. The LinkedIn post composer letterboxes every video in a 16:9 box — that is only the preview. |
| Reels / Shorts / Stories / TikTok | 1080×1920 (9:16) | Design for it from the start; padding a 4:5 video leaves dead space. |
| Website / YouTube | 1920×1080 or 960×540 | |

Set `canvas_width`/`canvas_height` to the final size and render at scale 1 — do not upscale afterwards.
Social video autoplays muted: never rely on sound, keep text large (≥ 60 px at 1080 wide).

## Looping

- Total frame count must be a multiple of every periodic effect (a light blinking every 10 frames on,
  10 off → multiple of 20; a walk cycle of 22 frames if the figure is visible at the seam).
- Make the first and last frames the same state. Easiest: the character enters from off-screen and leaves
  the same way, so the seam is an empty stage.
- A tracking camera or any lagged value must start from the value it ends at
  (initialise it from frame 0's target, not a constant).

## Style that works

- **Silhouette:** near-black figures (`[17,17,17]`) on an off-white or sunset background, one accent
  color (red) for emphasis marks, a lit LED, a padlock. Thick limbs (torso 50–60 px, limbs 25–35 px at
  1080 wide) read better than thin Pivot lines at social-media sizes.
- **Font:** Inter Display (Medium + Black) is installed at `/usr/share/fonts/opentype/inter/`. Put the
  punctuation of a question or answer in the accent color.
- **Effects:** impact marks = 3 short accent-colored lines radiating from a point for 4–6 frames; sparks =
  a figure of 10–12 rays with random angles each frame and a scale pulse; steam = a 4-segment chain with
  sine-wobbling angles.
- **Camera:** punch-in (scale 0.7–0.8) on the key beat, a decaying random shake of 6–14 px on impacts,
  a slow push-in at the end.

## Things that will bite you

- Segment angles are **absolute world angles** in radians, y axis pointing **down** (−π/2 is straight up).
  They are not relative to the parent.
- To mirror a figure to face left, mirror every angle: `a → π − a`, and mirror x offsets around the hip.
- A segment with length 0 still draws a round dot. To hide parts, swap to a different figure type for those
  frames (with a different `unique_id`) instead of shrinking them.
- `prepareBackgrounds` must run for every frame whose `background_id` differs, or that frame renders black.
- The renderer applies `frame.camera` itself; always pass `view: {x:0, y:0, scale:1}`.
- Load `http://127.0.0.1:<port>/` and then replace the DOM; loading other static paths returns 404.
- The headless page logs harmless `Cannot read properties of null` errors after the DOM swap. Ignore them.
