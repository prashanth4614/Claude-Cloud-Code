// 3D world for the ear-pop short, rendered deterministically frame by frame.
// The page exposes window.renderFrame(job) -> {anchors}; render_plates.mjs
// drives it from headless Chromium. Everything is procedural (no assets).
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const params = new URLSearchParams(location.search);
const W = +(params.get('w') || 1080), H = +(params.get('h') || 1920);

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.localClippingEnabled = true;
document.body.appendChild(renderer.domElement);

const pmrem = new THREE.PMREMGenerator(renderer);
const envMap = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

// Seeded random so every render of a frame is identical.
function rng(seed) {
  let s = seed >>> 0;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}
const lerp = (a, b, x) => a + (b - a) * x;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));

function gradientTexture(stops, w = 4, h = 512) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d');
  const grd = g.createLinearGradient(0, 0, 0, h);
  stops.forEach(([o, col]) => grd.addColorStop(o, col));
  g.fillStyle = grd;
  g.fillRect(0, 0, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function makeComposer(scene, camera, bloom = 0.35) {
  const rt = new THREE.WebGLRenderTarget(W, H, { samples: 4, type: THREE.HalfFloatType });
  const composer = new EffectComposer(renderer, rt);
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), bloom, 0.5, 0.92));
  composer.addPass(new OutputPass());
  return composer;
}

const std = (color, o = {}) => new THREE.MeshPhysicalMaterial({ color, envMap, roughness: 0.5, ...o });

// =============================================================== PLANE ====
function buildPlane() {
  const scene = new THREE.Scene();
  scene.background = gradientTexture([[0, '#0b3d91'], [0.55, '#3a86d1'], [1, '#bfe3ff']]);
  scene.add(new THREE.HemisphereLight('#cfe8ff', '#5577aa', 1.4));
  const sun = new THREE.DirectionalLight('#fff1d6', 3.2);
  sun.position.set(6, 10, 8);
  scene.add(sun);
  const camera = new THREE.PerspectiveCamera(38, W / H, 0.1, 400);

  const plane = new THREE.Group();
  const white = std('#f4f7fb', { roughness: 0.28, clearcoat: 1, clearcoatRoughness: 0.15 });
  const red = std('#e63946', { roughness: 0.35, clearcoat: 1 });
  const grey = std('#8d99ae', { roughness: 0.4, metalness: 0.6 });
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.62, 5.2, 12, 32), white);
  body.rotation.z = Math.PI / 2;
  plane.add(body);
  plane.add(new THREE.Mesh(new THREE.TorusGeometry(0.63, 0.05, 8, 48), red)).rotation.y = Math.PI / 2;
  const winMat = std('#1d3557', { roughness: 0.1, metalness: 0.2, clearcoat: 1 });
  for (let i = 0; i < 14; i++) {
    const w = new THREE.Mesh(new THREE.SphereGeometry(0.085, 16, 12), winMat);
    w.position.set(-1.9 + i * 0.3, 0.18, 0.58);
    w.scale.set(1, 1.3, 0.4);
    plane.add(w);
  }
  const cockpit = new THREE.Mesh(new THREE.SphereGeometry(0.3, 24, 16), winMat);
  cockpit.position.set(2.95, 0.22, 0.3);
  cockpit.scale.set(1, 0.5, 1.2);
  plane.add(cockpit);
  const wingShape = new THREE.Shape([new THREE.Vector2(0.6, 0), new THREE.Vector2(-0.9, 0),
    new THREE.Vector2(-1.9, 3.4), new THREE.Vector2(-1.3, 3.4)]);
  const wingGeo = new THREE.ExtrudeGeometry(wingShape, { depth: 0.08, bevelEnabled: true, bevelSize: 0.04, bevelThickness: 0.04, bevelSegments: 3 });
  for (const s of [1, -1]) {
    const wing = new THREE.Mesh(wingGeo, white);
    wing.rotation.x = s * Math.PI / 2;
    wing.position.set(0.2, -0.25, 0);
    plane.add(wing);
    const eng = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.26, 0.9, 24), grey);
    eng.rotation.z = Math.PI / 2;
    eng.position.set(-0.3, -0.55, s * 1.4);
    plane.add(eng);
  }
  const tailShape = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(-1.1, 0),
    new THREE.Vector2(-1.4, 1.5), new THREE.Vector2(-0.8, 1.5)]);
  const tail = new THREE.Mesh(new THREE.ExtrudeGeometry(tailShape, { depth: 0.08, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03 }), red);
  tail.position.set(-2.2, 0.35, -0.04);
  plane.add(tail);
  scene.add(plane);

  // Clouds: clusters of soft spheres, two parallax layers.
  const cloudMat = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 1, envMap, envMapIntensity: 0.6 });
  const clouds = [];
  const r = rng(7);
  for (let i = 0; i < 26; i++) {
    const g = new THREE.Group();
    for (let k = 0; k < 6; k++) {
      const s = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 3), cloudMat);
      s.position.set((r() - 0.5) * 3, (r() - 0.5) * 0.8, (r() - 0.5) * 1.5);
      s.scale.setScalar(0.6 + r() * 0.9);
      g.add(s);
    }
    g.userData = { x: (r() - 0.5) * 60, y: (r() - 0.5) * 50, z: -8 - r() * 40 };
    clouds.push(g);
    scene.add(g);
  }
  const composer = makeComposer(scene, camera, 0.18);
  return {
    render(job) {
      const { t, now } = job;
      const k = 1 - Math.pow(1 - clamp(t / 0.9), 3);
      plane.position.set(lerp(-9, 0, k), Math.sin(now * 2) * 0.12, 0);
      plane.rotation.set(0.25 + Math.sin(now * 1.3) * 0.03, -0.35, 0.28);
      for (const c of clouds) {
        const u = c.userData;
        c.position.set(((u.x - now * 6 + 30) % 60 + 60) % 60 - 30, ((u.y - now * 3.5 + 25) % 50 + 50) % 50 - 25, u.z);
      }
      camera.position.set(1.0 + Math.sin(now * 0.4) * 0.4, 0.9, 10.5);
      camera.lookAt(0, 0.3, 0);
      composer.render();
      return {};
    },
  };
}

