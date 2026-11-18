// Taj Elite — procedural implant → abutment → crown scene.
// Loaded lazily when the "from root to crown" section approaches the viewport.
// Scroll sets a target; a critically-damped spring moves the model toward it,
// so every scroll tick turns into continuous, weighted motion (never a jump).
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const smoother = (t) => t * t * t * (t * (t * 6 - 15) + 10);   // smootherstep: zero velocity at both ends

/* ---------- geometry ---------- */

const coreR = (y) => 0.2 + 0.15 * Math.sqrt(clamp((y + 2) / 1.8));

function buildFixture(mat) {
  const g = new THREE.Group();
  const pts = [new THREE.Vector2(0, -2.02)];
  for (let i = 0; i <= 40; i++) {
    const y = -2 + (i / 40) * 1.78;
    pts.push(new THREE.Vector2(coreR(y), y));
  }
  pts.push(new THREE.Vector2(0.39, -0.16), new THREE.Vector2(0.4, -0.02),
           new THREE.Vector2(0.37, 0), new THREE.Vector2(0.16, 0), new THREE.Vector2(0, -0.04));
  g.add(new THREE.Mesh(new THREE.LatheGeometry(pts, 72), mat));

  class Helix extends THREE.Curve {
    getPoint(t, target = new THREE.Vector3()) {
      const y = -1.8 + t * 1.5;
      const a = t * Math.PI * 2 * 9;
      const r = coreR(y) + 0.015;
      return target.set(Math.cos(a) * r, y, Math.sin(a) * r);
    }
  }
  g.add(new THREE.Mesh(new THREE.TubeGeometry(new Helix(), 720, 0.06, 6, false), mat));
  return g;
}

function buildAbutment(mat) {
  const p = [
    [0, 0], [0.3, 0], [0.36, 0.08], [0.41, 0.17], [0.36, 0.24],
    [0.29, 0.5], [0.26, 0.86], [0.2, 0.98], [0, 1.0],
  ].map(([x, y]) => new THREE.Vector2(x, y));
  return new THREE.Mesh(new THREE.LatheGeometry(p, 64), mat);
}

function buildCrown(mat) {
  let geo = new THREE.SphereGeometry(1, 120, 80);
  geo.deleteAttribute('uv');
  geo.deleteAttribute('normal');
  geo = mergeVertices(geo);
  const pos = geo.attributes.position;
  const v = new THREE.Vector3();
  const cusps = [[0.4, 0.36], [-0.4, 0.36], [0.4, -0.36], [-0.4, -0.36]];
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i);
    let { x, y, z } = v;
    const sq = 1 + 0.07 * Math.cos(4 * Math.atan2(z, x));
    x *= sq; z *= sq;
    if (y > 0) {
      y *= 0.56;
      const w = clamp((v.y - 0.35) / 0.65);
      let bump = 0;
      for (const [cx, cz] of cusps) bump += Math.exp(-((x - cx) ** 2 + (z - cz) ** 2) / 0.07);
      bump = 0.17 * bump - 0.16 * Math.exp(-(x * x + z * z) / 0.05) - 0.05 * Math.exp(-(x * x) / 0.008);
      y += bump * w;
    } else {
      const s = 1 - 0.42 * Math.pow(-y, 1.6);
      x *= s; z *= s; y *= 0.95;
    }
    pos.setXYZ(i, x * 0.82, y * 0.88, z * 0.76);
  }
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, mat);
}

/* ---------- scene ---------- */

