import * as THREE from 'three';
import './style.css';

const app = document.querySelector('#app');
const startScreen = document.querySelector('#start-screen');
const startButton = document.querySelector('#start-button');
const fpsEl = document.querySelector('#fps');
const statusEl = document.querySelector('#status');

const WORLD_SIZE = 320;
const HALF_WORLD = WORLD_SIZE * 0.5;
const WATER_LEVEL = -2.4;
const LAKE = { x: 72, z: -18, radius: 38 };
const EYE_HEIGHT = 1.72;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xa9bdc0);
scene.fog = new THREE.FogExp2(0xb6c2ad, 0.0125);

const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.05, 550);
camera.rotation.order = 'YXZ';

const renderer = new THREE.WebGLRenderer({
  antialias: true,
  powerPreference: 'high-performance',
});
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.65));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
renderer.outputColorSpace = THREE.SRGBColorSpace;
app.appendChild(renderer.domElement);

// ---------- seeded randomness ----------
let seed = 133742;
function random() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
}
function rand(min, max) {
  return min + (max - min) * random();
}
function hash2(x, z) {
  const s = Math.sin(x * 127.1 + z * 311.7) * 43758.5453123;
  return s - Math.floor(s);
}
function smoothstep(a, b, x) {
  const t = THREE.MathUtils.clamp((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
}

// ---------- terrain ----------
function terrainHeight(x, z) {
  const broad =
    Math.sin(x * 0.022) * 2.7 +
    Math.cos(z * 0.025) * 2.25 +
    Math.sin((x + z) * 0.014) * 1.8;

  const medium =
    Math.sin(x * 0.073 + z * 0.018) * 0.9 +
    Math.cos(z * 0.081 - x * 0.023) * 0.7;

  const micro = (hash2(Math.floor(x * 0.35), Math.floor(z * 0.35)) - 0.5) * 0.28;
  let h = broad + medium + micro;

  // Carve a shallow lake basin.
  const d = Math.hypot(x - LAKE.x, z - LAKE.z);
  if (d < LAKE.radius + 9) {
    const basin = 1 - smoothstep(LAKE.radius - 5, LAKE.radius + 9, d);
    h = THREE.MathUtils.lerp(h, WATER_LEVEL - 1.8, basin * 0.94);
  }

  return h;
}

function makeGroundTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#37412b';
  ctx.fillRect(0, 0, 512, 512);

  for (let i = 0; i < 10000; i++) {
    const x = random() * 512;
    const y = random() * 512;
    const r = rand(0.5, 2.8);
    const shade = Math.floor(rand(34, 78));
    ctx.fillStyle = `rgba(${shade + 15},${shade + 11},${Math.max(18, shade - 12)},${rand(0.12, 0.42)})`;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let i = 0; i < 850; i++) {
    ctx.save();
    ctx.translate(random() * 512, random() * 512);
    ctx.rotate(random() * Math.PI);
    ctx.fillStyle = random() > 0.5 ? 'rgba(104,69,39,.42)' : 'rgba(76,83,43,.34)';
    ctx.fillRect(-rand(2, 7), -rand(0.5, 1.4), rand(4, 13), rand(1, 2.6));
    ctx.restore();
  }

  const texture = new THREE.CanvasTexture(c);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(28, 28);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  return texture;
}

const groundGeo = new THREE.PlaneGeometry(WORLD_SIZE, WORLD_SIZE, 180, 180);
groundGeo.rotateX(-Math.PI / 2);
const gp = groundGeo.attributes.position;
const groundColors = [];
const low = new THREE.Color(0x293522);
const high = new THREE.Color(0x596348);

for (let i = 0; i < gp.count; i++) {
  const x = gp.getX(i);
  const z = gp.getZ(i);
  const y = terrainHeight(x, z);
  gp.setY(i, y);

  const color = low.clone().lerp(high, THREE.MathUtils.clamp((y + 5) / 14, 0, 1));
  const noise = (hash2(i, i * 0.13) - 0.5) * 0.12;
  color.offsetHSL(0, 0, noise);
  groundColors.push(color.r, color.g, color.b);
}
groundGeo.setAttribute('color', new THREE.Float32BufferAttribute(groundColors, 3));
groundGeo.computeVertexNormals();

const ground = new THREE.Mesh(
  groundGeo,
  new THREE.MeshStandardMaterial({
    map: makeGroundTexture(),
    vertexColors: true,
    roughness: 1,
    metalness: 0,
  }),
);
ground.receiveShadow = true;
scene.add(ground);

// ---------- lake ----------
const waterGeo = new THREE.CircleGeometry(LAKE.radius, 96);
waterGeo.rotateX(-Math.PI / 2);
const water = new THREE.Mesh(
  waterGeo,
  new THREE.MeshPhysicalMaterial({
    color: 0x718b82,
    roughness: 0.18,
    metalness: 0.02,
    transmission: 0.18,
    transparent: true,
    opacity: 0.78,
    clearcoat: 0.7,
    clearcoatRoughness: 0.2,
  }),
);
water.position.set(LAKE.x, WATER_LEVEL, LAKE.z);
water.receiveShadow = true;
scene.add(water);

// ---------- lights ----------
const hemi = new THREE.HemisphereLight(0xdce7da, 0x24301e, 1.55);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xfff1c5, 4.0);
sun.position.set(-58, 95, 36);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -95;
sun.shadow.camera.right = 95;
sun.shadow.camera.top = 95;
sun.shadow.camera.bottom = -95;
sun.shadow.camera.near = 10;
sun.shadow.camera.far = 240;
sun.shadow.bias = -0.00012;
sun.shadow.normalBias = 0.028;
scene.add(sun);

