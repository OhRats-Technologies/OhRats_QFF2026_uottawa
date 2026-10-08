import {color, split, map, picture, metric, bars} from './ui.js';

export function question(p,l,e,a,s) {
  const [left,right]=split(l.box,l.mobile,.48,l.gap);
  const b=p.panel(left,'ONTARIO · ANNUAL WILDFIRE SIZE');
  let y=b.y+24;
  y+=p.wrap('Can quantum similarity beat classical prediction?',b.x,y,b.w,l.mobile?28:38,color.mint,1.28);
  metric(p,Math.round(e.annual_example.mean_reported_size_ha),'hectares per reported fire · 2021',b.x,y+62,b.w,l.mobile?66:86);
  p.wrap('Real records. Matched models. Measured limits.',b.x,b.y+b.h-46,b.w,l.mobile?19:24,color.dim);
  const r=p.panel(right,'THE COMPLETE ONTARIO MAP');
  map(p,a,e,{...r,h:r.h-26},true);
  p.fit('Land cover + recorded fire locations',r.x,r.y+r.h-2,r.w,16,color.dim);
  p.receipt.target='annual mean reported size';
}

function timeline(p,box,mobile) {
  const cells=37, gap=3, width=(box.w-(cells-1)*gap)/cells;
  for(let i=0;i<cells;i++) p.rect(box.x+i*(width+gap),box.y,width,24,i<31?'#76a18c':'#ce6733');
  if(mobile) {
    p.text('31 training · 1988–2018',box.x,box.y+48,16,color.mint);
    p.text('6 reused · 2019–2024',box.x,box.y+72,16,color.amber);
  } else {
    p.text('31 training years · 1988–2018',box.x,box.y+50,22,color.mint);
    p.text('6 reused years · 2019–2024',box.x+box.w,box.y+50,22,color.amber,'right');
  }
}

export function data(p,l,e,a,s,on) {
  const body={...l.box,h:l.box.h-108};
  const [left,right]=split(body,l.mobile,.49,l.gap);
  const b=p.panel(left,s.dataStage==='annual'?'ONE ANNUAL LABEL':'NRCan · FIRE + FOREST RECORDS');
  const labels=[['forest','Pixels'],['records','Fires'],['annual','Annual row']];
  const bw=(b.w-16)/3;
  labels.forEach(([id,label],i)=>p.button(`map-${id}`,label,b.x+i*(bw+8),b.y,bw,34,()=>on('dataStage',id),{active:s.dataStage===id}));
  const visual={x:b.x,y:b.y+51,w:b.w,h:b.h-105};
  p.screen(visual.x-5,visual.y-5,visual.w+10,visual.h+10);
  if(s.dataStage==='forest') {
    picture(p,a.forest,visual);
    p.fit('Annual land-cover pixels · 2021',b.x,b.y+b.h-18,b.w,16,color.dim);
  } else if(s.dataStage==='records') {
    map(p,a,e,visual,true);
    p.fit('Historical NFDB fire locations',b.x,b.y+b.h-18,b.w,16,color.dim);
  } else {
    const ex=e.annual_example;
    const cx=visual.x+visual.w/2;
    p.fit(`${Math.round(ex.total_observed_size_ha).toLocaleString('en-CA')} hectares`,cx,visual.y+visual.h*.21,visual.w-16,l.mobile?25:34,color.mint,'center');
    p.fit(`÷ ${ex.size_observed_incidents.toLocaleString('en-CA')} reported fires`,cx,visual.y+visual.h*.39,visual.w-16,l.mobile?20:25,color.dim,'center');
    p.fit(`${Math.round(ex.mean_reported_size_ha)} ha/fire`,cx,visual.y+visual.h*.68,visual.w-16,l.mobile?42:66,color.amber,'center');
    p.fit('Ontario · 2021',b.x,b.y+b.h-18,b.w,16,color.dim);
  }
  const r=p.panel(right,'ECCC · MONTHLY CLIMATE');
  const entries=[['Annual temperature','annual_mean_temp_c','°C'],['Summer temperature','summer_mean_temp_c','°C'],
    ['Annual precipitation','annual_precip_mm','mm'],['Summer precipitation','summer_precip_mm','mm']];
  const step=Math.min(78,(r.h-70)/4);
  entries.forEach(([label,key,unit],i)=>{
    const y=r.y+i*step+15;
    p.fit(label,r.x,y,r.w-110,18,color.dim);
    p.text(`${e.annual_example[key].toFixed(1)} ${unit}`,r.x+r.w,y,l.mobile?18:23,color.mint,'right');
    p.line([[r.x,y+25],[r.x+r.w,y+25]],'#5c867233');
  });
  p.wrap('Join by year. One row per Ontario season.',r.x,r.y+step*4+14,r.w,l.mobile?21:26,color.amber);
  timeline(p,{x:l.box.x+16,y:l.box.y+l.box.h-86,w:l.box.w-32},l.mobile);
  p.receipt.dataStage=s.dataStage;
  p.receipt.annualExample=e.annual_example;
}

export function selection(p,l,e,a,s,on) {
  const [left,right]=split(l.box,l.mobile,.49,l.gap);
  const b=p.panel(left,'QAOA SAMPLES · SQD SELECTS');
  p.wrap('Choose 4 signals from 10.',b.x,b.y+8,b.w,l.mobile?23:30);
  const dy=Math.min(78,(b.h-160)/3), top=b.y+64;
  const states=[[1,1,0,0,1,0,0,1,0,0],[0,1,0,1,0,0,1,0,0,1],[1,0,0,1,0,1,0,0,1,0]];
  const cw=b.w/10;
  states.forEach((bits,row)=>bits.forEach((bit,j)=>{
    const x=b.x+j*cw,y=top+row*dy;
    p.rect(x,y,cw-5,Math.min(38,dy-10),bit?color.copper:'#092529');
    if(bit) p.rect(x+3,y+3,cw-11,4,color.amber);
    if(row===1) p.line([[x,y+42],[x+cw-5,y+42]],color.mint,2);
  }));
  const y=top+3*dy+14;
  p.fit('Sampled candidates · schematic',b.x,y,b.w,16,color.dim);
  p.wrap('SQD picks the best sampled subset.',b.x,y+44,b.w,l.mobile?21:27,color.amber);
  const r=p.panel(right,'SEPARATE FEATURE-SELECTION TEST');
  p.fit('Prediction error · fixed ridge · ha/fire',r.x,r.y+10,r.w,19,color.dim);
  const rows=[{label:'Exact search',value:e.selectors.exact_same_qubo,color:color.mint},
    {label:'Uniform sampling',value:e.selectors.uniform_bitstring_budget,color:color.blue},
    {label:'QAOA + SQD',value:e.selectors.qaoa_same_qubo,color:color.amber}];
  bars(p,rows,{x:r.x,y:r.y+56,w:r.w,h:Math.min(300,r.h-110)},110,s.progress);
  p.wrap('Subset cost and prediction error can disagree.',r.x,r.y+r.h-54,r.w,l.mobile?18:23,color.dim);
  p.receipt.selection={rows,feasibleSubsets:210,diagonalSQD:true};
}
