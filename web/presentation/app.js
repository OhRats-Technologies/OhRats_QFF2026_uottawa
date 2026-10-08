import {makeSlides} from './slides.js';
import {DeckPaint,color,layout} from './canvas/ui.js';
import {question,data,selection} from './canvas/chapters.js';
import {development,evaluation} from './canvas/comparisons.js';
import {geometry,encoding,resources} from './canvas/diagnostics.js';
import {conclusions} from './canvas/ending.js';
import {overlay,plainNotes} from './canvas/panels.js';

const canvas=document.querySelector('#stage'), ctx=canvas.getContext('2d');
const [evidence,sweep]=await Promise.all(['evidence.json','assets/shot-sweep.json'].map(url=>fetch(url).then(r=>r.json())));
evidence.shot_sweep=sweep;
const slides=makeSlides(evidence);
const assets=Object.fromEntries(await Promise.all([['cover','assets/ontario-cover.png'],['forest','assets/algonquin-cover.png']].map(async([name,url])=>{
  const image=new Image();image.src=url;await image.decode();return [name,image];
})));
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const state={index:0,panel:'',dataStage:'forest',scale:4,previousScale:4,year:0,scroll:0,noteScroll:0,
  changed:performance.now(),scaleAt:performance.now(),reduced:reduced.matches};
const renderers={question,data,selection,development,evaluation,geometry,conclusions,encoding,resources};
let last, hits=[],width,height,factor=1,dpr,hover='',focus='',lastFrame=0;
const cleanLabel=label=>label.replace(/[▶◀]/g,'').trim();

function show(index) {
  state.index=Math.max(0,Math.min(slides.length-1,index));
  state.panel='';state.scroll=state.noteScroll=0;state.changed=performance.now();
  history.replaceState(null,'',`#${slides[state.index].id}`);
  const slide=slides[state.index], notes=plainNotes(slide);
  document.querySelector('#description').textContent=slide.title;
  document.querySelector('#announcement').textContent=`${slide.backup?'Appendix':'Slide'} ${state.index+1}. ${slide.title}`;
  document.querySelector('#accessible-notes').innerHTML=slide.notes;
  canvas.setAttribute('aria-label',`${slide.title}. ${notes.text}`);
  render();
}

function action(type,value) {
  if(type==='show') return show(value);
  if(type==='next') return show(state.index+1);
  if(type==='previous') return show(state.index-1);
  if(type==='game') return window.open('../demo/','_blank','noopener');
  if(type==='source') return window.open(value,'_blank','noopener');
  if(type==='fullscreen') {
    const request=document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
    request?.catch(()=>{});return;
  }
  if(type==='scale') {state.previousScale=state.scale;state.scale=value;state.scaleAt=performance.now();}
  else {state[type]=value;if(type==='panel') state.noteScroll=0;}
  render();
}

function resize() {
  factor=innerWidth<760?Math.min(1,innerWidth/390):Math.min(1,innerWidth/1280,innerHeight/800);
  width=innerWidth/factor;height=innerHeight/factor;
  dpr=Math.min(devicePixelRatio||1,2);
  canvas.width=Math.round(innerWidth*dpr);canvas.height=Math.round(innerHeight*dpr);
  render();
}

