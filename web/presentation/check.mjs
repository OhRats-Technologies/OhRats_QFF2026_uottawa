// Canvas viewing QA. Reads saved evidence; never fits models or accesses hardware.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const require=createRequire(`${process.env.RUNTIME_NODE_MODULES}/../package.json`);
const {chromium}=require('playwright');
const base=process.env.PRESENTATION_BASE||'http://127.0.0.1:8790';
const out=process.env.PRESENTATION_OUTPUT||'.cache/presentation-canvas/verified';
await fs.mkdir(out,{recursive:true});
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const preserved=await Promise.all(['evidence.json','assets/shot-sweep.json','slides/ontario-wildfire.pdf','slides/ontario-wildfire.pptx'].map(async file=>({file,sha:sha(await fs.readFile(`web/presentation/${file}`))})));
const browser=await chromium.launch({headless:true,channel:'chrome'});
const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const errors=[], failed=[], external=new Set();
page.on('pageerror',error=>errors.push(error.message));
page.on('response',response=>{if(response.status()>=400) failed.push(response.url());});
await page.route('**/*',route=>{
  if(new URL(route.request().url()).origin===base) return route.continue();
  external.add(new URL(route.request().url()).hostname);return route.abort();
});
const snapshot=()=>page.evaluate(()=>presentation.snapshot());
async function click(id) {
  const hit=await page.evaluate(id=>presentation.controls().find(h=>h.id===id),id);
  assert.ok(hit&&!hit.disabled,`Enabled control ${id}`);
  const scale=(await snapshot()).factor;
  await page.mouse.click((hit.x+hit.w/2)*scale,(hit.y+hit.h/2)*scale);
  await page.waitForTimeout(60);
}
function layoutCheck(s) {
  assert.equal(s.progress,1);
  assert.ok(s.labels.every(r=>Number.isFinite(r.x+r.y+r.w+r.h)),`${s.id}: finite layout`);
  const clipped=s.labels.filter(r=>r.text&&(r.x<11||r.x+r.w>s.width-11));
  assert.deepEqual(clipped,[],`${s.id}: horizontal text clipping`);
  const labels=s.labels.filter(r=>r.text&&r.h>=12&&(!r.clip||(r.y>=r.clip.y&&r.y+r.h<=r.clip.y+r.clip.h)));
  const collisions=[];
  for(let i=0;i<labels.length;i++) for(let j=i+1;j<labels.length;j++) {
    const a=labels[i],b=labels[j];
    if(a.x+a.w>b.x+2&&b.x+b.w>a.x+2&&a.y+a.h>b.y+2&&b.y+b.h>a.y+2)
      collisions.push([a.text,b.text]);
  }
  assert.deepEqual(collisions,[],`${s.id}: overlapping text`);
}
const result={renderer:'Canvas2D',slides:[],viewports:[],externalHosts:[],preserved,errors};
try {
  await page.goto(`${base}/web/presentation/`);
  await page.waitForFunction(()=>window.presentation);
  assert.equal(await page.locator('canvas').count(),1);
  assert.equal(await page.locator('.slide,dialog').count(),0);
  assert.equal(await page.evaluate(()=>presentation.slides.reduce((sum,s)=>sum+s.seconds,0)),300);
  assert.equal(await page.evaluate(()=>presentation.slides.length),9);
  const evidence=await page.evaluate(()=>presentation.evidence);
  const expectedIds=['question','data','selection','development','evaluation','geometry','conclusions','encoding','resources'];
  assert.deepEqual(await page.evaluate(()=>presentation.slides.map(s=>s.id)),expectedIds);
  for(const city of evidence.map.cities) assert.ok(city.inside_official_boundary&&city.inside_crop&&city.roundtrip_error_degrees<1e-9);
  const first=(await snapshot()).receipt.map;
  assert.ok(first.fullBoundary&&Math.abs(first.h/first.w-1200/1118)<1e-8);
  await page.keyboard.press('End');assert.equal(await page.evaluate(()=>presentation.index),6);
  await page.keyboard.press('o');await click('chapter-5');assert.equal((await snapshot()).id,'geometry');
  for(const scale of [32,16,8,4,2]) {
    await click(`scale-${scale}`);
    const got=(await snapshot()).receipt.geometry;
    const expected=evidence.geometry.find(r=>r.inputs===10&&r.amplitude_pi_denominator===scale);
    assert.equal(got.scale,scale);assert.equal(got.effectiveRank,expected.effective_rank);
    assert.equal(got.similarity,expected.off_diagonal_mean);assert.deepEqual(got.matrix,expected.matrix);
  }
  await page.evaluate(()=>presentation.show(1));
  for(const stage of ['records','annual','forest']) {
    await click(`map-${stage}`);assert.equal((await snapshot()).dataStage,stage);
  }
  await page.evaluate(()=>presentation.show(4));
  const chart=(await snapshot()).receipt.evaluation;
  const mean=evidence.final.find(r=>r.id==='training_mean');
  assert.deepEqual(chart.actual,mean.actual_ha);assert.deepEqual(chart.years,mean.years);
  assert.equal(chart.baseline,mean.prediction_ha);
  assert.deepEqual(chart.quantum,evidence.final.find(r=>r.id==='matched_fidelity_svr_4').predicted_ha);
  assert.deepEqual(chart.rbf,evidence.final.find(r=>r.id==='matched_rbf_svr_4').predicted_ha);
  await click('year-2');assert.ok((await snapshot()).labels.some(r=>r.text.includes('2021 · QSVR')));
  await page.evaluate(()=>presentation.show(8));
  assert.deepEqual((await snapshot()).receipt.hardware.rows,evidence.shot_sweep.rows);
  await page.setViewportSize({width:390,height:844});
  await page.keyboard.press('n');assert.equal((await snapshot()).panel,'notes');
  await page.mouse.wheel(0,900);await page.waitForTimeout(60);assert.ok((await snapshot()).receipt.noteScrollMax>0);
  await page.screenshot({path:path.join(out,'mobile-notes.png')});
  await click('close');assert.equal((await snapshot()).panel,'');
  await page.keyboard.press('Home');assert.equal(await page.evaluate(()=>presentation.index),0);
  await page.keyboard.press('ArrowRight');assert.equal(await page.evaluate(()=>presentation.index),1);
  await page.goto(`${base}/web/presentation/#selection`);await page.waitForFunction(()=>window.presentation);
  assert.equal((await snapshot()).id,'selection');
  for(const viewport of [{width:1440,height:900},{width:1920,height:1080},{width:1024,height:640},{width:900,height:600},{width:390,height:844}]) {
    await page.setViewportSize(viewport);await page.waitForTimeout(60);
    for(let index=0;index<9;index++) {
      await page.evaluate(index=>presentation.show(index),index);await page.waitForTimeout(40);
      const s=await snapshot();layoutCheck(s);
      const controls=await page.evaluate(()=>presentation.controls());
      const footer=controls.filter(h=>['previous','next','guide','notes','overview','fullscreen'].includes(h.id));
      for(let i=0;i<footer.length;i++) for(let j=i+1;j<footer.length;j++) {
        const a=footer[i],b=footer[j];
        assert.ok(a.x+a.w<=b.x||b.x+b.w<=a.x||a.y+a.h<=b.y||b.y+b.h<=a.y,`Footer controls overlap: ${a.id}/${b.id}`);
      }
      await page.screenshot({path:path.join(out,`${viewport.width}-${viewport.height}-${index+1}.png`)});
      if(s.maxScroll) {
        await page.mouse.wheel(0,1500);await page.waitForTimeout(50);
        assert.equal((await snapshot()).scroll,s.maxScroll);
        await page.screenshot({path:path.join(out,`${viewport.width}-${viewport.height}-${index+1}-lower.png`)});
      }
      if(viewport.width===1440) result.slides.push({id:s.id,labels:s.labels.map(r=>r.text)});
    }
    result.viewports.push(viewport);
  }
  await page.setViewportSize({width:1440,height:900});
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.evaluate(()=>presentation.show(4));await page.waitForTimeout(110);
  assert.ok((await snapshot()).progress<1,'Entrance animation runs');
  await page.waitForTimeout(700);assert.equal((await snapshot()).progress,1);
  await page.evaluate(()=>presentation.show(5));await click('scale-32');
  await page.waitForTimeout(500);assert.equal((await snapshot()).receipt.geometry.scale,32);
  await page.screenshot({path:path.join(out,'interactive-geometry.png')});
  for(const item of preserved) assert.equal(sha(await fs.readFile(`web/presentation/${item.file}`)),item.sha);
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
  for(const route of ['/.env','/.git/config','/web/demo/lab.html','/web/demo/field.html']) {
    assert.equal((await fetch(base+route)).status,404);
  }
  result.externalHosts=[...external];result.status='passed';result.checkedUtc=new Date().toISOString();
  result.scope='Browser layout, navigation, accessibility controls and saved evidence bindings; no scientific fits or hardware jobs.';
  await fs.writeFile(path.join(out,'receipt.json'),JSON.stringify(result,null,2)+'\n');
  console.log(`Canvas presentation passed: 9 slides, 5 viewports, controls, animations, source bindings and unchanged evidence/exports. Screenshots: ${out}`);
} finally {await browser.close();}
