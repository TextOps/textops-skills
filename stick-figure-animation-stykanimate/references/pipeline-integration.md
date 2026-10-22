# Integrating stick clips into a video pipeline

This skill makes standalone clips. When the stick figures are instead **beats inside a larger
narrated video** (a Remotion/After Effects/web timeline), the rules change. These are the ones that
cost real round-trips to learn, from shipping a 3-minute explainer where stick figures carried the
story and a motion-graphics layer carried the code and numbers.

## Division of labor: sticks lead, graphics support

- **Never put stick figures and busy graphics in the same frame.** A stick beat gets its own
  full-screen clip and tells the story (a courier runs the stolen file to a server, a figure types a
  trigger, a figure draws a sandbox box). The graphics layer shows the code, the terminals and the
  numbers. Alternate them; don't composite one over the other unless you have a tested alpha clip.
- **One beat per sentence (~2.5–4 s).** A stick clip usually *opens* a section (the first spoken
  sentence) and then hands off to the graphics for the data. Don't hold one animation for 10 s.

## Export format: opaque black vs. alpha

Two encodings, two uses. Render frames with StykAnimate as usual, then:

- **Opaque black MP4** — the clip plays full-screen on a black-background video. Simplest and most
  robust; use it unless you specifically need to see through the figure.
  ```bash
  ffmpeg -y -framerate 30 -i frames/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 17 clip.mp4
  ```
- **Transparent WebM (alpha)** — only when the figure must sit over other footage. Test it in the real
  compositor; alpha WebM support is uneven.
  ```bash
  ffmpeg -y -framerate 30 -i frames/f%04d.png -c:v libvpx-vp9 -pix_fmt yuva420p -crf 20 -b:v 0 clip.webm
  ```
- **Colors on black:** near-black fills vanish. A dark prop (e.g. a `[13,15,18]` slab) is invisible on
  `#000`. Outline props in a mid/accent color instead of filling them dark. Figures should be near-white
  or a saturated color.

To render a beat straight to a staged clip, a small runner around `scripts/render.mjs` + the ffmpeg
line above is enough; pass `--black` semantics by rendering on a black page and encoding opaque.

## Locomotion must be foot-locked (the #1 quality bug)

A walking/running figure whose planted foot slides backward reads as broken, and it is the most common
defect in stick beats. The fix is structural, not cosmetic:

- The **stance foot is fixed in world X for its whole step**; the hip advances at a speed *derived from
  the stride* (`step / (period/2)`), not a speed the caller picks independently. Desyncing hip speed
  from stride is the slip.
- Prefer a `gait()` helper that **returns the hip x it used**, so a beat cannot set a mismatched body
  speed. (`scripts/rig.mjs` ships `person`/`ik`/`stride`; add a `gait` that locks the stance foot and
  returns `{x, hipY, hands, feet, ...}`.)
- **Gate it numerically before rendering the full clip:** sample the clip and assert the planted foot's
  world X does not move during its stance — expect **< 3 px** drift (0 if derived correctly). A visual
  check misses small slides; the number does not.

## Timing: use the narration, not forced alignment

- **Do not install Whisper / forced alignment to time a stick clip.** The TTS gives you each line's
  duration; that is enough to place a clip under the sentence it illustrates.
- When you regenerate narration for an existing timed layout, remap the beat frames proportionally
  (`new_section_frames / old_section_frames`). Same words → it tracks closely without word alignment.

## Voice (if the pipeline narrates)

- Clone **one** reference voice for the whole video, or every clip's narration sounds like a different
  person. Pass the reference explicitly (e.g. `use_reference: true` + a baked reference WAV); an empty
  voice description with no reference drifts per call.

## Generated clips are build artifacts

Rendered stick MP4s (and narration audio) are regenerated from the beat scripts. Keep them **out of
git** (gitignore the staged-clip and audio folders) the same way build output is ignored; commit the
beat scripts, not the megabytes.

## Checklist before handing a clip to the pipeline

1. Foot-drift gate passes (< 3 px) for any walk/run beat.
2. Encoded opaque-black (or tested alpha) at the pipeline's fps and resolution.
3. Colors are visible on the target background (no dark-on-black).
4. Duration matches the sentence/beat it illustrates.
5. The clip reads with sound off — the action is legible in 3 seconds.