const sunDisc = new THREE.Mesh(
  new THREE.SphereGeometry(4, 16, 8),
  new THREE.MeshBasicMaterial({ color: 0xfff4d3 }),
);
sunDisc.position.copy(sun.position).multiplyScalar(2.2);
scene.add(sunDisc);

// ---------- forest ----------
const treeColliders = [];
const TREE_COUNT = 560;
const trunkGeo = new THREE.CylinderGeometry(0.48, 0.72, 8.8, 8, 3);
const trunkMat = new THREE.MeshStandardMaterial({
  color: 0x4a3826,
  roughness: 0.97,
});
const trunks = new THREE.InstancedMesh(trunkGeo, trunkMat, TREE_COUNT);
trunks.castShadow = true;
trunks.receiveShadow = true;
trunks.instanceMatrix.setUsage(THREE.StaticDrawUsage);

const crownGeo = new THREE.IcosahedronGeometry(3.1, 1);
const crownMat = new THREE.MeshStandardMaterial({
  color: 0x38512e,
  roughness: 0.92,
});
const crowns = new THREE.InstancedMesh(crownGeo, crownMat, TREE_COUNT * 2);
crowns.castShadow = true;
crowns.receiveShadow = true;
crowns.instanceMatrix.setUsage(THREE.StaticDrawUsage);

const dummy = new THREE.Object3D();
const tempColor = new THREE.Color();

let treeIndex = 0;
let crownIndex = 0;
let attempts = 0;

while (treeIndex < TREE_COUNT && attempts < TREE_COUNT * 20) {
  attempts++;
  const x = rand(-HALF_WORLD + 7, HALF_WORLD - 7);
  const z = rand(-HALF_WORLD + 7, HALF_WORLD - 7);
  const lakeD = Math.hypot(x - LAKE.x, z - LAKE.z);
  const spawnD = Math.hypot(x, z - 14);

  if (lakeD < LAKE.radius + 5 || spawnD < 8) continue;

  const y = terrainHeight(x, z);
  const scale = rand(0.72, 1.48);
  const trunkHeight = 8.8 * scale;
  const radius = 0.55 * scale;

  dummy.position.set(x, y + trunkHeight * 0.5, z);
  dummy.rotation.set(rand(-0.035, 0.035), rand(0, Math.PI * 2), rand(-0.035, 0.035));
  dummy.scale.set(scale, scale, scale);
  dummy.updateMatrix();
  trunks.setMatrixAt(treeIndex, dummy.matrix);
  tempColor.setHSL(rand(0.07, 0.095), rand(0.26, 0.38), rand(0.19, 0.27));
  trunks.setColorAt(treeIndex, tempColor);

  const crownY = y + trunkHeight + rand(0.4, 1.3);
  const crownScale = rand(0.9, 1.35) * scale;

  dummy.position.set(x + rand(-0.45, 0.45), crownY, z + rand(-0.45, 0.45));
  dummy.rotation.set(rand(-0.2, 0.2), rand(0, Math.PI * 2), rand(-0.2, 0.2));
  dummy.scale.set(crownScale, crownScale * rand(0.8, 1.18), crownScale);
  dummy.updateMatrix();
  crowns.setMatrixAt(crownIndex, dummy.matrix);
  tempColor.setHSL(rand(0.23, 0.32), rand(0.36, 0.55), rand(0.20, 0.31));
  crowns.setColorAt(crownIndex++, tempColor);

  dummy.position.set(x + rand(-1.1, 1.1), crownY - rand(1.4, 2.5), z + rand(-1.1, 1.1));
  dummy.rotation.set(rand(-0.3, 0.3), rand(0, Math.PI * 2), rand(-0.3, 0.3));
  dummy.scale.set(crownScale * rand(0.65, 0.9), crownScale * rand(0.55, 0.8), crownScale * rand(0.65, 0.9));
  dummy.updateMatrix();
  crowns.setMatrixAt(crownIndex, dummy.matrix);
  tempColor.setHSL(rand(0.23, 0.33), rand(0.38, 0.58), rand(0.17, 0.27));
  crowns.setColorAt(crownIndex++, tempColor);

  treeColliders.push({ x, z, r: radius + 0.42 });
  treeIndex++;
}

