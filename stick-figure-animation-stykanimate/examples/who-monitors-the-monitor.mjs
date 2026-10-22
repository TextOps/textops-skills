// "Who monitors the monitor?" — a guard tries to unplug the camera that watches him. Native StykAnimate document.
import fs from 'node:fs';
// STYK_APP = the app directory printed by scripts/setup.sh
const APP = `${process.env.STYK_APP || `${process.env.HOME}/StykAnimate-App`}/src/`;
const { createObject, createFrame, emptyDocument } = await import(APP + 'demo.mjs');
const here = name => new URL('./' + name, import.meta.url);

const PI = Math.PI, W = 1080, H = 1350, FLOOR = 1150, FRAMES = 320;   // 320 = a multiple of the light's 20-frame blink, so the loop is seamless
const INK = [17, 17, 17], RED = [226, 35, 38];
const seg = (id, parent, length, angle, thickness, extra = {}) => ({ segment_id: id, parent_id: parent, length, angle_rad: angle,
  thickness, bend_rad: 0, primitive_code: 0, aux_code: 0, flags: 0, segment_type: 'line', segment_kind: 'line',
  color_rgb: INK, transparency: 0, visible: true, z_order: id, ...extra });
const fillCircle = { primitive_code: 3, flags: 3, segment_type: 'circle', segment_kind: 'circleFill' };
const figure = (id, name, segments) => ({ figure_type_id: id, name, segment_count: segments.length, segments, polyfills: [], image_assets: [], text_assets: [] });

// ---------- the guard (silhouette, peaked cap) ----------
// 1 torso, 2 head, 3-4 near arm, 5-6 far arm, 7-8 near leg, 9-10 far leg, 11-12 cap crown, 13 visor, 14 belt
const L = { torso: 190, head: 96, upper: 118, fore: 112, thigh: 150, shin: 146 };
const GUARD = figure(1, 'Guard', [
  seg(1, 0, L.torso, -PI / 2, 58), seg(2, 1, L.head, -PI / 2, 0, fillCircle),
  seg(3, 1, L.upper, 1.5, 30), seg(4, 3, L.fore, 1.5, 26), seg(5, 1, L.upper, 1.6, 30), seg(6, 5, L.fore, 1.6, 26),
  seg(7, 0, L.thigh, 1.4, 38), seg(8, 7, L.shin, 1.6, 32), seg(9, 0, L.thigh, 1.7, 38), seg(10, 9, L.shin, 1.6, 32),
  seg(11, 2, 34, 0, 40), seg(12, 2, 40, PI, 40), seg(13, 11, 34, .4, 12), seg(14, 0, 1, 0, 1, { visible: false }),
]);
[5, 6, 9, 10, 14, 1, 2, 11, 12, 13, 7, 8, 3, 4].forEach((id, i) => { GUARD.segments[id - 1].z_order = i + 1; });

// ---------- the camera on its bracket ----------
const PIVOT = [950, 430];
const CAMERA = figure(2, 'Camera', [
  seg(1, 0, 150, PI, 86), seg(2, 1, 22, PI, 64),                          // body, lens
  seg(3, 0, 44, -PI / 2, 1, { visible: false }), seg(4, 3, 178, PI, 14),   // hood over the lens
]);
const LED = figure(3, 'Camera light', [seg(1, 0, 16, 0, 0, { ...fillCircle, color_rgb: RED })]);
const BONK = figure(4, 'Impact', [0, 1, 2].map(i => seg(i + 1, 0, 30, 0, 7, { color_rgb: RED })));

// ---------- helpers ----------
const lerp = (a, b, t) => a + (b - a) * t;
const ease = t => (t = Math.max(0, Math.min(1, t)), t < .5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
function ik(sx, sy, tx, ty, a, b, pick) {
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
// keyed tracks: [[frame, value], ...] with eased segments
function track(keys, t) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) {
    const [t0, a] = keys[i - 1], [t1, b] = keys[i], u = ease((t - t0) / (t1 - t0));
    return Array.isArray(a) ? a.map((v, j) => lerp(v, b[j], u)) : lerp(a, b, u);
  }
  return keys.at(-1)[1];
}