function chrome(p,l) {
  p.frame(8,8,l.w-16,l.h-16);
  p.text('FIRELINE / RESEARCH',l.mobile?26:42,35,l.mobile?12:16,color.copper);
  const slide=slides[state.index];
  p.fit(slide.backup?'APPENDIX':`${String(state.index+1).padStart(2,'0')} / 07`,l.w-(l.mobile?26:42),35,l.w*.3,14,color.dim,'right');
  p.wrap(slide.title,l.mobile?26:42,l.mobile?69:90,l.w-(l.mobile?52:84),l.mobile?26:Math.min(44,l.w/30),color.mint,1.14);
  const y=l.h-66,x=l.mobile?24:42, bh=38;
  p.rect(18,y-14,l.w-36,78,'#0b272bdc');
  p.line([[24,y-14],[l.w-24,y-14]],'#628e7966');
  p.button('previous','◀',x,y,52,bh,()=>action('previous'),{disabled:state.index===0});
  p.button('next','▶',x+62,y,52,bh,()=>action('next'),{disabled:state.index===8,tone:'hot'});
  if(!l.mobile) {
    p.text(slide.backup?'Questions & methods':`${slide.seconds}s · five-minute talk`,x+138,y+20,15,color.dim);
    p.button('guide','Betty',l.w-484,y,74,bh,()=>action('panel','guide'));
    p.button('fullscreen','Fullscreen',l.w-174,y,132,bh,()=>action('fullscreen'));
  }
  p.button('notes','Notes',l.mobile?l.w-222:l.w-398,y,l.mobile?84:96,bh,()=>action('panel','notes'));
  p.button('overview',l.mobile?'Index':'Chapters',l.mobile?l.w-126:l.w-290,y,l.mobile?100:104,bh,()=>action('panel','index'));
  const done=slides.slice(0,state.index).reduce((sum,item)=>sum+item.seconds,0)/300;
  p.rect(12,l.h-8,(l.w-24)*Math.min(1,done),3,color.copper);
}

function syncAccessible(p) {
  const nav=document.querySelector('#accessible-controls'), signature=p.hits.map(h=>`${h.id}:${h.disabled}:${h.active??''}`).join('|');
  if(nav.dataset.signature===signature) return;
  nav.dataset.signature=signature;nav.replaceChildren();
  for(const hit of p.hits) {
    const button=document.createElement('button');button.textContent=hit.label;button.disabled=hit.disabled;
    button.dataset.control=hit.id;
    if(hit.active!==undefined) button.setAttribute('aria-pressed',String(hit.active));
    button.addEventListener('click',()=>hits.find(h=>h.id===hit.id)?.action());
    button.addEventListener('focus',()=>{
      focus=hit.id;
      const current=hits.find(h=>h.id===hit.id);
      if(current?.clip) {
        if(current.y<current.clip.y) state.scroll+=current.y-current.clip.y-8;
        if(current.y+current.h>current.clip.y+current.clip.h) state.scroll+=current.y+current.h-current.clip.y-current.clip.h+8;
      }
      render();
    });
    button.addEventListener('blur',()=>{focus='';render();});
    nav.append(button);
  }
}

function render(now=performance.now()) {
  if(!width) return;
  const l=layout(width,height);
  state.reduced=reduced.matches;
  state.time=state.reduced?0:now/1000;
  state.progress=state.reduced?1:Math.min(1,Math.max(0,(now-state.changed)/650));
  state.progress=1-(1-state.progress)**3;
  state.scaleBlend=state.reduced?1:Math.min(1,Math.max(0,(now-state.scaleAt)/450));
  ctx.setTransform(dpr*factor,0,0,dpr*factor,0,0);
  ctx.clearRect(0,0,width,height);
  const p=new DeckPaint(ctx);p.hover=hover;p.focus=focus;
  chrome(p,l);
  const headerHits=p.hits.length, headerLabels=p.labels.length;
  const maxScroll=Math.max(0,l.height-l.h);
  state.scroll=Math.min(maxScroll,Math.max(0,state.scroll));
  ctx.save();ctx.beginPath();ctx.rect(18,l.box.y-12,l.w-36,l.h-l.box.y-68);ctx.clip();
  ctx.translate(0,-state.scroll+12*(1-state.progress));
  ctx.globalAlpha=state.progress;
  renderers[slides[state.index].id](p,l,evidence,assets,state,action);
  ctx.restore();
  const clip={x:18,y:l.box.y-12,w:l.w-36,h:l.h-l.box.y-68};
  p.hits.slice(headerHits).forEach(hit=>{hit.y-=state.scroll;hit.clip=clip;});
  p.labels.slice(headerLabels).forEach(label=>{label.y-=state.scroll;label.clip=clip;});
  if(maxScroll) {
    const track=l.h-l.box.y-94, thumb=Math.max(28,track*l.h/l.height);
    p.rect(l.w-18,l.box.y,3,track,'#173e40');
    p.rect(l.w-18,l.box.y+(track-thumb)*state.scroll/maxScroll,3,thumb,color.copper);
  }
  if(state.panel) {p.hits=[];p.labels=[];overlay(p,l,state,slides,action);}
  hits=p.hits;last={id:slides[state.index].id,width,height,factor,scroll:state.scroll,maxScroll,panel:state.panel,
    dataStage:state.dataStage,scale:state.scale,progress:state.progress,labels:p.labels,receipt:p.receipt};
  syncAccessible(p);
}

