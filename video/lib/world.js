// Shared low-poly world: renderer, city, tower, crane, hoist, people, diagrams, overlay helpers.
// Extracted from p1/scene.html so later parts reuse the same look.
import * as THREE from 'three';
export { THREE };
// ---------- helpers ----------
const W = 1080, H = 1920, RW = 720, RH = 1280;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const ease = x => x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const easeOut = x => 1 - Math.pow(1 - x, 3);
const lerp = (a, b, x) => a + (b - a) * x;
const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, x) => a.clone().lerp(b, x);
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

const mats = {};
function mat(color, opts = {}) {
  const key = color + JSON.stringify(opts);
  if (!mats[key]) mats[key] = new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0, flatShading: true, ...opts });
  return mats[key];
}
function box(w, h, d, color, opts) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat(color, opts));
  m.castShadow = true; m.receiveShadow = true; return m;
}
function at(obj, x, y, z) { obj.position.set(x, y, z); return obj; }

// ---------- renderer ----------
const glCanvas = document.createElement('canvas');
const renderer = new THREE.WebGLRenderer({ canvas: glCanvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(RW, RH, false);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, RW / RH, 0.1, 2000);

const hemi = new THREE.HemisphereLight(0xcfe8ff, 0x9aa88a, 1.6); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff1dc, 2.6);
sun.position.set(45, 90, 35); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -70, right: 70, top: 70, bottom: -70, near: 1, far: 300 });
sun.shadow.bias = -0.0008;
scene.add(sun); scene.add(sun.target);

// sky dome
const skyGeo = new THREE.SphereGeometry(900, 24, 16);
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { top: { value: new THREE.Color('#2f8fe6') }, bottom: { value: new THREE.Color('#b8e2ff') } },
  vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
  fragmentShader: 'uniform vec3 top; uniform vec3 bottom; varying vec3 vP; void main(){ float h = clamp(vP.y*1.6+0.15,0.0,1.0); gl_FragColor = vec4(mix(bottom, top, h),1.0); }'
});
const sky = new THREE.Mesh(skyGeo, skyMat); scene.add(sky);
scene.fog = new THREE.Fog('#b8e2ff', 160, 520);

// ---------- CITY ----------
const city = new THREE.Group(); scene.add(city);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), mat('#6cc24a'));
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; city.add(ground);
// roads
for (const [w, d, x, z] of [[1200, 7, 0, 30], [7, 1200, -30, 0], [1200, 7, 0, -70], [7, 1200, 60, 0]]) {
  const r = box(w, 0.1, d, '#8d939c'); at(r, x, 0.05, z); r.castShadow = false; city.add(r);
}
// construction site dirt
const dirt = box(34, 0.2, 34, '#c8955a'); at(dirt, 0, 0.1, 0); city.add(dirt);
// houses & trees
const R = rng(7);
const roofCol = ['#e8643c', '#d9532f', '#f07b45'];
const wallCol = ['#fff6e6', '#f3efe6', '#ffe9c7', '#e8f1f8'];
for (let i = 0; i < 170; i++) {
  const x = (R() - 0.5) * 340, z = (R() - 0.5) * 340;
  if (Math.abs(x) < 22 && Math.abs(z) < 22) continue;
  if (Math.abs(z - 30) < 8 || Math.abs(x + 30) < 8 || Math.abs(z + 70) < 8 || Math.abs(x - 60) < 8) continue;
  if (R() < 0.62) {
    const w = 5 + R() * 3, d = 5 + R() * 3, h = 3 + R() * 2.5;
    const hs = new THREE.Group();
    hs.add(at(box(w, h, d, wallCol[i % 4]), 0, h / 2, 0));
    const roof = new THREE.Mesh(new THREE.ConeGeometry(Math.max(w, d) * 0.78, 2.6, 4), mat(roofCol[i % 3]));
    roof.rotation.y = Math.PI / 4; roof.position.y = h + 1.3; roof.castShadow = true; hs.add(roof);
    hs.add(at(box(0.9, 1.6, 0.1, '#7a4b2a'), 0, 0.8, d / 2 + 0.05));
    hs.add(at(box(1, 1, 0.1, '#7fc4ef'), w * 0.28, h * 0.6, d / 2 + 0.05));
    hs.add(at(box(1, 1, 0.1, '#7fc4ef'), -w * 0.28, h * 0.6, d / 2 + 0.05));
    hs.position.set(x, 0, z); hs.rotation.y = Math.floor(R() * 4) * Math.PI / 2; city.add(hs);
  } else {
    const tr = new THREE.Group();
    tr.add(at(box(0.5, 1.8, 0.5, '#7a5230'), 0, 0.9, 0));
    const c = new THREE.Mesh(new THREE.IcosahedronGeometry(1.6 + R() * 0.8, 0), mat(['#3fae49', '#56c45a', '#2e9a43'][i % 3]));
    c.position.y = 2.9; c.castShadow = true; tr.add(c); tr.position.set(x, 0, z); city.add(tr);
  }
}
// clouds
const clouds = new THREE.Group(); city.add(clouds);
const RC = rng(11);
for (let i = 0; i < 26; i++) {
  const c = new THREE.Group();
  const n = 3 + Math.floor(RC() * 3);
  for (let k = 0; k < n; k++) {
    const s = 4 + RC() * 5;
    const b = box(s * 1.6, s * 0.8, s, '#ffffff', { roughness: 1 }); b.castShadow = false;
    at(b, (k - n / 2) * s * 0.9, RC() * 2, (RC() - 0.5) * 3); c.add(b);
  }
  c.position.set((RC() - 0.5) * 500, 70 + RC() * 40, (RC() - 0.5) * 500 - 60);
  c.userData.speed = 0.6 + RC(); clouds.add(c);
}
const moon = new THREE.Mesh(new THREE.IcosahedronGeometry(14, 1), new THREE.MeshBasicMaterial({ color: '#fff7d6', fog: false }));
moon.position.set(-160, 220, -380); scene.add(moon);

