import * as THREE from "three";
import { managedVector } from "./quantum.js";
import { LensFallback } from "./lens-fallback.js";

export function bloch(theta, phi, damping = 0, dephasing = 0) {
  const transverse = Math.sqrt(1 - damping) * (1 - dephasing);
  return [
    transverse * Math.sin(theta) * Math.cos(phi),
    (1 - damping) * Math.cos(theta) + damping,
    transverse * Math.sin(theta) * Math.sin(phi),
  ];
}

export class QuantumLens {
  constructor() {
    this.host = document.querySelector("#sphere");
    this.theta = Math.PI / 2;
    this.phi = 0;
    this.target = this.theta;
    this.damping = 0;
    this.dephasing = 0;
    this.reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.animate = this.animate.bind(this);
    try {
      this.setup();
    } catch (error) {
      this.fallback = new LensFallback(this.host);
      console.warn("Quantum lens WebGL unavailable");
    }
    if (this.renderer)
      this.host.insertAdjacentHTML(
        "beforeend",
        '<span class="sphere-pole north">|0⟩</span><span class="sphere-pole south">|1⟩</span>',
      );
    let start;
    if (this.renderer)
      this.host.addEventListener("pointerdown", (event) => {
        start = event.clientX;
        this.host.setPointerCapture(event.pointerId);
      });
    this.host.addEventListener("pointermove", (event) => {
      if (start !== undefined) {
        this.group.rotation.y += (event.clientX - start) * 0.01;
        start = event.clientX;
        this.schedule();
      }
    });
    this.host.addEventListener("pointerup", () => (start = undefined));
    this.host.addEventListener("pointercancel", () => (start = undefined));
    new ResizeObserver(() => this.resize()).observe(this.host);
    this.resize();
    document.addEventListener("visibilitychange", () => this.schedule());
    matchMedia("(prefers-reduced-motion: reduce)").addEventListener(
      "change",
      (event) => {
        this.reduced = event.matches;
        this.schedule();
      },
    );
    this.schedule();
  }
  setup() {
    this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.host.append(this.renderer.domElement);
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 20);
    this.camera.position.set(0, 0.2, 4.4);
    this.group = new THREE.Group();
    this.group.rotation.set(0.1, -0.55, 0);
    this.scene.add(this.group);
    const gridMaterial = new THREE.LineBasicMaterial({
      color: 0x56746a,
      transparent: true,
      opacity: 0.55,
    });
    for (let index = 0; index < 6; index++) {
      const points = [];
      for (let n = 0; n <= 100; n++) {
        const angle = (n / 100) * Math.PI * 2;
        points.push(new THREE.Vector3(Math.cos(angle), Math.sin(angle), 0));
      }
      const ring = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(points),
        gridMaterial,
      );
      ring.rotation.y = (index * Math.PI) / 6;
      this.group.add(ring);
    }
    for (const y of [-0.5, 0, 0.5]) {
      const points = [],
        radius = Math.sqrt(1 - y * y);
      for (let n = 0; n <= 100; n++) {
        const angle = (n / 100) * Math.PI * 2;
        points.push(
          new THREE.Vector3(
            radius * Math.cos(angle),
            y,
            radius * Math.sin(angle),
          ),
        );
      }
      this.group.add(
        new THREE.Line(
          new THREE.BufferGeometry().setFromPoints(points),
          gridMaterial,
        ),
      );
    }
    const material = new THREE.MeshBasicMaterial({
      color: 0x9ad3b7,
      transparent: true,
      opacity: 0.045,
    });
    this.group.add(
      new THREE.Mesh(new THREE.SphereGeometry(1, 32, 24), material),
    );
    this.arrow = new THREE.ArrowHelper(
      new THREE.Vector3(1, 0, 0),
      new THREE.Vector3(),
      1,
      0xf0b37f,
      0.13,
      0.075,
    );
    this.group.add(this.arrow);
    this.tip = new THREE.Mesh(
      new THREE.SphereGeometry(0.035, 16, 12),
      new THREE.MeshBasicMaterial({ color: 0xffd19f }),
    );
    this.group.add(this.tip);
    this.trail = new THREE.Line(
      new THREE.BufferGeometry().setAttribute(
        "position",
        new THREE.BufferAttribute(new Float32Array(41 * 3), 3),
      ),
      new THREE.LineBasicMaterial({
        color: 0xf0b37f,
        transparent: true,
        opacity: 0.3,
      }),
    );
    this.group.add(this.trail);
  }
  resize() {
    if (!this.renderer) return;
    const { width, height } = this.host.getBoundingClientRect();
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.schedule();
  }
  setNoise(parameters) {
    Object.assign(this, parameters);
    this.schedule();
  }
  schedule() {
    if (!this.animate || this.pending || document.hidden) return;
    this.pending = true;
    requestAnimationFrame(() => {
      this.pending = false;
      this.animate();
    });
  }
  update(fire) {
    this.target = fire
      ? Math.PI * (0.15 + 0.7 * Math.tanh(fire.size / 2))
      : Math.PI / 2;
    this.phi = fire ? fire.x * Math.PI * 2 : 0;
    document.querySelector("#angle-readout").textContent =
      `θ ${Math.round((this.target / Math.PI) * 180)}°`;
    this.schedule();
  }
  animate() {
    this.theta = this.reduced
      ? this.target
      : this.theta + (this.target - this.theta) * 0.055;
    const input = [
      Math.sin(this.theta) * Math.cos(this.phi),
      Math.sin(this.theta) * Math.sin(this.phi),
      Math.cos(this.theta),
    ];
    const vector = managedVector(input, {
      idle: this.management ? 0.7 : 0,
      gate: this.management ? 0.3 : 0,
      dd: this.dd,
      twirl: this.twirl,
      damping: this.damping,
      dephasing: this.dephasing,
    });
    if (this.fallback) {
      this.fallback.render(vector);
      if (Math.abs(this.target - this.theta) > 0.0001) this.schedule();
      return;
    }
    const point = new THREE.Vector3(vector[0], vector[2], vector[1]);
    const length = point.length();
    this.arrow.setDirection(
      length > 1e-6 ? point.clone().normalize() : new THREE.Vector3(0, 1, 0),
    );
    this.arrow.setLength(
      Math.max(length, 0.001),
      Math.min(0.13, length * 0.25),
      0.075,
    );
    this.tip.position.copy(point);
    const positions = this.trail.geometry.attributes.position;
    for (let n = 0; n <= 40; n++) {
      const point = bloch((n / 40) * this.theta, this.phi);
      positions.setXYZ(n, ...point);
    }
    positions.needsUpdate = true;
    this.renderer.render(this.scene, this.camera);
    if (Math.abs(this.target - this.theta) > 0.0001) this.schedule();
  }
}