// ---------- choreography (24 fps) ----------
const T = { arrive: 54, lookCam: 66, lookPlug: 80, reach: 92, bonk: 100, step: 128, rattle: 140, giveUp: 172, shake: 178, salute: 206, tagline: 214, lower: 236, turn: 244, gone: 304 };
// he walks in from off-screen left and, after giving up, walks back out the same way: the loop point is an empty stage
const OFF = -170;
const hipX = t => t >= T.turn ? lerp(630, OFF, Math.min(1, (t - T.turn) / (T.gone - T.turn)))
  : track([[0, OFF], [T.arrive, 560], [T.step - 8, 560], [T.step, 630]], t);
const walking = t => (t < T.arrive) || (t > T.step - 8 && t < T.step) || t >= T.turn;
// head tilt (negative = looking up)
const headTilt = t => track([[0, 0], [T.arrive, 0], [T.lookCam, -.55], [T.lookPlug - 4, -.55], [T.lookPlug, .2], [T.bonk, .1], [T.bonk + 3, -.15], [T.bonk + 10, .15],
  [T.giveUp, .2], [T.shake, -.5], [T.salute + 6, -.35], [T.lower - 8, -.3], [T.lower, 0], [FRAMES, 0]], t);
const lean = t => track([[0, .08], [T.arrive, .08], [T.reach, .16], [T.bonk, .2], [T.bonk + 4, -.02], [T.bonk + 14, .06], [T.rattle, .14], [T.giveUp, .14], [T.shake, 0], [T.lower - 8, -.02], [T.turn, .08], [FRAMES, .08]], t);
const BOX_EDGE = 816, PLUG = [890, 740], LOCK = [890, 828];

function guardAt(t) {
  const x = hipX(t);
  let hipY = FLOOR - 286, feet;
  if (walking(t)) {
    const p = t * 2 * PI / 22;
    feet = [[x + 48 * Math.sin(p), Math.max(0, Math.cos(p)) * 34], [x - 48 * Math.sin(p), Math.max(0, -Math.cos(p)) * 34]];
    hipY -= 8 * Math.abs(Math.cos(p));
  } else feet = [[x + 46, 0], [x - 38, 0]];
  const torso = -PI / 2 + lean(t), sh = [x + L.torso * Math.cos(torso), hipY + L.torso * Math.sin(torso)];
  const head = torso + headTilt(t);
  // near arm: swing → reach → bonk → shake it off → rattle the lock → salute
  const swing = walking(t) ? Math.sin(t * 2 * PI / 22) : 0;
  const rest = [x + 30 + 40 * swing, hipY + 20];
  const hc = [sh[0] + L.head * .5 * Math.cos(head), sh[1] + L.head * .5 * Math.sin(head)];
  const salute = [hc[0] + 62, hc[1] - 22];   // fingertips at the cap's brim
  let hand = track([[0, rest], [T.reach - 4, [x + 40, hipY + 10]], [T.bonk, [BOX_EDGE, PLUG[1] - 8]],
    [T.bonk + 6, [x + 70, sh[1] + 40]], [T.step + 2, [x + 70, sh[1] + 50]], [T.rattle, [LOCK[0] - 8, LOCK[1] - 10]],
    [T.giveUp, [LOCK[0] - 8, LOCK[1] - 10]], [T.shake + 4, [x + 34, hipY + 10]], [T.salute, salute], [T.lower - 8, salute], [T.lower, [x + 30, hipY + 20]]], t);
  if (t >= T.lower) hand = rest;
  if (t >= T.bonk + 6 && t < T.step - 6) hand = [hand[0] + 14 * Math.sin(t * 1.9), hand[1] + 10 * Math.cos(t * 2.3)];  // shaking out the sting
  if (t >= T.rattle && t < T.giveUp) hand = [hand[0] + 9 * Math.sin(t * 2.6), hand[1] + 6 * Math.sin(t * 3.4)];          // rattling the padlock
  if (t >= T.step && t < T.rattle) hand = track([[T.step, [x + 70, sh[1] + 50]], [T.rattle, [LOCK[0] - 8, LOCK[1] - 10]]], t);
  const back = [x - 22 - 40 * swing, hipY + 26];
  const elbowNear = t >= T.salute - 12 && t < T.lower - 2 ? (o => o.ex) : (o => o.ey);
  const a1 = ik(...sh, ...hand, L.upper, L.fore, elbowNear), a2 = ik(...sh, ...back, L.upper, L.fore, o => o.ey - o.ex);
  const knee = o => o.ex;
  const l1 = ik(x, hipY, feet[0][0], FLOOR - feet[0][1], L.thigh, L.shin, knee), l2 = ik(x, hipY, feet[1][0], FLOOR - feet[1][1], L.thigh, L.shin, knee);
  const angles = [torso, head, a1.u, a1.v, a2.u, a2.v, l1.u, l1.v, l2.u, l2.v, head + PI / 2, head - PI / 2, head + PI / 2 + .45, 0];
  const headCenter = [sh[0] + L.head / 2 * Math.cos(head), sh[1] + L.head / 2 * Math.sin(head)];
  // walking away: the same walk, mirrored about the hip so he faces left
  if (t >= T.turn) return { root: [x, hipY], angles: angles.map(a => PI - a), headCenter: [2 * x - headCenter[0], headCenter[1]] };
  return { root: [x, hipY], angles, headCenter };
}

