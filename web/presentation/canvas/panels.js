import {color} from './ui.js';
import {beatrice} from '../../demo/canvas/beatrice.js';

export function plainNotes(slide) {
  const doc=new DOMParser().parseFromString(slide.notes,'text/html');
  return {text:doc.body.textContent.trim(),links:[...doc.querySelectorAll('a')].map(a=>({label:a.textContent,url:a.href}))};
}

export function overlay(p,l,s,slides,on) {
  if(!s.panel) return;
  p.rect(0,0,l.w,l.h,'#020e15dd');
  const mobile=l.w<760, box={x:mobile?16:l.w*.12,y:mobile?24:55,w:mobile?l.w-32:l.w*.76,h:l.h-(mobile?48:110)};
  const b=p.panel(box,s.panel==='index'?'CHAPTERS':s.panel==='guide'?'BETTY’S BRIEFING':'PRESENTER NOTES');
  p.button('close','Close',box.x+box.w-102,box.y+24,74,30,()=>on('panel',''));
  if(s.panel==='index') {
    const h=Math.min(48,(b.h-20)/9),dy=h+4;
    slides.forEach((slide,i)=>p.button(`chapter-${i}`,`${slide.backup?'A'+(i-6):String(i+1).padStart(2,'0')}  ${slide.title}`,b.x,b.y+i*dy,b.w,h,()=>on('show',i),{active:s.index===i}));
  } else if(s.panel==='notes') {
    const notes=plainNotes(slides[s.index]), sourceHeight=notes.links.length*40+24;
    p.c.save();
    p.c.beginPath();p.c.rect(b.x,b.y-10,b.w,b.h-sourceHeight);p.c.clip();
    const height=p.wrap(notes.text,b.x,b.y+10-s.noteScroll,b.w,mobile?16:21,color.mint,1.55);
    p.c.restore();
    p.receipt.noteScrollMax=Math.max(0,height-(b.h-sourceHeight-20));
    const top=b.y+b.h-sourceHeight+22;
    notes.links.forEach((link,i)=>p.button(`source-${i}`,link.label,b.x,top+i*40,b.w,32,()=>on('source',link.url)));
  } else {
    const size=Math.min(100,b.w/3);
    beatrice(p,b.x,b.y,size,s.reduced?0:s.time,{wave:1});
    p.wrap('Read the visual first. Open Notes for methods and sources.',b.x+size+20,b.y+16,b.w-size-20,mobile?18:25,color.amber);
    const lines=['Arrows or Space: change slide.','Click the map tabs and angle settings.','N: notes · O: chapters · F: fullscreen.'];
    lines.forEach((line,i)=>p.wrap(line,b.x,b.y+size+58+i*72,b.w,mobile?19:24));
  }
}
