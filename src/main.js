import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { SSAOPass } from 'three/addons/postprocessing/SSAOPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import './style.css';

const app = document.querySelector('#app');
const startScreen = document.querySelector('#start-screen');
const startButton = document.querySelector('#start-button');
const fpsEl = document.querySelector('#fps');
const statusEl = document.querySelector('#status');

const WORLD_SIZE = 82;
const HALF_WORLD = WORLD_SIZE * 0.5;
const WATER_LEVEL = -0.85;
const POND = { x: 12, z: -10, radius: 13.5 };
const EYE_HEIGHT = 1.72;

let seed = 980145;
function random() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
}
const rand = (min, max) => min + (max - min) * random();
function hash2(x, z) {
  const s = Math.sin(x * 127.1 + z * 311.7) * 43758.5453123;
  return s - Math.floor(s);
}
function smoothstep(a, b, x) {
  const t = THREE.MathUtils.clamp((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xa9b7ad);
scene.fog = new THREE.FogExp2(0x9eaa9a, 0.019);

const camera = new THREE.PerspectiveCamera(69, innerWidth / innerHeight, 0.04, 220);
camera.rotation.order = 'YXZ';

const renderer = new THREE.WebGLRenderer({
  antialias: true,
  powerPreference: 'high-performance',
  logarithmicDepthBuffer: false,
});
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.55));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.18;
renderer.outputColorSpace = THREE.SRGBColorSpace;
app.appendChild(renderer.domElement);

const maxAniso = Math.min(8, renderer.capabilities.getMaxAnisotropy());

function canvasTexture(size, draw, srgb = true) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  draw(ctx, size);
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.anisotropy = maxAniso;
  if (srgb) texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

const groundDiffuse = canvasTexture(1024, (ctx, s) => {
  const g = ctx.createLinearGradient(0, 0, s, s);
  g.addColorStop(0, '#3e3a28');
  g.addColorStop(0.5, '#4d4a31');
  g.addColorStop(1, '#343828');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, s, s);

  for (let i = 0; i < 26000; i++) {
    const x = random() * s;
    const y = random() * s;
    const r = rand(0.4, 2.6);
    const type = random();
    if (type < 0.46) ctx.fillStyle = `rgba(45,55,31,${rand(0.12,0.4)})`;
    else if (type < 0.78) ctx.fillStyle = `rgba(95,75,42,${rand(0.12,0.35)})`;
    else ctx.fillStyle = `rgba(20,25,18,${rand(0.08,0.22)})`;
    ctx.beginPath();
    ctx.ellipse(x, y, r * rand(0.7, 2), r, rand(0, Math.PI), 0, Math.PI * 2);
    ctx.fill();
  }

  for (let i = 0; i < 1800; i++) {
    const x = random() * s;
    const y = random() * s;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rand(0, Math.PI * 2));
    const leaf = random();
    ctx.fillStyle = leaf < 0.45 ? 'rgba(105,73,35,.72)' : leaf < 0.8 ? 'rgba(72,82,39,.6)' : 'rgba(132,98,47,.55)';
    ctx.beginPath();
    ctx.ellipse(0, 0, rand(1.5, 5), rand(0.7, 2.2), 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  for (let i = 0; i < 430; i++) {
    ctx.save();
    ctx.translate(random() * s, random() * s);
    ctx.rotate(rand(0, Math.PI * 2));
    ctx.strokeStyle = `rgba(53,35,21,${rand(0.35,0.8)})`;
    ctx.lineWidth = rand(1, 3);
    ctx.beginPath();
    ctx.moveTo(-rand(5, 15), 0);
    ctx.lineTo(rand(5, 18), 0);
    ctx.stroke();
    ctx.restore();
  }
});
groundDiffuse.repeat.set(13, 13);