function location(event) {
  const box=canvas.getBoundingClientRect();
  return {x:(event.clientX-box.left)/factor,y:(event.clientY-box.top)/factor};
}
function hitAt(point) {
  return [...hits].reverse().find(h=>!h.disabled&&(!h.clip||(point.y>=h.clip.y&&point.y<=h.clip.y+h.clip.h))&&point.x>=h.x&&point.x<=h.x+h.w&&point.y>=h.y&&point.y<=h.y+h.h);
}
let down;
canvas.addEventListener('pointerdown',event=>{down=location(event);canvas.setPointerCapture(event.pointerId);});
canvas.addEventListener('pointerup',event=>{
  const pos=location(event),distance=down?Math.hypot(pos.x-down.x,pos.y-down.y):0;
  if(distance<12) hitAt(pos)?.action();
  else if(width<760&&!state.panel&&down) state.scroll+=down.y-pos.y;
  down=null;render();
});
canvas.addEventListener('pointermove',event=>{
  const hit=hitAt(location(event));hover=hit?.id||'';canvas.style.cursor=hit?'pointer':'default';
});
canvas.addEventListener('wheel',event=>{
  event.preventDefault();
  if(state.panel==='notes') state.noteScroll=Math.min(last.receipt.noteScrollMax||0,Math.max(0,state.noteScroll+event.deltaY/factor));
  else if(!state.panel) state.scroll+=event.deltaY/factor;
  render();
},{passive:false});
addEventListener('keydown',event=>{
  if(event.target instanceof HTMLButtonElement&&['Enter',' '].includes(event.key)) return;
  if(event.key==='Escape') action('panel','');
  else if(!state.panel&&['ArrowRight','ArrowDown',' ','PageDown'].includes(event.key)) {event.preventDefault();action('next');}
  else if(!state.panel&&['ArrowLeft','ArrowUp','PageUp'].includes(event.key)) {event.preventDefault();action('previous');}
  else if(event.key==='Home') show(0);
  else if(event.key==='End') show(6);
  else if(event.key.toLowerCase()==='n') action('panel',state.panel==='notes'?'':'notes');
  else if(event.key.toLowerCase()==='o') action('panel',state.panel==='index'?'':'index');
  else if(event.key.toLowerCase()==='b') action('panel',state.panel==='guide'?'':'guide');
  else if(event.key.toLowerCase()==='f') action('fullscreen');
});
addEventListener('resize',resize);
addEventListener('hashchange',()=>{const index=slides.findIndex(s=>`#${s.id}`===window.location.hash);if(index>=0) show(index);});
reduced.addEventListener('change',()=>render());
function loop(now) {
  if(now-lastFrame>32) {render(now);lastFrame=now;}
  requestAnimationFrame(loop);
}
window.presentation={slides,evidence,get index(){return state.index;},show,
  snapshot:()=>structuredClone(last),controls:()=>hits.map(({id,label,x,y,w,h,disabled})=>({id,label,x,y,w,h,disabled}))};
resize();
show(Math.max(0,slides.findIndex(s=>`#${s.id}`===window.location.hash)));
requestAnimationFrame(loop);
