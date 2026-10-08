import {color,split} from './ui.js';
import {beatrice} from '../../demo/canvas/beatrice.js';

export function conclusions(p,l,e,a,s,on) {
  const [left,right]=split(l.box,l.mobile,.61,l.gap);
  const b=p.panel(left,'THREE USEFUL LESSONS');
  const lines=[['01','Encoding is a design choice.','More qubits can isolate every year.'],
    ['02','Subset cost is a proxy.','Optimize it, then check prediction error.'],
    ['03','Useful shots matter.','Candidate yield is different from accuracy.']];
  const step=Math.min(170,b.h/3);
  lines.forEach(([number,head,body],i)=>{
    const y=b.y+i*step+12;
    p.text(number,b.x,y,28,color.copper);
    p.wrap(head,b.x+52,y,b.w-52,l.mobile?22:30,color.mint,1.25);
    p.wrap(body,b.x+52,y+(l.mobile?58:54),b.w-52,l.mobile?17:22,color.dim,1.3);
  });
  const r=p.panel(right,'EXPLORE THE WORKSHOP');
  const size=Math.min(r.w*.6,r.h*.31,170);
  beatrice(p,r.x+(r.w-size)/2,r.y+5,size,s.reduced?0:s.time,{wave:1});
  const y=r.y+size+38;
  const headline=p.wrap('Build. Compare. Learn.',r.x,y,r.w,l.mobile?23:29,color.amber);
  p.wrap('A diagnostic benchmark. No demonstrated quantum advantage.',r.x,y+headline+16,r.w,l.mobile?18:22,color.mint);
  p.button('game','Play Fireline ▶',r.x,r.y+r.h-50,r.w,46,()=>on('game'),{tone:'hot'});
}
