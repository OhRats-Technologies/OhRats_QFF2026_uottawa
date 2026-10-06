import {sections,labels,initialState,fmt,angle} from './model.js';
import {views,explanation} from './views.js';

const scene=document.querySelector('#scene');
async function load(path) {
  const response=await fetch(path);
  if(!response.ok)throw new Error('Saved evidence could not be loaded.');
  return response.json();
}
const [evidence,data]=await Promise.all([load('../presentation/evidence.json'),load('data.json')]).catch(error=>{
  scene.innerHTML='<p>Saved evidence unavailable. Start the Bun server from the repository root, then reload.</p>';
  throw error;
});
const state=initialState();
const steps=document.querySelector('#steps');
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const notes=document.querySelector('#notes');
let phaseFrame=0;
steps.innerHTML=labels.map((label,i)=>`<button data-section="${i}" aria-label="${label}"><b>${i+1}</b><span>${label}</span></button>`).join('');

function render(focusSelector) {
  cancelAnimationFrame(phaseFrame);
  scene.innerHTML=views[state.section](evidence,data,state);
  scene.dataset.section=sections[state.section];
  steps.querySelectorAll('button').forEach((button,i)=>{
    if(i===state.section)button.setAttribute('aria-current','step');
    else button.removeAttribute('aria-current');
  });
  document.querySelector('#position').textContent=`${state.section+1} / 5`;
  document.querySelector('#previous').disabled=state.section===0;
  document.querySelector('#next').disabled=state.section===4;
  if(focusSelector)scene.querySelector(focusSelector)?.focus({preventScroll:true});
}
function show(index,update=true) {
  state.section=Math.max(0,Math.min(4,index));
  render();
  if(update)history.replaceState(null,'',`#${sections[state.section]}`);
  document.querySelector('#announce').textContent=labels[state.section];
  if(!reduced.matches)scene.animate([{opacity:.25,transform:'translateY(12px)'},{opacity:1,transform:'translateY(0)'}],{duration:500,easing:'cubic-bezier(.2,.8,.2,1)'});
  scrollTo({top:0,behavior:'instant'});
}
function drawPhases(z,denominator) {
  const visual=document.querySelector('#phase-visual');
  if(!visual)return;
  visual.querySelectorAll('[data-dial]').forEach((dial,i)=>{
    const x=100+i*160,y=135,theta=angle(z[i],denominator),phase=2*theta;
    dial.querySelector('.phase-arm').setAttribute('d',`M${x} ${y} L${x+62*Math.cos(phase)} ${y+23*Math.sin(phase)}`);
    dial.querySelector('.phase-tip').setAttribute('cx',x+62*Math.cos(phase));
    dial.querySelector('.phase-tip').setAttribute('cy',y+23*Math.sin(phase));
    dial.querySelector('.theta').textContent=`θ ${fmt(theta,2)}`;
  });
}
function updateInput(index,value) {
  state.z[index]=Math.round(Math.max(-3,Math.min(3,value))*100)/100;
  const slider=scene.querySelector(`[data-input="${index}"]`);
  slider.style.setProperty('--at',`${(state.z[index]+3)/6*100}%`);
  slider.setAttribute('aria-valuenow',state.z[index]);
  slider.setAttribute('aria-valuetext',`${fmt(state.z[index],2)} standard deviations`);
  document.querySelector(`#z-${index}`).innerHTML=`${fmt(state.z[index],2)} <small>z</small>`;
  drawPhases(state.z,state.denominator);
}
function changeAngle(next) {
  const previous=state.denominator;
  state.denominator=next;
  scene.querySelectorAll('[data-angle]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.angle)===next)));
  cancelAnimationFrame(phaseFrame);
  if(reduced.matches){drawPhases(state.z,next);return;}
  const began=performance.now();
  function tick(now) {
    const t=Math.min(1,(now-began)/600),ease=1-(1-t)**3;
    drawPhases(state.z,1/((1-ease)/previous+ease/next));
    if(t<1)phaseFrame=requestAnimationFrame(tick);
  }
  phaseFrame=requestAnimationFrame(tick);
}
steps.addEventListener('click',event=>{
  const button=event.target.closest('[data-section]');
  if(button)show(Number(button.dataset.section));
});
document.querySelector('#previous').onclick=()=>show(state.section-1);
document.querySelector('#next').onclick=()=>show(state.section+1);
document.querySelector('#details').onclick=()=>{
  document.querySelector('#note-content').innerHTML=explanation(state.section,data);
  notes.showModal();
};
document.querySelector('.close').onclick=()=>notes.close();
scene.addEventListener('click',event=>{
  const button=event.target.closest('button');
  if(button){
    const action=Object.keys(button.dataset)[0],value=button.dataset[action];
    if(action==='angle'){changeAngle(Number(value));return;}
    if(action==='year')state.year=Number(value);
    if(action==='map')state.map=value;
    if(action==='selector')state.selector=value;
    if(action==='sqd')state.sqdStage=Number(value);
    if(action==='width')state.width=Number(value);
    if(action==='scale')state.denominator=Number(value);
    if(action==='reveal')state.reveal=!state.reveal;
    render(`[data-${action}="${value}"]`);
    return;
  }
  const matrix=event.target.closest('#matrix');
  if(matrix){
    const bounds=matrix.getBoundingClientRect();
    state.pair=[Math.min(30,Math.floor((event.clientY-bounds.top)/bounds.height*31)),Math.min(30,Math.floor((event.clientX-bounds.left)/bounds.width*31))];
    render();
  }
});
scene.addEventListener('change',event=>{
  if(event.target.dataset.pair!==undefined){
    state.pair[Number(event.target.dataset.pair)]=Number(event.target.value);
    render(`[data-pair="${event.target.dataset.pair}"]`);
  }
});
scene.addEventListener('pointerdown',event=>{
  const slider=event.target.closest('[data-input]');
  if(!slider)return;
  cancelAnimationFrame(phaseFrame);
  slider.focus({preventScroll:true});
  slider.setPointerCapture(event.pointerId);
  const index=Number(slider.dataset.input);
  function move(e){
    const rect=slider.getBoundingClientRect();
    updateInput(index,(e.clientX-rect.left)/rect.width*6-3);
  }
  function finish(){
    slider.removeEventListener('pointermove',move);
    slider.removeEventListener('pointerup',finish);
    slider.removeEventListener('pointercancel',finish);
  }
  slider.addEventListener('pointermove',move);
  slider.addEventListener('pointerup',finish);
  slider.addEventListener('pointercancel',finish);
  move(event);
});
scene.addEventListener('keydown',event=>{
  const slider=event.target.closest('[data-input]');
  if(!slider)return;
  const increments={ArrowLeft:-.05,ArrowDown:-.05,ArrowRight:.05,ArrowUp:.05,PageDown:-.5,PageUp:.5};
  const index=Number(slider.dataset.input);
  let value=state.z[index];
  if(event.key in increments)value+=increments[event.key];
  else if(event.key==='Home')value=-3;
  else if(event.key==='End')value=3;
  else return;
  event.preventDefault();
  event.stopPropagation();
  cancelAnimationFrame(phaseFrame);
  updateInput(index,value);
});
addEventListener('keydown',event=>{
  if(notes.open||event.altKey||event.metaKey||event.ctrlKey)return;
  if(['BUTTON','A','SELECT'].includes(document.activeElement?.tagName))return;
  if(event.key==='ArrowRight'){event.preventDefault();show(state.section+1);}
  if(event.key==='ArrowLeft'){event.preventDefault();show(state.section-1);}
  if(event.key==='Home')show(0);
  if(event.key==='End')show(4);
  if(event.key.toLowerCase()==='n')document.querySelector('#details').click();
});
addEventListener('hashchange',()=>{
  const index=sections.indexOf(location.hash.slice(1));
  if(index>=0)show(index,false);
});
show(Math.max(0,sections.indexOf(location.hash.slice(1))),false);
window.demo={state,evidence,data,show,render};
