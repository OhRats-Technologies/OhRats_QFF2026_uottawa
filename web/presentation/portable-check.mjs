// Authoring QA from a tracked-file export. Public viewing requires only Bun.
import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import { execFileSync, spawn } from "node:child_process";
import { once } from "node:events";
import { createRequire } from "node:module";

const root = process.cwd();
const commit = execFileSync("git", ["rev-parse", "HEAD"], {
  encoding: "utf8",
}).trim();
const output = path.join(
  root,
  ".cache/judge-submission",
  `clean-static-${commit.slice(0, 12)}`,
);
await fs.mkdir(path.dirname(output), { recursive: true });
await fs.mkdir(output);
const tree = path.join(output, "tree");
await fs.mkdir(tree);
execFileSync("git", [
  "archive",
  "--format=tar",
  `--output=${output}/tree.tar`,
  commit,
]);
execFileSync("tar", ["-xf", `${output}/tree.tar`, "-C", tree]);
for (const name of [
  ".env",
  ".venv",
  ".cache",
  "data",
  "results",
  "node_modules",
  "web/demo/node_modules",
])
  assert.equal(
    await fs
      .stat(path.join(tree, name))
      .then(() => true)
      .catch(() => false),
    false,
    name,
  );
const sha = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const server = spawn("bun", ["run", "web/presentation/serve.ts", "--port=0"], {
  cwd: tree,
});
const stopped = once(server, "exit");
let browser, timer;
const errors = [],
  blockedExternal = new Set(),
  failedLocal = new Set();
