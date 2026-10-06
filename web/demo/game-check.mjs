// Own-app browser QA: real buttons/drag controls, accelerated browser clock, no scientific execution.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(path.join(process.env.RUNTIME_NODE_MODULES,'../package.json'));
const {chromium}=require('playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1280,height:720}});
const out=path.join(process.cwd(),'.cache/judge-submission/arcade-browser');await fs.mkdir(out,{recursive:true});
const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r));
await page.clock.install();await page.goto('http://127.0.0.1:8790/web/demo/');
await page.waitForFunction(()=>window.arcade?.ready);
assert.equal(await page.locator('#sound').getAttribute('aria-pressed'),'false');
await page.screenshot({path:path.join(out,'opening.png')});
await page.locator('#start').click();
await page.clock.runFor(300);
await page.keyboard.press('ArrowRight');
await page.locator('#pause').click();
const paused=await page.evaluate(()=>arcade.state.time);await page.clock.runFor(1000);
assert.equal(await page.evaluate(()=>arcade.state.time),paused);
await page.locator('#resume').click();await page.mouse.move(640,490);await page.mouse.down();
let projected=false,projectionChecked=false;
for(let i=0;i<550;i++){
  const state=await page.evaluate(()=>({status:arcade.state.status,charge:arcade.state.charge,entities:arcade.state.entities.map(e=>({kind:e.kind,x:e.x,z:e.z}))}));
  if(state.status!=='playing')break;
  const next=state.entities.filter(e=>e.kind==='packet'&&e.z<5).sort((a,b)=>b.z-a.z)[0];
  if(next)await page.mouse.move(1280*(.5+next.x/15),490);
  await page.clock.runFor(150);
  if(state.charge>=100&&!projected){
    await page.mouse.up();await page.locator('#pulse').click();projected=true;
    assert.equal(await page.locator('#projection').isVisible(),true);
    const data=await page.evaluate(()=>({best:arcade.state.projected,candidates:arcade.state.candidates}));
    assert.equal(data.best.energy,Math.min(...data.candidates.map(c=>c.energy)));
    assert.match(await page.locator('#projection').innerText(),/shield is a game reward/);
    await page.screenshot({path:path.join(out,'sqd.png')});projectionChecked=true;
    await page.locator('#world').focus();await page.mouse.move(640,490);await page.mouse.down();
  }
  if(i===100)await page.screenshot({path:path.join(out,'flight.png')});
  if(i===260)await page.screenshot({path:path.join(out,'similarity-flight.png')});
}
await page.mouse.up();
assert.equal(await page.evaluate(()=>arcade.state.status),'won');assert.equal(projectionChecked,true);
assert.match(await page.locator('#study').innerText(),/No main model beats the mean/);
await page.screenshot({path:path.join(out,'win.png')});
await page.reload();await page.waitForFunction(()=>arcade.ready);await page.locator('#start').click();
await page.mouse.move(640,490);await page.mouse.down();
for(let i=0;i<250;i++){
  const state=await page.evaluate(()=>({status:arcade.state.status,entities:arcade.state.entities.map(e=>({kind:e.kind,x:e.x,z:e.z}))}));
  if(state.status!=='playing')break;
  const next=state.entities.filter(e=>e.kind==='noise'&&e.z<5).sort((a,b)=>b.z-a.z)[0];
  if(next)await page.mouse.move(1280*(.5+next.x/15),490);
  await page.clock.runFor(150);
}
await page.mouse.up();assert.equal(await page.evaluate(()=>arcade.state.status),'lost');
assert.equal(await page.evaluate(()=>arcade.state.integrity),0);await page.screenshot({path:path.join(out,'loss.png')});
await page.locator('#retry').click();assert.equal(await page.evaluate(()=>arcade.state.count),0);
await page.locator('#pause').click();await page.locator('#sound').click();assert.equal(await page.evaluate(()=>arcade.soundEnabled),true);
await page.locator('#sound').click();assert.equal(await page.evaluate(()=>arcade.soundEnabled),false);
await page.setViewportSize({width:390,height:844});await page.reload();await page.waitForFunction(()=>arcade.ready);
assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
const mapBox=await page.locator('.intro-map').boundingBox();assert.equal(mapBox.x>=0&&mapBox.x+mapBox.width<=390,true,'Full mobile Ontario map fits horizontally');
await page.screenshot({path:path.join(out,'mobile-opening.png')});
await page.locator('#practice').click();await page.mouse.move(195,560);await page.mouse.down();await page.mouse.move(295,560);await page.clock.runFor(500);await page.mouse.up();
assert.equal(await page.evaluate(()=>arcade.state.x>2),true);
assert.equal(await page.evaluate(()=>Math.abs(arcade.playerScreen[0])<.9),true,'Mobile player stays in view');
await page.screenshot({path:path.join(out,'mobile-flight.png')});
await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await page.waitForFunction(()=>arcade.ready);
assert.equal(await page.evaluate(()=>arcade.reducedMotion),true);
for(const url of ['/.env','/web/demo/../../.env'])assert.equal((await page.request.get('http://127.0.0.1:8790'+url)).status(),404);
assert.equal(requests.every(r=>r.method()==='GET'),true);assert.equal(requests.every(r=>new URL(r.url()).hostname==='127.0.0.1'),true);
assert.deepEqual(errors,[]);
await fs.writeFile(path.join(out,'checks.json'),JSON.stringify({passed:true,standard_win:true,standard_loss:true,projection_minimum:true,pause:true,retry:true,sound_toggle:true,drag:true,portrait:390,reduced_motion:true,local_read_only:true,page_errors:errors},null,2));
await browser.close();console.log('Arcade browser playthrough, SQD minimum, win/loss/retry, drag/pause, audio toggle and mobile/reduced-motion checks passed.');
