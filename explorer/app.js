import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { gunzipSync, strFromU8 } from "fflate";
import { evolve } from "./model.js";
import { Timeline } from "./timeline.js";
import { ScientificCanvasRenderer } from "./canvas-renderer.js";

const $ = (id) => document.getElementById(id);
const payload = Uint8Array.from(atob($("payload").textContent.trim()), (c) =>
  c.charCodeAt(0),
);
const data = JSON.parse(strFromU8(gunzipSync(payload)));
$("payload").remove();
const colors = [
  "#52c7aa",
  "#dcb06a",
  "#c19be2",
  "#6cbddb",
  "#b7c67e",
  "#e49385",
  "#91abe3",
  "#d6c37a",
];
const names = data.nodes.map((n) => n.replace("_R", ""));
const state = {
  context: true,
  surfaces: true,
  section: false,
  phase: false,
  hardwareCase: 2,
  mode: "atlas",
  selected: null,
  region: null,
  body: "all",
  source: 0,
  lesion: -1,
  time: 0,
  lens: "quantum",
  difference: false,
  dark: true,
  playing: false,
  orbit: false,
};
let initializing = true;
const stage = $("stage"),
  scene = new THREE.Scene();
let renderer;
try {
  if (new URLSearchParams(location.search).get("renderer") === "canvas")
    throw new Error("Requested CPU renderer");
  renderer = new THREE.WebGLRenderer({
    antialias: true,
    preserveDrawingBuffer: true,
  });
} catch (e) {
  renderer = new ScientificCanvasRenderer();
}
stage.dataset.renderer = renderer.isFallback ? "canvas-3d" : "webgl";
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.localClippingEnabled = true;
stage.appendChild(renderer.domElement);
const camera = new THREE.OrthographicCamera(-400, 400, 260, -260, 1, 6000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.09;
controls.autoRotateSpeed = 0.4;
scene.add(new THREE.HemisphereLight(0xffffff, 0x697d7a, 2));
const light = new THREE.DirectionalLight(0xffffff, 2);
light.position.set(500, 500, 900);
scene.add(light);
const bounds = new THREE.Box3();
for (const r of data.anatomy.regions)
  for (let j = 0; j < r.vertices.length; j += 3)
    bounds.expandByPoint(new THREE.Vector3(...r.vertices.slice(j, j + 3)));
const center = bounds.getCenter(new THREE.Vector3());
const xyz = (p) =>
  new THREE.Vector3(p[0] - center.x, center.y - p[1], center.z - p[2]);
const anatomical = new THREE.Group(),
  schematic = new THREE.Group();
scene.add(anatomical, schematic);
const skeletons = [],
  surfaces = [];
const crop = bounds.clone().expandByScalar(35);
for (const n of data.anatomy.neurons) {
  const arr = [];
  for (let j = 0; j < n.edges.length; j += 2) {
    const a = n.edges[j] * 3,
      b = n.edges[j + 1] * 3;
    const p = new THREE.Vector3(...n.points.slice(a, a + 3)),
      q = new THREE.Vector3(...n.points.slice(b, b + 3));
    if (!crop.containsPoint(p) || !crop.containsPoint(q)) continue;
    arr.push(...xyz(p.toArray()).toArray(), ...xyz(q.toArray()).toArray());
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(arr, 3));
  geometry.computeBoundingSphere();
  const i = data.nodes.indexOf(n.group),
    anatomicalType = names.indexOf(n.type),
    color =
      i >= 0
        ? colors[i]
        : anatomicalType >= 0
          ? colors[anatomicalType]
          : colors[n.id % colors.length];
  const line = new THREE.LineSegments(
    geometry,
    new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: i >= 0 ? 0.86 : 0.75,
      depthWrite: false,
    }),
  );
  line.userData = n;
  anatomical.add(line);
  skeletons.push(line);
}
for (const r of data.anatomy.regions) {
  const p = [];
  for (let j = 0; j < r.vertices.length; j += 3)
    p.push(...xyz(r.vertices.slice(j, j + 3)).toArray());
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(p, 3));
  g.setIndex(r.faces);
  g.computeVertexNormals();
  const mesh = new THREE.Mesh(
    g,
    new THREE.MeshPhongMaterial({
      color: 0x91a69b,
      transparent: true,
      opacity: 0.025,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );
  anatomical.add(mesh);
  surfaces.push(mesh);
}
const waves = new THREE.Group(),
  results = new THREE.Group();
scene.add(waves, results);
const circle = names.map((_, i) => {
  const a = (i / 8) * Math.PI * 2 + Math.PI * 0.625;
  return new THREE.Vector3(
    Math.cos(a) * 150,
    Math.sin(a) * 150,
    Math.sin(a * 2) * 28,
  );
});
const graphNodes = [],
  edges = [],
  waveNodes = [],
  waveLines = [],
  bars = [],
  labels = [];
const material = (color, opacity = 1) =>
  new THREE.MeshStandardMaterial({
    color,
    roughness: 0.48,
    metalness: 0.08,
    transparent: opacity < 1,
    opacity,
  });
function sphere(parent, color, radius = 6) {
  const s = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 24, 16),
    material(color),
  );
  parent.add(s);
  return s;
}
function line(parent, color, opacity = 1, points = []) {
  const g = new THREE.BufferGeometry().setFromPoints(points);
  const l = new THREE.Line(
    g,
    new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity,
      depthWrite: false,
    }),
  );
  parent.add(l);
  return l;
}
for (let i = 0; i < 8; i++) {
  const node = sphere(schematic, colors[i], 9);
  node.position.copy(circle[i]);
  node.userData.node = i;
  graphNodes.push(node);
  const cursor = sphere(waves, colors[i], 4.5);
  cursor.userData.node = i;
  waveNodes.push(cursor);
  const baseline = (3.5 - i) * 68;
  const quantum = line(waves, colors[i], 0.95),
    future = line(waves, colors[i], 0.14),
    classical = line(waves, "#b5c4af", 0.35);
  const axis = line(waves, "#738a7e", 0.11, [
    new THREE.Vector3(-300, baseline, 0),
    new THREE.Vector3(300, baseline, 0),
  ]);
  waveLines.push({ quantum, future, classical, baseline, axis });
  const pair = [];
  for (let side = 0; side < 2; side++) {
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(1, 13, 13),
      material(side === 0 ? colors[i] : "#aabda8", side === 0 ? 0.9 : 0.45),
    );
    box.position.y = baseline;
    box.userData.node = i;
    results.add(box);
    pair.push(box);
  }
  bars.push(pair);
  const label = document.createElement("button");
  label.className = "scene-label";
  label.textContent = names[i];
  label.style.setProperty("--cell", colors[i]);
  label.setAttribute("aria-label", `Select ${names[i]}`);
  label.onclick = () => select(i);
  $("labels").appendChild(label);
  labels.push(label);
  const b = document.createElement("button");
  b.style.setProperty("--cell", colors[i]);
  b.className = "population";
  b.setAttribute("aria-label", `Select ${names[i]} population`);
  b.innerHTML = `<i></i><span>${names[i]}</span>`;
  b.onclick = () => select(i);
  $("population-dock").appendChild(b);
  $("source").add(new Option(names[i], String(i)));
}
const maxWeight = Math.max(...data.weights.flat());
for (let i = 0; i < 8; i++)
  for (let j = i + 1; j < 8; j++) {
    const strength = data.weights[i][j] / maxWeight;
    if (!strength) continue;
    const middle = circle[i].clone().add(circle[j]).multiplyScalar(0.23);
    middle.z -= 20;
    const curve = new THREE.QuadraticBezierCurve3(circle[i], middle, circle[j]);
    const tube = new THREE.Mesh(
      new THREE.TubeGeometry(
        curve,
        40,
        0.35 + 2 * Math.sqrt(strength),
        6,
        false,
      ),
      material("#789f8b", 0.18 + 0.5 * Math.sqrt(strength)),
    );
    tube.userData = { i, j, strength };
    schematic.add(tube);
    edges.push(tube);
  }