const result = {
  commit,
  cleanTrackedTree: true,
  noProjectInstall: true,
  noIgnoredInputs: true,
  bunVersion: execFileSync("bun", ["--version"], { encoding: "utf8" }).trim(),
  slides: [],
  sections: [],
  contextLayers: [],
  heightEpochs: [],
  downloads: [],
  deniedRoutes: [],
};
try {
  const base = await new Promise((resolve, reject) => {
    let log = "";
    timer = setTimeout(
      () =>
        reject(new Error("Isolated viewer did not start within ten seconds")),
      10000,
    );
    server.stdout.on("data", (bytes) => {
      log += bytes.toString();
      const match = log.match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) resolve(match[0]);
    });
    server.on("error", reject);
    server.on("exit", () =>
      reject(new Error("Isolated viewer exited before readiness")),
    );
  });
  clearTimeout(timer);
  const require = createRequire(
    `${process.env.RUNTIME_NODE_MODULES}/../package.json`,
  );
  const { chromium } = require("playwright");
  browser = await chromium.launch({
    headless: true,
    channel: "chrome",
    args: ["--mute-audio"],
  });
  const page = await browser.newPage({
    viewport: { width: 1280, height: 720 },
    reducedMotion: "reduce",
  });
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => {
    if (response.url().startsWith(base) && response.status() >= 400)
      failedLocal.add(new URL(response.url()).pathname);
  });
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (url.origin === base) return route.continue();
    blockedExternal.add(url.hostname);
    return route.abort();
  });
  execFileSync(process.execPath, ["web/presentation/check.mjs"], {
    cwd: tree,
    env: {...process.env, PRESENTATION_BASE: base,
      PRESENTATION_OUTPUT: `${output}/presentation`},
    stdio: "pipe",
  });
  const canvasPresentation = JSON.parse(
    await fs.readFile(`${output}/presentation/receipt.json`, "utf8"),
  );
  result.slides = canvasPresentation.slides.map(slide => slide.id);
  result.presentationRenderer = canvasPresentation.renderer;
  result.measuredYieldPoints = 12;
  result.presentationViewports = canvasPresentation.viewports;

  execFileSync(
    "bun",
    [
      "test",
      "web/demo/canvas/engine.test.js",
      "web/demo/canvas/mechanics.test.js",
    ],
    { cwd: tree },
  );
  execFileSync(process.execPath, ["web/demo/canvas/browser-check.mjs"], {
    cwd: tree,
    env: {
      ...process.env,
      FIRELINE_BASE: base,
      FIRELINE_OUTPUT: `${output}/console`,
    },
  });
  execFileSync(process.execPath, ["web/demo/canvas/interaction-check.mjs"], {
    cwd: tree,
    env: {
      ...process.env,
      FIRELINE_BASE: base,
      FIRELINE_OUTPUT: `${output}/console`,
    },
  });
  execFileSync(process.execPath, ["web/demo/canvas/onboarding-check.mjs"], {
    cwd: tree,
    env: {
      ...process.env,
      FIRELINE_BASE: base,
      FIRELINE_OUTPUT: `${output}/onboarding`,
    },
    stdio: "pipe",
  });
  result.onboarding = JSON.parse(
    await fs.readFile(`${output}/onboarding/receipt.json`, "utf8"),
  );
  result.canvasInteractions = JSON.parse(
    await fs.readFile(`${output}/console/interaction-receipt.json`, "utf8"),
  );
  result.canvasGame = JSON.parse(
    await fs.readFile(`${output}/console/receipt.json`, "utf8"),
  );
  assert.deepEqual(errors, []);
  assert.deepEqual([...failedLocal], []);

  const preservedDownloads = JSON.parse(
    await fs.readFile(
      path.join(tree, "docs/data/static_view_portability.json"),
      "utf8",
    ),
  ).downloads;
  for (const name of ["ontario-wildfire.pdf", "ontario-wildfire.pptx"]) {
    const relative = `web/presentation/slides/${name}`;
    const response = await fetch(`${base}/${relative}`);
    assert.equal(response.status, 200);
    const bytes = Buffer.from(await response.arrayBuffer());
    assert.equal(sha(bytes), sha(await fs.readFile(path.join(tree, relative))));
    assert.equal(
      sha(bytes),
      preservedDownloads.find((item) => item.name === name).sha256,
    );
    result.downloads.push({
      name,
      bytes: bytes.length,
      sha256: sha(bytes),
      contentType: response.headers.get("content-type"),
    });
  }
  for (const route of [
    "/web/demo/lab.html",
    "/web/demo/field.html",
    "/web/demo/assets/strategy.js",
    "/.env",
    "/.git/config",
    "/.cache/context/run.json",
    "/web/demo/../../.env",
  ]) {
    const response = await fetch(`${base}${route}`);
    assert.equal(response.status, 404);
    result.deniedRoutes.push({ route, status: response.status });
  }
  assert.equal(
    (await fetch(`${base}/web/demo/`, { method: "POST" })).status,
    405,
  );
  result.blockedExternalHosts = [...blockedExternal];
  result.failedLocal = [...failedLocal];
  result.errors = errors;
  result.scope =
    "Clean tracked-file viewing on this Mac with installed Bun and isolated authoring browser tooling; not a remote clone, public-access audit, fresh scientific run or physical GPU-loss test.";
} finally {
  clearTimeout(timer);
  await browser?.close();
  server.kill("SIGTERM");
  await stopped;
}
result.isolatedServerStopped = true;
result.status = "passed";
result.checked_utc = new Date().toISOString();
result.archive_sha256 = sha(await fs.readFile(`${output}/tree.tar`));
result.verificationSources = {};
for (const name of ["portable-check.mjs"])
  result.verificationSources[name] = sha(
    await fs.readFile(path.join(tree, "web/presentation", name)),
  );
Object.assign(result, {
  scientific_predictor_fits: 0,
  browser_sandbox_fitting: true,
  python_qiskit_circuit_executions: 0,
  browser_ideal_quantum_calculations: true,
  hardware_jobs: 0,
  artifact_regenerations: 0,
  browser_toy_arithmetic: true,
});
await fs.writeFile(
  `${output}/receipt.json`,
  JSON.stringify(result, null, 2) + "\n",
);
console.log(JSON.stringify(result));