// tower
const FH = 3.2, NF = 14, HALF = 6.6;
const COLS = [-6, -2, 2, 6];
const tower = new THREE.Group(); city.add(tower);
const floors = [];
for (let i = 0; i < NF; i++) {
  const f = new THREE.Group();
  for (const x of COLS) for (const z of COLS) f.add(at(box(0.62, FH, 0.62, '#b9bec4'), x, FH / 2, z));
  const slab = box(HALF * 2, 0.36, HALF * 2, '#c4c8cd'); at(slab, 0, FH - 0.18, 0); f.add(slab);
  f.position.y = i * FH; tower.add(f); floors.push(f);
}
// rebar stubs on top
const stubs = new THREE.Group(); tower.add(stubs);
for (const x of COLS) for (const z of COLS) for (const [dx, dz] of [[-.18, -.18], [.18, .18], [-.18, .18], [.18, -.18]]) {
  const r = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 1.2, 5), mat('#a0432a')); at(r, x + dx, 0.6, z + dz); stubs.add(r);
}
function setFloors(n) { // n may be fractional
  floors.forEach((f, i) => {
    const vis = clamp(n - i); f.visible = vis > 0; f.scale.y = Math.max(0.001, easeOut(vis));
  });
  stubs.position.y = Math.ceil(clamp(n, 1, NF)) * FH; stubs.visible = n >= 1;
}
// crane
const crane = new THREE.Group(); city.add(crane); crane.position.set(13, 0, -6);
const CRANE_H = NF * FH + 12;
for (const [dx, dz] of [[-.6, -.6], [.6, -.6], [-.6, .6], [.6, .6]]) crane.add(at(box(0.22, CRANE_H, 0.22, '#ff8a1f'), dx, CRANE_H / 2, dz));
for (let y = 2; y < CRANE_H; y += 2.4) { crane.add(at(box(1.4, 0.16, 0.16, '#ff8a1f'), 0, y, -.6)); crane.add(at(box(1.4, 0.16, 0.16, '#ff8a1f'), 0, y, .6)); crane.add(at(box(0.16, 0.16, 1.4, '#ff8a1f'), -.6, y, 0)); crane.add(at(box(0.16, 0.16, 1.4, '#ff8a1f'), .6, y, 0)); }
const jibG = new THREE.Group(); jibG.position.y = CRANE_H; crane.add(jibG);
jibG.add(at(box(36, 0.9, 0.9, '#ff8a1f'), -12, 0.4, 0));
jibG.add(at(box(10, 0.9, 0.9, '#ff8a1f'), 9, 0.4, 0));
jibG.add(at(box(3, 2.4, 2.4, '#7a8088'), 12.5, -0.5, 0));
jibG.add(at(box(1.8, 1.8, 1.8, '#f5f5f5'), 0.9, -1.2, 0.9));
jibG.add(at(box(0.6, 4, 0.6, '#ff8a1f'), 0, 2.4, 0));
const cable = box(0.06, 16, 0.06, '#333333'); at(cable, -20, -8, 0); jibG.add(cable);
jibG.add(at(box(0.8, 0.6, 0.8, '#ffd23f'), -20, -16.2, 0));
// hoist (elevator)
const hoist = new THREE.Group(); city.add(hoist); hoist.position.set(8.6, 0, 1.4);
const HW = 3.2, HD = 3.0, HHt = 3.7;
hoist.add(at(box(HW, 0.18, HD, '#5a6470'), 0, 0.09, 0));
hoist.add(at(box(HW, 0.18, HD, '#5a6470'), 0, HHt, 0));
for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) hoist.add(at(box(0.14, HHt, 0.14, '#ffd23f'), x * HW / 2, HHt / 2, z * HD / 2));
for (const y of [1.0, 1.9]) { hoist.add(at(box(HW, 0.08, 0.08, '#ffd23f'), 0, y, HD / 2)); hoist.add(at(box(0.08, 0.08, HD, '#ffd23f'), HW / 2, y, 0)); }
const mast = box(0.5, NF * FH + 3, 0.5, '#9aa1a9'); at(mast, 8.6 - HW / 2 - 0.3, (NF * FH + 3) / 2, 1.4); city.add(mast);

