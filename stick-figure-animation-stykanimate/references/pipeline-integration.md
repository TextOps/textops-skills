# Handing stick clips to a video pipeline

This skill makes standalone clips. When the stick figures are instead **beats inside a larger video**
(any editor or compositor — a timeline app, a web/Remotion renderer, After Effects, ffmpeg concat),
this skill's job is to hand that pipeline clean clips. The pipeline itself — narration, motion graphics,
music, timing — is not this skill's concern and differs every time. What follows is the clip contract:
make the clips right, and any pipeline can drop them in.

## Sticks lead, graphics support

- **Never put stick figures and busy graphics in the same frame.** A stick beat gets its own clip and
  tells the story (a courier runs a file to a server, a figure types, a figure draws a box). The host
  pipeline shows code, UI or numbers in separate shots. Alternate them; don't composite a stick over a
  busy card unless you have a tested transparent clip.
- **One action per clip, a few seconds.** A stick clip usually illustrates one sentence or beat, then
  hands back to the pipeline. Don't hold one animation for 10 s.
- **It must read with the sound off, in ~3 seconds.** The host may caption it or not; the action alone
  has to be legible.

## Export format

Render frames with StykAnimate, then encode to what the pipeline wants:

- **Opaque MP4 on a flat background** — simplest and most robust; use it when the clip plays full-frame
  on a solid-color video. Render the figures on that background color and encode:
  ```bash
  ffmpeg -y -framerate <fps> -i frames/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 17 clip.mp4
  ```
- **Transparent clip (alpha)** — only when the figure must sit over other footage. Alpha support is
  uneven across editors, so test it in the real one before committing:
  ```bash
  ffmpeg -y -framerate <fps> -i frames/f%04d.png -c:v qtrle clip.mov          # ProRes/QTRLE alpha
  # or VP9 alpha WebM: -c:v libvpx-vp9 -pix_fmt yuva420p -crf 20 -b:v 0 clip.webm
  ```
- **Match the host's fps and resolution** at export, and letterbox rather than stretch if aspect ratios
  differ.
- **Colors must be visible on the target background.** A near-black fill vanishes on black; outline dark
  props in a mid/accent color instead of filling them dark.

## Locomotion must be foot-locked (the #1 quality bug)

A walking or running figure whose planted foot slides backward reads as broken — the most common defect
in stick beats. The fix is structural:

- The **stance foot is fixed in world X for its whole step**, and the hip advances at a speed *derived
  from the stride* (`step / (period/2)`), not a speed chosen independently. Desyncing hip speed from
  stride is the slide.
- Prefer a walk helper that **returns the hip x it used**, so a beat cannot set a mismatched body speed.
  (Add a `gait` alongside the `person`/`ik`/`stride` helpers in `scripts/rig.mjs` that locks the stance
  foot and returns `{x, hipY, hands, feet}`.)
- **Gate it numerically before rendering the whole clip:** sample the clip and assert the planted foot's
  world X does not move during its stance — expect **< 3 px** drift (0 if derived correctly). A visual
  check misses small slides; the number does not.

## Timing

- You do **not** need forced alignment (Whisper etc.) to place a clip — that's the host pipeline's job.
  Export each clip at the duration of the beat it illustrates and let the pipeline position it.
- If the pipeline re-times later, keep the clip's action centered and loosely paced so a ±20% stretch
  still reads.

## Keep generated clips out of the repo

Rendered MP4s are regenerated from the beat scripts. In the host project, gitignore the staged-clip
folder the same way build output is ignored — commit the beat scripts, not the megabytes.

## Checklist before handing a clip over

1. Foot-drift gate passes (< 3 px) for any walk/run beat.
2. Encoded at the host's fps and resolution, opaque (or tested alpha).
3. Colors visible on the target background — no dark-on-background.
4. Duration matches the beat it illustrates.
5. Reads with sound off in ~3 seconds.
