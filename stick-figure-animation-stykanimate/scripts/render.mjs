// Render frames of a StykAnimate document with the app's own renderer (Canvas 2D path) in headless Chromium.
// Usage: node render.mjs <doc.json> <all|0,12,40> <out_dir>
// Needs the local service from setup.sh (STYK_PORT, default 47831). Writes out_dir/f0000.png ...
import fs from 'node:fs';
import path from 'node:path';

const [docPath, which = 'all', out = 'frames'] = process.argv.slice(2);
if (!docPath) { console.error('usage: node render.mjs <doc.json> <all|i,j,k> <out_dir>'); process.exit(2); }
const port = process.env.STYK_PORT || 47831;
let chromium;
try { ({ chromium } = await import('playwright')); }
catch { ({ chromium } = await import('/opt/node-tools/node_modules/playwright/index.mjs')); }

const doc = JSON.parse(fs.readFileSync(docPath, 'utf8'));
fs.mkdirSync(out, { recursive: true });
const executablePath = process.env.CHROMIUM_PATH || (fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined);
const browser = await chromium.launch({ executablePath });
try {
  const page = await browser.newPage();
  // After the DOM swap the app's own boot code logs harmless null-element errors; surface anything else.
  page.on('pageerror', e => { if (!/null/.test(e.message)) console.error('pageerror:', e.message); });
  await page.goto(`http://127.0.0.1:${port}/`);
  await page.evaluate(async (doc) => {
    const { createRenderer } = await import('/src/renderer.mjs');
    const { buildGeometry } = await import('/src/pivot/geometry.mjs');
    document.documentElement.innerHTML = '<body style="margin:0"></body>';
    const canvas = document.createElement('canvas'); document.body.append(canvas);
    const r = await createRenderer(canvas, { forceCanvas2D: true });
    r.resize(doc.canvas_width, doc.canvas_height, 1);
    window.draw = async (i) => {
      const frame = doc.keyframes[i];
      await r.prepareBackgrounds?.(doc, frame);          // every frame: backgrounds can switch
      r.render({ report: doc, frame, geometry: buildGeometry(doc, frame), view: { x: 0, y: 0, scale: 1 } });
      await new Promise(res => requestAnimationFrame(res));
      return canvas.toDataURL('image/png');
    };
    await window.draw(0); await new Promise(res => setTimeout(res, 500));   // warm up fonts and atlases
  }, doc);
  const list = which === 'all' ? doc.keyframes.map((_, i) => i) : which.split(',').map(Number);
  for (const i of list) {
    const url = await page.evaluate(i => window.draw(i), i);
    fs.writeFileSync(path.join(out, `f${String(i).padStart(4, '0')}.png`), Buffer.from(url.split(',')[1], 'base64'));
  }
  console.log(`rendered ${list.length} frame(s) to ${out}`);
} finally {
  await browser.close();
}