trunks.instanceMatrix.needsUpdate = true;
crowns.instanceMatrix.needsUpdate = true;
if (trunks.instanceColor) trunks.instanceColor.needsUpdate = true;
if (crowns.instanceColor) crowns.instanceColor.needsUpdate = true;
scene.add(trunks, crowns);

// ---------- rocks ----------
const ROCK_COUNT = 150;
const rockGeo = new THREE.DodecahedronGeometry(1, 0);
const rockMat = new THREE.MeshStandardMaterial({ color: 0x687066, roughness: 1 });
const rocks = new THREE.InstancedMesh(rockGeo, rockMat, ROCK_COUNT);
rocks.castShadow = true;
rocks.receiveShadow = true;

for (let i = 0; i < ROCK_COUNT; i++) {
  let x;
  let z;
  do {
    x = rand(-HALF_WORLD + 4, HALF_WORLD - 4);
    z = rand(-HALF_WORLD + 4, HALF_WORLD - 4);
  } while (Math.hypot(x - LAKE.x, z - LAKE.z) < LAKE.radius + 2);

  const y = terrainHeight(x, z);
  const s = rand(0.25, 1.7);
  dummy.position.set(x, y + s * 0.35, z);
  dummy.rotation.set(rand(0, Math.PI), rand(0, Math.PI), rand(0, Math.PI));
  dummy.scale.set(s * rand(0.8, 1.5), s * rand(0.45, 0.9), s * rand(0.8, 1.45));
  dummy.updateMatrix();
  rocks.setMatrixAt(i, dummy.matrix);

  tempColor.setHSL(rand(0.19, 0.31), rand(0.04, 0.12), rand(0.30, 0.46));
  rocks.setColorAt(i, tempColor);
}
rocks.instanceMatrix.needsUpdate = true;
if (rocks.instanceColor) rocks.instanceColor.needsUpdate = true;
scene.add(rocks);

// ---------- grass ----------
const GRASS_COUNT = 5600;
const grassGeo = new THREE.PlaneGeometry(0.42, 1.4);
grassGeo.translate(0, 0.7, 0);
const grassMat = new THREE.MeshStandardMaterial({
  color: 0x58794a,
  roughness: 1,
  side: THREE.DoubleSide,
});
const grass = new THREE.InstancedMesh(grassGeo, grassMat, GRASS_COUNT);
grass.receiveShadow = true;

let gi = 0;
while (gi < GRASS_COUNT) {
  const x = rand(-HALF_WORLD + 3, HALF_WORLD - 3);
  const z = rand(-HALF_WORLD + 3, HALF_WORLD - 3);
  if (Math.hypot(x - LAKE.x, z - LAKE.z) < LAKE.radius + 2) continue;

  const y = terrainHeight(x, z);
  const s = rand(0.35, 1.1);
  dummy.position.set(x, y + 0.01, z);
  dummy.rotation.set(0, rand(0, Math.PI * 2), rand(-0.08, 0.08));
  dummy.scale.set(s * rand(0.65, 1.2), s, s);
  dummy.updateMatrix();
  grass.setMatrixAt(gi, dummy.matrix);

  tempColor.setHSL(rand(0.22, 0.34), rand(0.32, 0.54), rand(0.25, 0.42));
  grass.setColorAt(gi, tempColor);
  gi++;
}
grass.instanceMatrix.needsUpdate = true;
if (grass.instanceColor) grass.instanceColor.needsUpdate = true;
scene.add(grass);

// ---------- atmosphere / floating motes ----------
const moteCount = 900;
const motePositions = new Float32Array(moteCount * 3);
for (let i = 0; i < moteCount; i++) {
  motePositions[i * 3] = rand(-90, 90);
  motePositions[i * 3 + 1] = rand(0, 24);
  motePositions[i * 3 + 2] = rand(-90, 90);
}
const moteGeo = new THREE.BufferGeometry();
moteGeo.setAttribute('position', new THREE.BufferAttribute(motePositions, 3));
const motes = new THREE.Points(
  moteGeo,
  new THREE.PointsMaterial({
    color: 0xfff4cf,
    size: 0.055,
    transparent: true,
    opacity: 0.34,
    depthWrite: false,
  }),
);
scene.add(motes);

