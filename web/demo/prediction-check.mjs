// Authoring-only check of the displayed frozen annual comparison.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { predictionRows } from './model.js';

const read = async file => JSON.parse(await fs.readFile(file, 'utf8'));
const hash = async file => createHash('sha256')
  .update(await fs.readFile(file)).digest('hex');
const evidence = await read('web/presentation/evidence.json');
const final = await read('docs/results/annual-final.json');
const audit = await read('docs/data/annual_source_review.json');
for (const [file, expected] of Object.entries(evidence.sources_sha256)) {
  assert.equal(await hash(file), expected, file);
}
const years = [2019, 2020, 2021, 2022, 2023, 2024];
const sourceChecks = years.map(year => {
  const rows = predictionRows(evidence, year);
  const source = audit.annual.find(row => row.year === year);
  assert.equal(source.mean_reported_size_ha,
    source.total_observed_size_ha / source.size_observed_incidents);
  for (const row of rows) {
    const frozen = final.main_results.find(result => result.id === row.id);
    const index = frozen.years.indexOf(year);
    assert.equal(row.value, frozen.predicted_ha[index]);
    assert.equal(row.actual, frozen.actual_ha[index]);
    assert.equal(row.mae, frozen.mae_ha);
    assert.ok(Math.abs(row.actual - source.mean_reported_size_ha) < 1e-9);
    assert.ok(row.value >= 0 && row.value <= 700);
  }
  assert.ok(rows[0].actual >= 0 && rows[0].actual <= 700);
  return { year, predictions: rows.map(row => row.value), recorded: rows[0].actual };
});

const require = createRequire(path.join(process.env.RUNTIME_NODE_MODULES, '../package.json'));
const { chromium } = require('playwright');
const browser = await chromium.launch({ headless: true, channel: 'chrome' });
const out = '.cache/judge-submission/prediction-clarity';
await fs.mkdir(out, { recursive: true });
const base = process.env.DEMO_BASE_URL ?? 'http://127.0.0.1:8790';
const checks = [], errors = [], requests = [];
try {
  const page = await browser.newPage({ reducedMotion: 'reduce' });
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => requests.push({
    url: request.url(), method: request.method(),
  }));
  await page.route('**/*', route => new URL(route.request().url()).origin === base
    ? route.continue() : route.abort());
  for (const [width, height] of [[1280, 720], [1024, 768], [390, 844]]) {
    await page.setViewportSize({ width, height });
    await page.goto(`${base}/web/demo/lab.html#prediction`);
    await page.waitForFunction(() => window.demo);
    assert.equal(await page.locator('.series-3').count(), 1);
    assert.equal(await page.locator('.series-3').isVisible(), true);
    assert.equal(await page.locator('[data-reveal]').count(), 0);
    assert.equal((await page.locator('.bar-value').allTextContents())[3], '657.0');
    for (const year of years) {
      await page.locator(`[data-year="${year}"]`).click();
      const source = sourceChecks.find(row => row.year === year);
      const expected = [...source.predictions, source.recorded];
      assert.deepEqual(await page.locator('.bar-value').allTextContents(),
        expected.map(value => value.toFixed(1)));
      const chart = page.locator('.prediction-chart svg');
      const description = await chart.getAttribute('aria-label');
      assert.match(description, new RegExp(`${year} annual mean hectares`));
      for (const value of expected) assert.ok(description.includes(`${value.toFixed(1)} ha/fire`));
      assert.match(await page.locator('.prediction-stage>.context-note').innerText(),
        /annual mean, not the size of one fire/);
      const geometry = await chart.evaluate(svg => {
        const box = svg.viewBox.baseVal;
        return {
          horizontalOverflow: document.documentElement.scrollWidth > innerWidth,
          heights: [...svg.querySelectorAll('.pred-bar')].map(bar => Number(bar.getAttribute('height'))),
          clipped: [...svg.querySelectorAll('text')].filter(text => {
            const b = text.getBBox();
            return b.x < box.x || b.y < box.y || b.x + b.width > box.width || b.y + b.height > box.height;
          }).map(text => text.textContent),
        };
      });
      assert.equal(geometry.horizontalOverflow, false, `${width}/${year}`);
      assert.deepEqual(geometry.clipped, [], `${width}/${year}`);
      geometry.heights.forEach((height, i) => assert.ok(Math.abs(height - expected[i] / 700 * 290) < 1e-10));
      checks.push({ width, height, year, displayed: expected.map(value => value.toFixed(1)), clipped: [] });
    }
    await page.locator('[data-year="2021"]').click();
    await page.screenshot({ path: path.join(out, `${width}.png`), fullPage: true });
  }
  assert.deepEqual(errors, []);
  assert.ok(requests.every(request => request.method === 'GET' && new URL(request.url).origin === base));
  const files = ['web/demo/model.js', 'web/demo/app.js', 'web/demo/views.js',
    'web/demo/graphics.js', 'web/demo/quantum.css', 'web/demo/responsive.css',
    'web/demo/prediction-check.mjs', 'web/presentation/evidence.json'];
  const sourceHashes = Object.fromEntries(await Promise.all(files.map(async file => [file, await hash(file)])));
  const receipt = {
    checked_utc: new Date().toISOString(), status: 'passed',
    base_commit: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
    source_sha256: sourceHashes, frozen_sources_sha256: evidence.sources_sha256,
    default_recorded_bar_visible: true, reveal_toggle_removed: true,
    source_checks: sourceChecks, browser_checks: checks, page_errors: errors,
    fixed_scale_ha_per_fire: [0, 700], predictor_fits: 0, quantum_states: 0, hardware_jobs: 0,
    scope: 'Displayed frozen values, source arithmetic, SVG geometry and reduced-motion layouts on this Mac; no new fit, statistical validation or human usability trial.',
  };
  await fs.writeFile(path.join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log('All six recorded means and three predictions match sources at three viewport sizes.');
} finally {
  await browser.close();
}
