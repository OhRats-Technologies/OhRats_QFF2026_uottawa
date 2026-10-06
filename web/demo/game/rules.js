// Arcade rules. Rewards and collisions are fictional; subset costs come from saved evidence.
export const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export const stages=['COLLECT / FEATURE SUBSETS','ENCODE / PHASES','COMPARE / SIMILARITY'];
export function random(seed) {
  let n=seed>>>0;
  return ()=>{n=(1664525*n+1013904223)>>>0;return n/4294967296;};
}
export function createRun(mode,basis,seed=2026) {
  return {mode,basis,random:random(seed),status:'playing',time:0,duration:55,x:0,target:0,
    integrity:100,count:0,charge:0,invulnerable:0,entities:[],candidates:[],
    nextWave:0.4,wave:0,stage:0,projected:null,pulseAt:-100,events:[]};
}
export function bestSample(candidates) {
  return candidates.reduce((best,c)=>!best||c.energy<best.energy?c:best,null);
}
export function project(run) {
  if(run.status!=='playing'||run.charge<100)return null;
  const best=bestSample(run.candidates);
  run.projected=best;run.charge=0;run.invulnerable=2.5;run.pulseAt=run.time;
  for(const e of run.entities)if(e.kind==='noise'&&e.z>-55)e.removed=true;
  run.events.push({kind:'project',best});return best;
}
export function step(run,dt,direction=0) {
  if(run.status!=='playing')return [];
  run.events=[];dt=clamp(dt,0,.05);run.time+=dt;
  run.invulnerable=Math.max(0,run.invulnerable-dt);
  if(direction)run.target=clamp(run.target+direction*dt*13,-6,6);
  run.x+=(run.target-run.x)*(1-Math.exp(-dt*12));
  run.stage=Math.min(2,Math.floor(run.time/18));
  if(run.time>=run.nextWave&&run.time<run.duration-4){
    const lane=Math.floor(run.random()*3),lanes=[-4.3,0,4.3];
    run.entities.push({id:run.wave*3,x:lanes[lane],z:-90,kind:'packet',
      candidate:run.basis[run.wave%run.basis.length]});
    const other=(lane+1+(run.random()>.5?1:0))%3;
    run.entities.push({id:run.wave*3+1,x:lanes[other],z:-90,kind:'noise'});
    if(run.stage===2)run.entities.push({id:run.wave*3+2,x:lanes[3-lane-other],z:-90,kind:'noise'});
    run.wave++;run.nextWave+=run.mode==='practice'?1.55:1.22;
  }
  const speed=(19+run.time*.07)*(run.mode==='practice'?.75:1);
  for(const e of run.entities){
    const previousZ=e.z;
    e.z+=speed*dt;
    const radius=run.mode==='practice'?1.65:1.2;
    if(!e.removed&&previousZ<5&&e.z>=5&&Math.abs(e.x-run.x)<radius){
      e.removed=true;
      if(e.kind==='packet'){
        run.count++;run.candidates.push(e.candidate);run.charge=Math.min(100,run.charge+25);
        run.events.push({kind:'collect',x:e.x,z:e.z,candidate:e.candidate});
      }else if(run.invulnerable===0){
        run.integrity=Math.max(0,run.integrity-(run.mode==='practice'?0:34));
        run.invulnerable=1.3;run.events.push({kind:'hit',x:e.x,z:e.z});
      }
    }
  }
  run.entities=run.entities.filter(e=>!e.removed&&e.z<12);
  if(run.integrity===0)run.status='lost';
  else if(run.mode!=='practice'&&run.time>=run.duration)run.status=run.count>=12?'won':'lost';
  if(run.mode==='practice'&&run.count>=12)run.status='won';
  if(run.mode==='practice'&&run.time>=run.duration&&run.count<12)run.duration+=20;
  return run.events;
}