const groundBump = canvasTexture(512, (ctx, s) => {
  ctx.fillStyle = '#777';
  ctx.fillRect(0, 0, s, s);
  const image = ctx.getImageData(0, 0, s, s);
  const d = image.data;
  for (let y = 0; y < s; y++) {
    for (let x = 0; x < s; x++) {
      const i = (y * s + x) * 4;
      const n =
        Math.sin(x * 0.17) * 11 +
        Math.cos(y * 0.19) * 10 +
        Math.sin((x + y) * 0.071) * 8 +
        (hash2(x, y) - 0.5) * 42;
      const v = THREE.MathUtils.clamp(118 + n, 60, 190);
      d[i] = d[i + 1] = d[i + 2] = v;
      d[i + 3] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);
}, false);
groundBump.repeat.set(13, 13);

const barkDiffuse = canvasTexture(512, (ctx, s) => {
  ctx.fillStyle = '#4a3426';
  ctx.fillRect(0, 0, s, s);
  for (let i = 0; i < 1700; i++) {
    const x = random() * s;
    const w = rand(1, 6);
    const h = rand(10, 85);
    ctx.fillStyle = random() > 0.45 ? `rgba(28,17,12,${rand(0.2,0.62)})` : `rgba(103,73,43,${rand(0.12,0.38)})`;
    ctx.fillRect(x, random() * s, w, h);
  }
  for (let i = 0; i < 700; i++) {
    ctx.strokeStyle = `rgba(24,15,11,${rand(0.18,0.5)})`;
    ctx.lineWidth = rand(1, 3);
    const x = random() * s;
    const y = random() * s;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.bezierCurveTo(x + rand(-8,8), y + rand(8,25), x + rand(-8,8), y + rand(24,52), x + rand(-5,5), y + rand(45,95));
    ctx.stroke();
  }
});
barkDiffuse.repeat.set(2, 5);

const leafTexture = canvasTexture(512, (ctx, s) => {
  ctx.clearRect(0, 0, s, s);
  for (let i = 0; i < 240; i++) {
    const x = rand(20, s - 20);
    const y = rand(20, s - 20);
    const rx = rand(8, 28);
    const ry = rand(4, 15);
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rand(0, Math.PI * 2));
    const hue = rand(84, 118);
    const sat = rand(28, 52);
    const light = rand(18, 38);
    ctx.fillStyle = `hsla(${hue},${sat}%,${light}%,${rand(0.72,0.98)})`;
    ctx.beginPath();
    ctx.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}, true);

function terrainHeight(x, z) {
  const broad =
    Math.sin(x * 0.11) * 0.62 +
    Math.cos(z * 0.095) * 0.52 +
    Math.sin((x + z) * 0.061) * 0.42;
  const detail =
    Math.sin(x * 0.31 + z * 0.07) * 0.12 +
    Math.cos(z * 0.28 - x * 0.11) * 0.1;
  let h = broad + detail;

  const d = Math.hypot(x - POND.x, z - POND.z);
  if (d < POND.radius + 5.5) {
    const basin = 1 - smoothstep(POND.radius - 2.0, POND.radius + 5.5, d);
    const bowl = WATER_LEVEL - 0.6 - Math.max(0, (POND.radius - d) / POND.radius) * 2.75;
    h = THREE.MathUtils.lerp(h, bowl, basin * 0.98);
  }

  // Flatter spawn clearing.
  const spawnD = Math.hypot(x + 8, z - 12);
  if (spawnD < 8) h = THREE.MathUtils.lerp(h, 0.1, 1 - smoothstep(2, 8, spawnD));
  return h;
}

const groundGeo = new THREE.PlaneGeometry(WORLD_SIZE, WORLD_SIZE, 180, 180);
groundGeo.rotateX(-Math.PI / 2);
const gp = groundGeo.attributes.position;
const colors = [];
for (let i = 0; i < gp.count; i++) {
  const x = gp.getX(i);
  const z = gp.getZ(i);
  const y = terrainHeight(x, z);
  gp.setY(i, y);
  const d = Math.hypot(x - POND.x, z - POND.z);
  const wet = 1 - smoothstep(POND.radius - 1.2, POND.radius + 3.2, d);
  const c = new THREE.Color().setHSL(
    0.19 + hash2(i, i * 2.1) * 0.04,
    0.26 + hash2(i * 3.1, i) * 0.14,
    THREE.MathUtils.lerp(0.24, 0.12, wet),
  );
  colors.push(c.r, c.g, c.b);
}
groundGeo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
groundGeo.computeVertexNormals();

const groundMat = new THREE.MeshStandardMaterial({
  map: groundDiffuse,
  bumpMap: groundBump,
  bumpScale: 0.075,
  vertexColors: true,
  roughness: 0.96,
  metalness: 0,
});
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.receiveShadow = true;
scene.add(ground);

// Lighting
const hemi = new THREE.HemisphereLight(0xd6e1dc, 0x1d2419, 1.32);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xffefc5, 5.1);
sun.position.set(-28, 48, 18);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -48;
sun.shadow.camera.right = 48;
sun.shadow.camera.top = 48;
sun.shadow.camera.bottom = -48;
sun.shadow.camera.near = 4;
sun.shadow.camera.far = 110;
sun.shadow.bias = -0.0002;
sun.shadow.normalBias = 0.018;
scene.add(sun);

const fill = new THREE.DirectionalLight(0x9ab4c4, 0.5);
fill.position.set(32, 18, -30);
scene.add(fill);

