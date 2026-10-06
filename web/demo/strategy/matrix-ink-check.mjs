// Compare visible values and composited text contrast against the pinned bundle.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';

const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require('playwright');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const output = '.cache/judge-submission/matrix-ink';
await fs.mkdir(output, { recursive: true });
const baselineCommit = '69d9677';
const oldBundle = execFileSync('git', ['show', `${baselineCommit}:web/demo/assets/strategy.js`]);
const oldStyle = execFileSync('git', ['show', `${baselineCommit}:web/demo/strategy/styles/research.css`]);
const browser = await chromium.launch({ headless: true, channel: 'chrome' });
const cases = [], errors = [];

async function read(page) {
  return page.evaluate(() => {
    const rgb = colour => colour.match(/[\d.]+/g).map(Number);
    const luminance = channels => channels.map(value => {
      value /= 255;
      return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
    }).reduce((sum, channel, i) => sum + channel * [.2126, .7152, .0722][i], 0);
    const base = rgb(getComputedStyle(document.querySelector('#instrument-dialog')).backgroundColor);
    const cells = [...document.querySelectorAll('#lab-matrix span')].map(element => {
      const style = getComputedStyle(element), ink = rgb(style.color), rgba = rgb(style.backgroundColor);
      const alpha = rgba[3] ?? 1;
      const background = rgba.slice(0, 3).map((value, i) => value * alpha + base[i] * (1 - alpha));
      const a = luminance(ink), b = luminance(background);
      return { value: element.textContent, background: style.backgroundColor,
        contrast: (Math.max(a, b) + .05) / (Math.min(a, b) + .05) };
    });
    const options = [...document.querySelectorAll('[data-technique]')].map(button => ({
      text: button.textContent, disabled: button.disabled, opacity: Number(getComputedStyle(button).opacity) }));
    return { cells, options, metrics: document.querySelector('#lab-metrics').textContent,
      channel: document.querySelector('#channel-fidelity').textContent,
      save: localStorage.getItem('fireline-season') };
  });
}

try {
  for (const [width, height] of [[1280, 720], [390, 844]]) {
    const old = await browser.newPage({ viewport: { width, height } });
    const current = await browser.newPage({ viewport: { width, height } });
    for (const page of [old, current]) page.on('pageerror', error => errors.push(error.message));
    await old.route('**/assets/strategy.js', route => route.fulfill({ body: oldBundle, contentType: 'text/javascript' }));
    await old.route('**/strategy/styles/research.css', route => route.fulfill({ body: oldStyle, contentType: 'text/css' }));
    for (const technique of ['none', 'dd', 'twirl', 'postselect', 'readout', 'psd', 'lowrank']) {
      const versions = [];
      for (const page of [old, current]) {
        await page.goto(`http://127.0.0.1:8790/web/demo/?qa=ink-${width}-${technique}#season=7`);
        await page.locator('#start').click();
        await page.locator('#lab-open').click();
        if (technique !== 'none') await page.locator(`[data-technique="${technique}"]`).click();
        versions.push(await read(page));
      }
      const [before, after] = versions;
      assert.equal(after.cells.length, 16);
      assert.deepEqual(after.cells.map(cell => [cell.value, cell.background]), before.cells.map(cell => [cell.value, cell.background]));
      assert.equal(after.metrics, before.metrics);
      assert.equal(after.channel, before.channel);
      assert.equal(after.save, before.save);
      assert.deepEqual(after.options.map(({ text, disabled }) => [text, disabled]), before.options.map(({ text, disabled }) => [text, disabled]));
      assert.ok(after.options.every(option => option.opacity === 1));
      assert.ok(after.cells.every(cell => cell.contrast >= 4.5));
      await current.locator('#instrument-close').click();
      assert.equal(await current.evaluate(() => localStorage.getItem('fireline-season')), after.save);
      const minimum = cells => Math.min(...cells.map(cell => cell.contrast));
      cases.push({ width, height, technique, cells: 16, minimum_before: minimum(before.cells),
        minimum_after: minimum(after.cells), values_and_backgrounds_exact: true,
        metrics_channel_and_save_exact: true, close_preserves_save: true,
        option_labels_and_disabled_states_exact: true, descriptions_visible_when_disabled: true,
        minimum_option_opacity_before: Math.min(...before.options.map(option => option.opacity)),
        minimum_option_opacity_after: Math.min(...after.options.map(option => option.opacity)) });
      if (technique === 'lowrank') {
        await current.locator('#lab-open').click();
        await current.locator('#lab-matrix').scrollIntoViewIfNeeded();
        await current.screenshot({ path: `${output}/${width}-lowrank.png` });
      }
    }
    await old.close();
    await current.close();
  }
  assert.deepEqual(errors, []);
  const sources = ['web/demo/strategy/matrix-ink.js', 'web/demo/strategy/instruments.js',
    'web/demo/assets/strategy.js', 'web/demo/strategy/styles/dialogs.css',
    'web/demo/strategy/styles/research.css', 'web/demo/strategy/matrix-ink-check.mjs'];
  const source_sha256 = Object.fromEntries(await Promise.all(sources.map(async path => [path, sha(await fs.readFile(path))])));
  const receipt = { checked_utc: new Date().toISOString(), status: 'passed', source_sha256,
    baseline: { commit: baselineCommit, bundle_sha256: sha(oldBundle), research_css_sha256: sha(oldStyle) }, cases, errors,
    new_predictor_fits: 0, new_quantum_states: 0, hardware_jobs: 0,
    scope: 'Actual Chromium composited colours and native dialog controls for seven displays at two sizes. '
      + 'Locator scrolling is allowed for typography inspection. This is a matrix-number readability check, '
      + 'not whole-site accessibility, physical-device or predictive certification.' };
  await fs.writeFile(`${output}/receipt.json`, JSON.stringify(receipt, null, 2) + '\n');
  console.log(JSON.stringify({ cases: cases.length, cells_checked: cases.length * 16,
    minimum_before: Math.min(...cases.map(row => row.minimum_before)),
    minimum_after: Math.min(...cases.map(row => row.minimum_after)), errors }));
} finally {
  await browser.close();
}