export function mount(canvas, { reduced = false, accent = '#C8A87A' } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.02;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();

  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 50);
  camera.position.set(0, 0.25, 8.6);

  const key = new THREE.DirectionalLight(0xfff1dc, 1.5); key.position.set(-3, 4, 5);
  const rim = new THREE.DirectionalLight(new THREE.Color(accent), 2.2); rim.position.set(4, 1.5, -4);
  const fill = new THREE.DirectionalLight(0xffffff, 0.35); fill.position.set(3, -2, 3);
  scene.add(key, rim, fill);

  const titanium = new THREE.MeshPhysicalMaterial({ color: 0xb9bdc2, metalness: 1, roughness: 0.32 });
  const gold = new THREE.MeshPhysicalMaterial({ color: 0xcfae78, metalness: 1, roughness: 0.28, transparent: true });
  const porcelain = new THREE.MeshPhysicalMaterial({
    color: 0xf3efe6, roughness: 0.3, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.14,
    sheen: 0.5, sheenColor: new THREE.Color(0xffffff), transparent: true,
  });

  // tilt (pointer) → spin (scroll) → model (idle rotation)
  const tilt = new THREE.Group();
  const spin = new THREE.Group();
  const model = new THREE.Group();
  const fixture = buildFixture(titanium);
  const abut = buildAbutment(gold);
  const crown = buildCrown(porcelain);
  model.add(fixture, abut, crown);
  spin.add(model);
  tilt.add(spin);
  tilt.rotation.set(0.14, 0, -0.06);
  model.rotation.y = 0.6;
  scene.add(tilt);

  const s = { target: 0, p: 0, v: 0, visible: true, px: 0, py: 0, raf: 0, last: 0 };

  function layout(p) {
    const a = smoother(clamp((p - 0.1) / 0.42));    // abutment glides in (overlaps with crown start)
    const c = smoother(clamp((p - 0.46) / 0.46));   // crown descends and settles
    abut.position.y = (1 - a) * 2.6;
    abut.scale.setScalar(0.9 + 0.1 * a);
    gold.opacity = clamp(a * 1.5);
    abut.visible = gold.opacity > 0.005;

    crown.position.y = 0.95 + (1 - c) * 3.0;
    crown.rotation.y = (1 - c) * 1.4;               // unscrews into place as it lands
    crown.scale.setScalar(0.9 + 0.1 * c);
    porcelain.opacity = clamp(c * 1.5);
    crown.visible = porcelain.opacity > 0.005;

    model.position.y = 0.95 - 0.95 * (0.35 * a + 0.65 * c);
    spin.rotation.y = p * Math.PI * 1.1;            // scroll turns the model, so motion is felt even between stages
  }

  function resize() {
    const { clientWidth: w, clientHeight: h } = canvas;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.position.z = w / h < 0.7 ? 10.4 : 8.6;
    camera.updateProjectionMatrix();
    renderer.render(scene, camera);
  }

  function tick(now) {
    s.raf = 0;
    const dt = Math.min(1 / 30, (now - (s.last || now)) / 1000);
    s.last = now;
    // critically damped spring toward the scroll target
    const k = 70, damp = 2 * Math.sqrt(k);
    s.v += (k * (s.target - s.p) - damp * s.v) * dt;
    s.p += s.v * dt;
    layout(s.p);
    if (!reduced) {
      model.rotation.y += dt * 0.22;
      const f = Math.min(1, dt * 3);
      tilt.rotation.x += ((0.14 + s.py * 0.12) - tilt.rotation.x) * f;
      tilt.rotation.z += ((-0.06 - s.px * 0.08) - tilt.rotation.z) * f;
    }
    renderer.render(scene, camera);
    const settling = Math.abs(s.target - s.p) > 0.0005 || Math.abs(s.v) > 0.0005;
    if (s.visible && (!reduced || settling)) loop();
  }
  function loop() { if (!s.raf) s.raf = requestAnimationFrame(tick); }

  new ResizeObserver(resize).observe(canvas);
  new IntersectionObserver(([e]) => {
    s.visible = e.isIntersecting;
    if (s.visible) { s.last = 0; loop(); }
  }).observe(canvas);

  if (!reduced) {
    addEventListener('pointermove', (e) => {
      s.px = e.clientX / innerWidth - 0.5;
      s.py = e.clientY / innerHeight - 0.5;
    }, { passive: true });
  }

  resize();
  layout(0);
  loop();

  return {
    setProgress(p) { s.target = clamp(p); loop(); },
    setAccent(hex) { rim.color.set(hex.trim()); loop(); },
  };
}