// ---------- player ----------
const player = {
  position: new THREE.Vector3(0, terrainHeight(0, 14), 14),
  velocityY: 0,
  grounded: true,
  yaw: 0,
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
  statusEl.textContent = pointerLocked ? 'FOREST // PLAYABLE BUILD' : 'CLICK TO RESUME';
});

document.addEventListener('mousemove', (e) => {
  if (!pointerLocked) return;
  const sensitivity = 0.0018;
  player.yaw -= e.movementX * sensitivity;
  player.pitch -= e.movementY * sensitivity;
  player.pitch = THREE.MathUtils.clamp(player.pitch, -1.48, 1.48);
});

addEventListener('keydown', (e) => {
  keys.add(e.code);
  if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) {
    e.preventDefault();
  }

  if (e.code === 'Space' && player.grounded && pointerLocked) {
    player.velocityY = 9.8;
    player.grounded = false;
  }
});

addEventListener('keyup', (e) => keys.delete(e.code));

function resolveTreeCollision(pos) {
  for (let i = 0; i < treeColliders.length; i++) {
    const t = treeColliders[i];
    const dx = pos.x - t.x;
    const dz = pos.z - t.z;
    const min = t.r + 0.34;
    const d2 = dx * dx + dz * dz;
    if (d2 < min * min && d2 > 0.000001) {
      const d = Math.sqrt(d2);
      const push = min - d;
      pos.x += (dx / d) * push;
      pos.z += (dz / d) * push;
    }
  }
}

const moveForward = new THREE.Vector3();
const moveRight = new THREE.Vector3();
const desired = new THREE.Vector3();

function updatePlayer(dt, time) {
  const sprinting = keys.has('ShiftLeft') || keys.has('ShiftRight');
  const forwardInput = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0);
  const sideInput = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0);

  moveForward.set(-Math.sin(player.yaw), 0, -Math.cos(player.yaw));
  moveRight.set(Math.cos(player.yaw), 0, -Math.sin(player.yaw));
  desired.set(0, 0, 0)
    .addScaledVector(moveForward, forwardInput)
    .addScaledVector(moveRight, sideInput);

  const moving = desired.lengthSq() > 0.0001;
  if (moving) desired.normalize();

  const speed = sprinting ? 10.2 : 5.4;
  const next = player.position.clone().addScaledVector(desired, speed * dt);
  next.x = THREE.MathUtils.clamp(next.x, -HALF_WORLD + 2, HALF_WORLD - 2);
  next.z = THREE.MathUtils.clamp(next.z, -HALF_WORLD + 2, HALF_WORLD - 2);
  resolveTreeCollision(next);

  player.position.x = next.x;
  player.position.z = next.z;

  const groundY = terrainHeight(player.position.x, player.position.z);
  player.velocityY -= 27 * dt;
  player.position.y += player.velocityY * dt;

  if (player.position.y <= groundY) {
    player.position.y = groundY;
    player.velocityY = 0;
    player.grounded = true;
  } else {
    player.grounded = false;
  }

  const flatSpeed = moving && player.grounded ? speed : 0;
  if (flatSpeed > 0.1) {
    player.bobTime += dt * (sprinting ? 12.2 : 8.5);
  }

  const bob = flatSpeed > 0.1 ? Math.sin(player.bobTime) * (sprinting ? 0.055 : 0.035) : 0;
  const sway = flatSpeed > 0.1 ? Math.cos(player.bobTime * 0.5) * 0.018 : 0;

  camera.position.set(
    player.position.x + Math.cos(player.yaw) * sway,
    player.position.y + EYE_HEIGHT + bob,
    player.position.z - Math.sin(player.yaw) * sway,
  );
  camera.rotation.y = player.yaw;
  camera.rotation.x = player.pitch;

  const targetFov = sprinting && moving ? 78 : 72;
  camera.fov = THREE.MathUtils.lerp(camera.fov, targetFov, 1 - Math.pow(0.001, dt));
  camera.updateProjectionMatrix();

  motes.position.x = player.position.x * 0.12;
  motes.position.z = player.position.z * 0.12;
  motes.rotation.y = time * 0.015;
}

// ---------- loop ----------
const clock = new THREE.Clock();
let frames = 0;
let fpsTimer = 0;
let lastFps = 60;

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  const elapsed = clock.elapsedTime;

  updatePlayer(dt, elapsed);

  // Slow water shimmer.
  water.material.opacity = 0.75 + Math.sin(elapsed * 0.7) * 0.025;

  frames++;
  fpsTimer += dt;
  if (fpsTimer >= 0.5) {
    lastFps = Math.round(frames / fpsTimer);
    fpsEl.textContent = `${lastFps} FPS`;
    frames = 0;
    fpsTimer = 0;
  }

  renderer.render(scene, camera);
}

function onResize() {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.65));
  renderer.setSize(innerWidth, innerHeight);
}
addEventListener('resize', onResize);

animate();