// Soft fake sun shafts through canopy.
const shaftMat = new THREE.MeshBasicMaterial({
  color: 0xffefc9,
  transparent: true,
  opacity: 0.045,
  side: THREE.DoubleSide,
  depthWrite: false,
  blending: THREE.AdditiveBlending,
});
for (let i = 0; i < 9; i++) {
  const geo = new THREE.ConeGeometry(rand(1.4, 3.0), rand(14, 24), 18, 1, true);
  const mesh = new THREE.Mesh(geo, shaftMat);
  mesh.position.set(rand(-28, 25), rand(6, 12), rand(-30, 26));
  mesh.rotation.z = rand(-0.16, 0.12);
  mesh.rotation.x = rand(-0.08, 0.08);
  scene.add(mesh);
}

// Trees: detailed trunks + foliage cards.
const treeColliders = [];
const TREE_COUNT = 132;
const TRUNK_SEGMENTS = 3;
const FOLIAGE_PER_TREE = 9;
const trunkGeo = new THREE.CylinderGeometry(0.42, 0.58, 3.8, 10, 4, false);
const trunkMat = new THREE.MeshStandardMaterial({
  map: barkDiffuse,
  bumpMap: barkDiffuse,
  bumpScale: 0.085,
  roughness: 0.98,
});
const trunks = new THREE.InstancedMesh(trunkGeo, trunkMat, TREE_COUNT * TRUNK_SEGMENTS);
trunks.castShadow = true;
trunks.receiveShadow = true;

const branchGeo = new THREE.CylinderGeometry(0.09, 0.16, 2.6, 7, 1);
const branchMat = trunkMat;
const branches = new THREE.InstancedMesh(branchGeo, branchMat, TREE_COUNT * 4);
branches.castShadow = true;

const leafGeo = new THREE.PlaneGeometry(4.2, 3.1);
const leafMat = new THREE.MeshStandardMaterial({
  map: leafTexture,
  alphaMap: leafTexture,
  alphaTest: 0.18,
  transparent: true,
  side: THREE.DoubleSide,
  roughness: 0.94,
  depthWrite: true,
});
const foliage = new THREE.InstancedMesh(leafGeo, leafMat, TREE_COUNT * FOLIAGE_PER_TREE * 2);
foliage.castShadow = true;
foliage.receiveShadow = false;

const dummy = new THREE.Object3D();
const tempColor = new THREE.Color();
let ti = 0;
let bi = 0;
let fi = 0;
let accepted = 0;
let attempts = 0;

while (accepted < TREE_COUNT && attempts < TREE_COUNT * 30) {
  attempts++;
  const edgeBias = random();
  let x;
  let z;
  if (edgeBias < 0.4) {
    const side = Math.floor(random() * 4);
    if (side === 0) { x = rand(-HALF_WORLD, HALF_WORLD); z = rand(-HALF_WORLD, -22); }
    if (side === 1) { x = rand(-HALF_WORLD, HALF_WORLD); z = rand(22, HALF_WORLD); }
    if (side === 2) { x = rand(-HALF_WORLD, -22); z = rand(-HALF_WORLD, HALF_WORLD); }
    if (side === 3) { x = rand(22, HALF_WORLD); z = rand(-HALF_WORLD, HALF_WORLD); }
  } else {
    x = rand(-HALF_WORLD + 2, HALF_WORLD - 2);
    z = rand(-HALF_WORLD + 2, HALF_WORLD - 2);
  }

  const pondD = Math.hypot(x - POND.x, z - POND.z);
  const spawnD = Math.hypot(x + 8, z - 12);
  if (pondD < POND.radius + 2.2 || spawnD < 6.5) continue;

  const baseY = terrainHeight(x, z);
  const s = rand(0.78, 1.35);
  const leanX = rand(-0.035, 0.035);
  const leanZ = rand(-0.035, 0.035);
  const yaw = rand(0, Math.PI * 2);
  const height = 10.6 * s;

  for (let seg = 0; seg < TRUNK_SEGMENTS; seg++) {
    const segY = baseY + (seg + 0.5) * (height / TRUNK_SEGMENTS);
    const taper = 1 - seg * 0.12;
    dummy.position.set(x + leanX * seg * 2.1, segY, z + leanZ * seg * 2.1);
    dummy.rotation.set(leanZ, yaw, -leanX);
    dummy.scale.set(s * taper, (height / TRUNK_SEGMENTS) / 3.8, s * taper);
    dummy.updateMatrix();
    trunks.setMatrixAt(ti, dummy.matrix);
    tempColor.setHSL(rand(0.065, 0.09), rand(0.28, 0.42), rand(0.20, 0.31));
    trunks.setColorAt(ti++, tempColor);
  }

  for (let b = 0; b < 4; b++) {
    const angle = yaw + b * Math.PI * 0.5 + rand(-0.55, 0.55);
    const by = baseY + height * rand(0.52, 0.8);
    dummy.position.set(x + Math.cos(angle) * 0.7, by, z + Math.sin(angle) * 0.7);
    dummy.rotation.set(Math.PI * 0.5 + rand(-0.35, 0.2), 0, -angle + rand(-0.22, 0.22));
    dummy.scale.set(s * rand(0.75, 1.2), s * rand(0.7, 1.25), s * rand(0.75, 1.2));
    dummy.updateMatrix();
    branches.setMatrixAt(bi++, dummy.matrix);
  }

  for (let c = 0; c < FOLIAGE_PER_TREE; c++) {
    const a = rand(0, Math.PI * 2);
    const rr = rand(0.8, 3.3) * s;
    const yy = baseY + height * rand(0.57, 1.0);
    const cx = x + Math.cos(a) * rr;
    const cz = z + Math.sin(a) * rr;
    const scale = rand(0.75, 1.38) * s;

    for (let cross = 0; cross < 2; cross++) {
      dummy.position.set(cx, yy + rand(-0.4, 0.45), cz);
      dummy.rotation.set(rand(-0.18,0.18), a + cross * Math.PI * 0.5 + rand(-0.25,0.25), rand(-0.1,0.1));
      dummy.scale.set(scale, scale * rand(0.72,1.18), scale);
      dummy.updateMatrix();
      foliage.setMatrixAt(fi, dummy.matrix);
      tempColor.setHSL(rand(0.25, 0.34), rand(0.38, 0.58), rand(0.19, 0.34));
      foliage.setColorAt(fi++, tempColor);
    }
  }

  treeColliders.push({ x, z, r: 0.48 * s + 0.28 });
  accepted++;
}

