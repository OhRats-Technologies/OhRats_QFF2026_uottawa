// Authoring-only browser QA. All gameplay uses actual visible controls.
import fs from "node:fs/promises";
import { checkPersistence } from "./persistence-check.mjs";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import {
  createRun,
  action,
  advance,
  active,
  available,
  forecast,
} from "./rules.js";
import { upgradeChoices, applyUpgrade } from "./upgrades.js";

const require = createRequire(
  `${process.env.RUNTIME_NODE_MODULES}/../package.json`,
);
const { chromium } = require("playwright");
const source = JSON.parse(
  await fs.readFile("web/demo/assets/context/scenario.json", "utf8"),
);
const output = ".cache/judge-submission/strategy-browser";
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const page = await browser.newPage({
  viewport: { width: 1440, height: 960 },
  deviceScaleFactor: 1,
});
const errors = [],
  requests = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("request", (request) =>
  requests.push({ url: request.url(), method: request.method() }),
);
const results = [];
let navigation = 0;

async function begin(seed) {
  await page.goto(
    `http://127.0.0.1:8790/web/demo/?qa=${navigation++}#season=${seed}`,
    {
      waitUntil: "domcontentloaded",
    },
  );
  await page.locator("#start").click();
  const theme = await page.evaluate(() => ({
    background: getComputedStyle(document.body).backgroundColor,
    layout: getComputedStyle(document.querySelector("#game")).display,
  }));
  assert.equal(theme.background, "rgb(10, 23, 27)");
  assert.equal(theme.layout, page.viewportSize().width < 760 ? "flex" : "grid");
}
async function chooseUpgrade(state) {
  const order = ["training", "logistics", "network", "precision"];
  const choice = upgradeChoices(state).sort(
    (a, b) => order.indexOf(a.id) - order.indexOf(b.id),
  )[0];
  await page.locator(`[data-upgrade=${choice.id}]`).click();
  applyUpgrade(state, choice.id);
}
async function respond(state, fire, kind) {
  await page.locator(`[data-incident="${fire.id}"]`).click();
  const button = page.locator(`[data-action=${kind}]`);
  if (await button.isDisabled()) return false;
  await button.click();
  assert.equal(action(state, fire.id, kind), true);
  assert.equal(
    await page.locator("#supplies").textContent(),
    String(state.supplies),
  );
  return true;
}
async function play(seed, policy) {
  await begin(seed);
  const state = createRun(seed, source.pool);
  while (state.status === "playing") {
    if (state.upgradePending) await chooseUpgrade(state);
    if (policy === "triage") {
      const fires = active(state).sort((a, b) => b.size - a.size);
      for (const fire of fires)
        if (!fire.crew && available(state) > 0)
          await respond(state, fire, "crew");
      for (const fire of fires) {
        if (forecast(state, fire) > 1.1 && state.supplies >= 4)
          await respond(state, fire, "water");
      }
    }
    await page.locator("#advance").click();
    assert.equal(advance(state), true);
    assert.equal(
      await page.locator("#integrity").textContent(),
      String(Math.round(state.integrity)),
    );
    assert.equal(
      await page.locator("#crews").textContent(),
      `${available(state)}/${state.crewTotal}`,
    );
  }
  assert.equal(
    await page.locator("#debrief-title").textContent(),
    state.status === "won" ? "The season held." : "The line broke.",
  );
  const endpoint = page.locator("#debrief-chart [data-season-end]");
  assert.equal(
    await endpoint.getAttribute("data-season-end"),
    String(state.turn),
  );
  assert.equal(
    Number(await endpoint.getAttribute("cx")),
    34 + (state.turn / 12) * 448,
  );
  assert.match(
    await page.locator("#debrief-chart svg").getAttribute("aria-label"),
    /Loss limit: 40/,
  );
  await page.screenshot({ path: `${output}/${policy}-${seed}.png` });
  results.push({
    seed,
    policy,
    status: state.status,
    integrity: state.integrity,
    turns: state.turn,
    contained: state.contained,
  });
  return state;
}

