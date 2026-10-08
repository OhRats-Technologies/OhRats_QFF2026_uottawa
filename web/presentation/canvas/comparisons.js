import {color,split,bars} from './ui.js';

export function development(p,l,e,a,s) {
  const [left,right]=split(l.box,l.mobile,.48,l.gap);
  const b=p.panel(left,'SAME INPUTS · SAME REGRESSION SOLVER');
  const names=['Annual temperature','Summer temperature','Annual precipitation','Summer precipitation'];
  const step=Math.min(50,(b.h-145)/4);
  names.forEach((name,i)=>{
    const y=b.y+i*step;
    p.rect(b.x,y,b.w,step-9,'#0c292c');
    p.circle(b.x+14,y+(step-9)/2,4,color.amber);
    p.fit(name,b.x+30,y+(step-9)/2,b.w-45,19);
  });
  const y=b.y+4*step+18, w=(b.w-16)/2;
  [['RBF','Distances',color.blue],['Quantum','State overlaps',color.amber]].forEach(([name,sub,tint],i)=>{
    const x=b.x+i*(w+16);
    p.rect(x,y,w,66,'#071f23');
    p.fit(name,x+w/2,y+20,w-16,23,tint,'center');
    p.fit(sub,x+w/2,y+46,w-16,15,color.dim,'center');
    p.line([[x+w/2,y+72],[x+w/2,y+94]],tint,3);
  });
  p.fit('Classical SVR optimizer',b.x+b.w/2,y+122,b.w,23,color.mint,'center');
  const r=p.panel(right,'CHRONOLOGICAL DEVELOPMENT');
  p.fit('Average prediction error · ha/fire',r.x,r.y+12,r.w,20,color.dim);
  const rows=[{label:'Classical RBF',value:e.development.matched_rbf_svr_4.mae,color:color.blue},
    {label:'Quantum QSVR',value:e.development.matched_fidelity_svr_4.mae,color:color.amber},
    {label:'Training-average guess',value:e.development.training_mean.mae,color:color.dim}];
  bars(p,rows,{x:r.x,y:r.y+68,w:r.w,h:Math.min(294,r.h-110)},110,s.progress);
  p.wrap('RBF has lower average validation error.',r.x,r.y+r.h-52,r.w,l.mobile?18:24,color.mint);
  p.receipt.development=rows;
}

function yearChart(p,box,mean,q,rbf,s,on,mobile) {
  const left=box.x+(mobile?28:44), top=box.y+42;
  const width=box.w-(mobile?38:56), height=box.h-98, max=750;
  const base=top+height, step=width/6, bw=Math.min(24,step*.19);
  [0,250,500,750].forEach(value=>{
    const y=base-height*value/max;
    p.line([[left,y],[left+width,y]],'#709d882a');
    p.text(value,left-10,y,mobile?11:14,color.dim,'right');
  });
  const by=base-height*mean.prediction_ha/max;
  p.c.setLineDash([6,5]);
  p.line([[left,by],[left+width,by]],color.dim,2);
  p.c.setLineDash([]);
  mean.actual_ha.forEach((v,i)=>{
    const x=left+step*(i+.5);
    if(s.year===i) p.rect(x-step/2+2,top-14,step-4,height+14,'#aed6b609');
    [[v,-1.5,color.amber],[q.predicted_ha[i],-.5,color.mint],[rbf.predicted_ha[i],.5,color.blue]].forEach(([value,offset,tint])=>{
      const h=height*value/max*s.progress;
      p.rect(x+offset*bw,base-h,bw-2,h,tint);
    });
    p.text(Math.round(v),x-bw-.5,base-height*v/max-14,mobile?13:18,color.amber,'center');
    p.button(`year-${i}`,String(mean.years[i]),x-step*.43,base+18,step*.86,28,()=>on('year',i),{active:s.year===i});
  });
  return {actual:mean.actual_ha,quantum:q.predicted_ha,rbf:rbf.predicted_ha,baseline:mean.prediction_ha,years:mean.years};
}

export function evaluation(p,l,e,a,s,on) {
  const [left,right]=split(l.box,l.mobile,.68,l.gap);
  const b=p.panel(left,'ANNUAL AVERAGE HECTARES PER REPORTED FIRE');
  const mean=e.final.find(r=>r.id==='training_mean');
  const q=e.final.find(r=>r.id==='matched_fidelity_svr_4');
  const rbf=e.final.find(r=>r.id==='matched_rbf_svr_4');
  const legend=[['Observed',color.amber],['QSVR',color.mint],['RBF',color.blue]];
  legend.forEach(([label,tint],i)=>{
    const x=b.x+i*(l.mobile?94:114);
    p.rect(x,b.y+3,10,10,tint); p.text(label,x+17,b.y+8,l.mobile?14:17,tint);
  });
  p.receipt.evaluation=yearChart(p,{x:b.x,y:b.y+10,w:b.w,h:b.h-80},mean,q,rbf,s,on,l.mobile);
  p.fit(`${mean.years[s.year]} · QSVR ${q.predicted_ha[s.year].toFixed(1)} · RBF ${rbf.predicted_ha[s.year].toFixed(1)} ha/fire`,b.x,b.y+b.h-40,b.w,16,color.mint);
  p.fit(`Dashed line: training average = ${mean.prediction_ha.toFixed(1)} ha/fire`,b.x,b.y+b.h-8,b.w,16,color.dim);
  const r=p.panel(right,'HOW FAR OFF?');
  p.wrap('Average prediction error',r.x,r.y+10,r.w,l.mobile?24:26);
  p.fit('ha/fire · lower is better',r.x,r.y+76,r.w,18,color.dim);
  const rows=[['Training-average guess',mean,color.dim],['Quantum QSVR',q,color.amber],['Classical RBF',rbf,color.blue]];
  const dy=Math.min(110,(r.h-138)/3);
  rows.forEach(([label,row,tint],i)=>{
    const y=r.y+126+i*dy;
    p.fit(label,r.x,y,r.w,17,tint);
    p.fit(row.mae_ha.toFixed(1),r.x,y+36,r.w,40,tint);
  });
  p.receipt.errors=rows.map(([label,row])=>({label,mae:row.mae_ha}));
}