let dirty = true,
  transition = null,
  lastNow = 0,
  curveKey = "",
  initialHash = location.hash;
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const request = () => {
  dirty = true;
};
const waveScale = Array(8).fill(1);
const getModel = () =>
  evolve(data.models[String(state.lesion)].spectral, state.source, state.time);
const timeline = new Timeline($("time"), (value) => {
  state.time = value;
  state.playing = false;
  updateEvolution();
  updateUI();
  writeHash();
});
function wavePoint(i, t, model) {
  const a = Math.sqrt(Math.max(0, model.quantum[i]) / waveScale[i]);
  return new THREE.Vector3(
    -300 + t * 75,
    waveLines[i].baseline +
      (state.phase
        ? Math.cos(model.phase[i]) * a * 34
        : (model.quantum[i] / waveScale[i]) * 52),
    state.phase ? Math.sin(model.phase[i]) * a * 34 : 0,
  );
}
function rebuildWaves() {
  const key = `${state.source}/${state.lesion}/${state.phase}`;
  if (key === curveKey) return;
  curveKey = key;
  const samples = Array.from({ length: 401 }, (_, k) =>
    evolve(data.models[String(state.lesion)].spectral, state.source, k / 50),
  );
  for (let i = 0; i < 8; i++)
    waveScale[i] = Math.max(
      1e-12,
      ...samples.map((m) => Math.max(m.quantum[i], m.classical[i])),
    );
  const q = Array.from({ length: 8 }, () => []),
    c = Array.from({ length: 8 }, () => []);
  for (let k = 0; k <= 400; k++) {
    const t = k / 50,
      m = samples[k];
    for (let i = 0; i < 8; i++) {
      q[i].push(wavePoint(i, t, m));
      c[i].push(
        new THREE.Vector3(
          -300 + t * 75,
          waveLines[i].baseline + (m.classical[i] / waveScale[i]) * 52,
          0,
        ),
      );
    }
  }
  waveLines.forEach((row, i) => {
    for (const object of [row.quantum, row.future]) {
      object.geometry.dispose();
      object.geometry = new THREE.BufferGeometry().setFromPoints(q[i]);
    }
    row.classical.geometry.dispose();
    row.classical.geometry = new THREE.BufferGeometry().setFromPoints(c[i]);
    row.classical.visible = !state.phase;
  });
}
function updateEvolution() {
  if (state.mode !== "interference") return;
  rebuildWaves();
  const m = getModel();
  waveLines.forEach((row, i) => {
    const attribute = row.quantum.geometry.attributes.position,
      original = row.future.geometry.attributes.position;
    if (row.endpoint !== undefined)
      attribute.setXYZ(
        row.endpoint,
        original.getX(row.endpoint),
        original.getY(row.endpoint),
        original.getZ(row.endpoint),
      );
    const endpoint = Math.min(400, Math.floor(state.time * 50) + 1),
      point = wavePoint(i, state.time, m);
    attribute.setXYZ(endpoint, point.x, point.y, point.z);
    attribute.needsUpdate = true;
    row.endpoint = endpoint;
    row.quantum.geometry.setDrawRange(0, endpoint + 1);
    waveNodes[i].position.copy(point);
    waveNodes[i].scale.setScalar(0.7 + Math.sqrt(m.quantum[i]) * 1.3);
    row.quantum.material.opacity =
      state.selected === null || state.selected === i ? 1 : 0.15;
    row.future.material.opacity =
      state.selected === null || state.selected === i ? 0.2 : 0.055;
    row.classical.material.opacity =
      state.selected === null || state.selected === i ? 0.45 : 0.1;
  });
  if (state.selected !== null) {
    $("selected-probability").textContent =
      `${(m.quantum[state.selected] * 100).toFixed(1)}% / ${(m.classical[state.selected] * 100).toFixed(1)}%`;
  }
  timeline.set(state.time);
  $("play").innerHTML = `<span>${state.playing ? "Ⅱ" : "▶"}</span>`;
  $("play").setAttribute(
    "aria-label",
    state.playing ? "Pause evolution" : "Play evolution",
  );
  stage.dataset.modelTime = state.time.toFixed(4);
  stage.dataset.modelTv = (
    m.quantum.reduce((a, v, i) => a + Math.abs(v - m.classical[i]), 0) / 2
  ).toFixed(8);
  request();
}
function updateAnatomy() {
  skeletons.forEach((s) => {
    const i = data.nodes.indexOf(s.userData.group),
      hit = state.selected === i,
      body = state.body === "all" || String(s.userData.id) === state.body;
    s.visible = (i >= 0 || state.context) && body;
    s.material.opacity = state.region
      ? 0.075
      : state.selected === null
        ? i >= 0
          ? 0.94
          : 0.8
        : hit
          ? 0.98
          : 0.04;
  });
  surfaces.forEach((s, i) => {
    const hit = data.anatomy.regions[i].name === state.region;
    s.visible = state.surfaces || hit;
    s.material.opacity = hit ? 0.17 : 0.021;
    s.material.color.set(hit ? "#7fb9a2" : "#91a69b");
  });
  const planes = [];
  if (state.section) {
    const z =
      bounds.min.z +
      (bounds.max.z - bounds.min.z) * (+$("section-depth").value / 100);
    planes.push(new THREE.Plane(new THREE.Vector3(0, 0, 1), z - center.z));
  }
  for (const s of [...skeletons, ...surfaces])
    s.material.clippingPlanes = planes;
  request();
}
function updateGraph() {
  graphNodes.forEach((s, i) => {
    s.scale.setScalar(state.selected === i ? 1.3 : 1);
    s.material.color.set(colors[i]);
  });
  edges.forEach((e) => {
    const focus =
      state.selected === null ||
      e.userData.i === state.selected ||
      e.userData.j === state.selected;
    e.material.opacity = focus
      ? 0.2 + 0.65 * Math.sqrt(e.userData.strength)
      : 0.035;
  });
  request();
}
const cases = [
  ["Initial state", "The starting point, before the walk."],
  ["Short walk", "The intact graph at model time 4."],
  ["Long walk", "The intact graph at model time 8."],
  ["Pm2a disconnected", "The graph at time 8 with Pm2a links removed."],
];
cases.forEach(([name, hint], i) => {
  const b = document.createElement("button");
  b.textContent = name;
  b.dataset.hint = hint;
  b.setAttribute("aria-label", name);
  b.onclick = () => {
    state.hardwareCase = i;
    updateUI();
    writeHash();
  };
  $("compare-controls").appendChild(b);
});
function updateResults() {
  const c = data.hardware.cases[state.hardwareCase];
  bars.forEach((pair, i) => {
    pair.forEach((b, side) => {
      const p = side === 0 ? c.observed[i] : c.expected[i],
        length = p * 250;
      b.visible = p > 1e-12;
      b.scale.x = length;
      b.position.x = (side === 0 ? -1 : 1) * (length / 2 + 4);
      b.material.opacity =
        state.selected === null || state.selected === i
          ? side === 0
            ? 0.95
            : 0.55
          : 0.12;
    });
  });
  stage.dataset.resultTv = c.total_variation_from_ideal.toFixed(8);
  request();
}
const modes = ["atlas", "circuit", "interference", "hardware"];
function select(i) {
  state.selected = i;
  state.region = null;
  state.body = "all";
  updateUI();
  writeHash();
}
function mode(m) {
  if (!modes.includes(m)) return;
  state.mode = m;
  if (m !== "atlas") {
    state.region = null;
    state.body = "all";
  }
  state.playing = false;
  curveKey = "";
  $("selection").classList.remove("expanded");
  updateUI();
  fit(false);
  writeHash();
}
function updateUI() {
  const atlas = state.mode === "atlas",
    circuit = state.mode === "circuit",
    walk = state.mode === "interference",
    compare = state.mode === "hardware";
  document.body.dataset.mode = state.mode;
  anatomical.visible = atlas;
  schematic.visible = circuit;
  waves.visible = walk;
  results.visible = compare;
  $("atlas-controls").hidden = !atlas;
  $("walk-controls").hidden = !walk;
  $("compare-controls").hidden = !compare;
  $("scale").hidden = !atlas;
  $("labels").hidden = atlas;
  $("population-dock").hidden = !atlas && !circuit;
  stage.setAttribute(
    "aria-label",
    atlas
      ? "Interactive three-dimensional fly anatomy"
      : circuit
        ? "Weighted population connections"
        : walk
          ? "Continuous quantum and classical evolution traces"
          : "Paired measured and reference probability bars",
  );
  document.querySelectorAll("button[data-mode]").forEach((b) => {
    const yes = b.dataset.mode === state.mode;
    b.setAttribute("aria-pressed", yes);
    b.classList.toggle("selected", yes);
  });
  [...$("population-dock").children].forEach((b, i) => {
    b.classList.toggle("selected", i === state.selected);
    b.setAttribute("aria-pressed", i === state.selected);
  });
  const n = state.selected,
    body = data.anatomy.neurons.find((n) => String(n.id) === state.body);
  $("selection").hidden = n === null && !state.region && !body;
  $("selection-name").textContent =
    state.region || body?.type || (n !== null ? names[n] : "");
  $("body-select").hidden = !atlas || !!state.region || n === null;
  $("focus").hidden = !atlas;
  $("disconnect").hidden = !walk || n === null || state.lesion === n;
  $("restore").hidden = !walk || state.lesion < 0;
  $("selected-probability").hidden = !(walk || compare) || n === null;
  if (compare && n !== null) {
    const c = data.hardware.cases[state.hardwareCase];
    $("selected-probability").textContent =
      `${(c.observed[n] * 100).toFixed(1)}% / ${(c.expected[n] * 100).toFixed(1)}%`;
  }
  $("neighbors").hidden = !circuit || n === null;
  $("neighbors").replaceChildren();
  if (circuit && n !== null) {
    data.weights[n]
      .map((w, i) => ({ w, i }))
      .filter((x) => x.i !== n && x.w > 0)
      .sort((a, b) => b.w - a.w)
      .slice(0, 3)
      .forEach((x) => {
        const b = document.createElement("button");
        b.textContent = names[x.i];
        b.style.setProperty("--strength", x.w / maxWeight);
        b.onclick = () => select(x.i);
        $("neighbors").appendChild(b);
      });
  }
  if (atlas && n !== null) {
    $("body-select").replaceChildren(new Option("All branches", "all"));
    data.anatomy.neurons
      .filter((x) => x.group === data.nodes[n])
      .forEach((x) =>
        $("body-select").add(new Option(String(x.id), String(x.id))),
      );
    $("body-select").value = state.body;
  }
  $("source").value = state.source;
  $("phase").setAttribute("aria-pressed", state.phase);
  $("context").setAttribute("aria-pressed", state.context);
  $("regions").setAttribute("aria-pressed", state.surfaces);
  $("section").setAttribute("aria-pressed", state.section);
  $("section-control").hidden = !state.section;
  [...$("compare-controls").children].forEach((b, i) =>
    b.classList.toggle("selected", i === state.hardwareCase),
  );
  $("key-primary").textContent = atlas
    ? ""
    : circuit
      ? ""
      : walk
        ? state.phase
          ? "Amplitude"
          : "Quantum"
        : "Measured";
  $("key-secondary").textContent = walk
    ? state.phase
      ? ""
      : "Classical"
    : compare
      ? "Reference"
      : "";
  $("key-detail").textContent = atlas
    ? "Published neuron branches. Select a cell or region to focus."
    : circuit
      ? "Thicker links mean more contacts. Select a population to follow its strongest connections."
      : walk
        ? state.phase
          ? "Radius is amplitude magnitude; angle is relative phase. Drag to reveal the three-dimensional trace."
          : "Colored: quantum probability. Pale: classical diffusion. Each row has its own scale. Bright paths have elapsed; dim paths lie ahead."
        : "Left: measured frequencies. Right: ideal probabilities. Choose a saved experiment below.";
  document.body.classList.toggle("light", !state.dark);
  scene.background = new THREE.Color(state.dark ? "#101e1d" : "#f5f6f0");
  updateAnatomy();
  updateGraph();
  updateResults();
  updateEvolution();
  request();
}
function fit(selection = false, immediate = false) {
  const w = stage.clientWidth,
    h = stage.clientHeight,
    safeWidth = w - (w < 760 ? 40 : 160),
    spanBase =
      state.mode === "atlas" ? 600 : state.mode === "circuit" ? 480 : 700;
  let span = Math.max(
      spanBase,
      ((state.mode === "atlas" ? 800 : state.mode === "circuit" ? 370 : 650) *
        h) /
        safeWidth,
    ),
    target = new THREE.Vector3();
  if (selection && state.mode === "atlas") {
    const box = new THREE.Box3();
    if (state.region)
      box.expandByObject(
        surfaces[
          data.anatomy.regions.findIndex((r) => r.name === state.region)
        ],
      );
    else
      skeletons
        .filter((s) => s.visible && s.material.opacity > 0.2)
        .forEach((s) => box.expandByObject(s));
    if (!box.isEmpty()) {
      target = box.getCenter(new THREE.Vector3());
      const d = box.getSize(new THREE.Vector3());
      span = Math.max(d.y, d.z, (d.x * h) / safeWidth) * 1.25;
    }
  }
  const endPos = target.clone().add(new THREE.Vector3(0, 0, 1500)),
    endZoom = 850 / span;
  camera.up.set(0, 1, 0);
  if (immediate || reduced || camera.position.length() < 1) {
    camera.position.copy(endPos);
    camera.zoom = endZoom;
    controls.target.copy(target);
    camera.lookAt(target);
    camera.updateProjectionMatrix();
    controls.update();
    transition = null;
  } else
    transition = {
      start: performance.now(),
      position: camera.position.clone(),
      target: controls.target.clone(),
      zoom: camera.zoom,
      endPos,
      endTarget: target,
      endZoom,
    };
  request();
}
let viewportW = 0,
  viewportH = 0;
