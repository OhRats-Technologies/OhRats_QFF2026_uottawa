import {color, split, matrix, metric} from './ui.js';
import {sphere} from '../../demo/canvas/instruments.js';

export function geometry(p,l,e,a,s,on) {
  const [left,right]=split(l.box,l.mobile,.58,l.gap);
  const b=p.panel(left,'10 QUBITS · 31 TRAINING YEARS');
  const row=e.geometry.find(r=>r.inputs===10&&r.amplitude_pi_denominator===s.scale);
  const prev=e.geometry.find(r=>r.inputs===10&&r.amplitude_pi_denominator===s.previousScale);
  const bounds={x:b.x,y:b.y,w:b.w,h:b.h-52};
  if(prev&&s.scaleBlend<1) matrix(p,prev.matrix,bounds);
  p.c.save(); p.c.globalAlpha=s.scaleBlend; const image=matrix(p,row.matrix,bounds);p.c.restore();
  p.fit('Different years',b.x,b.y+b.h-14,b.w/2,17,color.dim);
  p.fit('Same year = 1',b.x+b.w,b.y+b.h-14,b.w/2,17,color.amber,'right');
  const r=p.panel(right,'ANGLE SCALE SHAPES SIMILARITY');
  const radius=Math.min(r.w*.24,r.h*.15,90);
  sphere(p,r.x+r.w/2,r.y+radius+8,radius,2*Math.PI/s.scale,s.time,{x:Math.cos(2*Math.PI/s.scale),y:Math.sin(2*Math.PI/s.scale),z:0});
  p.fit('Single-qubit phase illustration',r.x+r.w/2,r.y+2*radius+35,r.w,15,color.dim,'center');
  const buttonY=r.y+2*radius+67, bw=(r.w-24)/5;
  [32,16,8,4,2].forEach((d,i)=>p.button(`scale-${d}`,`π/${d}`,r.x+i*(bw+6),buttonY,bw,40,()=>on('scale',d),{active:s.scale===d}));
  const y=buttonY+86;
  metric(p,row.effective_rank.toFixed(1),'effective rank / 31',r.x,y,r.w/2-8,l.mobile?34:44,color.mint);
  metric(p,row.off_diagonal_mean.toFixed(3),'mean similarity',r.x+r.w/2+8,y,r.w/2-8,l.mobile?34:44);
  p.wrap(s.scale<=8?'Wide angles isolate years.':'Narrow angles link seasons.',r.x,r.y+r.h-48,r.w,l.mobile?19:24,color.mint);
  p.receipt.geometry={scale:s.scale,effectiveRank:row.effective_rank,similarity:row.off_diagonal_mean,matrix:row.matrix,image};
}

export function encoding(p,l,e,a,s) {
  const [left,right]=split(l.box,l.mobile,.6,l.gap);
  const b=p.panel(left,'SHALLOW ZZ FEATURE MAP · SCHEMATIC');
  const top=b.y+26, dy=Math.min(77,(b.h-82)/4), wire=b.w-40;
  for(let i=0;i<4;i++) {
    const y=top+i*dy;
    p.text(`q${i}`,b.x,y,16,color.dim);
    p.line([[b.x+30,y],[b.x+b.w,y]],'#719d8977',2);
    const gate=(fraction,label,tint)=>{
      const x=b.x+30+wire*fraction, w=Math.min(78,wire*.25);
      p.rect(x-w/2,y-20,w,40,'#153c3d');
      p.line([[x-w/2,y-20],[x+w/2,y-20],[x+w/2,y+20],[x-w/2,y+20],[x-w/2,y-20]],tint);
      p.fit(label,x,y,w-6,17,tint,'center');
    };
    gate(.16,'H',color.mint);gate(.47,'P(2θ)',color.amber);
    if(i<3) {
      const x=b.x+30+wire*(.70+.075*(i%2));
      p.line([[x,y],[x,y+dy]],color.copper,3);
      p.circle(x,y,5,color.amber);p.circle(x,y+dy,5,color.amber);
      p.rect(x-14,y+dy/2-13,28,26,'#153c3d');p.text('ZZ',x,y+dy/2,14,color.amber,'center');
    }
    if(!s.reduced) p.circle(b.x+30+wire*((s.time*.15+i*.08)%1),y,3,color.mint);
  }
  p.fit('H: superposition     P: feature phase     ZZ: coupling',b.x,b.y+b.h-8,b.w,16,color.dim);
  const r=p.panel(right,'MEASUREMENTS BECOME SIMILARITIES');
  const lines=[['Standardize','Training-fold statistics'],['Bound the angle','θ = a tanh(z / 2)'],
    ['Compare quantum states','k(x,y) = |〈φ(x)|φ(y)〉|²'],['Predict a number','Kernel matrix + classical SVR']];
  const dy2=Math.min(120,r.h/4);
  lines.forEach(([label,value],i)=>{
    const y=r.y+i*dy2+10;
    p.fit(label,r.x,y,r.w,19,color.dim);
    p.fit(value,r.x,y+34,r.w,l.mobile?18:24,i===1||i===2?color.amber:color.mint);
    if(i<3) p.line([[r.x,y+64],[r.x+r.w,y+64]],'#5c86722a');
  });
  p.receipt.encoding={inputs:4,solver:'classical SVR',diagram:'schematic'};
}

