import assert from "node:assert/strict";

export async function checkPersistence(page, output, begin) {
  // Resume rebuilds response moves and instrument credits; a deep link to the same seed keeps progress.
  await page.setViewportSize({ width: 1440, height: 960 });
  await begin(2);
  await page.locator('[data-incident="3"]').click();
  await page.locator('[data-action="crew"]').click();
  await page.locator("#lab-open").click();
  await page.locator('[data-technique="dd"]').click();
  await page.locator("#instrument-close").click();
  await page.locator("#advance").click();
  const savedReadout = {};
  for (const id of [
    "front-number",
    "supplies",
    "crew-status",
    "integrity",
    "lab-loadout",
  ])
    savedReadout[id] = await page.locator(`#${id}`).textContent();
  await page.goto("http://127.0.0.1:8790/web/demo/?resume=check#season=2");
  assert.match(await page.locator("#start").textContent(), /Continue front 2/);
  await page.locator("#start").click();
  for (const [id, value] of Object.entries(savedReadout))
    assert.equal(await page.locator(`#${id}`).textContent(), value);
  assert.match(await page.locator("#lab-open").textContent(), /0 credits/);
  await page.screenshot({ path: `${output}/resumed-season.png` });
  await page.reload();
  await page.locator("#fresh").click();
  assert.equal(await page.locator("#supplies").textContent(), "18");
  assert.match(await page.locator("#front-number").textContent(), /1 \/ 12/);
  assert.match(await page.locator("#lab-open").textContent(), /1 credit/);
}