for (const mesh of [trunks, branches, foliage]) {
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  scene.add(mesh);
}

// Forest floor details.
const ROCK_COUNT = 120;
const rockGeo = new THREE.DodecahedronGeometry(0.58, 1);
const rockMat = new THREE.MeshStandardMaterial({
  color: 0x65705e,
  roughness: 0.98,
  bumpMap: groundBump,
  bumpScale: 0.025,
});
const rocks = new THREE.InstancedMesh(rockGeo, rockMat, ROCK_COUNT);
rocks.castShadow = true;
rocks.receiveShadow = true;

for (let i = 0; i < ROCK_COUNT; i++) {
  let x, z, pd;
  do {
    x = rand(-HALF_WORLD + 2, HALF_WORLD - 2);
    z = rand(-HALF_WORLD + 2, HALF_WORLD - 2);
    pd = Math.hypot(x - POND.x, z - POND.z);
  } while (pd < POND.radius - 2.0);
  const y = terrainHeight(x, z);
  const s = rand(0.25, 1.6);
  dummy.position.set(x, y + s * 0.18, z);
  dummy.rotation.set(rand(0, Math.PI), rand(0, Math.PI), rand(0, Math.PI));
  dummy.scale.set(s * rand(0.8,1.6), s * rand(0.35,0.85), s * rand(0.75,1.5));
  dummy.updateMatrix();
  rocks.setMatrixAt(i, dummy.matrix);
  tempColor.setHSL(rand(0.18,0.31), rand(0.05,0.18), rand(0.28,0.48));
  rocks.setColorAt(i, tempColor);
}
rocks.instanceMatrix.needsUpdate = true;
if (rocks.instanceColor) rocks.instanceColor.needsUpdate = true;
scene.add(rocks);

const grassGeo = new THREE.PlaneGeometry(0.34, 1.0);
grassGeo.translate(0, 0.5, 0);
const grassMat = new THREE.MeshStandardMaterial({
  color: 0x516e43,
  roughness: 1,
  side: THREE.DoubleSide,
  alphaTest: 0.05,
});
const GRASS_COUNT = 4800;
const grass = new THREE.InstancedMesh(grassGeo, grassMat, GRASS_COUNT);
grass.receiveShadow = true;
for (let i = 0; i < GRASS_COUNT; i++) {
  let x = rand(-HALF_WORLD + 1, HALF_WORLD - 1);
  let z = rand(-HALF_WORLD + 1, HALF_WORLD - 1);
  const pd = Math.hypot(x - POND.x, z - POND.z);
  if (pd < POND.radius - 1.4) {
    i--;
    continue;
  }
  const y = terrainHeight(x, z);
  const s = rand(0.28, 1.05);
  dummy.position.set(x, y + 0.01, z);
  dummy.rotation.set(rand(-0.08,0.08), rand(0, Math.PI * 2), rand(-0.14,0.14));
  dummy.scale.set(s * rand(0.65,1.4), s, s);
  dummy.updateMatrix();
  grass.setMatrixAt(i, dummy.matrix);
  tempColor.setHSL(rand(0.22,0.35), rand(0.30,0.58), rand(0.22,0.43));
  grass.setColorAt(i, tempColor);
}
grass.instanceMatrix.needsUpdate = true;
if (grass.instanceColor) grass.instanceColor.needsUpdate = true;
scene.add(grass);