function resize() {
  const w = stage.clientWidth,
    h = stage.clientHeight,
    changed = viewportW > 0 && (w !== viewportW || h !== viewportH);
  viewportW = w;
  viewportH = h;
  renderer.setSize(w, h);
  camera.left = (-425 * w) / h;
  camera.right = (425 * w) / h;
  camera.top = 425;
  camera.bottom = -425;
  camera.updateProjectionMatrix();
  if (changed) fit(!!state.region || state.body !== "all", true);
  request();
}
new ResizeObserver(resize).observe(stage);
controls.addEventListener("change", request);
controls.addEventListener("start", () => {
  transition = null;
});
const raycaster = new THREE.Raycaster();
raycaster.params.Line.threshold = 2;
let pointerDown;
renderer.domElement.addEventListener("pointerdown", (e) => {
  pointerDown = [e.clientX, e.clientY];
});
renderer.domElement.addEventListener("pointerup", (e) => {
  if (
    !pointerDown ||
    Math.hypot(e.clientX - pointerDown[0], e.clientY - pointerDown[1]) > 5
  )
    return;
  const r = stage.getBoundingClientRect();
  raycaster.setFromCamera(
    new THREE.Vector2(
      ((e.clientX - r.left) / r.width) * 2 - 1,
      1 - ((e.clientY - r.top) / r.height) * 2,
    ),
    camera,
  );
  const objects =
    state.mode === "atlas"
      ? skeletons.filter((s) => s.visible && s.material.opacity > 0.15)
      : state.mode === "circuit"
        ? graphNodes
        : state.mode === "interference"
          ? waveNodes
          : bars.flat();
  const hit = raycaster.intersectObjects(objects)[0];
  if (!hit) return;
  const n = hit.object.userData;
  if (state.mode === "atlas") {
    const i = data.nodes.indexOf(n.group);
    select(i >= 0 ? i : null);
    state.body = String(n.id);
    updateUI();
    writeHash();
  } else select(n.node);
});
function writeHash() {
  if (initializing) return;
  const p = new URLSearchParams();
  if (state.mode === "atlas") {
    if (state.region) p.set("region", state.region);
    else if (state.body !== "all") p.set("body", state.body);
    else if (state.selected !== null)
      p.set("population", names[state.selected]);
  } else if (state.mode === "hardware") p.set("case", state.hardwareCase);
  else if (state.mode === "interference") {
    if (state.source) p.set("source", names[state.source]);
    if (state.time) p.set("t", state.time.toFixed(3));
    if (state.lesion >= 0) p.set("disconnect", names[state.lesion]);
    if (state.phase) p.set("phase", "1");
  }
  const hash = `#${state.mode}${p.size ? "?" + p : ""}`;
  if (location.hash !== hash) history.replaceState(null, "", hash);
}
function readHash(hash = location.hash) {
  const [m, raw] = hash.slice(1).split("?");
  if (!modes.includes(m)) return;
  state.mode = m;
  const p = new URLSearchParams(raw);
  if (m === "atlas") {
    const body = data.anatomy.neurons.find(
      (n) => String(n.id) === p.get("body"),
    );
    state.body = body ? String(body.id) : "all";
    state.selected = body
      ? data.nodes.includes(body.group)
        ? data.nodes.indexOf(body.group)
        : null
      : names.includes(p.get("population"))
        ? names.indexOf(p.get("population"))
        : null;
    state.region = data.anatomy.regions.some((r) => r.name === p.get("region"))
      ? p.get("region")
      : null;
  }
  if (m === "interference") {
    state.source = Math.max(0, names.indexOf(p.get("source")));
    state.time = Math.max(0, Math.min(8, Number(p.get("t")) || 0));
    state.lesion = names.indexOf(p.get("disconnect"));
    state.phase = p.get("phase") === "1";
  }
  if (m === "hardware")
    state.hardwareCase = Math.max(
      0,
      Math.min(3, Math.floor(Number(p.get("case")) || 0)),
    );
  state.playing = false;
  curveKey = "";
  updateUI();
  fit(!!state.region || state.body !== "all", initializing);
}
window.addEventListener("hashchange", () => readHash());
document
  .querySelectorAll("button[data-mode]")
  .forEach((b) => (b.onclick = () => mode(b.dataset.mode)));
