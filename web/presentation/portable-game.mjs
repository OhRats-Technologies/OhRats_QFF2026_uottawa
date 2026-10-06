import assert from "node:assert/strict";

// Public assets only: no project dependencies or ignored data are read here.
export async function verifyGame(page, base, output, imagesReady) {
  const result = { contextLayers: [], heightEpochs: [], gameControls: {} };
  await page.goto(`${base}/web/demo/?qa=portable#season=2`, {
    waitUntil: "domcontentloaded",
  });
  await page.locator("#start").click();
  const layers = await page.locator("#layer option")
    .evaluateAll(nodes => nodes.map(node => node.value));
  for (const key of layers) {
    await page.locator("#layer").selectOption(key);
    await page.locator("#map-image").evaluate(image => image.decode());
    result.contextLayers.push(key);
    if (key === "height") {
      for (const epoch of await page.locator("[data-epoch]").all()) {
        await epoch.click();
        await page.locator("#map-image").evaluate(image => image.decode());
        result.heightEpochs.push(Number(await epoch.getAttribute("data-epoch")));
      }
    }
  }
  await page.locator("#layer").selectOption("cover");
  const beforeLegend = await page.evaluate(() => localStorage.getItem("fireline-season"));
  await page.locator("#legend-toggle").press("Enter");
  assert.equal(await page.locator("[data-cover-codes]").count(), 13);
  assert.equal((await page.locator('[data-cover-codes="0,255"]').textContent()).trim(), "Unclassified / missing");
  assert.equal(await page.locator("#legend-toggle").getAttribute("aria-expanded"), "true");
  await page.locator("#legend-toggle").press("Enter");
  assert.equal(await page.locator("#map-legend").isVisible(), false);
  assert.equal(await page.evaluate(() => localStorage.getItem("fireline-season")), beforeLegend);
  result.gameControls.completeCoverLegend = { groups: 13, gameSaveUnchanged: true };
  await page.locator('[data-action="water"]').click();
  assert.equal(await page.locator("#supplies").textContent(), "14");
  await page.locator("#incident-list button").first().focus();
  await page.keyboard.press("n");
  assert.equal(await page.locator("#front-number").textContent(), "2 / 12");
  assert.equal(await page.locator("#supplies").textContent(), "16");
  result.gameControls.advanceFromIncidentFocus = true;
  await page.locator("#sample").click();
  await page.locator("#matrix-mode").click();
  assert.equal(await page.locator("#bench-dialog").evaluate(dialog => dialog.open), true);
  await page.locator("#bench-close").click();

  const saveBefore = await page.evaluate(() => localStorage.getItem("fireline-season"));
  await page.locator('[data-milestone="4"]').press("Enter");
  await page.locator("#progression[open]").waitFor();
  assert.equal(await page.locator('[data-build-effect="crews"]').textContent(), "2");
  assert.equal(await page.locator('[data-build-effect="power"]').textContent(), "0.90");
  assert.equal(await page.locator('[data-build-effect="supplies"]').textContent(), "2");
  assert.equal(await page.locator('[data-build-effect="water"]').textContent(), "58%");
  assert.equal(await page.locator("[data-build-upgrade]").count(), 4);
  await page.keyboard.press("Escape");
  assert.equal(await page.locator('[data-milestone="4"]').evaluate(node => node === document.activeElement), true);
  assert.equal(await page.evaluate(() => localStorage.getItem("fireline-season")), saveBefore);
  result.gameControls.responseLedger = true;

  await page.locator("#lab-open").click();
  await page.locator("#instrument-dialog[open]").waitFor();
  assert.equal(await page.locator("#instrument-options button").count(), 6);
  const before = Number(await page.locator('[data-fidelity="before"]').textContent());
  await page.locator('[data-technique="dd"]').press("Enter");
  const after = Number(await page.locator('[data-fidelity="after"]').textContent());
  assert.ok(after > before && after <= 1);
  assert.match(await page.locator("#instrument-feedback").textContent(), /Echo sequence equipped.*Channel fidelity/);
  assert.equal(await page.locator("#instrument-close").evaluate(node => node === document.activeElement), true);
  const saveAfter = JSON.parse(await page.evaluate(() => localStorage.getItem("fireline-season")));
  assert.deepEqual(saveAfter.moves, JSON.parse(saveBefore).moves);
  assert.deepEqual(saveAfter.techniques, ["dd"]);
  await page.locator("#instrument-close").click();
  result.gameControls.channelEffect = { before, after, gameMovesUnchanged: true };

  assert.equal(await page.locator("#sound").getAttribute("aria-pressed"), "false");
  await page.locator("#sound").click();
  await page.locator('#sound[aria-pressed="true"]').waitFor();
  await page.locator("#sound").click();
  assert.equal(await page.locator("#sound").getAttribute("aria-pressed"), "false");
  result.gameControls.optInAudioAndMute = true;

  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("#guide-open").click();
  await page.locator("#guide-progress").press("Enter");
  await page.locator("#progression[open]").waitFor();
  assert.equal(await page.locator("#guide").evaluate(dialog => dialog.open), false);
  assert.equal(await page.locator("#progression").evaluate(dialog => dialog.scrollWidth <= dialog.clientWidth), true);
  await page.screenshot({ path: `${output}/mobile-build.png` });
  await page.keyboard.press("Escape");
  assert.equal(await page.locator("#guide-open").evaluate(node => node === document.activeElement), true);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  result.gameControls.mobileLedger = true;
  await page.setViewportSize({ width: 1280, height: 720 });
  await imagesReady();
  await page.screenshot({ path: `${output}/fireline.png` });

  const checkpoint = await page.evaluate(() => localStorage.getItem("fireline-season"));
  const readout = async () => Object.fromEntries(await Promise.all(
    ["front-number", "integrity", "supplies", "crews", "contained"].map(async id =>
      [id, await page.locator(`#${id}`).textContent()]),
  ));
  const beforeTrip = await readout();
  await page.locator("#guide-open").click();
  await page.locator('.guide-links a[href="lab.html#prediction"]').click();
  await page.locator('#scene[data-section="prediction"]').waitFor();
  assert.equal(await page.locator(".prediction-chart .pred-bar").count(), 4);
  assert.equal(await page.evaluate(() => localStorage.getItem("fireline-season")), checkpoint);
  await page.locator('.transport a[href="index.html"]').click();
  await page.locator("#welcome[open]").waitFor();
  assert.equal(await page.locator("#start").textContent(), "Continue front 2 →");
  await page.locator("#start").click();
  await imagesReady();
  assert.equal(await page.evaluate(() => localStorage.getItem("fireline-season")), checkpoint);
  assert.deepEqual(await readout(), beforeTrip);
  assert.equal(await page.evaluate(() => scrollY), 0);
  assert.equal(await page.locator("#game-title").evaluate(node => node === document.activeElement), true);
  result.gameControls.evidenceRoundTrip = {
    destination: "lab.html#prediction", visiblePredictionBars: 4,
    movesSelectionEquipmentPreserved: true, responseReadouts: beforeTrip,
    continuesAtMap: true,
  };
  return result;
}
