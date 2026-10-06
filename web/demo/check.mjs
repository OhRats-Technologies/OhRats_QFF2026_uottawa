// Authoring QA uses the bundled Playwright runtime; viewing needs only Bun.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {subsetCost,angle,predictionRows} from './model.js';
const data=JSON.parse(await fs.readFile('web/demo/data.json','utf8'));
const evidence=JSON.parse(await fs.readFile('web/presentation/evidence.json','utf8'));
for(const [file,hash] of Object.entries(data.sources_sha256))assert.equal(createHash('sha256').update(await fs.readFile(file)).digest('hex'),hash);
const costs=[];
for(let a=0;a<7;a++)for(let b=a+1;b<8;b++)for(let c=b+1;c<9;c++)for(let d=c+1;d<10;d++)costs.push(subsetCost([a,b,c,d],data));
assert.equal(costs.length,210);
assert.ok(Math.abs(Math.min(...costs)-data.record.exact_objective)<1e-12);
assert.ok(Math.abs(data.teaching_basis[0].energy-Math.min(...costs))<1e-12);
for(const r of data.teaching_basis)assert.ok(Math.abs(subsetCost(r.indices,data)-r.energy)<1e-12);
assert.equal(angle(0,4),0);
assert.ok(Math.abs(angle(3,4))<Math.PI/4);
const require=createRequire(path.join(process.env.RUNTIME_NODE_MODULES,'../package.json'));
const {chromium}=require('playwright');
const browser=await chromium.launch({headless:true,channel:'chrome'});
const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
const errors=[],requests=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('request',r=>requests.push({url:r.url(),method:r.method()}));
const out='.cache/judge-submission/demo-browser';
await fs.mkdir(out,{recursive:true});
await page.goto('http://127.0.0.1:8790/web/demo/lab.html');
await page.waitForFunction(()=>window.demo);
assert.equal(await page.locator('#steps button').count(),5);
assert.equal(await page.locator('#scene').getAttribute('data-section'),'data');
for(const year of [2019,2020,2021,2022,2023,2024]){
  await page.locator(`[data-year="${year}"]`).click();
  const r=evidence.source_review.annual.find(r=>r.year===year);
  assert.match(await page.locator('.answer').innerText(),new RegExp(r.mean_reported_size_ha.toFixed(1).replace('.','\\.')));
}
await page.locator('[data-year="2021"]').click();
await page.locator('[data-map="pixels"]').click();
await page.locator('.pixel-land').evaluate(e=>e.decode());
assert.equal(await page.locator('.pixel-land').evaluate(e=>e.complete&&e.naturalWidth>0),true);
await page.locator('[data-map="cover"]').click();
await page.evaluate(()=>demo.show(1));
assert.equal(await page.locator('.feature.selected').count(),4);
await page.locator('[data-selector="exact_same_qubo"]').click();
for(const stage of [0,1,2]){
  await page.locator(`[data-sqd="${stage}"]`).click();
  assert.equal(await page.evaluate(()=>demo.state.sqdStage),stage);
}
assert.equal(await page.locator('.minimum').count(),1);
assert.match(await page.locator('.projection-caption').innerText(),/no optimization benefit/);
await page.screenshot({path:path.join(out,'sqd.png'),fullPage:true,animations:'disabled'});
await page.evaluate(()=>demo.show(2));
const slider=page.locator('[data-input="0"]');
await slider.focus();
await page.keyboard.press('Home');
assert.equal(await slider.getAttribute('aria-valuenow'),'-3');
await page.keyboard.press('ArrowRight');
assert.equal(await slider.getAttribute('aria-valuenow'),'-2.95');
assert.equal(await page.evaluate(()=>demo.state.section),2);
await page.keyboard.press('End');
assert.equal(await slider.getAttribute('aria-valuenow'),'3');
const rect=await slider.boundingBox();
await page.mouse.move(rect.x+rect.width/4,rect.y+rect.height/2);
await page.mouse.down();
await page.mouse.move(rect.x+rect.width*.75,rect.y+rect.height/2,{steps:12});
await page.mouse.up();
assert.ok(Math.abs(Number(await slider.getAttribute('aria-valuenow'))-1.5)<.02);
const before=await page.locator('.phase-arm').first().getAttribute('d');
await page.locator('[data-angle="32"]').click();
await page.waitForTimeout(700);
assert.notEqual(await page.locator('.phase-arm').first().getAttribute('d'),before);
await page.evaluate(()=>demo.show(3));
for(const width of [4,10])for(const scale of [32,16,8,4,2]){
  await page.locator(`[data-width="${width}"]`).click();
  await page.locator(`[data-scale="${scale}"]`).click();
  const row=evidence.geometry.find(r=>r.inputs===width&&r.amplitude_pi_denominator===scale);
  assert.equal(await page.locator('#fidelity').innerText(),row.matrix[19][20].toFixed(6));
}
await page.locator('[data-pair="0"]').selectOption('20');
assert.equal(await page.locator('#fidelity').innerText(),'1.000000');
await page.locator('[data-pair="0"]').selectOption('19');
await page.locator('[data-scale="4"]').click();
await page.evaluate(()=>demo.show(4));
for(const year of [2019,2020,2021,2022,2023,2024]){
  await page.locator(`[data-year="${year}"]`).click();
  const rows=predictionRows(evidence,year);
  const shown=await page.locator('.bar-value').allTextContents();
  assert.deepEqual(shown,[...rows.map(r=>r.value),rows[0].actual].map(v=>v.toFixed(1)));
  assert.equal(await page.locator('.series-3').count(),1);
}
await page.locator('[data-year="2021"]').click();
assert.equal(await page.locator('.series-3').count(),1);
assert.match(await page.locator('.prediction-stage>.context-note').innerText(),/annual mean, not the size of one fire/);
await page.locator('#details').click();
assert.equal(await page.locator('#notes').evaluate(e=>e.open),true);
await page.keyboard.press('Escape');
await page.locator('#scene').focus();
await page.keyboard.press('Home');
assert.equal(await page.evaluate(()=>demo.state.section),0);
await page.keyboard.press('ArrowRight');
assert.equal(await page.evaluate(()=>demo.state.section),1);
for(const [width,height] of [[1440,900],[1280,800],[390,844]]){
  await page.setViewportSize({width,height});
  for(let i=0;i<5;i++){
    await page.evaluate(i=>demo.show(i),i);
    await page.waitForTimeout(650);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Horizontal overflow: ${width}, section ${i}`);
    await page.screenshot({path:path.join(out,`${width}-section-${i+1}.png`),fullPage:true,animations:'disabled'});
  }
}
await page.emulateMedia({reducedMotion:'reduce'});
await page.evaluate(()=>demo.show(0));
assert.equal(await page.locator('.province-map').evaluate(e=>getComputedStyle(e).animationName),'none');
await page.goto('http://127.0.0.1:8790/web/demo/lab.html#kernel');
await page.waitForFunction(()=>window.demo);
assert.equal(await page.evaluate(()=>demo.state.section),3);
for(const route of ['/.env','/docs/results/annual-final.json','/web/demo/data.py','/web/demo/%2e%2e/%2e%2e/.env'])assert.equal((await page.request.get('http://127.0.0.1:8790'+route)).status(),404);
assert.ok(requests.every(r=>r.method==='GET'),'Demo must not submit requests');
assert.ok(requests.every(r=>new URL(r.url).origin==='http://127.0.0.1:8790'),'No third-party request');
assert.deepEqual(errors,[]);
await fs.writeFile(path.join(out,'checks.json'),JSON.stringify({status:'passed',source_hashes:true,feasible_objectives:210,saved_scales:10,year_values:6,custom_pointer_slider:true,keyboard_slider:true,independent_sections:5,viewports:[1440,1280,390],reduced_motion:true,read_only_requests:true,private_routes_denied:true,page_errors:errors},null,2));
await browser.close();
console.log('Guided demo source, objective, controls, saved results and viewport checks passed.');