// camera aims at the guard's head; after the failed attempt it "shakes its head" no
function cameraAt(t, target) {
  let aim = Math.atan2(target[1] - PIVOT[1], target[0] - PIVOT[0]);
  aim = Math.max(PI * .62, Math.min(PI * 1.02, aim < 0 ? aim + 2 * PI : aim));
  if (t >= T.shake && t < T.salute) aim += .16 * Math.sin((t - T.shake) * 2 * PI / 9) * (1 - (t - T.shake) / (T.salute - T.shake));
  return aim;
}

// ---------- document ----------
const doc = emptyDocument();
doc.canvas_width = W; doc.canvas_height = H; doc.fps = 24;
doc.figure_types = [GUARD, CAMERA, LED, BONK];
const png = f => 'data:image/png;base64,' + fs.readFileSync(here(f)).toString('base64');
doc.backgrounds = [{ background_id: 1, kind: 1, mime_type: 'image/png', asset_url: png('mon_bg1.png') },
  { background_id: 2, kind: 1, mime_type: 'image/png', asset_url: png('mon_bg2.png') }];
doc._styk.name = 'Who monitors the monitor';

let camAngle = cameraAt(0, guardAt(0).headCenter);
const frames = [];
for (let t = 0; t < FRAMES; t++) {
  const g = guardAt(t), objects = [];
  // the camera follows with a little lag, like a servo
  camAngle = lerp(camAngle, cameraAt(t, g.headCenter), t >= T.shake && t < T.salute ? 1 : .25);
  const up = camAngle + PI / 2;
  const cam = createObject(CAMERA, 2, ...PIVOT); cam.angles = [camAngle, camAngle, up, camAngle];
  objects.push(cam);
  // red light near the front of the camera; blinks steadily, stays lit while it watches closely
  const ledPos = [PIVOT[0] + 108 * Math.cos(camAngle) + 22 * Math.cos(up), PIVOT[1] + 108 * Math.sin(camAngle) + 22 * Math.sin(up)];
  if (Math.floor(t / 10) % 2 === 0 || (t >= T.lookCam && t < T.salute)) objects.push(createObject(LED, 3, ...ledPos));
  const guard = createObject(GUARD, 1, ...g.root); guard.angles = g.angles;
  objects.push(guard);
  // impact marks: knuckles on glass, then the padlock rattle
  const marks = (at, base, age, uid) => {
    const b = createObject(BONK, uid, ...at);
    b.angles = [base - .6, base, base + .6]; b.scale = [.7, 1.1, 1, .8, .6][Math.min(4, age)];
    objects.push(b);
  };
  if (t >= T.bonk && t < T.bonk + 6) marks([BOX_EDGE - 8, PLUG[1] - 40], -PI * .75, t - T.bonk, 10);
  if (t >= T.rattle && t < T.giveUp && (t - T.rattle) % 8 < 4) marks([LOCK[0] + 38, LOCK[1] - 6], -PI * .2, (t - T.rattle) % 8, 11);
  const frame = createFrame(objects, 1);
  frame.background_id = t >= T.tagline ? 2 : 1;
  frames.push(frame);
}
doc.keyframes = frames;
fs.writeFileSync(here('monitor.json'), JSON.stringify(doc));
console.log('frames', frames.length);