// crack + seal on floor 12
const LVL = 12, LY = LVL * FH;
const CRACK_C = v3(0, LY + 0.012, -4.2);
const crackG = new THREE.Group(); crackG.position.copy(CRACK_C); city.add(crackG);
const crackPts = [];
{ const RR = rng(3); let p = v3(-1.8, 0, -0.9); crackPts.push(p.clone());
  for (let i = 0; i < 18; i++) { p = p.clone().add(v3(0.2 + RR() * 0.05, 0, 0.1 + (RR() - 0.5) * 0.28)); crackPts.push(p.clone()); } }
const crackSegs = [];
for (let i = 0; i < crackPts.length - 1; i++) {
  const a = crackPts[i], b = crackPts[i + 1]; const len = a.distanceTo(b);
  const s = new THREE.Mesh(new THREE.BoxGeometry(len + 0.02, 0.02, 0.045), new THREE.MeshBasicMaterial({ color: '#1d1f24' }));
  s.position.copy(a.clone().add(b).multiplyScalar(0.5)); s.rotation.y = -Math.atan2(b.z - a.z, b.x - a.x);
  crackG.add(s); crackSegs.push(s);
}
const sealMid = crackPts[9].clone().add(crackPts[10]).multiplyScalar(0.5);
const crackDir = Math.atan2(crackPts[10].z - crackPts[9].z, crackPts[10].x - crackPts[9].x);
const seal = new THREE.Group(); seal.position.copy(sealMid); seal.rotation.y = -crackDir; crackG.add(seal);
const sealA = box(0.18, 0.05, 0.36, '#ffffff', { roughness: 1 }); const sealB = box(0.18, 0.05, 0.36, '#ffffff', { roughness: 1 });
sealA.position.x = -0.09; sealB.position.x = 0.09; seal.add(sealA, sealB);