$("play").onclick = () => {
  state.playing = !state.playing;
  if (state.playing && state.time >= 8) state.time = 0;
  lastNow = performance.now();
  updateEvolution();
  writeHash();
};
$("phase").onclick = () => {
  state.phase = !state.phase;
  curveKey = "";
  updateUI();
  writeHash();
};
$("source-toggle").onclick = () => {
  $("source").hidden = !$("source").hidden;
  if (!$("source").hidden) $("source").focus();
};
$("source").onchange = () => {
  state.source = +$("source").value;
  curveKey = "";
  updateUI();
  writeHash();
};
$("disconnect").onclick = () => {
  state.lesion = state.selected;
  curveKey = "";
  updateUI();
  writeHash();
};
$("restore").onclick = () => {
  state.lesion = -1;
  curveKey = "";
  updateUI();
  writeHash();
};
$("clear-selection").onclick = () => {
  select(null);
  fit(false);
};
$("body-select").onchange = () => {
  state.body = $("body-select").value;
  updateUI();
  writeHash();
};
$("focus").onclick = () => fit(true);
$("context").onclick = () => {
  state.context = !state.context;
  updateUI();
};
$("regions").onclick = () => {
  state.surfaces = !state.surfaces;
  updateUI();
};
$("section").onclick = () => {
  state.section = !state.section;
  updateUI();
};
$("section-depth").oninput = updateAnatomy;
$("rotate").onclick = () => {
  state.orbit = !state.orbit;
  controls.autoRotate = state.orbit;
  $("rotate").setAttribute("aria-pressed", state.orbit);
  request();
};
$("reset").onclick = () => fit();
$("theme").onclick = () => {
  state.dark = !state.dark;
  updateUI();
};
$("save").onclick = () => {
  renderer.render(scene, camera);
  const a = document.createElement("a");
  a.download = `fly-${state.mode}.png`;
  a.href = renderer.domElement.toDataURL();
  a.click();
};
$("immersive").onclick = () => {
  const on = document.body.classList.toggle("immersed");
  $("immersive").setAttribute("aria-pressed", on);
  $("immersive").setAttribute(
    "aria-label",
    on ? "Show interface" : "Hide interface",
  );
};
$("methods-open").onclick = () => $("methods").showModal();
$("methods-close").onclick = () => $("methods").close();
$("methods").onclick = (e) => {
  if (e.target === $("methods")) $("methods").close();
};
function toggleSearch() {
  const show = $("search-panel").hidden;
  $("search-panel").hidden = !show;
  if (show) $("search").focus();
}
$("search-toggle").onclick = toggleSearch;
$("search").oninput = () => {
  const query = $("search").value.trim().toLowerCase(),
    box = $("search-results");
  box.replaceChildren();
  if (!query) return;
  const add = (text, action) => {
    const b = document.createElement("button");
    b.textContent = text;
    b.onclick = () => {
      action();
      $("search-panel").hidden = true;
      $("search").value = "";
      fit(true);
    };
    box.appendChild(b);
  };
  data.anatomy.regions
    .filter((r) => r.name.toLowerCase().includes(query))
    .slice(0, 4)
    .forEach((r) =>
      add(r.name, () => {
        select(null);
        state.region = r.name;
        mode("atlas");
      }),
    );
  data.anatomy.neurons
    .filter((n) =>
      `${n.type} ${n.id} ${n.instance}`.toLowerCase().includes(query),
    )
    .slice(0, 8)
    .forEach((n) =>
      add(`${n.type} · ${n.side} / ${n.id}`, () => {
        select(
          data.nodes.includes(n.group) ? data.nodes.indexOf(n.group) : null,
        );
        state.body = String(n.id);
        mode("atlas");
      }),
    );
  if (!box.children.length) box.textContent = "No matches";
};
document.addEventListener("keydown", (e) => {
  if ($("methods").open) return;
  if (e.key === "Escape") {
    $("search-panel").hidden = true;
    if (document.body.classList.contains("immersed")) $("immersive").click();
  }
  if (["INPUT", "SELECT"].includes(e.target.tagName)) return;
  if (e.key === "/") {
    e.preventDefault();
    toggleSearch();
  }
  if (
    e.code === "Space" &&
    state.mode === "interference" &&
    e.target.id !== "time"
  ) {
    e.preventDefault();
    $("play").click();
  }
  if (["1", "2", "3", "4"].includes(e.key)) mode(modes[+e.key - 1]);
});
function animate(now) {
  requestAnimationFrame(animate);
  const dt = lastNow ? Math.min(0.06, (now - lastNow) / 1000) : 0;
  lastNow = now;
  if (transition) {
    const t = transition,
      u = Math.min(1, (now - t.start) / 1000),
      e = u * u * (3 - 2 * u);
    camera.position.lerpVectors(t.position, t.endPos, e);
    controls.target.lerpVectors(t.target, t.endTarget, e);
    camera.zoom = t.zoom + (t.endZoom - t.zoom) * e;
    camera.updateProjectionMatrix();
    dirty = true;
    if (u === 1) transition = null;
  }
  controls.update();
  if (state.playing && state.mode === "interference") {
    state.time = Math.min(8, state.time + dt * 0.7);
    if (state.time === 8) state.playing = false;
    updateEvolution();
    if (!state.playing) writeHash();
  }
  if (!dirty && !state.orbit) return;
  dirty = false;
  if (state.mode !== "atlas") {
    for (let i = 0; i < 8; i++) {
      const p =
        state.mode === "circuit"
          ? circle[i]
          : state.mode === "interference"
            ? new THREE.Vector3(-325, waveLines[i].baseline, 0)
            : new THREE.Vector3(0, waveLines[i].baseline + 19, 0);
      const v = p.clone().project(camera);
      labels[i].style.left = `${((v.x + 1) / 2) * stage.clientWidth}px`;
      labels[i].style.top =
        `${((1 - v.y) / 2) * stage.clientHeight + (state.mode === "circuit" ? 22 : 0)}px`;
      labels[i].classList.toggle("selected", state.selected === i);
    }
  }
  $("scale").style.width =
    `${(100 * camera.zoom * stage.clientHeight) / 850}px`;
  const before = performance.now();
  renderer.render(scene, camera);
  stage.dataset.renderMs = (performance.now() - before).toFixed(2);
}
resize();
updateUI();
fit(false, true);
readHash(initialHash);
initializing = false;
writeHash();
$("loading").remove();
requestAnimationFrame(animate);
