import {World} from './world.js';
import {Sound} from './sound.js';
import {createRun,step,project,clamp,stages} from './rules.js';

const $=id=>document.getElementById(id),canvas=$('world');
const reduced=matchMedia('(prefers-reduced-motion:reduce)').matches;
const sound=new Sound();let world,run=null,last=performance.now(),clock=0,toastUntil=0;
const data=await (await fetch('data.json')).json();
const evidence=await (await fetch('../presentation/evidence.json')).json();
try { world=new World(canvas,reduced,evidence.geometry.find(r=>r.inputs===4&&r.amplitude_pi_denominator===4).matrix); }
catch(error){$('title').textContent='WebGL unavailable';$('start').hidden=true;$('practice').hidden=true;$('message').textContent='Use Inside QSVR for the accessible evidence walkthrough.';console.warn('WebGL unavailable');}
let keys=new Set(),dragging=false,lastStage=-1;
function announce(text){$('message').textContent=text;}
function start(mode='standard'){
  if(!world)return;
  run=createRun(mode,data.teaching_basis);world.reset();keys.clear();lastStage=-1;
  for(const id of ['intro','result','paused','projection'])$(id).hidden=true;
  for(const id of ['hud','bottom','pause'])$(id).hidden=false;
  $('steer-help').textContent='← → or drag';
  document.querySelector('.game-label').textContent=mode==='practice'?'Practice · no damage':'Arcade metaphor';canvas.focus();announce('Collect twelve mint packets. Avoid orange obstacles.');
}
function togglePause(){
  if(!run||!['playing','paused'].includes(run.status))return;
  const paused=run.status==='playing';run.status=paused?'paused':'playing';
  $('paused').hidden=!paused;keys.clear();announce(paused?'Paused':'Resumed');
  if(paused)$('resume').focus();else canvas.focus();
}
function pulse(){
  if(!run)return;const best=project(run);if(!best)return;
  hud();sound.play('project');toastUntil=clock+4.5;$('projection').hidden=false;
  const basis=[...new Map(run.candidates.map(c=>[c.indices.join(','),c])).values()].sort((a,b)=>a.energy-b.energy).slice(0,4);
  const size=basis.length;$('diagonal').style.gridTemplateColumns=`repeat(${size},1fr)`;
  $('diagonal').innerHTML=Array.from({length:size*size},(_,n)=>{
    const i=Math.floor(n/size),j=n%size,c=basis[i];
    return `<i class="${i===j?'diag':''} ${i===0&&j===0?'best':''}">${i===j&&c?c.energy.toFixed(3):'0'}</i>`;
  }).join('');
  $('minimum').textContent=`Kept [${best.indices.join(', ')}] · ${best.energy.toFixed(4)}`;
  announce('Projected the collected subset space. Lowest sampled cost selected.');
}
function finish(){
  $('result').hidden=false;for(const id of ['hud','bottom','pause','projection'])$(id).hidden=true;
  const won=run.status==='won';sound.play(run.status);
  $('result-kicker').textContent=run.mode==='practice'?'Practice flight':`${run.count} packets · ${run.integrity}% integrity`;
  $('result-title').textContent=won?'Signal delivered.':'Signal interrupted.';
  $('result-summary').textContent=won?'You brought the candidate packets through the pipeline.':'Catch the mint rings. Leave space around the orange cubes. Practice gives you wider catches and no damage.';
  const q=evidence.final.find(r=>r.id==='matched_fidelity_svr_4'),b=evidence.final.find(r=>r.id==='training_mean'),index=b.years.indexOf(2021);
  const rows=[['Recorded',b.actual_ha[index],'#f4ad7d'],['QSVR',q.predicted_ha[index],'#9df5d0'],['Training mean',b.predicted_ha[index],'#8da5ae']];
  $('study').innerHTML=`<p class="study-label">Saved study · Ontario 2021 · mean ha / recorded fire</p>${rows.map(([n,v,c])=>`<div class="study-row"><span>${n}</span><i style="width:${v/700*270}px;background:${c}"></i><b>${v.toFixed(1)}</b></div>`).join('')}<p class="study-note">The research missed the extremes. No main model beats the mean across six later years.<br>Your arcade score is separate from prediction quality.</p>`;
  announce(won?'Signal delivered':'Signal interrupted');$('retry').focus();
}
function hud(){
  $('counter').innerHTML=`${run.count} <small>/ 12</small>`;
  $('time').textContent=Math.max(0,Math.ceil(run.duration-run.time));
  $('integrity').setAttribute('aria-valuenow',run.integrity);$('integrity').firstElementChild.style.width=run.integrity+'%';
  $('charge').textContent=run.charge<100?run.charge+'%':'Space';$('pulse').disabled=run.charge<100;
  if(run.stage!==lastStage){lastStage=run.stage;$('stage').textContent=stages[run.stage];announce(stages[run.stage]);}
}
function frame(now){
  const dt=Math.min(.05,(now-last)/1000);last=now;clock+=dt;
  if(run?.status==='playing'){
    const direction=(keys.has('ArrowRight')||keys.has('d')?1:0)-(keys.has('ArrowLeft')||keys.has('a')?1:0);
    const events=step(run,dt,direction);
    for(const e of events){sound.play(e.kind);world.burst(e.x,e.z,e.kind);if(e.kind==='hit'){
      $('hit').classList.remove('flash');void $('hit').offsetWidth;$('hit').classList.add('flash');announce('Noise hit. Integrity '+run.integrity+' percent.');
    }}
    hud();if(['won','lost'].includes(run.status))finish();
  }
  if(clock>toastUntil)$('projection').hidden=true;
  world?.update(run,dt,clock);requestAnimationFrame(frame);
}
$('start').onclick=()=>start();$('practice').onclick=()=>start('practice');
$('retry').onclick=()=>start(run.mode);$('restart').onclick=()=>start(run.mode);
$('pause').onclick=togglePause;$('resume').onclick=togglePause;$('pulse').onclick=pulse;
$('sound').onclick=()=>{sound.enable(!sound.enabled);$('sound').textContent=sound.enabled?'Sound on':'Sound off';$('sound').setAttribute('aria-pressed',sound.enabled);if(sound.enabled)sound.play('collect');};
window.addEventListener('keydown',e=>{
  if(['ArrowLeft','ArrowRight','a','d'].includes(e.key)&&run?.status==='playing'){e.preventDefault();keys.add(e.key);}
  if(e.key==='Escape')togglePause();
  if(e.code==='Space'&&e.target===canvas&&run?.status==='playing'){e.preventDefault();if(!e.repeat)pulse();}
});
window.addEventListener('keyup',e=>keys.delete(e.key));window.addEventListener('blur',()=>{keys.clear();if(run?.status==='playing')togglePause();});
function steer(e){if(run?.status==='playing')run.target=clamp((e.clientX/innerWidth-.5)*15,-6,6);}
canvas.addEventListener('pointerdown',e=>{dragging=true;canvas.setPointerCapture(e.pointerId);steer(e);});
canvas.addEventListener('pointermove',e=>{if(dragging)steer(e);});
canvas.addEventListener('pointerup',()=>dragging=false);canvas.addEventListener('pointercancel',()=>dragging=false);
document.addEventListener('visibilitychange',()=>{if(document.hidden&&run?.status==='playing')togglePause();});
window.arcade={get state(){return run;},get ready(){return !!world;},get soundEnabled(){return sound.enabled;},get reducedMotion(){return reduced;},get playerScreen(){return world.player.position.clone().project(world.camera).toArray();}};
requestAnimationFrame(frame);