// ---------- PEOPLE ----------
function person({ shirt, pants, skin = '#f2c6a0', hair, helmet, vest = null, hairType = 'teo', badge = true, cup = false }) {
  const g = new THREE.Group();
  const p = {};
  p.legL = new THREE.Group(); p.legL.position.set(-0.21, 0.9, 0); p.legL.add(at(box(0.34, 0.9, 0.36, pants), 0, -0.45, 0)); p.legL.add(at(box(0.36, 0.14, 0.44, '#2b2b2b'), 0, -0.86, 0.04));
  p.legR = new THREE.Group(); p.legR.position.set(0.21, 0.9, 0); p.legR.add(at(box(0.34, 0.9, 0.36, pants), 0, -0.45, 0)); p.legR.add(at(box(0.36, 0.14, 0.44, '#2b2b2b'), 0, -0.86, 0.04));
  p.body = new THREE.Group(); p.body.position.y = 0.9; g.add(p.legL, p.legR, p.body);
  p.body.add(at(box(0.92, 0.98, 0.52, shirt), 0, 0.49, 0));
  if (vest) { p.body.add(at(box(0.96, 0.8, 0.56, vest), 0, 0.5, 0)); p.body.add(at(box(0.97, 0.1, 0.57, '#f4f4f4'), 0, 0.38, 0)); }
  if (badge) { p.body.add(at(box(0.05, 0.42, 0.03, '#2d3340'), -0.14, 0.72, 0.275)); p.body.add(at(box(0.05, 0.42, 0.03, '#2d3340'), 0.14, 0.72, 0.275)); p.body.add(at(box(0.26, 0.32, 0.04, '#ffffff'), 0, 0.46, 0.29)); p.body.add(at(box(0.16, 0.08, 0.02, '#9aa4b2'), 0, 0.5, 0.315)); }
  p.armL = new THREE.Group(); p.armL.position.set(-0.6, 0.92, 0); p.armL.add(at(box(0.27, 0.62, 0.3, shirt), 0, -0.25, 0)); p.armL.add(at(box(0.24, 0.3, 0.26, skin), 0, -0.7, 0));
  p.armR = new THREE.Group(); p.armR.position.set(0.6, 0.92, 0); p.armR.add(at(box(0.27, 0.62, 0.3, shirt), 0, -0.25, 0)); p.armR.add(at(box(0.24, 0.3, 0.26, skin), 0, -0.7, 0));
  if (cup) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.09, 0.24, 8), mat('#ffffff')); at(c, 0, -0.82, 0.2); c.castShadow = true; p.armR.add(c); p.armR.add(at(box(0.18, 0.02, 0.18, '#5a3a22'), 0, -0.695, 0.2)); }
  p.body.add(p.armL, p.armR);
  p.head = new THREE.Group(); p.head.position.y = 1.0; p.body.add(p.head);
  p.head.add(at(box(0.98, 0.96, 0.94, skin), 0, 0.48, 0));
  p.eyeL = at(box(0.13, 0.17, 0.04, '#1b1b1b'), -0.21, 0.55, 0.48); p.eyeR = at(box(0.13, 0.17, 0.04, '#1b1b1b'), 0.21, 0.55, 0.48);
  p.head.add(p.eyeL, p.eyeR);
  p.head.add(at(box(0.05, 0.05, 0.02, '#ffffff'), -0.18, 0.6, 0.505)); p.head.add(at(box(0.05, 0.05, 0.02, '#ffffff'), 0.24, 0.6, 0.505));
  p.browL = at(box(0.22, 0.06, 0.04, '#4a2c18'), -0.21, 0.72, 0.48); p.browR = at(box(0.22, 0.06, 0.04, '#4a2c18'), 0.21, 0.72, 0.48); p.head.add(p.browL, p.browR);
  p.head.add(at(box(0.17, 0.09, 0.03, '#f28c8c'), -0.34, 0.38, 0.475)); p.head.add(at(box(0.17, 0.09, 0.03, '#f28c8c'), 0.34, 0.38, 0.475));
  p.mouth = at(box(0.32, 0.08, 0.04, '#8a2b2b'), 0, 0.24, 0.48); p.head.add(p.mouth);
  p.mouthO = at(box(0.2, 0.22, 0.04, '#5a1a1a'), 0, 0.22, 0.48); p.mouthO.visible = false; p.head.add(p.mouthO);
  if (hairType === 'teo') {
    p.head.add(at(box(1.04, 0.26, 1.0, hair), 0, 0.98, -0.01)); p.head.add(at(box(1.04, 0.7, 0.22, hair), 0, 0.7, -0.4));
    p.head.add(at(box(0.36, 0.2, 0.2, hair), -0.25, 0.86, 0.44)); p.head.add(at(box(0.3, 0.16, 0.2, hair), 0.2, 0.9, 0.44));
    p.head.add(at(box(0.16, 0.5, 0.7, hair), -0.52, 0.72, -0.1)); p.head.add(at(box(0.16, 0.5, 0.7, hair), 0.52, 0.72, -0.1));
  } else {
    p.head.add(at(box(1.04, 0.22, 1.0, hair), 0, 0.98, -0.01)); p.head.add(at(box(1.06, 0.9, 0.24, hair), 0, 0.6, -0.4));
    p.head.add(at(box(0.18, 0.66, 0.8, hair), -0.53, 0.62, -0.06)); p.head.add(at(box(0.18, 0.66, 0.8, hair), 0.53, 0.62, -0.06));
  }
  if (helmet) {
    const dome = new THREE.Mesh(new THREE.SphereGeometry(0.6, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), mat(helmet)); dome.position.y = 1.02; dome.scale.set(1, 0.75, 1); dome.castShadow = true; p.head.add(dome);
    const brim = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.72, 0.07, 12), mat(helmet)); brim.position.set(0, 1.03, 0.08); brim.castShadow = true; p.head.add(brim);
    p.head.add(at(box(0.12, 0.42, 1.04, helmet), 0, 1.15, 0));
  }
  g.userData.p = p; return g;
}
function pose(g, { walk = 0, wave = 0, shock = 0, kneel = 0, look = 0, sip = 0 } = {}) {
  const p = g.userData.p;
  const s = Math.sin(walk);
  p.legL.rotation.x = s * 0.5 * (1 - kneel) + kneel * -Math.PI / 2 * 0.0; p.legR.rotation.x = -s * 0.5 * (1 - kneel);
  p.armL.rotation.x = -s * 0.45; p.armR.rotation.x = s * 0.45 - sip * 1.6;
  p.armR.rotation.z = wave ? 2.6 + Math.sin(wave) * 0.35 : 0;
  // kneel: legs fold back, body lowers
  if (kneel > 0) { p.legL.rotation.x = kneel * Math.PI / 2; p.legR.rotation.x = kneel * Math.PI / 2 * 0.15 - kneel * 1.2;
    p.body.position.y = 0.9 - kneel * 0.55; p.body.rotation.x = kneel * 0.35; p.head.rotation.x = kneel * 0.4; p.armR.rotation.x = -kneel * 1.1; p.armL.rotation.x = -kneel * 0.7; }
  else { p.body.position.y = 0.9 + Math.abs(Math.cos(walk)) * 0.04 * (walk ? 1 : 0); p.body.rotation.x = 0; p.head.rotation.x = look; }
  const sh = shock; p.mouth.visible = sh < 0.5; p.mouthO.visible = sh >= 0.5;
  const es = 1 + sh * 0.45; p.eyeL.scale.set(es, es, 1); p.eyeR.scale.set(es, es, 1);
  p.browL.position.y = 0.72 + sh * 0.08; p.browR.position.y = 0.72 + sh * 0.08;
  p.browL.rotation.z = -sh * 0.25; p.browR.rotation.z = sh * 0.25;
}
const teo = person({ shirt: '#f2b632', pants: '#2f5fa8', hair: '#6b3f22', helmet: '#ffd23f', cup: true });
const marta = person({ shirt: '#3b6fc4', pants: '#4a5263', hair: '#b5b5b5', helmet: '#ffffff', vest: '#ff7a1a', hairType: 'marta', skin: '#e9b48f' });
city.add(teo, marta);

