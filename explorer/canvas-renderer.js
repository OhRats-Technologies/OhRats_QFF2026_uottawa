// CPU 3D projection fallback. Published geometry is retained; subpixel branches
// are omitted from rasterization only. The camera and picking remain Three.js.
import * as THREE from "three";
export class ScientificCanvasRenderer {
  constructor() {
    this.domElement = document.createElement("canvas");
    this.ctx = this.domElement.getContext("2d");
    this.ratio = 1;
    this.info = { render: { calls: 0 } };
    this.isFallback = true;
  }
  setPixelRatio(r) {
    this.ratio = Math.min(r, 1.25);
  }
  setSize(w, h) {
    this.width = w;
    this.height = h;
    this.domElement.width = Math.round(w * this.ratio);
    this.domElement.height = Math.round(h * this.ratio);
    this.domElement.style.width = w + "px";
    this.domElement.style.height = h + "px";
  }
  render(scene, camera) {
    const ctx = this.ctx,
      w = this.width,
      h = this.height;
    if (!w || !h) return;
    scene.updateMatrixWorld();
    camera.updateMatrixWorld();
    const projection = new THREE.Matrix4().multiplyMatrices(
      camera.projectionMatrix,
      camera.matrixWorldInverse,
    );
    ctx.setTransform(this.ratio, 0, 0, this.ratio, 0, 0);
    ctx.globalAlpha = 1;
    ctx.fillStyle = "#" + scene.background.getHexString();
    ctx.fillRect(0, 0, w, h);
    ctx.lineCap = "round";
    const dark = scene.background.r < 0.3;
    const draw = [];
    scene.traverseVisible((o) => {
      if ((o.isLine || o.isMesh) && o.geometry) draw.push(o);
    });
    draw.sort((a, b) => (a.material.opacity || 1) - (b.material.opacity || 1));
    for (const o of draw) {
      const mat = o.material,
        attribute = o.geometry.attributes.position;
      if (!attribute || mat.opacity < 0.03) continue;
      const ar = attribute.array,
        m = new THREE.Matrix4().multiplyMatrices(
          projection,
          o.matrixWorld,
        ).elements;
      const screen = (i) => {
        const x = ar[i],
          y = ar[i + 1],
          z = ar[i + 2],
          den = m[3] * x + m[7] * y + m[11] * z + m[15];
        return [
          (((m[0] * x + m[4] * y + m[8] * z + m[12]) / den) * w) / 2 + w / 2,
          h / 2 - (((m[1] * x + m[5] * y + m[9] * z + m[13]) / den) * h) / 2,
        ];
      };
      const clipped = (i) =>
        mat.clippingPlanes?.some(
          (p) =>
            p.normal.x * ar[i] +
              p.normal.y * ar[i + 1] +
              p.normal.z * ar[i + 2] +
              p.constant <
            0,
        );
      ctx.strokeStyle = "#" + mat.color.getHexString();
      ctx.fillStyle = ctx.strokeStyle;
      ctx.globalAlpha = mat.opacity ?? 1;
      if (o.isLine) {
        ctx.lineWidth = o.isLineSegments ? (dark ? 0.8 : 0.7) : 1.2;
        ctx.beginPath();
        const step = o.isLineSegments ? 6 : 3;
        for (
          let i = o.geometry.drawRange.start * 3;
          i <
          Math.min(
            ar.length - 3,
            (o.geometry.drawRange.start + o.geometry.drawRange.count) * 3 - 3,
          );
          i += step
        ) {
          if (clipped(i) || clipped(i + 3)) continue;
          const a = screen(i),
            b = screen(i + 3);
          if (Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) < 0.45) continue;
          ctx.moveTo(...a);
          ctx.lineTo(...b);
        }
        ctx.stroke();
      } else if (o.geometry.type === "TubeGeometry") {
        const points = o.geometry.parameters.path.getPoints(40);
        const world = new THREE.Vector3();
        ctx.lineWidth = Math.max(
          0.7,
          (o.geometry.parameters.radius * 2 * camera.zoom * h) / 850,
        );
        ctx.globalAlpha = mat.opacity;
        ctx.beginPath();
        points.forEach((p, i) => {
          world.copy(p).applyMatrix4(o.matrixWorld).project(camera);
          const x = ((world.x + 1) * w) / 2,
            y = ((1 - world.y) * h) / 2;
          i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
        });
        ctx.stroke();
      } else if (o.geometry.type === "BoxGeometry") {
        const indices = o.geometry.index.array;
        ctx.globalAlpha = mat.opacity;
        for (let i = 0; i < indices.length; i += 3) {
          const a = screen(indices[i] * 3),
            b = screen(indices[i + 1] * 3),
            c = screen(indices[i + 2] * 3);
          ctx.beginPath();
          ctx.moveTo(...a);
          ctx.lineTo(...b);
          ctx.lineTo(...c);
          ctx.closePath();
          ctx.fill();
        }
      } else if (o.geometry.type === "SphereGeometry") {
        const pos = o.getWorldPosition(new THREE.Vector3()).project(camera),
          x = ((pos.x + 1) * w) / 2,
          y = ((1 - pos.y) * h) / 2,
          r =
            (o.geometry.parameters.radius * o.scale.x * camera.zoom * h) / 850;
        ctx.globalAlpha = 0.18;
        const glow = ctx.createRadialGradient(x, y, 0, x, y, r * 4);
        glow.addColorStop(0, ctx.fillStyle);
        glow.addColorStop(1, "transparent");
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(x, y, r * 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.fillStyle = "#" + mat.color.getHexString();
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = dark ? "#dbe9e2" : "#233632";
        ctx.globalAlpha = 0.5;
        ctx.lineWidth = 0.6;
        ctx.stroke();
      } else {
        const indices = o.geometry.index?.array;
        if (!indices) continue;
        const ring = o.geometry.type === "RingGeometry";
        ctx.lineWidth = ring ? 1 : 0.45;
        ctx.globalAlpha = ring ? mat.opacity : dark ? 0.06 : 0.07;
        ctx.beginPath();
        const stride = ring ? 3 : 36;
        for (let i = 0; i < indices.length; i += stride) {
          const a = indices[i] * 3,
            b = indices[i + 1] * 3,
            c = indices[i + 2] * 3;
          if (clipped(a) || clipped(b) || clipped(c)) continue;
          const p = screen(a),
            q = screen(b),
            r = screen(c);
          ctx.moveTo(...p);
          ctx.lineTo(...q);
          if (!ring) {
            ctx.lineTo(...r);
            ctx.closePath();
          }
        }
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
  }
}
