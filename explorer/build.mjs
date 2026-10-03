import { readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { gzipSync } from "node:zlib";
const root = new URL(".", import.meta.url);
const read = (p) => readFile(new URL(p, root), "utf8");
const [template, style, data] = await Promise.all(
  ["template.html", "styles.css", "data.json"].map(read),
);
const result = await Bun.build({
  entrypoints: [new URL("app.js", root).pathname],
  minify: true,
  target: "browser",
  format: "iife",
});
if (!result.success) throw new Error(result.logs.join("\n"));
const packed = gzipSync(data, { level: 9 });
const script = (await result.outputs[0].text()).replaceAll(
  "</script",
  "<\\/script",
);
const licenses = await read("THIRD_PARTY_LICENSES.txt");
const html = template
  .replace(
    "</head>",
    () => `<!-- ${licenses.replaceAll("--", "—")} -->\n</head>`,
  )
  .replace("__STYLE__", () => style)
  .replace("__PAYLOAD__", () => packed.toString("base64"))
  .replace("__SCRIPT__", () => script);
await writeFile(new URL("index.html", root), html);
const hash = (s) => createHash("sha256").update(s).digest("hex");
const manifest = {
  version: 1,
  format: "self-contained HTML with gzip JSON",
  runtime: "Bun " + Bun.version,
  html_sha256: hash(html),
  html_bytes: Buffer.byteLength(html),
  data_sha256: hash(data),
  data_bytes: Buffer.byteLength(data),
  packed_bytes: packed.length,
  sources: {},
};
for (const path of [
  "app.js",
  "canvas-renderer.js",
  "model.js",
  "timeline.js",
  "model.test.js",
  "build.mjs",
  "template.html",
  "styles.css",
  "bun.lock",
  "package.json",
  "serve.mjs",
  "THIRD_PARTY_LICENSES.txt",
  "../flybrain/explorer.py",
  "../flybrain/morphology.py",
  "../datasets/fly/morphology/manifest.json",
])
  manifest.sources[path] = hash(await read(path));
await writeFile(
  new URL("manifest.json", root),
  JSON.stringify(manifest, null, 2) + "\n",
);
console.log(
  `Built offline explorer: ${(manifest.html_bytes / 1e6).toFixed(2)} MB; packed data ${(packed.length / 1e6).toFixed(2)} MB.`,
);