// Ferns
const fernGroup = new THREE.Group();
const fernMat = new THREE.MeshStandardMaterial({
  color: 0x35603b,
  side: THREE.DoubleSide,
  roughness: 0.9,
});
for (let i = 0; i < 180; i++) {
  const x = rand(-HALF_WORLD + 2, HALF_WORLD - 2);
  const z = rand(-HALF_WORLD + 2, HALF_WORLD - 2);
  const pd = Math.hypot(x - POND.x, z - POND.z);
  if (pd < POND.radius - 1) continue;
  const y = terrainHeight(x, z);
  const plant = new THREE.Group();
  const fronds = 5;
  for (let f = 0; f < fronds; f++) {
    const geo = new THREE.PlaneGeometry(rand(0.18,0.28), rand(0.9,1.5), 1, 3);
    geo.translate(0, 0.5, 0);
    const m = new THREE.Mesh(geo, fernMat);
    m.rotation.y = (f / fronds) * Math.PI * 2 + rand(-0.2,0.2);
    m.rotation.x = rand(-0.75,-0.35);
    m.rotation.z = rand(-0.18,0.18);
    m.position.y = 0.04;
    plant.add(m);
  }
  plant.position.set(x, y, z);
  plant.scale.setScalar(rand(0.55,1.2));
  fernGroup.add(plant);
}
scene.add(fernGroup);

// Fallen logs
const logGeo = new THREE.CylinderGeometry(0.34, 0.46, 5.8, 10, 4);
for (let i = 0; i < 8; i++) {
  const x = rand(-30, 30);
  const z = rand(-30, 30);
  if (Math.hypot(x - POND.x, z - POND.z) < POND.radius + 1.2) continue;
  const y = terrainHeight(x,z);
  const log = new THREE.Mesh(logGeo, trunkMat);
  log.castShadow = true;
  log.receiveShadow = true;
  log.position.set(x, y + 0.32, z);
  log.rotation.z = Math.PI * 0.5 + rand(-0.15,0.15);
  log.rotation.y = rand(0, Math.PI * 2);
  log.scale.set(rand(0.75,1.25), rand(0.7,1.35), rand(0.75,1.25));
  scene.add(log);
}

// Pond water
const waterBump = canvasTexture(256, (ctx, s) => {
  const img = ctx.createImageData(s, s);
  for (let y = 0; y < s; y++) {
    for (let x = 0; x < s; x++) {
      const i = (y*s+x)*4;
      const v = 128 + Math.sin(x*0.16 + Math.sin(y*0.05)*2.2)*24 + Math.cos(y*0.19)*18;
      img.data[i] = img.data[i+1] = img.data[i+2] = v;
      img.data[i+3] = 255;
    }
  }
  ctx.putImageData(img,0,0);
}, false);
waterBump.repeat.set(4,4);

const waterGeo = new THREE.CircleGeometry(POND.radius, 128);
waterGeo.rotateX(-Math.PI / 2);
const waterMat = new THREE.MeshPhysicalMaterial({
  color: 0x496f68,
  roughness: 0.12,
  metalness: 0,
  transmission: 0.28,
  transparent: true,
  opacity: 0.72,
  clearcoat: 1,
  clearcoatRoughness: 0.08,
  bumpMap: waterBump,
  bumpScale: 0.055,
  depthWrite: false,
});
const water = new THREE.Mesh(waterGeo, waterMat);
water.position.set(POND.x, WATER_LEVEL, POND.z);
water.receiveShadow = true;
water.renderOrder = 3;
scene.add(water);

// Reeds and shoreline plants.
const reedGeo = new THREE.CylinderGeometry(0.014, 0.022, 1.35, 5);
const reedMat = new THREE.MeshStandardMaterial({ color: 0x536b36, roughness: 0.9 });
const REED_COUNT = 520;
const reeds = new THREE.InstancedMesh(reedGeo, reedMat, REED_COUNT);
for (let i = 0; i < REED_COUNT; i++) {
  const a = rand(0, Math.PI * 2);
  const r = rand(POND.radius - 1.6, POND.radius + 1.25);
  const x = POND.x + Math.cos(a) * r;
  const z = POND.z + Math.sin(a) * r;
  const y = Math.max(terrainHeight(x,z), WATER_LEVEL - 0.8);
  const h = rand(0.55,1.5);
  dummy.position.set(x, y + h * 0.45, z);
  dummy.rotation.set(rand(-0.12,0.12), rand(0,Math.PI*2), rand(-0.12,0.12));
  dummy.scale.set(1, h, 1);
  dummy.updateMatrix();
  reeds.setMatrixAt(i,dummy.matrix);
  tempColor.setHSL(rand(0.20,0.31),rand(0.35,0.55),rand(0.23,0.38));
  reeds.setColorAt(i,tempColor);
}
reeds.instanceMatrix.needsUpdate = true;
if(reeds.instanceColor) reeds.instanceColor.needsUpdate = true;
scene.add(reeds);