// ---------- SOIL DIAGRAM ----------
const soil = new THREE.Group(); soil.position.set(1000, 0, 0); scene.add(soil);
const layers = [['#5fbf4a', 0.8], ['#d9a86c', 7], ['#c07a42', 7], ['#6b6e78', 40]];
{ let y = 0; for (const [c, h] of layers) { const b = box(46, h, 16, c); at(b, 0, y - h / 2, -8); b.castShadow = false; soil.add(b); y -= h; } }
const RS = rng(5);
for (let i = 0; i < 70; i++) { const pb = new THREE.Mesh(new THREE.IcosahedronGeometry(0.25 + RS() * 0.45, 0), mat(['#b98955', '#9b6133', '#555862', '#8a8d96'][i % 4])); const ly = i % 2 ? -1 - RS() * 13 : -15.5 - RS() * 5.5; at(pb, (RS() - 0.5) * 44, ly, 0.05); pb.castShadow = false; soil.add(pb); }
const rockGlow = box(46.2, 0.5, 16.2, '#ffe28a', { emissive: '#ffcc33', emissiveIntensity: 0 }); at(rockGlow, 0, -14.8, -8); soil.add(rockGlow);
// building base above soil
const sb = new THREE.Group(); soil.add(sb);
for (let i = 0; i < 4; i++) { for (const x of [-7, -2.3, 2.3, 7]) sb.add(at(box(0.7, FH, 0.7, '#b9bec4'), x, i * FH + FH / 2 + 0.8, 0)); sb.add(at(box(16, 0.4, 7, '#c4c8cd'), 0, (i + 1) * FH + 0.6, 0)); }
sb.add(at(box(17, 0.8, 8, '#a9aeb4'), 0, 0.4, 0));
const piles = [];
for (const x of [-7, -2.3, 2.3, 7]) { const g = new THREE.Group(); g.position.set(x, 0, 0.15); const c = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 1, 10), mat('#9fa5ad')); c.position.y = -0.5; c.castShadow = true; g.add(c); soil.add(g); piles.push(g); }
const PILE_LEN = 15.8;
// soil-side helpers
for (const x of [-18, 16]) { const t = new THREE.Group(); t.add(at(box(0.5, 1.8, 0.5, '#7a5230'), 0, 0.9, 0)); const c = new THREE.Mesh(new THREE.IcosahedronGeometry(2, 0), mat('#3fae49')); c.position.y = 3; c.castShadow = true; t.add(c); t.position.set(x, 0.8, 0); soil.add(t); }