// =============================================================== CABIN ====
function buildCabin() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#141d33');
  scene.environment = envMap;
  scene.add(new THREE.HemisphereLight('#dfe8ff', '#30264a', 0.5));
  const key = new THREE.DirectionalLight('#fff0dd', 1.7);
  key.position.set(-3, 4, 6);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.radius = 6;
  scene.add(key);
  const rim = new THREE.PointLight('#9fd3ff', 30, 20);
  rim.position.set(3.2, 2.2, -1);
  scene.add(rim);
  const camera = new THREE.PerspectiveCamera(32, W / H, 0.1, 100);

  // fuselage wall + window with animated sky
  const wall = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 20, 64, 1, true, -0.6, 2.2),
    std('#7d8799', { side: THREE.BackSide, roughness: 0.8, envMapIntensity: 0.4 }));
  wall.rotation.y = Math.PI;
  wall.position.set(-2.5, 0, -2);
  scene.add(wall);
  const skyCanvas = document.createElement('canvas');
  skyCanvas.width = 256; skyCanvas.height = 384;
  const skyTex = new THREE.CanvasTexture(skyCanvas);
  skyTex.colorSpace = THREE.SRGBColorSpace;
  const winGroup = new THREE.Group();
  const frame = new THREE.Mesh(new RoundedBoxGeometry(1.5, 2.1, 0.25, 6, 0.6), std('#c9d1dc', { roughness: 0.6 }));
  const glass = new THREE.Mesh(new RoundedBoxGeometry(1.15, 1.75, 0.05, 6, 0.5),
    new THREE.MeshBasicMaterial({ map: skyTex, toneMapped: false }));
  glass.position.z = 0.11;
  winGroup.add(frame, glass);
  winGroup.position.set(2.55, 1.1, -0.9);
  winGroup.rotation.y = -0.5;
  scene.add(winGroup);

  // seat
  const fabric = std('#2b4590', { roughness: 0.95, sheen: 1, sheenColor: new THREE.Color('#6d8be0') });
  const seatBack = new THREE.Mesh(new RoundedBoxGeometry(2.6, 4.2, 0.7, 8, 0.35), fabric);
  seatBack.position.set(0, 0.3, -0.75);
  seatBack.castShadow = seatBack.receiveShadow = true;
  const head = new THREE.Mesh(new RoundedBoxGeometry(1.7, 0.75, 0.25, 6, 0.12), std('#eef1f5', { roughness: 0.9 }));
  head.position.set(0, 2.05, -0.38);
  scene.add(seatBack, head);
  for (const s of [-1, 1]) {
    const wing = new THREE.Mesh(new RoundedBoxGeometry(0.5, 1.4, 0.9, 6, 0.22), fabric);
    wing.position.set(s * 1.15, 1.6, -0.45);
    wing.castShadow = true;
    scene.add(wing);
  }

  // ---- Max (original character) ----
  const max = new THREE.Group();
  const skin = std('#f3b48c', { roughness: 0.55, sheen: 0.5, sheenColor: new THREE.Color('#ff9a7a'), clearcoat: 0.08 });
  const skinD = std('#e39a73', { roughness: 0.6, sheen: 0.4, sheenColor: new THREE.Color('#ff8a6a') });
  const shirt = std('#1f9e93', { envMapIntensity: 0.5, roughness: 0.85, sheen: 0.6, sheenColor: new THREE.Color('#9ff7ec') });
  const hairM = std('#4a2c1a', { roughness: 0.45, clearcoat: 0.4, clearcoatRoughness: 0.5 });
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(1.0, 1.2, 12, 32), shirt);
  torso.scale.set(1.15, 1, 0.75);
  torso.position.set(0, -1.6, 0);
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.34, 0.8, 24), skinD);
  neck.position.set(0, -0.35, 0);
  const headM = new THREE.Mesh(new THREE.SphereGeometry(1, 64, 48), skin);
  headM.scale.set(0.98, 1.04, 0.95);
  headM.position.set(0, 0.85, 0.05);
  for (const m of [torso, neck, headM]) { m.castShadow = m.receiveShadow = true; max.add(m); }
  // hair: top cap + tufts
  const cap = new THREE.Mesh(new THREE.SphereGeometry(1.04, 48, 32, 0, Math.PI * 2, 0, Math.PI * 0.42), hairM);
  cap.position.copy(headM.position);
  cap.rotation.x = -0.25;
  max.add(cap);
  const tr = rng(11);
  for (let i = 0; i < 9; i++) {
    const tuft = new THREE.Mesh(new THREE.SphereGeometry(0.28, 20, 16), hairM);
    const a = -1.2 + i * 0.3;
    tuft.position.set(Math.sin(a) * 0.82, 1.68 + Math.cos(a) * 0.12 + tr() * 0.05, 0.38 + Math.cos(a) * 0.2);
    tuft.scale.set(1, 0.7, 0.9);
    max.add(tuft);
  }
  // ears
  const ears = [];
  for (const s of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.SphereGeometry(0.26, 32, 24), skinD);
    ear.scale.set(0.55, 1, 0.8);
    ear.position.set(s * 0.98, 0.8, 0);
    const inner = new THREE.Mesh(new THREE.SphereGeometry(0.15, 24, 16), std('#c97b5a', { roughness: 0.7 }));
    inner.scale.set(0.4, 0.9, 0.5);
    inner.position.set(s * 1.07, 0.8, 0.06);
    max.add(ear, inner);
    ears.push(ear);
  }
  // eyes: glossy whites, iris, pupil, eyelids for blinking
  const eyeWhite = std('#ffffff', { roughness: 0.08, clearcoat: 1 });
  const iris = std('#6b3f22', { roughness: 0.2, clearcoat: 1 });
  const pupil = std('#120a06', { roughness: 0.1, clearcoat: 1 });
  const lids = [], irises = [];
  for (const s of [-1, 1]) {
    const eye = new THREE.Group();
    const ball = new THREE.Mesh(new THREE.SphereGeometry(0.22, 32, 24), eyeWhite);
    ball.scale.set(1, 1.12, 0.6);
    const ir = new THREE.Mesh(new THREE.SphereGeometry(0.12, 24, 16), iris);
    ir.scale.set(1, 1, 0.35);
    ir.position.z = 0.12;
    const pu = new THREE.Mesh(new THREE.SphereGeometry(0.065, 16, 12), pupil);
    pu.scale.set(1, 1, 0.3);
    pu.position.z = 0.155;
    const irisGroup = new THREE.Group();
    irisGroup.add(ir, pu);
    eye.add(ball, irisGroup);
    const lid = new THREE.Mesh(new THREE.SphereGeometry(0.235, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), skin);
    lid.scale.set(1, 1.12, 0.66);
    eye.add(lid);
    eye.position.set(s * 0.36, 0.95, 0.83);
    max.add(eye);
    lids.push(lid);
    irises.push(irisGroup);
  }
  const brows = [-1, 1].map((s) => {
    const b = new THREE.Mesh(new THREE.CapsuleGeometry(0.05, 0.26, 6, 12), hairM);
    b.rotation.z = Math.PI / 2;
    b.position.set(s * 0.36, 1.3, 0.86);
    max.add(b);
    return b;
  });
  const nose = new THREE.Mesh(new THREE.SphereGeometry(0.11, 24, 16), skinD);
  nose.position.set(0, 0.68, 0.98);
  nose.scale.set(1, 0.8, 0.9);
  max.add(nose);
  const smile = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.035, 12, 32, Math.PI), std('#6b1d1d', { roughness: 0.4 }));
  smile.rotation.z = Math.PI;
  smile.position.set(0, 0.44, 0.92);
  max.add(smile);
  const mouthOpen = new THREE.Mesh(new THREE.SphereGeometry(0.2, 32, 24), std('#5c1a1a', { roughness: 0.5 }));
  mouthOpen.position.set(0, 0.36, 0.86);
  mouthOpen.scale.set(0.8, 1, 0.4);
  max.add(mouthOpen);
  // arms resting on the armrests
  for (const sgn of [-1, 1]) {
    const upper = new THREE.Mesh(new THREE.CapsuleGeometry(0.3, 1.0, 8, 20), shirt);
    upper.position.set(sgn * 1.25, -1.45, 0.1);
    upper.rotation.z = sgn * 0.18;
    const fore = new THREE.Mesh(new THREE.CapsuleGeometry(0.24, 0.9, 8, 20), skinD);
    fore.position.set(sgn * 1.05, -2.35, 0.55);
    fore.rotation.set(1.2, 0, -sgn * 0.35);
    const hand = new THREE.Mesh(new THREE.SphereGeometry(0.26, 24, 16), skin);
    hand.position.set(sgn * 0.75, -2.55, 1.05);
    for (const m of [upper, fore, hand]) { m.castShadow = true; max.add(m); }
  }
  const collar = new THREE.Mesh(new THREE.TorusGeometry(0.36, 0.07, 10, 32, Math.PI), std('#178077', { roughness: 0.8 }));
  collar.rotation.set(Math.PI / 2 + 0.3, 0, Math.PI);
  collar.position.set(0, -0.62, 0.22);
  max.add(collar);
  max.position.set(0, 0.2, 0);
  scene.add(max);

  // glowing ring for the zoom-in onto the ear
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.03, 12, 64),
    new THREE.MeshBasicMaterial({ color: '#ffd60a', toneMapped: false }));
  ring.position.set(1.0, 1.0, 0.3);
  ring.rotation.y = Math.PI / 2 - 0.2;
  scene.add(ring);

  const composer = makeComposer(scene, camera, 0.25);
  const earWorld = new THREE.Vector3();

  function drawSky(now) {
    const g = skyCanvas.getContext('2d');
    const grd = g.createLinearGradient(0, 0, 0, 384);
    grd.addColorStop(0, '#2f6fd1'); grd.addColorStop(1, '#b9e0ff');
    g.fillStyle = grd; g.fillRect(0, 0, 256, 384);
    const r = rng(3);
    g.fillStyle = 'rgba(255,255,255,0.9)';
    for (let i = 0; i < 6; i++) {
      const x = r() * 256, y = ((r() * 384 + now * 160) % 520) - 70;
      for (const [dx, dy, rr] of [[0, 0, 26], [26, -10, 32], [55, 0, 24]]) {
        g.beginPath(); g.arc(x + dx - 30, y + dy, rr, 0, Math.PI * 2); g.fill();
      }
    }
    skyTex.needsUpdate = true;
  }

  return {
    render(job) {
      const { now, t, dur } = job;
      const expr = job.expr || 'neutral';
      drawSky(now);
      const blink = (now % 3.3) < 0.13 && expr !== 'yawn';
      const closed = expr === 'yawn' || expr === 'wince';
      lids.forEach((l) => { l.rotation.x = closed || blink ? -Math.PI / 2 - 0.05 : -0.15; });
      irises.forEach((ir) => { ir.rotation.y = (job.look?.[0] || 0) * 0.35; ir.rotation.x = -(job.look?.[1] || 0) * 0.3; });
      brows.forEach((b, i) => {
        const s = i ? 1 : -1;
        b.rotation.z = Math.PI / 2 + (expr === 'wince' ? s * 0.35 : expr === 'smile' ? -s * 0.12 : 0);
      });
      const yawn = expr === 'yawn' ? 0.6 + 0.4 * Math.sin(now * 3) ** 2 : 0;
      mouthOpen.visible = expr === 'yawn';
      mouthOpen.scale.set(0.8, 0.6 + yawn * 0.9, 0.4);
      smile.visible = expr !== 'yawn';
      smile.scale.setScalar(expr === 'smile' ? 1.3 : 1);
      max.rotation.y = Math.sin(now * 0.7) * 0.06;
      max.position.y = 0.2 + Math.sin(now * 1.6) * 0.02;
      // camera: medium shot, optional dolly onto the ear
      const z = job.zoom ? clamp((t - dur * 0.35) / (dur * 0.65)) : 0;
      const ez = z * z * (3 - 2 * z);
      ears[1].getWorldPosition(earWorld);
      const base = new THREE.Vector3(0.8, 1.3, 11.5), target0 = new THREE.Vector3(0.2, 0.3, 0);
      const close = earWorld.clone().add(new THREE.Vector3(1.6, 0.1, 1.3));
      camera.position.lerpVectors(base, close, ez);
      camera.lookAt(target0.clone().lerp(earWorld, ez));
      ring.visible = !!job.zoom;
      ring.position.copy(earWorld).add(new THREE.Vector3(0.12, 0, 0));
      ring.scale.setScalar(1 + 0.12 * Math.sin(now * 8));
      composer.render();
      return {};
    },
  };
}

