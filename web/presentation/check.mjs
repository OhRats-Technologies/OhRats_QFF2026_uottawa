// Functional browser checks and ignored QA export; preserves published artifacts.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(path.join(process.env.RUNTIME_NODE_MODULES,'../package.json'));
const {chromium}=require('playwright');
const browser=await chromium.launch({headless:true,channel:'chrome'});
const root=process.cwd(),out=path.join(root,'.cache/judge-submission/browser');
await fs.mkdir(out,{recursive:true});
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const published=['ontario-wildfire.pdf','ontario-wildfire.pptx'];
const before=Object.fromEntries(await Promise.all(published.map(async name=>
  [name,hash(await fs.readFile(path.join(root,'web/presentation/slides',name)))])));
const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
const errors=[];page.on('pageerror',error=>errors.push(error.message));
const url='http://127.0.0.1:8790/web/presentation/';
await page.goto(url);await page.waitForFunction(()=>window.presentation);
assert.equal(await page.locator('.slide').count(),9);
assert.equal(await page.evaluate(()=>presentation.slides.reduce((sum,s)=>sum+s.seconds,0)),300);
await page.keyboard.press('ArrowRight');assert.equal(await page.evaluate(()=>presentation.index),1);
await page.keyboard.press('n');assert.equal(await page.locator('#panel').evaluate(e=>e.open),true);
assert.match(await page.locator('#panel-content').innerText(),/39,616/);
await page.keyboard.press('Escape');
assert.deepEqual(await page.evaluate(()=>presentation.slides.filter(s=>!s.backup).map(s=>s.id)),['question','data','selection','development','evaluation','geometry','conclusions']);
await page.evaluate(()=>presentation.show(1));
assert.match(await page.locator('#data').innerText(),/784,447/);
await page.evaluate(()=>presentation.show(2));
assert.match(await page.locator('#selection').innerText(),/SQD/);
assert.match(await page.locator('#selection').innerText(),/79.58/);
await page.evaluate(()=>presentation.show(1));
for(const stage of ['records','annual','forest']){
  await page.locator(`[data-map-stage="${stage}"]`).click();
  assert.equal(await page.locator('#data').getAttribute('data-stage'),stage);
  if(stage==='annual'){
    await page.waitForTimeout(900);
    assert.equal(await page.locator('.annual-row-preview').evaluate(e=>getComputedStyle(e).opacity),'1');
    const expected=await page.evaluate(()=>presentation.evidence.annual_example.annual_mean_temp_c.toFixed(1));
    assert.match(await page.locator('.annual-row-preview').innerText(),new RegExp(expected.replace('.','\\.')));
  }
}
assert.equal(await page.locator('.cover .fire-point').count()>1000,true);
const cities=await page.evaluate(()=>presentation.evidence.map.cities);
assert.deepEqual(cities.map(c=>c.name),['Toronto / GTA','Ottawa','Windsor','Thunder Bay']);
assert.equal(cities.every(c=>c.inside_official_boundary&&c.inside_crop&&c.roundtrip_error_degrees<1e-9),true);
assert.match(await page.locator('.cover .source-map img').getAttribute('alt'),/Toronto/);
await page.evaluate(()=>presentation.show(0));
assert.equal(await page.locator('.hero-map').evaluate(e=>{const b=e.getBoundingClientRect(),s=e.closest('.slide').getBoundingClientRect();return b.top>=s.top&&b.bottom<=s.bottom&&b.left>=s.left&&b.right<=s.right;}),true,'Full Ontario opening map fits slide');
assert.equal(await page.locator('#data img.forest-detail').evaluate(e=>e.complete&&e.naturalWidth>0),true);
await page.keyboard.press('End');
assert.equal(await page.evaluate(()=>presentation.index),6);
await page.keyboard.press('o');await page.locator('[data-jump="5"]').click();
assert.equal(await page.evaluate(()=>presentation.index),5);
let lastVectors=await page.locator(".state-arm path").evaluateAll(nodes=>nodes.map(n=>n.getAttribute("d")));
for(const d of [32,16,8,4,2]){
  await page.locator(`[data-scale="${d}"]`).click();
  assert.equal(await page.locator(`[data-scale="${d}"]`).getAttribute('aria-pressed'),'true');
  await page.waitForTimeout(1000);
  const vectors=await page.locator('.state-arm path').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('d')));
  assert.notDeepEqual(vectors,lastVectors);lastVectors=vectors;
  const expected=await page.evaluate(d=>presentation.evidence.geometry.find(r=>r.inputs===10&&r.amplitude_pi_denominator===d).effective_rank.toFixed(2),d);
  assert.match(await page.locator('.geometry-detail .stat').innerText(),new RegExp(expected.replace('.','\\.')));
}
await page.locator('[data-scale="4"]').click();
await page.evaluate(()=>presentation.show(4));
const bars=await page.locator('#evaluation .annual-bar').evaluateAll(nodes=>nodes.map(n=>({series:n.dataset.series,year:Number(n.dataset.year),value:Number(n.dataset.value)})));
assert.equal(bars.length,24);
const actual=await page.evaluate(()=>presentation.evidence.final.find(r=>r.id==='training_mean'));
assert.deepEqual(bars.filter(r=>r.series==='Recorded').map(r=>r.value),actual.actual_ha);
assert.deepEqual(bars.filter(r=>r.series==='Recorded').map(r=>r.year),actual.years);
assert.equal(await page.locator('#evaluation path.series').count(),0);
assert.match(await page.locator('#evaluation svg').getAttribute('aria-label'),/hectares per fire/);
await page.keyboard.press('Home');assert.equal(await page.evaluate(()=>presentation.index),0);
for(let i=0;i<9;i++){
  await page.evaluate(i=>presentation.show(i),i);
  await page.waitForTimeout(2500);
  await page.screenshot({path:path.join(out,`slide-${i+1}.png`),animations:'disabled'});
  const clipped=await page.locator('.slide:not([hidden])').evaluate(slide=>{
    const r=slide.getBoundingClientRect();
    return [...slide.querySelectorAll('h1,h2,p,table')].filter(e=>{
      const b=e.getBoundingClientRect();return b.bottom>r.bottom+1||b.right>r.right+1||b.left<r.left-1;
    }).map(e=>e.textContent.slice(0,60));
  });assert.deepEqual(clipped,[],`Slide ${i+1} clipped text`);
}
await page.emulateMedia({reducedMotion:'reduce'});await page.evaluate(()=>presentation.show(3));
assert.equal(await page.locator('.slide:not([hidden]) .draw').count(),0);
await page.evaluate(()=>presentation.show(4));
assert.equal(await page.locator('#evaluation .annual-bar').first().evaluate(e=>getComputedStyle(e).animationName),'none');
await page.emulateMedia({reducedMotion:'no-preference'});
await page.setViewportSize({width:390,height:844});await page.evaluate(()=>presentation.show(5));
await page.waitForTimeout(2500);
assert.equal(await page.locator('.slide:not([hidden])').count(),1);
assert.equal(await page.locator('.slide:not([hidden])').evaluate(e=>getComputedStyle(e).transform),'none');
assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
await page.screenshot({path:path.join(out,'mobile-geometry.png'),fullPage:true,animations:'disabled'});
for (const [index,name] of [[1,'data'],[2,'selection'],[4,'evaluation'],[7,'encoding'],[8,'resources']]) {
  await page.evaluate(i=>presentation.show(i),index);
  await page.waitForTimeout(2500);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.join(out,`mobile-${name}.png`),fullPage:true,animations:'disabled'});
}
await page.setViewportSize({width:1920,height:1080});await page.evaluate(()=>presentation.show(0));
await page.screenshot({path:path.join(out,'wide-cover.png'),animations:'disabled'});
const denied=await page.request.get('http://127.0.0.1:8790/.env');assert.equal(denied.status(),404);
const traversal=await page.request.get('http://127.0.0.1:8790/web/presentation/%2e%2e/%2e%2e/.env');assert.equal(traversal.status(),404);
await page.setViewportSize({width:1280,height:720});
await page.pdf({path:path.join(out,'qa-presentation.pdf'),preferCSSPageSize:true,printBackground:true});
const pdf=await fs.readFile(path.join(out,'qa-presentation.pdf'));
assert.equal((pdf.toString('latin1').match(/\/Type\s*\/Page\b/g)||[]).length,9,'PDF must contain nine pages, with no blank tail');
assert.deepEqual(errors,[]);
for(const name of published)
  assert.equal(hash(await fs.readFile(path.join(root,'web/presentation/slides',name))),before[name],name);
await fs.writeFile(path.join(out,'checks.json'),JSON.stringify({status:'passed',slides:9,main_seconds:300,keyboard:true,notes:true,index:true,measured_scales:5,reduced_motion:true,portrait_width:390,wide_width:1920,private_paths_denied:true,page_errors:errors,qa_pdf_exported:true,published_artifacts_sha256:before,published_artifacts_preserved:true},null,2));
await browser.close();console.log('Browser checks and cached QA PDF pass; published PDF/PPTX remain unchanged.');
