# StykAnimate document model (what a scene script writes)

Source of truth: `src/demo.mjs`, `src/pivot/geometry.mjs`, `src/editor-camera.mjs`, `backend/README.md`
in the StykAnimate-App repository. Import helpers from the app instead of re-creating them:

```js
const { createObject, createFrame, emptyDocument } = await import(`${APP}/src/demo.mjs`);
```

## Document

```js
const doc = emptyDocument();             // version 5, fps 24, _styk metadata
doc.canvas_width = 1080; doc.canvas_height = 1350; doc.fps = 24;
doc.figure_types = [/* figures */];
doc.backgrounds = [{ background_id: 1, kind: 1, mime_type: 'image/png', asset_url: 'data:image/png;base64,...' }];
doc.keyframes = [/* one frame per output frame */];
doc._styk.name = 'Project name';         // shown in the app
```

## Figure type

```js
{ figure_type_id: 1, name: 'Guard', segment_count: n, segments: [...], polyfills: [], image_assets: [], text_assets: [] }
```

Segment:

```js
{ segment_id: 1, parent_id: 0,           // 0 = attached to the figure's root (the object's root_x/root_y)
  length: 190, angle_rad: -Math.PI/2,    // default pose; frames override angles
  thickness: 58, color_rgb: [r, g, b], transparency: 0,    // the user's colors; transparency 0–255
  visible: true, z_order: 1,             // higher draws on top
  segment_type: 'line', segment_kind: 'line', primitive_code: 0, aux_code: 0, flags: 0, bend_rad: 0 }
```

- A segment starts at its parent's **end** point and runs `length` px along `angle`.
- Filled circle (head, LED, spark core): `primitive_code: 3, flags: 3, segment_type: 'circle', segment_kind: 'circleFill'`.
  The segment is the circle's diameter; it is drawn between the segment's start and end.
- Outline circle: `primitive_code: 1, flags: 1, segment_type: 'circle', segment_kind: 'circle'`.
- Invisible connector (to offset a child, e.g. a code line or a hood): `visible: false`.

## Object (a figure instance in a frame)

```js
const obj = createObject(figure, uniqueId, rootX, rootY);
obj.angles = [...];       // one ABSOLUTE world angle per segment, same order as figure.segments
obj.scale = 1;            // multiplies lengths (sparks pulse with this)
obj.len_flag = 1; obj.lengths = [...];   // optional per-frame lengths (growing text bars, progress bars)
```

- Keep `uniqueId` stable for the same character across frames; the app uses it to link keyframes.
- To change a figure's parts mid-animation (sword knocked out of a hand, more lines of code appear), use a
  second figure type and a different `uniqueId` from that frame on.

## Frame

```js
const frame = createFrame(objects, 1);   // duration_raw 1 = one frame at doc.fps
frame.background_id = 1;                 // 0 = none
frame.camera = { is_default: false, x: dx, y: dy, scale: s, angle_rad: 0 };
```

Draw order between objects is the array order (later is on top).

## Camera

- `x`, `y` = offset of the camera centre from the canvas centre, in document px.
- `scale` = size of the camera frame relative to the canvas. `0.75` **zooms in** (the frame is smaller).
- To centre the shot on point `(cx, cy)` at zoom `1/s`: `x = cx - W/2, y = cy - H/2, scale = s`.
- `is_default: true` with zeros is the identity camera.

## Coordinates and angles

- Origin top-left, y down. `angle = 0` points right, `-π/2` up, `π/2` down, `π` left.
- Facing left = mirror: `angle → π − angle`, `x → 2·hipX − x`.
- Human proportions at 960×540: torso 80, head 42, upper arm 54, forearm 50, thigh 66, shin 64.
  Multiply by ~2.3 for a full-height figure at 1080×1350.

## Service endpoints used by the scripts

The local service is `node scripts/serve.mjs --port 47831` in the app directory. Requests must send
`Origin: http://127.0.0.1:47831`.

| Request | Use |
| --- | --- |
| `GET /api/health` | readiness |
| `POST /api/import?filename=x.json` (raw body) | normalises the document → `{ok, document, sourceId}` |
| `POST /api/export` `{document, sourceId, format: 'styk', filename}` | binary `.styk` |
