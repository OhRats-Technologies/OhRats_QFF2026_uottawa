// Offline synthesis/mute checks plus opt-in and unavailable-audio controls.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const require = createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const { chromium } = require("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", args: ["--mute-audio"] });
const out = ".cache/judge-submission/forest-audio";
await fs.mkdir(out, { recursive: true });
const errors = [], fallback = [];
const oldCommit = "f2c86e2";
const oldSource = execFileSync("git", ["show", `${oldCommit}:web/demo/strategy/sound.js`]);
try {
  const page = await browser.newPage({ reducedMotion: "reduce" });
  page.on("pageerror", error => errors.push(error.message));
  await page.route("https://**/*", route => route.abort());
  await page.addInitScript(() => {
    const NativeAudio = AudioContext;
    window.audioCheck = { contexts: [], started: 0, immediateStops: 0 };
    window.AudioContext = class extends NativeAudio {
      constructor(...args) {
        super(...args);
        window.audioCheck.contexts.push(this);
        for (const method of ["createOscillator", "createBufferSource"]) {
          const create = this[method].bind(this);
          this[method] = (...params) => {
            const source = create(...params), start = source.start.bind(source), stop = source.stop.bind(source);
            source.start = (...times) => { window.audioCheck.started++; return start(...times); };
            source.stop = (...times) => {
              if (!times.length || times[0] <= this.currentTime) window.audioCheck.immediateStops++;
              return stop(...times);
            };
            return source;
          };
        }
      }
    };
  });
  await page.goto("http://127.0.0.1:8790/web/demo/?qa=audio#season=2");
  await page.locator("#start").click();
  await page.locator("#advance").click();
  assert.equal(await page.evaluate(() => window.audioCheck.contexts.length), 0);
  assert.equal(await page.locator("#sound").textContent(), "Sound off");
  await page.locator("#sound").click();
  await page.locator('#sound[aria-pressed="true"]:not(:disabled)').waitFor();
  assert.equal(await page.evaluate(() => window.audioCheck.contexts.length), 1);
  const save = await page.evaluate(() => localStorage.getItem("fireline-season"));
  await page.locator("#sound").click();
  await page.locator('#sound[aria-pressed="false"]:not(:disabled)').waitFor();
  assert.ok(await page.evaluate(() => window.audioCheck.immediateStops >= 2));
  assert.equal(await page.evaluate(() => localStorage.getItem("fireline-season")), save);
  await page.locator("#sound").click();
  await page.locator('#sound[aria-pressed="true"]:not(:disabled)').waitFor();
  const stopped = await page.evaluate(() => window.audioCheck.immediateStops);
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", { configurable: true, get: () => true });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  assert.ok(await page.evaluate(() => window.audioCheck.immediateStops) > stopped);
  const started = await page.evaluate(() => window.audioCheck.started);
  await page.locator("#advance").click();
  assert.equal(await page.evaluate(() => window.audioCheck.started), started);
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", { configurable: true, get: () => false });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  assert.equal(await page.evaluate(() => window.audioCheck.started), started);
  await page.locator("#sound").click();
  await page.locator('#sound[aria-pressed="false"]:not(:disabled)').waitFor();

  const offline = await page.evaluate(async oldURL => {
    const { Sound } = await import("./strategy/sound.js");
    const { Sound: OldSound } = await import(oldURL);
    const summary = samples => ({
      peak: samples.reduce((max, value) => Math.max(max, Math.abs(value)), 0),
      rms: Math.sqrt(samples.reduce((sum, value) => sum + value * value, 0) / samples.length),
      finite: samples.every(Number.isFinite),
    });
    const cues = [];
    for (const kind of ["crew", "water", "inspect", "advance", "upgrade", "won", "lost"]) {
      const context = new OfflineAudioContext(1, 48000 * 1.5, 48000);
      const sound = new Sound(context);
      sound.enabled = true;
      sound.play(kind);
      const buffer = await context.startRendering(), samples = Array.from(buffer.getChannelData(0));
      cues.push({ kind, ...summary(samples), tail_peak: summary(samples.slice(48000)).peak,
        samples: ["water", "advance"].includes(kind) ? samples : undefined });
    }
    async function muted(Type, hidden = false) {
      const context = new OfflineAudioContext(1, 48000, 48000);
      const sound = Type === OldSound ? new Type() : new Type(context);
      sound.context = context;
      sound.enabled = true;
      sound.play("won");
      if (hidden) sound.setHidden(true);
      else await sound.enable(false);
      return summary(Array.from((await context.startRendering()).getChannelData(0)));
    }
    return { cues, old_mute: await muted(OldSound), mute: await muted(Sound), hidden: await muted(Sound, true) };
  }, `data:text/javascript;base64,${oldSource.toString("base64")}`);
  for (const cue of offline.cues) {
    assert.equal(cue.finite, true);
    assert.ok(cue.peak > 0.005 && cue.peak < 0.3, cue.kind);
    assert.equal(cue.tail_peak, 0);
    if (cue.samples) {
      const pcm = Buffer.alloc(cue.samples.length * 2), header = Buffer.alloc(44);
      cue.samples.forEach((value, i) => pcm.writeInt16LE(Math.round(Math.max(-1, Math.min(1, value)) * 32767), i * 2));
      header.write("RIFF"); header.writeUInt32LE(36 + pcm.length, 4); header.write("WAVEfmt ", 8);
      header.writeUInt32LE(16, 16); header.writeUInt16LE(1, 20); header.writeUInt16LE(1, 22);
      header.writeUInt32LE(48000, 24); header.writeUInt32LE(96000, 28); header.writeUInt16LE(2, 32);
      header.writeUInt16LE(16, 34); header.write("data", 36); header.writeUInt32LE(pcm.length, 40);
      await fs.writeFile(`${out}/${cue.kind}.wav`, Buffer.concat([header, pcm]));
      delete cue.samples;
    }
  }
  assert.ok(offline.old_mute.peak > 0.01);
  assert.equal(offline.mute.peak, 0);
  assert.equal(offline.hidden.peak, 0);
  for (const failure of ["constructor", "resume"]) {
    const blocked = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce" });
    blocked.on("pageerror", error => errors.push(error.message));
    await blocked.route("https://**/*", route => route.abort());
    await blocked.addInitScript(failure => {
      const NativeAudio = AudioContext;
      window.AudioContext = failure === "constructor" ? class {
        constructor() { throw new Error("Disposable unavailable-audio fixture"); }
      } : class extends NativeAudio {
        resume() { return Promise.reject(new Error("Disposable denied-resume fixture")); }
      };
    }, failure);
    await blocked.goto(`http://127.0.0.1:8790/web/demo/?qa=audio-${failure}#season=2`);
    await blocked.locator("#start").click();
    await blocked.locator("#sound").click();
    await blocked.getByRole("button", { name: "Sound unavailable", exact: true }).waitFor();
    assert.equal(await blocked.locator("#sound").isDisabled(), true);
    assert.equal(await blocked.locator("#sound").getAttribute("aria-pressed"), "false");
    await blocked.locator("#advance").click();
    assert.equal(await blocked.locator("#front-number").textContent(), "2 / 12");
    assert.equal(await blocked.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await blocked.screenshot({ path: `${out}/${failure}.png`, fullPage: true });
    fallback.push({ failure, gameplay_continues: true, no_horizontal_overflow: true });
    await blocked.close();
  }
  assert.deepEqual(errors, []);
  const hashes = {};
  for (const file of ["sound.js", "main.js", "audio-check.mjs", "rules.js", "scenario.js", "upgrades.js", "session.js"]) {
    const name = `web/demo/strategy/${file}`;
    hashes[name] = hash(await fs.readFile(name));
    if (["rules.js", "scenario.js", "upgrades.js", "session.js"].includes(file))
      assert.equal(hashes[name], hash(execFileSync("git", ["show", `HEAD:${name}`])));
  }
  hashes["web/demo/assets/strategy.js"] = hash(await fs.readFile("web/demo/assets/strategy.js"));
  await fs.writeFile(`${out}/receipt.json`, JSON.stringify({
    checked_utc: new Date().toISOString(), status: "passed", source_sha256: hashes,
    old_commit: oldCommit, old_source_sha256: hash(oldSource), offline,
    no_context_before_opt_in: true, mute_stops_scheduled_sources: true,
    hidden_stops_sources_and_prevents_cues: true, returning_does_not_replay: true,
    sound_toggle_preserves_save: true, fallback, errors,
    predictor_fits: 0, quantum_states: 0, hardware_jobs: 0,
    scope: "Offline waveform and browser control/failure-injection checks. Browser output muted during authoring; not a speaker/listening trial, measured loudness certification or OS visibility test.",
  }, null, 2) + "\n");
  console.log("Seven bounded cues, immediate mute, hidden cleanup, opt-in and unavailable-audio play pass.");
} finally {
  await browser.close();
}