// ======================================================= EAR SECTION ======
function buildEar() {
  const scene = new THREE.Scene();
  scene.background = gradientTexture([[0, '#2a0f18'], [0.5, '#4a1a26'], [1, '#1a0a10']]);
  scene.environment = envMap;
  scene.fog = new THREE.Fog('#2a0f18', 14, 30);
  scene.add(new THREE.HemisphereLight('#ffd9d0', '#3a1020', 0.35));
  const key = new THREE.DirectionalLight('#fff3ea', 1.6);
  key.position.set(-4, 6, 9);
  scene.add(key);
  const fill = new THREE.PointLight('#ff8fa3', 12, 30);
  fill.position.set(5, -3, 5);
  scene.add(fill);
  const flash = new THREE.PointLight('#fff2a8', 0, 12);
  flash.position.set(-0.3, 0.6, 2);
  scene.add(flash);
  const camera = new THREE.PerspectiveCamera(36, W / H, 0.1, 100);

  // cut-away: show only the back half of every tube (z <= 0)
  const cut = [new THREE.Plane(new THREE.Vector3(0, 0, -1), 0.0)];
  const tissue = std('#c9655f', { envMapIntensity: 0.35, roughness: 0.32, clearcoat: 0.8, clearcoatRoughness: 0.25, side: THREE.DoubleSide,
    clippingPlanes: cut, sheen: 0.5, sheenColor: new THREE.Color('#ffb3a7') });
  const tissueOuter = std('#8a3540', { envMapIntensity: 0.3, roughness: 0.6, side: THREE.DoubleSide, clippingPlanes: cut });

  // background soft "cells" for depth
  const bokeh = new THREE.Group();
  const br = rng(21);
  for (let i = 0; i < 40; i++) {
    const m = new THREE.Mesh(new THREE.SphereGeometry(0.3 + br() * 0.7, 20, 16),
      std('#ff9aa8', { roughness: 0.3, transparent: true, opacity: 0.18 + br() * 0.15 }));
    m.position.set((br() - 0.5) * 22, (br() - 0.5) * 34, -5 - br() * 10);
    bokeh.add(m);
  }
  scene.add(bokeh);

  const canalCurve = new THREE.CatmullRomCurve3([new THREE.Vector3(-9, 0.75, 0), new THREE.Vector3(-4, 0.62, 0),
    new THREE.Vector3(-0.35, 0.6, 0)]);
  const canal = new THREE.Mesh(new THREE.TubeGeometry(canalCurve, 64, 0.82, 40, false), tissue);
  const canalOut = new THREE.Mesh(new THREE.TubeGeometry(canalCurve, 64, 1.0, 40, false), tissueOuter);
  scene.add(canal, canalOut);

  const chamberGeo = new THREE.SphereGeometry(1.55, 64, 48);
  const chamber = new THREE.Mesh(chamberGeo, tissue);
  chamber.position.set(1.35, 0.55, 0);
  chamber.scale.set(1, 1.08, 1);
  const chamberOut = new THREE.Mesh(new THREE.SphereGeometry(1.75, 48, 32), tissueOuter);
  chamberOut.position.copy(chamber.position);
  chamberOut.scale.copy(chamber.scale);
  scene.add(chamber, chamberOut);

  const tubeCurve = new THREE.CatmullRomCurve3([new THREE.Vector3(1.6, -0.9, -0.2), new THREE.Vector3(1.8, -2.5, -0.3),
    new THREE.Vector3(0.4, -3.6, -0.3), new THREE.Vector3(-0.7, -5.0, -0.2)]);
  const tubeMat = tissue.clone();
  tubeMat.clippingPlanes = cut;
  let tubeMesh = null, lastR = -1;
  function setTube(radius, red) {
    if (Math.abs(radius - lastR) > 0.005) {
      if (tubeMesh) { scene.remove(tubeMesh); tubeMesh.geometry.dispose(); }
      tubeMesh = new THREE.Mesh(new THREE.TubeGeometry(tubeCurve, 80, radius, 32, false), tubeMat);
      scene.add(tubeMesh);
      lastR = radius;
    }
    tubeMat.color.set('#c9655f').lerp(new THREE.Color('#ff3040'), red);
    tubeMat.emissive.set('#ff0020').multiplyScalar(red * 0.35);
  }
  const throat = new THREE.Mesh(new THREE.SphereGeometry(1.4, 48, 32), tissue);
  throat.position.set(-1.0, -5.9, 0);
  throat.scale.set(1.4, 0.75, 1);
  scene.add(throat);

  // eardrum: displaced disc with an iridescent membrane look
  const drumGeo = new THREE.CircleGeometry(0.86, 64, 0, Math.PI * 2);
  const drumBase = drumGeo.attributes.position.array.slice();
  const drumMat = new THREE.MeshPhysicalMaterial({ color: '#f7e8dc', roughness: 0.25, clearcoat: 1, iridescence: 0.8,
    iridescenceIOR: 1.6, envMap, transparent: true, opacity: 0.94, side: THREE.DoubleSide, emissive: new THREE.Color('#ff2a2a') });
  const drum = new THREE.Mesh(drumGeo, drumMat);
  drum.rotation.y = Math.PI / 2;
  drum.position.set(-0.3, 0.6, 0);
  scene.add(drum);
  function setDrum(bulge) {
    const p = drumGeo.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = drumBase[i * 3], y = drumBase[i * 3 + 1];
      const r2 = (x * x + y * y) / (0.86 * 0.86);
      p.setZ(i, bulge * 0.7 * (1 - r2)); // local +z faces the canal (outward)
    }
    p.needsUpdate = true;
    drumGeo.computeVertexNormals();
    drumMat.emissiveIntensity = Math.abs(bulge) * 0.35;
  }

  // ossicles (tiny bones) chained from the eardrum
  const bone = std('#f3e5c8', { roughness: 0.4, clearcoat: 0.6 });
  const bonePts = [new THREE.Vector3(-0.25, 0.6, -0.1), new THREE.Vector3(0.75, 1.25, -0.3),
    new THREE.Vector3(1.35, 1.2, -0.35), new THREE.Vector3(1.9, 0.6, -0.3)];
  const bones = [];
  for (let i = 0; i < 3; i++) {
    const b = new THREE.Mesh(new THREE.CapsuleGeometry(0.11, 1, 8, 16), bone);
    bones.push(b);
    scene.add(b);
    const j = new THREE.Mesh(new THREE.SphereGeometry(0.17, 20, 16), bone);
    j.position.copy(bonePts[i + 1]);
    scene.add(j);
  }
  function setBones(bulge) {
    bonePts[0].x = -0.25 - bulge * 0.55;
    for (let i = 0; i < 3; i++) {
      const a = bonePts[i], b = bonePts[i + 1];
      const mid = a.clone().add(b).multiplyScalar(0.5);
      bones[i].position.copy(mid);
      bones[i].scale.set(1, a.distanceTo(b), 1);
      bones[i].quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    }
  }

  // glowing air molecules (instanced)
  const molGeo = new THREE.SphereGeometry(0.075, 12, 10);
  const molMat = new THREE.MeshBasicMaterial({ color: new THREE.Color('#9fe0ff').multiplyScalar(2.2), toneMapped: false });
  const outside = new THREE.InstancedMesh(molGeo, molMat, 60);
  const inside = new THREE.InstancedMesh(molGeo, molMat, 40);
  const flowing = new THREE.InstancedMesh(molGeo, molMat, 14);
  scene.add(outside, inside, flowing);
  const tmp = new THREE.Object3D();
  const ro = rng(1), ri = rng(2);
  const outSeeds = Array.from({ length: 60 }, () => [ro() * 8.4, ro() * 1.1 - 0.55, ro() * 0.9 - 0.8, 0.4 + ro() * 1.2, ro() * 6]);
  const inSeeds = Array.from({ length: 40 }, () => [ri() * 6, ri() * 6, ri() * 6, 0.6 + ri() * 0.8, 0.6 + ri() * 0.8]);

  // pressure arrows (glowing), outside pushes right, inside pushes left
  function arrow(color) {
    const g = new THREE.Group();
    const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(1.6), toneMapped: false, transparent: true });
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 1, 12), m);
    const head = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.28, 16), m);
    g.add(shaft, head);
    g.userData = { shaft, head, m };
    scene.add(g);
    return g;
  }
  const outArrows = [0, 1, 2].map(() => arrow('#4cc9f0'));
  const inArrows = [0, 1, 2].map(() => arrow('#ffb703'));
  function setArrow(a, x0, x1, y, alpha) {
    const { shaft, head, m } = a.userData;
    const len = Math.abs(x1 - x0), d = Math.sign(x1 - x0) || 1;
    a.visible = alpha > 0.01;
    m.opacity = alpha;
    a.position.set(x0, y, 0.45);
    a.rotation.z = d > 0 ? -Math.PI / 2 : Math.PI / 2;
    shaft.scale.y = Math.max(0.01, len - 0.25);
    shaft.position.y = (len - 0.25) / 2;
    head.position.y = len - 0.12;
  }

  // muffled sound rings
  const rings = [0, 1, 2, 3].map(() => {
    const m = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.035, 8, 48),
      new THREE.MeshBasicMaterial({ color: '#ffffff', transparent: true, toneMapped: false }));
    m.rotation.y = Math.PI / 2;
    scene.add(m);
    return m;
  });

  const composer = makeComposer(scene, camera, 0.3);
  const anchorsWorld = {
    canal: new THREE.Vector3(-1.9, 1.4, 0), drum: new THREE.Vector3(-0.3, -0.2, 0),
    middle: new THREE.Vector3(1.6, 2.1, 0), tube: new THREE.Vector3(1.3, -3.0, 0), throat: new THREE.Vector3(-0.6, -5.4, 0),
  };

  return {
    render(job) {
      const st = job.st, now = job.now;
      setDrum(st.bulge);
      setBones(st.bulge);
      setTube(lerp(0.12, 0.42, st.tube), st.red);
      const nOut = Math.round(40 * st.p_out);
      for (let i = 0; i < 60; i++) {
        const [x0, y0, z0, v, ph] = outSeeds[i];
        const x = -8.6 + ((x0 + now * v) % 8.0);
        tmp.position.set(x, 0.62 + y0 + Math.sin(now * 3 + ph) * 0.08, z0);
        tmp.scale.setScalar(i < nOut ? 1 : 0);
        tmp.updateMatrix();
        outside.setMatrixAt(i, tmp.matrix);
      }
      outside.instanceMatrix.needsUpdate = true;
      for (let i = 0; i < 40; i++) {
        const [a, b, c, f1, f2] = inSeeds[i];
        tmp.position.set(1.35 + 1.1 * Math.sin(now * f1 + a), 0.55 + 1.15 * Math.sin(now * f2 + b), -0.8 + 0.6 * Math.sin(now + c));
        tmp.scale.setScalar(i < 30 ? 1 : 0);
        tmp.updateMatrix();
        inside.setMatrixAt(i, tmp.matrix);
      }
      inside.instanceMatrix.needsUpdate = true;
      for (let i = 0; i < 14; i++) {
        const u = (now * 0.6 + i / 14) % 1;
        tmp.position.copy(tubeCurve.getPoint(u));
        tmp.scale.setScalar(st.flow > 0.05 ? st.flow : 0);
        tmp.updateMatrix();
        flowing.setMatrixAt(i, tmp.matrix);
      }
      flowing.instanceMatrix.needsUpdate = true;
      const lo = lerp(0.5, 2.3, clamp(st.p_out / 1.5));
      [0.25, 0.6, 0.95].forEach((y, i) => {
        const edge = -0.42 + st.bulge * 0.6 * (1 - Math.abs(y - 0.6) / 0.9);
        setArrow(outArrows[i], edge - 0.1 - lo, edge - 0.1, y, st.arrows);
        setArrow(inArrows[i], 1.25, edge + 0.12 - st.bulge * 0.1 + 0.05, y, st.arrows);
      });
      rings.forEach((r, i) => {
        const ph = (now * 0.9 + i * 0.25) % 1;
        r.visible = st.waves > 0.01;
        r.position.set(lerp(-7, -2, ph), 0.62, 0);
        r.material.opacity = st.waves * (1 - ph) ** 2;
      });
      flash.intensity = st.pop_k > 0 ? 120 * Math.max(0, 1 - st.pop_k / 0.4) : 0;
      // gentle orbiting camera, plus a shake on the pop
      const shake = st.pop_k > 0 && st.pop_k < 0.35 ? (1 - st.pop_k / 0.35) * 0.12 : 0;
      camera.position.set(-0.2 + Math.sin(now * 0.35) * 1.0 + Math.sin(now * 90) * shake, -1.6 + Math.cos(now * 77) * shake, 17.0);
      camera.lookAt(0.2, -1.25, 0);
      composer.render();
      const anchors = {};
      for (const [k, v] of Object.entries(anchorsWorld)) {
        const p = v.clone().project(camera);
        anchors[k] = [(p.x + 1) / 2 * W, (1 - p.y) / 2 * H];
      }
      return { anchors };
    },
  };
}

const shots = { plane: buildPlane(), cabin: buildCabin(), ear: buildEar() };
window.renderFrame = (job) => shots[job.shot].render(job);
window.grab = () => renderer.domElement.toDataURL('image/jpeg', 0.93);
window.ready = true;
