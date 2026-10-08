import {Paint, color} from '../../demo/canvas/paint.js';
export {color};

export class DeckPaint extends Paint {
  constructor(ctx) { super(ctx); this.labels = []; this.receipt = {}; }
  text(s, x, y, size = 20, fill = color.mint, align = 'left') {
    s = String(s);
    super.text(s, x, y, size, fill, align);
    const width = this.c.measureText(s).width;
    this.labels.push({text:s, x:x-(align==='center'?width/2:align==='right'?width:0), y:y-size/2, w:width, h:size});
  }
  fit(s, x, y, width, size = 24, fill = color.mint, align = 'left') {
    this.c.font = `${size >= 22 ? 'bold ' : ''}${size}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
    this.text(s, x, y, Math.min(size, size*width/Math.max(1,this.c.measureText(s).width)), fill, align);
  }
  wrap(s, x, y, width, size = 22, fill = color.mint, leading = 1.4) {
    const lines = []; let line = '';
    this.c.font = `${size >= 22 ? 'bold ' : ''}${size}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
    for (const word of s.split(/\s+/)) {
      const next = line ? `${line} ${word}` : word;
      if (line && this.c.measureText(next).width > width) { lines.push(line); line = word; }
      else line = next;
    }
    if (line) lines.push(line);
    lines.forEach((item,i)=>this.text(item,x,y+i*size*leading,size,fill));
    return lines.length*size*leading;
  }
  button(id, label, x, y, w, h, action, options = {}) {
    const arrow = /[▶◀]/.test(label), backward = label.includes('◀');
    super.button(id, arrow ? (backward?'◀':'▶') : '', x,y,w,h,action,options);
    this.hits.at(-1).active = options.active;
    this.hits.at(-1).label = label.replace(/[▶◀]/g,'').trim() || (backward?'Previous slide':'Next slide');
    this.fit(label.replace(/[▶◀]/g,'').trim(), x+w/2+(backward?10:arrow?-10:0),y+h/2,w-(arrow?50:16),
      h>42?18:15, options.active||options.tone==='hot'?'#151c1c':color.mint,'center');
  }
  panel(box, title) {
    const {x,y,w,h}=box;
    this.frame(x,y,w,h);
    this.rect(x+24,y+20,w-48,36,'#0a2527');
    this.fit(title,x+36,y+38,w-72,18,color.mint);
    return {x:x+32,y:y+76,w:w-64,h:h-108};
  }
  arrow(x,y,w=42,t=0) {
    const offset = Math.sin(t*3)*3;
    this.line([[x,y],[x+w+offset,y]],color.copper,5);
    this.line([[x+w-9+offset,y-8],[x+w+offset,y],[x+w-9+offset,y+8]],color.amber,3);
  }
}

export function layout(w,h) {
  const mobile=w<760, x=mobile?18:42, gap=mobile?16:24;
  const height=mobile?Math.max(h,1180):Math.max(h,640);
  return {mobile,w,h,height,gap,box:{x,y:mobile?134:152,w:w-2*x,h:height-(mobile?228:248)}};
}

export function split(box,mobile,ratio=.5,gap=24) {
  const {x,y,w,h}=box;
  return mobile
    ? [{x,y,w,h:(h-gap)/2},{x,y:y+(h+gap)/2,w,h:(h-gap)/2}]
    : [{x,y,w:(w-gap)*ratio,h},{x:x+(w-gap)*ratio+gap,y,w:(w-gap)*(1-ratio),h}];
}

export function picture(p,image,box) {
  if(!image) return null;
  const scale=Math.min(box.w/image.width,box.h/image.height);
  const r={x:box.x+(box.w-image.width*scale)/2,y:box.y+(box.h-image.height*scale)/2,w:image.width*scale,h:image.height*scale};
  p.c.imageSmoothingEnabled=false;
  p.c.drawImage(image,r.x,r.y,r.w,r.h);
  return {...r,scale};
}

const matrixCache=new WeakMap();
export function matrix(p,values,box) {
  let image=matrixCache.get(values);
  if(!image) {
    image=document.createElement('canvas'); image.width=image.height=values.length*8;
    const ctx=image.getContext('2d');
    values.forEach((row,i)=>row.forEach((v,j)=>{
      ctx.fillStyle=`hsl(26 75% ${7+v*57}%)`;ctx.fillRect(j*8,i*8,7.7,7.7);
    }));
    matrixCache.set(values,image);
  }
  return picture(p,image,box);
}

export function metric(p,value,label,x,y,width,size=54,tone=color.amber) {
  p.fit(value,x,y,width,size,tone);
  p.fit(label,x,y+size*.7,width,18,color.dim);
}

export function bars(p,rows,box,max,progress=1) {
  const step=box.h/rows.length;
  rows.forEach((row,i)=>{
    const y=box.y+i*step;
    p.fit(row.label,box.x,y+12,box.w-100,18,row.color);
    p.text(row.value.toFixed(1),box.x+box.w,y+12,24,row.color,'right');
    p.rect(box.x,y+36,box.w,18,'#061e22');
    p.rect(box.x,y+36,box.w*row.value/max*progress,18,row.color);
  });
}

export function map(p,assets,e,box,points=true) {
  const r=picture(p,assets.cover,box);
  if(!r) return;
  if(points) for(const pt of e.map.points) {
    p.circle(r.x+pt.x*r.scale,r.y+pt.y*r.scale,pt.ha>=100?2.6:1.3,pt.ha>=100?'#ffb653aa':'#bf773b66');
  }
  p.receipt.map={...r,fullBoundary:true,points:points?e.map.points.length:0};
}