// ---------- COLUMN DIAGRAM ----------
const colD = new THREE.Group(); colD.position.set(-1000, 0, 0); scene.add(colD);
const floorD = box(60, 0.4, 60, '#e9edf2'); at(floorD, 0, -0.2, 0); colD.add(floorD);
const cage = new THREE.Group(); colD.add(cage); cage.position.set(-2.6, 0, 0);
for (const [x, z] of [[-.55, -.55], [.55, -.55], [-.55, .55], [.55, .55]]) { const r = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 7, 8), mat('#b0482c')); r.position.set(x, 3.5, z); r.castShadow = true; cage.add(r); }
for (let y = 0.4; y < 7; y += 0.55) { for (const [w, d, x, z] of [[1.2, .07, 0, -.55], [1.2, .07, 0, .55], [.07, 1.2, -.55, 0], [.07, 1.2, .55, 0]]) cage.add(at(box(w, .07, d, '#c25a35'), x, y, z)); }
const concBlock = box(2.2, 3.2, 2.2, '#b9bec4'); at(concBlock, 2.8, 1.6, 0); colD.add(concBlock);
const shell = new THREE.Mesh(new THREE.BoxGeometry(1.9, 7, 1.9), new THREE.MeshStandardMaterial({ color: '#b9bec4', transparent: true, opacity: 0, roughness: 0.9, flatShading: true, depthWrite: false }));
shell.position.set(0, 3.5, 0); cage.add(shell);
function arrow(color) { const g = new THREE.Group(); const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 1.2, 8), mat(color, { emissive: color, emissiveIntensity: 0.25 })); sh.position.y = 0.6; const hd = new THREE.Mesh(new THREE.ConeGeometry(0.32, 0.6, 10), mat(color, { emissive: color, emissiveIntensity: 0.25 })); hd.position.y = 1.5; g.add(sh, hd); return g; }
const pullUp = arrow('#ff5a3c'), pullDn = arrow('#ff5a3c'); colD.add(pullUp, pullDn);
const pushDn = arrow('#2f8fe6'), pushUp = arrow('#2f8fe6'); colD.add(pushDn, pushUp);


let skyNight = 0;
function setSky(dayAmt) { // 1 day, 0 night, 0.5 sunrise
  const night = { top: new THREE.Color('#0b1636'), bot: new THREE.Color('#1d2c57') };
  const dawn = { top: new THREE.Color('#4a74c9'), bot: new THREE.Color('#ffb27a') };
  const day = { top: new THREE.Color('#2f8fe6'), bot: new THREE.Color('#b8e2ff') };
  let top, bot;
  if (dayAmt < 0.5) { const x = dayAmt / 0.5; top = night.top.clone().lerp(dawn.top, x); bot = night.bot.clone().lerp(dawn.bot, x); }
  else { const x = (dayAmt - 0.5) / 0.5; top = dawn.top.clone().lerp(day.top, x); bot = dawn.bot.clone().lerp(day.bot, x); }
  skyMat.uniforms.top.value.copy(top); skyMat.uniforms.bottom.value.copy(bot); scene.fog.color.copy(bot);
  sun.intensity = lerp(0.15, 2.6, clamp(dayAmt * 1.3)); hemi.intensity = lerp(0.35, 1.6, dayAmt);
  sun.color.set(dayAmt < 0.75 ? '#ffc08a' : '#fff1dc');
  moon.visible = dayAmt < 0.45;
}