// Upgrade the procedural fallback with lightweight photo-scanned CC0 assets.
// If a remote asset ever fails, the procedural materials above stay active.
async function upgradePhotoAssets() {
  const loader = new THREE.TextureLoader();
  loader.crossOrigin = 'anonymous';

  async function loadTexture(url, { srgb = false, repeatX = 1, repeatY = 1 } = {}) {
    try {
      const texture = await loader.loadAsync(url);
      texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
      texture.repeat.set(repeatX, repeatY);
      texture.anisotropy = maxAniso;
      if (srgb) texture.colorSpace = THREE.SRGBColorSpace;
      return texture;
    } catch (error) {
      console.warn('Optional photo asset failed; using procedural fallback:', url);
      return null;
    }
  }

  const base = 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k';
  const [forestDiff, forestNormal, forestRough, barkDiff, barkNormal, barkRough, leavesDiff, leavesAlpha] = await Promise.all([
    loadTexture(`${base}/forrest_ground_01/forrest_ground_01_diff_1k.jpg`, { srgb: true, repeatX: 13, repeatY: 13 }),
    loadTexture(`${base}/forrest_ground_01/forrest_ground_01_nor_gl_1k.jpg`, { repeatX: 13, repeatY: 13 }),
    loadTexture(`${base}/forrest_ground_01/forrest_ground_01_rough_1k.jpg`, { repeatX: 13, repeatY: 13 }),
    loadTexture(`${base}/bark_brown_01/bark_brown_01_diff_1k.jpg`, { srgb: true, repeatX: 2, repeatY: 5 }),
    loadTexture(`${base}/bark_brown_01/bark_brown_01_nor_gl_1k.jpg`, { repeatX: 2, repeatY: 5 }),
    loadTexture(`${base}/bark_brown_01/bark_brown_01_rough_1k.jpg`, { repeatX: 2, repeatY: 5 }),
    loadTexture('https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/tree_small_02/tree_small_02_leaves_diff_1k.jpg', { srgb: true }),
    loadTexture('https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/tree_small_02/tree_small_02_leaves_alpha_1k.jpg'),
  ]);

  if (forestDiff) groundMat.map = forestDiff;
  if (forestNormal) {
    groundMat.normalMap = forestNormal;
    groundMat.normalScale.set(0.72, 0.72);
    groundMat.bumpMap = null;
  }
  if (forestRough) groundMat.roughnessMap = forestRough;
  groundMat.needsUpdate = true;

  if (barkDiff) trunkMat.map = barkDiff;
  if (barkNormal) {
    trunkMat.normalMap = barkNormal;
    trunkMat.normalScale.set(0.85, 0.85);
    trunkMat.bumpMap = null;
  }
  if (barkRough) trunkMat.roughnessMap = barkRough;
  trunkMat.needsUpdate = true;

  if (leavesDiff) leafMat.map = leavesDiff;
  if (leavesAlpha) leafMat.alphaMap = leavesAlpha;
  leafMat.alphaTest = 0.32;
  leafMat.transparent = true;
  leafMat.needsUpdate = true;

  try {
    const hdr = await new RGBELoader().loadAsync(
      'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/rainforest_trail_1k.hdr'
    );
    hdr.mapping = THREE.EquirectangularReflectionMapping;
    scene.environment = hdr;
    scene.background = hdr;
    scene.backgroundBlurriness = 0.12;
    scene.backgroundIntensity = 0.68;
    groundMat.envMapIntensity = 0.32;
    trunkMat.envMapIntensity = 0.22;
    rockMat.envMapIntensity = 0.26;
    waterMat.envMapIntensity = 1.0;
  } catch (error) {
    console.warn('Optional HDR forest environment failed; using procedural sky.');
  }
}
upgradePhotoAssets();

// Air motes and insects
const MOTE_COUNT = 700;
const moteGeo = new THREE.BufferGeometry();
const motePos = new Float32Array(MOTE_COUNT * 3);
for (let i = 0; i < MOTE_COUNT; i++) {
  motePos[i*3] = rand(-35,35);
  motePos[i*3+1] = rand(0.2,12);
  motePos[i*3+2] = rand(-35,35);
}
moteGeo.setAttribute('position', new THREE.BufferAttribute(motePos,3));
const motes = new THREE.Points(
  moteGeo,
  new THREE.PointsMaterial({
    color: 0xffefbf,
    size: 0.035,
    transparent: true,
    opacity: 0.36,
    depthWrite: false,
  }),
);
scene.add(motes);

