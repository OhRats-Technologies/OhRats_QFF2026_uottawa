import {test,expect} from 'bun:test';
import {createRun,step,project,bestSample} from './rules.js';
const basis=[{indices:[0,1,2,3],energy:.1},{indices:[2,4,5,8],energy:-.2}];
function fly(run,policy,seconds=70){
  for(let i=0;i<seconds*60&&run.status==='playing';i++){
    run.target=policy(run);step(run,1/60);
  }
  return run;
}
test('seeded arcade route is playable, collectable and winnable',()=>{
  const r=fly(createRun('standard',basis),r=>r.entities.filter(e=>e.kind==='packet'&&e.z<5).sort((a,b)=>b.z-a.z)[0]?.x??r.target);
  expect(r.status).toBe('won');expect(r.count).toBeGreaterThanOrEqual(12);expect(r.integrity).toBeGreaterThan(0);
});
test('three unprotected noise hits lose; restart creates a clean state',()=>{
  const r=fly(createRun('standard',basis),r=>r.entities.filter(e=>e.kind==='noise'&&e.z<5).sort((a,b)=>b.z-a.z)[0]?.x??r.target);
  expect(r.status).toBe('lost');expect(r.integrity).toBe(0);expect(createRun('standard',basis).count).toBe(0);
});
test('practice extends time, never damages and can finish',()=>{
  const r=createRun('practice',basis);r.time=54.99;step(r,.02);expect(r.status).toBe('playing');expect(r.duration).toBe(75);
  const result=fly(createRun('practice',basis),r=>r.entities.filter(e=>e.kind==='packet'&&e.z<5).sort((a,b)=>b.z-a.z)[0]?.x??r.target);
  expect(result.status).toBe('won');expect(result.integrity).toBe(100);
});
test('SQD selects only the lowest collected cost; shield reward is independent',()=>{
  const r=createRun('standard',basis);expect(project(r)).toBeNull();
  r.candidates=[basis[0],basis[0]];r.charge=100;expect(project(r)).toEqual(basis[0]);
  expect(r.projected).not.toEqual(basis[1]);expect(r.invulnerable).toBe(2.5);
  r.candidates.push(basis[1]);r.charge=100;expect(project(r)).toEqual(bestSample(r.candidates));expect(r.charge).toBe(0);
});
test('paused physics does not advance, seed reproduces waves',()=>{
  const a=createRun('standard',basis),b=createRun('standard',basis);
  for(let i=0;i<200;i++){step(a,.02);step(b,.02);}expect(a.entities).toEqual(b.entities);
  const time=a.time;a.status='paused';step(a,.05,1);expect(a.time).toBe(time);
});
