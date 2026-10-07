import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
const require = createRequire(import.meta.url),
  { chromium } = require(`${process.env.RUNTIME_NODE_MODULES}/playwright`);
const out = process.env.FIRELINE_OUTPUT || ".cache/fireline-canvas";
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true });
const receipts = [];
for (const [width, height] of [
  [1440, 900],
  [1280, 640],
  [1920, 1080],
  [390, 844],
  [320, 568],
  [844, 390],
]) {
  const context = await browser.newContext({
    viewport: { width, height },
    reducedMotion: "reduce",
    hasTouch: width < 500,
  });
  const page = await context.newPage(),
    errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(
    `${process.env.FIRELINE_BASE || "http://127.0.0.1:8790"}/web/demo/`,
  );
  await page.waitForFunction(() => window.fireline);
  const click = async (id) => {
    await page.waitForFunction(
      (id) =>
        window.fireline.controls().some((h) => h.id === id && !h.disabled),
      id,
    );
    const h = await page.evaluate(
        (id) => window.fireline.controls().find((h) => h.id === id),
        id,
      ),
      scale = width / Math.max(390, width);
    await page.mouse.click((h.x + h.w / 2) * scale, (h.y + h.h / 2) * scale);
    await page.waitForTimeout(35);
  };
  await page.screenshot({ path: `${out}/menu-${width}.png` });
  await click("continue");
  if (await page.evaluate(() => window.fireline.snapshot().guideIntro))
    await click("guide-skip");
  await page.screenshot({ path: `${out}/build-${width}.png` });
  await click("signal-0");
  while (
    !(await page.evaluate(() =>
      window.fireline.controls().some((h) => h.id === "signal-5"),
    ))
  )
    await click("rack-page");
  await click("signal-5");
  await click("run");
  await page.waitForFunction(
    () =>
      window.fireline.snapshot().attempts === 1 &&
      !window.fireline.snapshot().running,
  );
  if (width < 920) await click("tab-kernel");
  await page.screenshot({ path: `${out}/kernel-${width}.png` });
  await click(width < 920 ? "tab-rack" : "foundry");
  if (width < 920) await click("foundry");
  await click("method-qaoa");
  await page.screenshot({ path: `${out}/foundry-${width}.png` });
  await click("apply");
  await click("run");
  await page.waitForFunction(
    () =>
      window.fireline.snapshot().attempts === 2 &&
      !window.fireline.snapshot().running,
  );
  await page.screenshot({ path: `${out}/results-${width}.png` });
  await click("help");
  await page.screenshot({ path: `${out}/notes-${width}.png` });
  await page.keyboard.press("Escape");
  const before = await page.evaluate(() => window.fireline.snapshot());
  await page.reload();
  await page.waitForFunction(() => window.fireline);
  const after = await page.evaluate(() => window.fireline.snapshot());
  if (after.attempts !== 2 || after.result.mae !== before.result.mae)
    throw new Error("Persistence lost");
  await click("continue");
  await page.keyboard.press("Tab");
  const focused = await page.evaluate(() => document.activeElement.dataset.id);
  if (!focused) throw new Error("No keyboard focus");
  const geometry = await page.evaluate(() => ({
    controls: window.fireline.controls(),
    width: Math.max(390, innerWidth),
    height: innerHeight / (innerWidth / Math.max(390, innerWidth)),
    scroll: document.documentElement.scrollWidth,
  }));
  const overflow = geometry.controls.filter(
    (h) =>
      h.x < 0 ||
      h.y < 0 ||
      h.x + h.w > geometry.width + 1 ||
      h.y + h.h > geometry.height + 1,
  );
  if (overflow.length)
    throw new Error(
      `Offscreen controls ${width}: ${overflow.map((h) => h.id).join(",")}`,
    );
  if (errors.length) throw new Error(errors.join(";"));
  receipts.push({
    width,
    height,
    attempts: after.attempts,
    mae: after.result.mae,
    focused,
    controls: geometry.controls.length,
    overflow: 0,
    errors,
  });
  await context.close();
}
await browser.close();
writeFileSync(
  `${out}/receipt.json`,
  JSON.stringify({ viewports: receipts }, null, 2) + "\n",
);
console.log(JSON.stringify(receipts));