// Subtle boundary forest wall.
const wallMat = new THREE.MeshStandardMaterial({
  color: 0x1e2e1e,
  roughness: 1,
  side: THREE.DoubleSide,
});
for (let i = 0; i < 28; i++) {
  const a = (i / 28) * Math.PI * 2;
  const x = Math.cos(a) * (HALF_WORLD + 5);
  const z = Math.sin(a) * (HALF_WORLD + 5);
  const mesh = new THREE.Mesh(new THREE.ConeGeometry(rand(3,5), rand(14,22), 7), wallMat);
  mesh.position.set(x, terrainHeight(THREE.MathUtils.clamp(x,-40,40),THREE.MathUtils.clamp(z,-40,40)) + 7, z);
  scene.add(mesh);
}

// Post processing
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));

const ssao = new SSAOPass(scene, camera, innerWidth, innerHeight);
ssao.kernelRadius = 12;
ssao.minDistance = 0.002;
ssao.maxDistance = 0.12;
ssao.output = SSAOPass.OUTPUT.Default;
composer.addPass(ssao);

const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.11, 0.38, 0.92);
composer.addPass(bloom);
composer.addPass(new OutputPass());

// UI overlay for underwater.
const underwaterOverlay = document.createElement('div');
underwaterOverlay.id = 'underwater-overlay';
document.body.appendChild(underwaterOverlay);

// Player
const player = {
  position: new THREE.Vector3(-8, terrainHeight(-8,12), 12),
  velocityY: 0,
  grounded: true,
  swimming: false,
  submerged: false,
  yaw: Math.PI,
  pitch: -0.03,
  bobTime: 0,
};

const keys = new Set();
let pointerLocked = false;