function hardwarePlot(p,box,device,rows,progress,mobile) {
  const b=p.panel(box,device==='marrakesh'?'IBM MARRAKESH':'IBM QUEBEC');
  p.fit('Usable 4-of-20 selections · %',b.x,b.y+8,b.w,18,color.dim);
  const left=b.x+30,top=b.y+48,w=b.w-45,h=b.h-120;
  const px=i=>left+w*i/2, py=v=>top+h*(1-v/.2);
  for(const value of [0,.05,.10,.15,.2]) {
    const y=py(value);p.line([[left,y],[left+w,y]],'#709d882a');
    p.text(Math.round(value*100),left-8,y,12,color.dim,'right');
  }
  for(const [arm,tint] of [['raw',color.amber],['dd_twirl',color.blue]]) {
    const points=rows.filter(r=>r.device===device&&r.arm===arm).sort((a,b)=>a.shots-b.shots);
    p.line(points.map((r,i)=>[px(i),py(r.fraction*progress)]),tint,2);
    points.forEach((r,i)=>{
      const y0=py(r.wilson95[0]),y1=py(r.wilson95[1]),x=px(i);
      p.line([[x,y0],[x,y1]],tint,2);
      p.line([[x-5,y0],[x+5,y0]],tint,2);p.line([[x-5,y1],[x+5,y1]],tint,2);
      p.circle(x,py(r.fraction*progress),5,tint);
    });
  }
  [512,1024,2048].forEach((shot,i)=>p.text(shot.toLocaleString('en-CA'),px(i),top+h+22,14,color.mint,'center'));
  p.fit('shots per circuit',b.x+b.w/2,top+h+49,b.w,15,color.dim,'center');
  return rows.filter(r=>r.device===device);
}

export function resources(p,l,e,a,s) {
  const body={...l.box,h:l.box.h-(l.mobile?134:108)};
  const [left,right]=split(body,l.mobile,.5,l.gap);
  const sweep=e.shot_sweep;
  hardwarePlot(p,left,'marrakesh',sweep.rows,s.progress,l.mobile);
  hardwarePlot(p,right,'quebec',sweep.rows,s.progress,l.mobile);
  const y=l.box.y+l.box.h-(l.mobile?114:82), w=l.box.w;
  p.rect(l.box.x,y,w,2,'#6f9c8555');
  if(l.mobile) {
    p.text('12 jobs · 108 QPU seconds',l.box.x,y+26,17,color.amber);
    p.text('301,056 returned shots',l.box.x,y+54,17,color.mint);
    p.text('Raw / DD + twirling · 95% Wilson bars',l.box.x,y+88,14,color.dim);
  } else {
    p.text('12 real jobs',l.box.x,y+32,25,color.amber);
    p.text('108 QPU seconds',l.box.x+w*.29,y+32,25,color.amber);
    p.text('301,056 shots',l.box.x+w*.65,y+32,25,color.mint);
    p.text('Orange: raw   Blue: DD + twirling   Bars: 95% Wilson shot intervals',l.box.x,y+68,16,color.dim);
  }
  p.receipt.hardware={rows:sweep.rows,jobs:sweep.jobs,chargedSeconds:sweep.charged_seconds,shots:sweep.physical_shots};
}
