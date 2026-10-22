// Helpers for scene scripts: figure/segment builders, two-bone IK, eased key tracks, mirroring.
export const PI = Math.PI;

export const seg = (id, parent, length, angle, thickness, extra = {}) => ({
  segment_id: id, parent_id: parent, length, angle_rad: angle, thickness, bend_rad: 0,
  primitive_code: 0, aux_code: 0, flags: 0, segment_type: 'line', segment_kind: 'line',
  color_rgb: [17, 17, 17], transparency: 0, visible: true, z_order: id, ...extra,
});
export const fillCircle = { primitive_code: 3, flags: 3, segment_type: 'circle', segment_kind: 'circleFill' };
export const figure = (id, name, segments) => ({
  figure_type_id: id, name, segment_count: segments.length, segments, polyfills: [], image_assets: [], text_assets: [],
});
/** Reorder drawing: ids listed first draw at the back. */
export const drawOrder = (fig, ids) => ids.forEach((id, i) => { fig.segments[id - 1].z_order = i + 1; });

/**
 * Standard person: 1 torso, 2 head, 3-4 near arm, 5-6 far arm, 7-8 near leg, 9-10 far leg.
 * `color` / `farColor` are the user's chosen colors (required). `k` scales the 960×540 proportions (use ~2.3 for a full-height figure at 1080×1350).
 */
export function person(id, name, { k = 1, color, farColor = color, torso = 13, limb = 10 } = {}) {
  if (!color) throw new Error('person(): pass the color the user chose');
  const L = { torso: 80 * k, head: 42 * k, upper: 54 * k, fore: 50 * k, thigh: 66 * k, shin: 64 * k };
  const far = { color_rgb: farColor };
  const f = figure(id, name, [
    seg(1, 0, L.torso, -PI / 2, torso * k, { color_rgb: color }), seg(2, 1, L.head, -PI / 2, 0, { ...fillCircle, color_rgb: color }),
    seg(3, 1, L.upper, 1.4, limb * k, { color_rgb: color }), seg(4, 3, L.fore, 1.4, limb * .9 * k, { color_rgb: color }),
    seg(5, 1, L.upper, 1.7, limb * k, far), seg(6, 5, L.fore, 1.7, limb * .9 * k, far),
    seg(7, 0, L.thigh, 1.4, limb * 1.2 * k, { color_rgb: color }), seg(8, 7, L.shin, 1.6, limb * 1.1 * k, { color_rgb: color }),
    seg(9, 0, L.thigh, 1.7, limb * 1.2 * k, far), seg(10, 9, L.shin, 1.6, limb * 1.1 * k, far),
  ]);
  drawOrder(f, [5, 6, 9, 10, 1, 2, 7, 8, 3, 4]);
  return { figure: f, L };
}

/**
 * Two-bone IK from joint (sx,sy) to target (tx,ty). Returns {u, v, ex, ey}: world angles of both bones and
 * the middle joint. `pick(option)` chooses between the two solutions — larger wins:
 *   elbows down: o => o.ey      knees forward (facing right): o => o.ex      elbow up: o => -o.ey
 * Unreachable targets are clamped (the limb straightens toward them).
 */
export function ik(sx, sy, tx, ty, a, b, pick) {
  let dx = tx - sx, dy = ty - sy, d = Math.hypot(dx, dy);
  const max = a + b - .5, min = Math.abs(a - b) + .5;
  if (d > max) { dx *= max / d; dy *= max / d; d = max; }
  if (d < min) { dx *= min / d; dy *= min / d; d = min; }
  const base = Math.atan2(dy, dx), off = Math.acos((a * a + d * d - b * b) / (2 * a * d));
  return [base + off, base - off].map(u => {
    const ex = sx + a * Math.cos(u), ey = sy + a * Math.sin(u);
    return { u, ex, ey, v: Math.atan2(sy + dy - ey, sx + dx - ex) };
  }).sort((p, q) => pick(q) - pick(p))[0];
}

export const lerp = (a, b, t) => a + (b - a) * t;
export const ease = t => (t = Math.max(0, Math.min(1, t)), t < .5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);

/** Eased keyed value: track([[frame, value], ...], t). Values may be numbers or [x, y] arrays. */
export function track(keys, t) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) {
    const [t0, a] = keys[i - 1], [t1, b] = keys[i], u = ease((t - t0) / (t1 - t0));
    return Array.isArray(a) ? a.map((v, j) => lerp(v, b[j], u)) : lerp(a, b, u);
  }
  return keys.at(-1)[1];
}

/** Mirror a right-facing pose so it faces left. */
export const mirrorAngles = angles => angles.map(a => PI - a);

/** Walk/run cycle: feet [dx, lift] relative to the hip and a hip bob, for frame t. */
export function stride(t, { period = 22, reach = 48, lift = 34, bob = 8 } = {}) {
  const p = t * 2 * PI / period;
  return {
    near: [reach * Math.sin(p), Math.max(0, Math.cos(p)) * lift],
    far: [-reach * Math.sin(p), Math.max(0, -Math.cos(p)) * lift],
    bob: -bob * Math.abs(Math.cos(p)),
    swing: Math.sin(p),
  };
}

/** Deterministic pseudo-random numbers, so re-renders match. */
export function random(seed = 7) {
  return () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
}

/** Read a PNG as a data URL for doc.backgrounds. */
export async function pngDataUrl(file) {
  const fs = await import('node:fs');
  return 'data:image/png;base64,' + fs.readFileSync(file).toString('base64');
}