function lockPointer() {
  renderer.domElement.requestPointerLock();
}
startButton.addEventListener('click', lockPointer);
renderer.domElement.addEventListener('click', () => {
  if (!pointerLocked) lockPointer();
});
document.addEventListener('pointerlockchange', () => {
  pointerLocked = document.pointerLockElement === renderer.domElement;
  startScreen.classList.toggle('hidden', pointerLocked);
  if (!pointerLocked) statusEl.textContent = 'CLICK TO RESUME';
});
document.addEventListener('mousemove', (e) => {
  if (!pointerLocked) return;
  player.yaw -= e.movementX * 0.00175;
  player.pitch -= e.movementY * 0.00165;
  player.pitch = THREE.MathUtils.clamp(player.pitch, -1.47, 1.47);
});
addEventListener('keydown', (e) => {
  keys.add(e.code);
  if (['Space','ControlLeft','ControlRight','KeyC','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code)) e.preventDefault();
  if (e.code === 'Space' && player.grounded && !player.swimming && pointerLocked) {
    player.velocityY = 8.2;
    player.grounded = false;
  }
});
addEventListener('keyup', (e) => keys.delete(e.code));

function resolveTreeCollision(pos) {
  for (let i = 0; i < treeColliders.length; i++) {
    const t = treeColliders[i];
    const dx = pos.x - t.x;
    const dz = pos.z - t.z;
    const min = t.r + 0.32;
    const d2 = dx*dx + dz*dz;
    if (d2 < min*min && d2 > 0.000001) {
      const d = Math.sqrt(d2);
      const push = min - d;
      pos.x += dx / d * push;
      pos.z += dz / d * push;
    }
  }
}

const moveForward = new THREE.Vector3();
const moveRight = new THREE.Vector3();
const desired = new THREE.Vector3();

function updatePlayer(dt, elapsed) {
  const forwardInput = (keys.has('KeyW')?1:0) - (keys.has('KeyS')?1:0);
  const sideInput = (keys.has('KeyD')?1:0) - (keys.has('KeyA')?1:0);
  const sprinting = keys.has('ShiftLeft') || keys.has('ShiftRight');

  moveForward.set(-Math.sin(player.yaw),0,-Math.cos(player.yaw));
  moveRight.set(Math.cos(player.yaw),0,-Math.sin(player.yaw));
  desired.set(0,0,0)
    .addScaledVector(moveForward,forwardInput)
    .addScaledVector(moveRight,sideInput);
  const moving = desired.lengthSq() > 0.001;
  if (moving) desired.normalize();

  const pondD = Math.hypot(player.position.x - POND.x, player.position.z - POND.z);
  const groundY = terrainHeight(player.position.x,player.position.z);
  const depth = WATER_LEVEL - groundY;
  const insidePond = pondD < POND.radius - 0.2;
  player.swimming = insidePond && depth > 1.15;

  let speed = sprinting ? 8.0 : 4.5;
  if (player.swimming) speed = sprinting ? 4.0 : 2.65;

  const next = player.position.clone().addScaledVector(desired,speed*dt);
  next.x = THREE.MathUtils.clamp(next.x,-HALF_WORLD+1,HALF_WORLD-1);
  next.z = THREE.MathUtils.clamp(next.z,-HALF_WORLD+1,HALF_WORLD-1);
  if (!player.swimming) resolveTreeCollision(next);
  player.position.x = next.x;
  player.position.z = next.z;

  const currentGround = terrainHeight(player.position.x,player.position.z);
  const currentPondD = Math.hypot(player.position.x - POND.x, player.position.z - POND.z);
  const currentDepth = WATER_LEVEL - currentGround;
  const nowSwimming = currentPondD < POND.radius - 0.15 && currentDepth > 1.15;
  player.swimming = nowSwimming;

  if (player.swimming) {
    player.grounded = false;
    const dive = keys.has('ControlLeft') || keys.has('ControlRight') || keys.has('KeyC');
    const rise = keys.has('Space');
    const surfaceRoot = WATER_LEVEL - 0.34;
    const bottomRoot = currentGround + 0.35;

    if (rise) player.velocityY += 7.5 * dt;
    if (dive) player.velocityY -= 7.5 * dt;
    if (!rise && !dive) player.velocityY += (surfaceRoot - player.position.y) * 4.0 * dt;
    player.velocityY *= Math.pow(0.08,dt);
    player.position.y += player.velocityY * dt;
    player.position.y = THREE.MathUtils.clamp(player.position.y,bottomRoot,surfaceRoot);
  } else {
    player.velocityY -= 24 * dt;
    player.position.y += player.velocityY * dt;
    if (player.position.y <= currentGround) {
      player.position.y = currentGround;
      player.velocityY = 0;
      player.grounded = true;
    } else {
      player.grounded = false;
    }
  }

  const moveAmount = moving && (player.grounded || player.swimming) ? speed : 0;
  if (moveAmount > 0.05) player.bobTime += dt * (player.swimming ? 4.6 : sprinting ? 11.2 : 7.9);
  const bob = player.swimming
    ? Math.sin(player.bobTime) * 0.025
    : moveAmount > 0.05 ? Math.sin(player.bobTime) * (sprinting ? 0.045 : 0.027) : 0;
  const sway = moveAmount > 0.05 ? Math.cos(player.bobTime*0.5) * 0.014 : 0;

  const camHeight = player.swimming ? 0.46 : EYE_HEIGHT;
  camera.position.set(
    player.position.x + Math.cos(player.yaw)*sway,
    player.position.y + camHeight + bob,
    player.position.z - Math.sin(player.yaw)*sway,
  );
  camera.rotation.y = player.yaw;
  camera.rotation.x = player.pitch;

  player.submerged = player.swimming && camera.position.y < WATER_LEVEL - 0.08;
  underwaterOverlay.classList.toggle('active',player.submerged);

  if (player.submerged) {
    scene.fog.color.set(0x355b56);
    scene.fog.density = 0.07;
    renderer.toneMappingExposure = THREE.MathUtils.lerp(renderer.toneMappingExposure,0.78,0.08);
    statusEl.textContent = 'SWIMMING UNDERWATER // SPACE RISE · CTRL/C DIVE';
  } else {
    scene.fog.color.set(0x9eaa9a);
    scene.fog.density = 0.019;
    renderer.toneMappingExposure = THREE.MathUtils.lerp(renderer.toneMappingExposure,1.18,0.08);
    if (player.swimming) statusEl.textContent = 'SWIMMING // SPACE RISE · CTRL/C DIVE';
    else if (pointerLocked) statusEl.textContent = 'FOREST // HIGH DETAIL SLICE';
  }

  const targetFov = sprinting && moving ? (player.swimming ? 72 : 75) : 69;
  camera.fov = THREE.MathUtils.lerp(camera.fov,targetFov,1-Math.pow(0.0008,dt));
  camera.updateProjectionMatrix();

  waterBump.offset.x = elapsed * 0.012;
  waterBump.offset.y = elapsed * 0.007;
  water.position.y = WATER_LEVEL + Math.sin(elapsed*0.55)*0.012;
  motes.rotation.y = elapsed*0.012;
}

const clock = new THREE.Clock();
let frames = 0;
let fpsTimer = 0;

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(),0.045);
  const elapsed = clock.elapsedTime;
  updatePlayer(dt,elapsed);

  frames++;
  fpsTimer += dt;
  if (fpsTimer > 0.55) {
    fpsEl.textContent = `${Math.round(frames/fpsTimer)} FPS`;
    frames = 0;
    fpsTimer = 0;
  }

  composer.render();
}
animate();

function onResize() {
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.55));
  renderer.setSize(innerWidth,innerHeight);
  composer.setSize(innerWidth,innerHeight);
  ssao.setSize(innerWidth,innerHeight);
}
addEventListener('resize',onResize);
