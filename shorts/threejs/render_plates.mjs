// Render 3D background plates frame by frame in headless Chromium.
//   node render_plates.mjs jobs.json outDir [--workers 3] [--w 1080 --h 1920]
// jobs.json: [{shot, now, t, dur, ...}, ...] (one per output frame).
// Writes outDir/00000.jpg ... and outDir/anchors.json (screen-space label points).
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { extname, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const here = dirname(fileURLToPath(import.meta.url));
const [jobsPath, outDir, ...rest] = process.argv.slice(2);
const opt = (k, d) => { const i = rest.indexOf(`--${k}`); return i >= 0 ? rest[i + 1] : d; };
const workers = +opt('workers', 3), w = +opt('w', 1080), h = +opt('h', 1920);
const chrome = process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript' };
const server = createServer(async (req, res) => {
  try {
    const path = join(here, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!path.startsWith(here)) throw new Error('outside');
    const body = await readFile(path);
    res.writeHead(200, { 'content-type': types[extname(path)] || 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404); res.end(); }
}).listen(0, '127.0.0.1');
await new Promise((r) => server.once('listening', r));
const url = `http://127.0.0.1:${server.address().port}/index.html?w=${w}&h=${h}`;

const jobs = JSON.parse(await readFile(jobsPath, 'utf8'));
await mkdir(outDir, { recursive: true });
const browser = await chromium.launch({ executablePath: chrome,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const anchors = new Array(jobs.length);
let next = 0, done = 0;
const t0 = Date.now();

async function worker() {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  page.on('pageerror', (e) => { console.error('page error:', e.message); process.exit(1); });
  await page.goto(url);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
  while (next < jobs.length) {
    const i = next++;
    const res = await page.evaluate((job) => window.renderFrame(job), jobs[i]);
    const data = await page.evaluate(() => window.grab());
    await writeFile(join(outDir, `${String(i).padStart(5, '0')}.jpg`), Buffer.from(data.split(',')[1], 'base64'));
    anchors[i] = res.anchors || null;
    if (++done % 60 === 0) console.log(`${done}/${jobs.length} frames, ${((Date.now() - t0) / done).toFixed(0)} ms/frame`);
  }
}
await Promise.all(Array.from({ length: workers }, worker));
await writeFile(join(outDir, 'anchors.json'), JSON.stringify(anchors));
console.log(`done: ${jobs.length} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
await browser.close();
server.close();