const colBg = new THREE.Color('#cfe9ff');
function show(which) { city.visible = which === 'city'; soil.visible = which === 'soil'; colD.visible = which === 'col'; sky.visible = which !== 'col'; scene.background = which === 'col' ? colBg : null; }


function cam(pos, tgt, fov = 50) { camera.position.copy(pos); camera.lookAt(tgt); camera.fov = fov; camera.updateProjectionMatrix(); }
function camPath(t, a, b, p0, p1, t0, t1, fov0 = 50, fov1 = fov0, f = ease) { const x = f(seg(t, a, b)); cam(lerpV(p0, p1, x), lerpV(t0, t1, x), lerp(fov0, fov1, x)); }

const out = document.getElementById('out'); const ctx = out.getContext('2d');
function clean(w) { return w.replace(/[.,:;!?…]+$/g, '').replace(/…/g, ''); }
function project(v) { const p = v.clone().project(camera); return { x: (p.x * 0.5 + 0.5) * W, y: (-p.y * 0.5 + 0.5) * H, behind: p.z > 1 }; }
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
function outlined(text, x, y, size, fill, stroke = '#1b2030', sw = null, font = 'Lilita') {
  ctx.font = `${size}px ${font}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  ctx.lineWidth = sw ?? size * 0.16; ctx.strokeStyle = stroke;
  ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowOffsetY = size * 0.06; ctx.strokeText(text, x, y); ctx.restore();
  ctx.fillStyle = fill; ctx.fillText(text, x, y);
}
function pill(x, y, text, dot, age) {
  const s = easeOut(clamp(age / 0.18)); if (s <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.font = '800 40px Inter'; const tw = ctx.measureText(text).width; const w = tw + 84, h = 68;
  ctx.shadowColor = 'rgba(0,0,0,0.28)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 4;
  rr(-w / 2, -h / 2, w, h, h / 2); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.shadowColor = 'transparent';
  ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(27,32,48,0.15)'; ctx.stroke();
  ctx.beginPath(); ctx.arc(-w / 2 + 33, 0, 13, 0, Math.PI * 2); ctx.fillStyle = dot; ctx.fill(); ctx.lineWidth = 2.5; ctx.strokeStyle = 'rgba(0,0,0,0.25)'; ctx.stroke();
  ctx.fillStyle = '#1b2030'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(text, -w / 2 + 58, 2);
  ctx.restore();
}

let WARP = null; // [[newT, oldT], ...] maps narration time to animation timeline
function warp(t) { if (!WARP) return t; const A = WARP; if (t <= A[0][0]) return A[0][1] + (t - A[0][0]); for (let i = 1; i < A.length; i++) if (t <= A[i][0]) { const [n0, o0] = A[i - 1], [n1, o1] = A[i]; return o0 + (o1 - o0) * (t - n0) / (n1 - n0); } const L = A[A.length - 1]; return L[1] + (t - L[0]); }

export function setWarp(w) { WARP = w; }
export { sealB, ctx, COLS, CRACK_C, CRANE_H, FH, H, HALF, HD, HHt, HW, LVL, LY, NF, PILE_LEN, R, RC, RH, RS, RW, W, WARP, arrow, at, box, cable, cage, cam, camPath, camera, city, clamp, clean, clouds, colBg, colD, concBlock, crackDir, crackG, crackPts, crackSegs, crane, dirt, ease, easeOut, floorD, floors, glCanvas, ground, hemi, hoist, jibG, layers, lerp, lerpV, marta, mast, mat, mats, moon, out, outlined, person, piles, pill, pose, project, pullDn, pullUp, pushDn, pushUp, renderer, rng, rockGlow, roofCol, rr, sb, scene, seal, sealA, sealMid, seg, setFloors, setSky, shell, show, sky, skyGeo, skyMat, skyNight, soil, stubs, sun, teo, tower, v3, wallCol, warp };