const loss = await play(7, "idle");
assert.equal(loss.status, "lost");
await page.locator("#retry").click();
assert.equal(await page.locator("#supplies").textContent(), "18");
assert.equal(await page.locator(".fire").count(), 3);
const win = await play(2, "triage");
assert.equal(win.status, "won");
await page.locator("#new-season").click();
assert.match(page.url(), /#season=3/);
await page.locator("#sound").click();
assert.equal(await page.locator("#sound").getAttribute("aria-pressed"), "true");
await page.locator("#sound").click();

// Real map layers remain aligned; every advertised image and legend loads.
for (const layer of ["cover", "canopy", "lorey", "recovery", "water", "fuel"]) {
  await page.locator("#layer").selectOption(layer);
  await page.locator("#map-image").evaluate((image) => image.decode());
  assert.equal(
    await page.locator("#map-image").evaluate((image) => image.naturalWidth),
    1118,
  );
  await page.locator("#legend-toggle").click();
  if (layer !== "cover")
    await page.locator("#map-legend img").evaluate((image) => image.decode());
  await page.locator("#legend-toggle").click();
}
await page.locator("#layer").selectOption("height");
const beforeEpoch = await page.locator("#supplies").textContent();
for (const year of [1985, 1990, 1995, 2000, 2005, 2010, 2015]) {
  await page.locator(`[data-epoch="${year}"]`).click();
  await page.locator("#map-image").evaluate((image) => image.decode());
  assert.equal(
    await page.locator("#map-image").evaluate((image) => image.naturalWidth),
    1118,
  );
  assert.match(
    await page.locator("#layer-caption").textContent(),
    new RegExp(String(year)),
  );
  assert.equal(
    await page.locator(`[data-epoch="${year}"]`).getAttribute("aria-pressed"),
    "true",
  );
  assert.equal(await page.locator("#supplies").textContent(), beforeEpoch);
}
await page.locator("#legend-toggle").click();
await page.locator("#map-legend img").evaluate((image) => image.decode());
await page.screenshot({ path: `${output}/height-context.png` });
await page.locator("#legend-toggle").click();
await page.locator("#layer").selectOption("cover");
assert.equal(await page.locator("#cities").isVisible(), false); // Baked source labels avoid duplicates.
await page.screenshot({ path: `${output}/desktop.png` });

// Each accepted steer has a working, bounded instrument control.
for (const technique of [
  "dd",
  "twirl",
  "postselect",
  "readout",
  "psd",
  "lowrank",
]) {
  await begin(7);
  await page.locator("#lab-open").click();
  const before = await page.locator("#lab-metrics").textContent();
  await page.locator(`[data-technique=${technique}]`).click();
  assert.match(await page.locator("#lab-open").textContent(), /0 credits/);
  assert.equal(
    await page.locator(`[data-technique=${technique}]`).isDisabled(),
    true,
  );
  const after = await page.locator("#lab-metrics").textContent();
  if (["postselect", "readout", "psd", "lowrank"].includes(technique))
    assert.notEqual(after, before);
  if (technique === "postselect") assert.match(after, /invalid 0/);
  if (["dd", "twirl"].includes(technique))
    assert.equal(await page.locator("#coherent-noise").isChecked(), true);
  await page.screenshot({ path: `${output}/instrument-${technique}.png` });
}
await begin(7);
await page.locator("#lens-toggle").click();
await page.locator("#damping").press("End");
assert.equal(
  await page.locator("#damping").getAttribute("aria-valuenow"),
  "1.00",
);
await page.locator("#dephasing").press("Home");
for (let n = 0; n < 5; n++) await page.locator("#dephasing").press("PageUp");
assert.equal(
  await page.locator("#dephasing").getAttribute("aria-valuenow"),
  "0.50",
);
const slider = await page.locator("#damping .slider-rail").boundingBox();
await page.mouse.move(slider.x, slider.y);
await page.mouse.down();
await page.mouse.move(slider.x + slider.width * 0.35, slider.y, { steps: 4 });
await page.mouse.up();
assert.equal(
  await page.locator("#damping").getAttribute("aria-valuenow"),
  "0.35",
);
const sliderFront = await page.locator("#front-number").textContent();
await page.locator("#damping").press("Space");
assert.equal(await page.locator("#front-number").textContent(), sliderFront);
await page.locator("#sample").click();
assert.ok(Number(await page.locator("#sample-count").textContent()) > 1);
await page.locator("#guide-open").click();
assert.equal(
  await page.locator("#guide").evaluate((dialog) => dialog.open),
  true,
);
await page.keyboard.press("Escape");
assert.equal(
  await page.locator("#guide").evaluate((dialog) => dialog.open),
  false,
);

// Narrow layout has usable controls, full Ontario and no horizontal overflow.
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({ path: `${output}/mobile.png`, fullPage: true });
assert.ok(
  await page.evaluate(
    () => document.documentElement.scrollWidth <= innerWidth + 1,
  ),
);
const frame = await page.locator("#map-frame").boundingBox();
assert.ok(frame.x >= 0 && frame.x + frame.width <= 390);
await page.locator('[data-incident="2"]').click();
await page.locator("[data-action=crew]").click();
assert.equal(await page.locator("#supplies").textContent(), "16");
await page.emulateMedia({ reducedMotion: "reduce" });
await begin(9);
await page.screenshot({ path: `${output}/reduced-motion.png`, fullPage: true });
assert.equal(
  (await page.request.get("http://127.0.0.1:8790/.env")).status(),
  404,
);
await checkPersistence(page, output, begin);
assert.ok(requests.every((request) => request.method === "GET"));
assert.deepEqual(errors, []);
await fs.writeFile(
  `${output}/receipt.json`,
  JSON.stringify(
    {
      results,
      errors,
      requests: requests.length,
      source_count: source.count,
      checked_layers: 6,
      checked_height_epochs: 7,
      custom_sliders:
        "Pointer, keyboard steps, limits and no accidental front advancement",
      persistence:
        "Same-seed reload/continuation preserves resources and loadout; new season resets",
      instruments: 6,
      viewports: [
        [1440, 960],
        [390, 844],
      ],
      scope:
        "Control-driven UI and model arithmetic; no fits, quantum hardware or final-evidence changes.",
    },
    null,
    2,
  ) + "\n",
);
console.log(
  JSON.stringify({ results, errors, receipt: `${output}/receipt.json` }),
);
await browser.close();
