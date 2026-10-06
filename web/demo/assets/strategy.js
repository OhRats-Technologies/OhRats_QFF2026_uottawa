function rn(e){let t=e.rng|0;return t^=t<<13,t^=t>>>17,t^=t<<5,e.rng=t>>>0,e.rng/4294967296}var ps=(e,t=0,n=1)=>Math.min(n,Math.max(t,e));function ci(e,t){let n=[...e];for(let i=n.length-1;i>0;i--){let s=Math.floor(rn(t)*(i+1));[n[i],n[s]]=[n[s],n[i]]}return n}var uu=[{name:"Dry start",dry:0.62,wind:0.32,rain:0,detail:"Small ignitions. Crews take two turns to return."},{name:"Southwest wind",dry:0.68,wind:0.61,rain:0,detail:"Wind lifts pressure. Water drops act immediately."},{name:"Lightning line",dry:0.74,wind:0.48,rain:0,detail:"Two new fires. Keep a crew in reserve."},{name:"Patchy rain",dry:0.47,wind:0.27,rain:0.48,detail:"Rain slows growth; it does not guarantee containment."},{name:"Heat ridge",dry:0.86,wind:0.42,rain:0,detail:"Choose your first upgrade before the next front."},{name:"Smoke drift",dry:0.78,wind:0.67,rain:0,detail:"Crews dispatched now need three turns."},{name:"Dry lightning",dry:0.9,wind:0.71,rain:0,detail:"Three new ignitions. Watch rising fires, not just new ones."},{name:"Wind shift",dry:0.76,wind:0.81,rain:0,detail:"Strong growth. Supplies must last through the season."},{name:"Cool break",dry:0.48,wind:0.28,rain:0.35,detail:"Two new fires. Choose a second upgrade; relief is temporary."},{name:"Late heat",dry:0.83,wind:0.68,rain:0,detail:"Returning crews can change the balance."},{name:"Rain band",dry:0.3,wind:0.25,rain:0.75,detail:"Two last ignitions. Rain slows growth; keep crews available."},{name:"Season closes",dry:0.4,wind:0.29,rain:0.38,detail:"One last turn. Reserve supplies earn a small debrief bonus."}],du={0:3,2:2,4:2,6:3,8:2,10:2};function fl(e,t){let n={rng:e||1},i=ci(t,n),s=uu.map((o)=>({...o,dry:Math.min(1,Math.max(0,o.dry+(rn(n)-0.5)*0.12)),wind:Math.min(1,Math.max(0,o.wind+(rn(n)-0.5)*0.12))})),r=[],a=0;for(let[o,c]of Object.entries(du))for(let l=0;l<c;l++){let u=i[a%i.length],d=u.x<0.38?"Northwest":u.y<0.46?"Far north":"Central";r.push({id:a+1,name:`${d} ${String(a+1).padStart(2,"0")}`,spawn:Number(o),x:u.x,y:u.y,cover:u.cover,fuel:0.25+rn(n)*0.7,exposure:0.6+rn(n)*0.6,size:0.55+rn(n)*0.95,crew:0,dropTurn:-1,status:"waiting",history:[]}),a++}return{weather:s,incidents:r}}var zn=(e)=>e.incidents.filter((t)=>t.status==="burning"),fu=(e)=>zn(e).filter((t)=>t.crew>0).length,hi=(e)=>e.crewTotal-fu(e),pl=(e,t)=>0.12+0.22*t.dry+0.15*t.wind+0.18*e-0.28*t.rain,Er=(e,t)=>0.68*Math.pow(e,1.2)*t,ki=(e)=>e.status==="playing"&&!e.upgradePending;function Gi(e,t){let n=fl(e,t),i={seed:e,turn:0,status:"playing",integrity:100,supplies:18,crewTotal:2,crewPower:0.9,resupply:2,dropFactor:0.42,upgrades:[],upgradePending:!1,selected:1,contained:0,spent:0,drops:0,deployments:0,damage:0,log:[],history:[],...n};return ml(i),i}function ml(e){e.incidents.filter((t)=>t.spawn===e.turn).forEach((t)=>{t.status="burning",e.log.push({turn:e.turn,type:"ignition",text:t.name})})}function gl(e,t){let n=e.weather[e.turn],i=ps(t.size*(1+pl(t.fuel,n))-(t.crew?e.crewPower:0),0,9);return i<=0.16?0:i}function ui(e,t,n){if(!ki(e))return!1;let i=e.incidents.find((a)=>a.id===t);if(!i||i.status!=="burning")return!1;let r={crew:2,water:4}[n];if(r===void 0||e.supplies<r)return!1;if(n==="crew"&&(i.crew||hi(e)<=0))return!1;if(n==="water"&&i.dropTurn===e.turn)return!1;if(e.supplies-=r,e.spent+=r,n==="crew")i.crew=e.turn===5?3:2,e.deployments++;else if(n==="water")i.size*=e.dropFactor,i.dropTurn=e.turn,e.drops++,_l(e,i);return e.log.push({turn:e.turn,type:n,fire:t,text:i.name}),!0}function _l(e,t){if(t.size<=0.16&&t.status==="burning")t.size=0,t.status="contained",t.crew=0,e.contained++,e.log.push({turn:e.turn,type:"contained",fire:t.id,text:t.name})}function di(e){if(!ki(e))return!1;let t=e.weather[e.turn],n=0;for(let i of zn(e)){i.size=ps(i.size*(1+pl(i.fuel,t))-(i.crew?e.crewPower:0),0,9),_l(e,i);let s=Er(i.size,i.exposure);if(n+=s,i.history.push({turn:e.turn,size:i.size,damage:s}),i.crew>0)i.crew--}if(e.damage+=n,e.integrity=ps(100-e.damage,0,100),e.history.push({turn:e.turn,integrity:e.integrity,damage:n,supplies:e.supplies,burning:zn(e).length}),e.turn++,e.integrity<=40)e.status="lost";else if(e.turn>=12)e.status="won";if(e.status==="playing"){if(e.supplies=Math.min(26,e.supplies+e.resupply),ml(e),e.upgradePending=[4,8].includes(e.turn),!zn(e).some((i)=>i.id===e.selected))e.selected=zn(e)[0]?.id}else e.score=Math.round(e.integrity*10+e.contained*18+e.supplies*2),e.log.push({turn:e.turn,type:e.status,text:e.status==="won"?"Season held":"Season overwhelmed"});return!0}var Hi=[{id:"network",name:"Mutual aid",branch:"Response",description:"One additional crew for the rest of the season.",effect:(e)=>e.crewTotal++},{id:"training",name:"Crew training",branch:"Response",description:"Crew suppression: 0.90 → 1.15 pressure per turn.",effect:(e)=>e.crewPower=1.15},{id:"logistics",name:"Supply corridor",branch:"Logistics",description:"Resupply: 2 → 3 supply credits each turn.",effect:(e)=>e.resupply=3},{id:"precision",name:"Targeted drops",branch:"Logistics",description:"Water removes 70% instead of 58% of current pressure.",effect:(e)=>e.dropFactor=0.3}];function Tr(e){let t={rng:e.seed+e.turn*7919>>>0};return ci(Hi.filter((n)=>!e.upgrades.includes(n.id)),t).slice(0,3)}function ms(e,t){if(!e.upgradePending)return!1;let n=Tr(e).find((i)=>i.id===t);if(!n)return!1;return n.effect(e),e.upgrades.push(t),e.upgradePending=!1,e.log.push({turn:e.turn,type:"upgrade",text:n.name}),!0}function gs(e,t=!1){let n=e.status==="contained",i=e.crew?t?"Crew assigned · season ended":`Crew returns in ${e.crew} front${e.crew===1?"":"s"}`:"";return{glyph:n?"✓":String(e.id),badge:e.crew?t?"◇":String(e.crew):"",tooltip:`${e.name}
${n?"Contained":i||"Burning"}`,aria:`${e.name}, ${e.status}, pressure ${e.size.toFixed(1)}${i?`, ${i}`:""}`}}class Ar{constructor(e){this.onSelect=e,this.panel=document.createElement("dialog"),this.panel.id="nearby-fires",this.panel.setAttribute("aria-label","Nearby fires"),document.body.append(this.panel),window.addEventListener("resize",()=>this.close()),this.panel.addEventListener("close",()=>{this.opener?.removeAttribute("aria-expanded"),this.returnFocus?.focus({preventScroll:!0})}),this.panel.addEventListener("click",(t)=>{let n=this.panel.getBoundingClientRect();if(t.clientX<n.left||t.clientX>n.right||t.clientY<n.top||t.clientY>n.bottom)this.close()})}close(){if(this.panel.open)this.panel.close()}select(e,t,n,i){if(!e.detail)return this.onSelect(t);let s=n.incidents.filter((o)=>{let c=i.get(o.id);if(!c)return!1;let l=c.getBoundingClientRect();return o.id===t||Math.hypot(e.clientX-l.left-l.width/2,e.clientY-l.top-l.height/2)<=l.width/2}).sort((o,c)=>Number(o.status==="contained")-Number(c.status==="contained")||o.id-c.id);if(s.length<2)return this.onSelect(t);this.opener=this.returnFocus=i.get(t),this.opener.setAttribute("aria-expanded","true"),this.panel.replaceChildren();let r=document.createElement("div");r.className="nearby-heading",r.innerHTML='<span>Nearby fires</span><button aria-label="Close nearby fires">×</button>',r.querySelector("button").onclick=()=>this.close(),this.panel.append(r);for(let o of s){let c=document.createElement("button");c.dataset.pickFire=o.id,c.setAttribute("aria-pressed",o.id===n.selected);let l=document.createElement("b"),u=document.createElement("span");l.textContent=o.name,u.textContent=o.status==="contained"?"Contained":`${o.size.toFixed(1)} pressure${o.crew?" · crew assigned":""}`,c.append(l,u),c.onclick=()=>{this.returnFocus=i.get(o.id),this.close(),this.onSelect(o.id)},this.panel.append(c)}this.panel.showModal();let a=this.panel.getBoundingClientRect();this.panel.style.left=`${Math.max(8,Math.min(e.clientX+12,innerWidth-a.width-8))}px`,this.panel.style.top=`${Math.max(8,Math.min(e.clientY-a.height/2,innerHeight-a.height-8))}px`,this.panel.querySelector("[data-pick-fire]").focus({preventScroll:!0})}}class Cr{constructor(e,t){this.frame=document.querySelector("#map-frame"),this.markers=document.querySelector("#markers"),this.canvas=document.querySelector("#map-effects"),this.ctx=this.canvas.getContext("2d"),this.onSelect=t,this.picker=new Ar(t),this.buttons=new Map,this.effects=[],this.reduced=matchMedia("(prefers-reduced-motion: reduce)").matches,this.draw=this.draw.bind(this),document.addEventListener("visibilitychange",()=>{if(document.hidden)cancelAnimationFrame(this.pending),this.pending=null;else this.schedule()}),matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change",(n)=>{this.reduced=n.matches,this.effects=[],this.schedule()});for(let n of e.city_controls){let i=document.createElement("span");i.className="city",i.textContent=n.name,i.style.left=`${n.x/e.width*100}%`,i.style.top=`${n.y/e.height*100}%`,document.querySelector("#cities").append(i)}new ResizeObserver(()=>this.resize()).observe(this.frame),this.resize(),this.schedule()}resize(){let e=this.frame.parentElement.getBoundingClientRect(),t=Math.min(e.width,e.height*1118/1200);this.frame.style.width=`${t}px`,this.frame.style.height=`${t*1200/1118}px`;let n=this.frame.getBoundingClientRect();this.width=n.width,this.height=n.height;let i=Math.min(devicePixelRatio,2);this.canvas.width=Math.round(this.width*i),this.canvas.height=Math.round(this.height*i),this.ctx.setTransform(i,0,0,i,0,0),this.schedule()}reset(){this.picker.close(),this.buttons.clear(),this.markers.replaceChildren(),this.effects=[],this.schedule()}update(e){this.picker.close(),this.state=e;for(let t of e.incidents.filter((n)=>n.status!=="waiting")){let n=this.buttons.get(t.id);if(!n)n=document.createElement("button"),n.innerHTML='<span class="fire-number" aria-hidden="true"></span><span class="fire-crew" aria-hidden="true" hidden></span><span class="fire-name" aria-hidden="true"></span>',n.style.left=`${t.x*100}%`,n.style.top=`${t.y*100}%`,n.style.setProperty("--label-left",t.x<0.25?"0%":t.x>0.75?"100%":"50%"),n.style.setProperty("--label-shift",t.x<0.25?"0%":t.x>0.75?"-100%":"-50%"),n.onclick=(r)=>this.picker.select(r,t.id,this.state,this.buttons),n.dataset.fire=t.id,this.markers.append(n),this.buttons.set(t.id,n);n.className=`fire ${t.status}${e.selected===t.id?" selected":""}${t.crew?" has-crew":""}`;let i=gs(t,e.status!=="playing");n.querySelector(".fire-number").textContent=i.glyph,n.querySelector(".fire-name").textContent=i.tooltip;let s=n.querySelector(".fire-crew");s.textContent=i.badge,s.hidden=!i.badge,n.setAttribute("aria-label",i.aria),n.setAttribute("aria-pressed",e.selected===t.id),n.style.setProperty("--pressure",t.size)}this.schedule()}effect(e,t){if(this.reduced)return;this.effects.push({x:e.x,y:e.y,kind:t,time:performance.now()}),this.schedule()}schedule(){if(this.pending!=null||document.hidden)return;this.pending=requestAnimationFrame((e)=>{if(this.pending=null,!document.hidden)this.draw(e)})}draw(e){let t=this.ctx,n=this.width,i=this.height;if(t.clearRect(0,0,n,i),this.state)for(let s of this.state.incidents.filter((r)=>r.status==="burning")){let r=s.x*n,a=s.y*i,o=7+Math.min(s.size,5)*4,c=t.createRadialGradient(r,a,0,r,a,o*2.6);if(c.addColorStop(0,"#ee6e4435"),c.addColorStop(1,"#ee6e4400"),t.fillStyle=c,t.beginPath(),t.arc(r,a,o*2.6,0,Math.PI*2),t.fill(),!this.reduced){for(let l=0;l<6;l++){let u=(e*0.00022+l*0.19+s.id*0.1)%1;t.globalAlpha=(1-u)*0.65,t.fillStyle="#ffbd79",t.beginPath(),t.arc(r+Math.sin(l*8+s.id)*7+u*12,a-u*o*3,1.3*(1-u),0,Math.PI*2),t.fill()}t.globalAlpha=1}if(s.crew)t.strokeStyle="#a5e0ca88",t.lineWidth=1,t.setLineDash([3,4]),t.beginPath(),t.moveTo(r-23,a+23),t.lineTo(r-8,a+8),t.stroke(),t.setLineDash([]),t.fillStyle="#a5e0ca",t.fillRect(r-25,a+21,4,4)}this.effects=this.effects.filter((s)=>e-s.time<1400);for(let s of this.effects){let r=(e-s.time)/1400,a=s.x*n,o=s.y*i;if(t.strokeStyle=s.kind==="water"?`rgba(114,202,235,${1-r})`:`rgba(175,223,179,${1-r})`,t.lineWidth=2,t.beginPath(),t.arc(a,o,10+r*55,0,Math.PI*2),t.stroke(),s.kind==="water")t.fillStyle=`rgba(114,202,235,${(1-r)*0.18})`,t.beginPath(),t.arc(a,o,10+r*25,0,Math.PI*2),t.fill()}if(!this.reduced&&(this.effects.length||this.state?.incidents.some((s)=>s.status==="burning")))this.schedule()}}function xl(e){let t=e.incidents.map((s)=>({id:s.id,name:s.name,impact:s.history.reduce((r,a)=>r+a.damage,0)})),n=t.reduce((s,r)=>s+r.impact,0),i=e.history.reduce((s,r)=>!s||r.damage>s.damage?r:s,null);return{total:n,top:t.filter((s)=>s.impact>0).sort((s,r)=>r.impact-s.impact||s.id-r.id).slice(0,3).map((s)=>({...s,share:s.impact/n})),peak:i?{front:i.turn+1,impact:i.damage,weather:e.weather[i.turn].name}:null}}function vl(e){if(!e.total)return"<small>No pressure impact was recorded.</small>";return`<small id="impact-heading" title="Cumulative simulated damage before reserve is floored at zero.">Largest pressure impact · share of total</small>${e.top.map((n)=>`<div class="impact-row" data-impact-fire="${n.id}">
    <span>${n.name}</span><span>${n.impact.toFixed(1)} · ${(n.share*100).toFixed(0)}%</span>
    <i aria-hidden="true"><b style="width:${n.share*100}%"></b></i>
  </div>`).join("")}`}function yl(e){let t=(l)=>34+l/12*448,n=(l)=>12+(100-l)/100*76,s=[100,...e.history.map((l)=>l.integrity)].map((l,u)=>`${t(u)},${n(l)}`).join(" "),r=t(e.turn),a=n(e.integrity),o=Math.round(e.integrity),c=[0,4,8,12].map((l)=>`<text x="${t(l)}" y="108" text-anchor="middle">${l}</text>`).join("");return`<svg viewBox="0 0 500 130" role="img" aria-label="Reserve starts at 100 and ends at ${o} after ${e.turn} of 12 fronts. Loss limit: 40. Fictional game units.">
    <g fill="#8caaa5" font-size="11">
      <text x="0" y="16">100</text><text x="0" y="${n(40)+4}">40</text>
      ${c}<text x="258" y="126" text-anchor="middle">Weather front</text>
    </g>
    <line x1="34" y1="${n(40)}" x2="482" y2="${n(40)}" stroke="#b87e5b" stroke-dasharray="4 5"/>
    <text x="482" y="${n(40)-6}" text-anchor="end" fill="#b87e5b" font-size="10">Loss limit</text>
    <line x1="${r}" y1="12" x2="${r}" y2="90" stroke="#8caaa5" opacity=".2"/>
    <polyline points="${s}" fill="none" stroke="#a9d2ac" stroke-width="2"/>
    <circle data-season-end="${e.turn}" cx="${r}" cy="${a}" r="3" fill="#e9ede4"/>
    <text x="${r-7}" y="${a-8}" text-anchor="end" fill="#e9ede4" font-size="12">${o}</text>
  </svg>`}function Sl(e,t=null){let n=structuredClone(e);if(t&&!ui(n,n.selected,t))return null;if(!di(n))return null;return{reserve:n.integrity,loss:n.damage-e.damage,supplies:n.supplies,contained:n.contained-e.contained,status:n.status}}function Ml(e){if(!e)return"";let t=e.status==="lost"?" · line breaks":"";return`After this front: ${e.reserve.toFixed(1)} reserve · ${e.supplies} supplies${t}`}class Rr{constructor(e,t,n){this.container=e,this.onSelect=t,this.fallback=n,this.buttons=new Map}render(e,t,n=!1){let i=document.activeElement,s=this.container.contains(i),r=i.dataset.incident,a=new Set(e.map((o)=>o.id));for(let[o,c]of this.buttons)if(!a.has(o))c.remove(),this.buttons.delete(o);if(e.forEach((o,c)=>{let l=this.buttons.get(o.id);if(!l)l=document.createElement("button"),l.className="incident-chip",l.dataset.incident=o.id,l.onclick=()=>this.onSelect(o.id),this.buttons.set(o.id,l);if(l.textContent=`${o.name} · ${o.size.toFixed(1)}${o.crew?" ◇":""}`,l.setAttribute("aria-label",gs(o,n).aria),l.setAttribute("aria-pressed",t===o.id),this.container.children[c]!==l)this.container.insertBefore(l,this.container.children[c]??null)}),s)(this.buttons.get(Number(r))??this.buttons.get(t)??this.buttons.get(e[0]?.id)??this.fallback).focus({preventScroll:!0})}}function bl(e,t){if(e.status!=="playing")return{pressure:null,loss:null};if(t.status!=="burning")return{pressure:null,loss:0};let n=gl(e,t);return{pressure:n,loss:Er(n,t.exposure)}}var wl={network:"＋",training:"↑",logistics:"⇄",precision:"◉"},Ir=[4,8],Xt=(e)=>document.getElementById(e);class Pr{constructor(){Xt("upgrade-track").setAttribute("aria-label","Response upgrade milestones"),this.slots=Ir.map((e)=>{let t=document.createElement("button");return t.className="upgrade-token empty",t.dataset.milestone=e,t.onclick=()=>this.show(t),Xt("upgrade-track").append(t),t}),document.body.insertAdjacentHTML("beforeend",`
      <dialog id="progression" aria-labelledby="progression-title">
        <button id="progression-close" class="close" aria-label="Close upgrade ledger">×</button>
        <span class="eyebrow">Response / logistics</span><h2 id="progression-title">Your season build.</h2>
        <div id="progression-milestones"></div><div id="progression-effects"></div>
        <div id="progression-branches"></div>
        <p class="progression-boundary">Choose one of three offered upgrades after fronts 4 and 8.
          Effects last this season. This ledger only reviews choices; quantum instrument credits are separate.</p>
      </dialog>`),Xt("progression-close").onclick=()=>Xt("progression").close(),Xt("progression").addEventListener("close",()=>this.returnTarget?.focus()),Xt("guide-progress").onclick=()=>{Xt("guide").close(),this.show(Xt("guide-open"))}}render(e){this.state=e;for(let[t,n]of Ir.entries()){let i=Hi.find((r)=>r.id===e.upgrades[t]),s=i?i.name:e.status!=="playing"?"Not earned":e.turn>=n?"Choose an upgrade":`After front ${n}`;this.slots[t].textContent=i?wl[i.id]:n,this.slots[t].classList.toggle("empty",!i),this.slots[t].title=i?`${i.name}: ${i.description}`:s,this.slots[t].setAttribute("aria-label",`Front ${n}: ${s}. Open upgrade ledger.`)}Xt("progression-milestones").innerHTML=Ir.map((t,n)=>{let i=Hi.find((r)=>r.id===e.upgrades[n]),s=i?i.name:e.status!=="playing"?"Not earned":e.turn>=t?"Choice ready":`In ${t-e.turn} fronts`;return`<div class="progression-step ${i?"earned":""}"><span>Front ${t}</span><b>${s}</b></div>`}).join(""),Xt("progression-effects").innerHTML=[[e.crewTotal,"total crews","crews"],[e.crewPower.toFixed(2),"pressure / crew front","power"],[e.resupply,"supplies / front","supplies"],[Math.round((1-e.dropFactor)*100)+"%","pressure removed / drop","water"]].map(([t,n,i])=>`<div><strong data-build-effect="${i}">${t}</strong><span>${n}</span></div>`).join(""),Xt("progression-branches").innerHTML=["Response","Logistics"].map((t)=>`<section><h3>${t}</h3>${Hi.filter((n)=>n.branch===t).map((n)=>{let i=e.upgrades.includes(n.id);return`<div class="progression-node ${i?"earned":""}" data-build-upgrade="${n.id}">
          <span>${wl[n.id]}</span><div><b>${n.name}</b><small>${n.description}</small></div>
          <em>${i?"Equipped":"Not chosen"}</em></div>`}).join("")}</section>`).join("")}show(e){this.returnTarget=e,this.render(this.state),Xt("progression").showModal()}}function El(e,t){if(e.status!=="playing")return"Season finished. Inspect the map or open the season report.";if(!e.upgradePending&&e.turn===4)return"Heat lifts pressure. Keep crews moving as new fires arrive.";if(!e.upgradePending&&e.turn===8)return"Two new fires. Rain slows growth; relief is temporary.";return t.detail.replace(/\bturn(s)?\b/g,(n,i)=>`front${i??""}`)}var De=(e)=>document.getElementById(e),Vi=(e)=>e.toFixed(1),pu={210:"Coniferous cover",220:"Broadleaf cover",230:"Mixedwood cover"};class Lr{constructor(e,t){this.onSelect=e,this.onUpgrade=t,this.incidents=new Rr(De("incident-list"),e,De("advance")),this.progression=new Pr,De("upgrade").addEventListener("cancel",(n)=>n.preventDefault());for(let n of document.querySelectorAll("[data-action], #advance"))n.setAttribute("aria-describedby","action-feedback"),n.addEventListener("pointerenter",()=>this.preview(n.dataset.action)),n.addEventListener("focus",()=>this.preview(n.dataset.action)),n.addEventListener("pointerleave",()=>this.clearPreview()),n.addEventListener("blur",()=>this.clearPreview())}preview(e){if(!this.state)return;let t=Sl(this.state,e);De("action-feedback").textContent=t?Ml(t):this.feedback}clearPreview(){let e=document.activeElement;if(e.matches("[data-action], #advance"))this.preview(e.dataset.action);else De("action-feedback").textContent=this.feedback}render(e,t=""){this.state=e,this.feedback=t;let n=e.incidents.find((a)=>a.id===e.selected),i=e.status!=="playing",s=i?Math.max(0,e.turn-1):e.turn,r=e.weather[Math.min(s,11)];if(De("front-number").textContent=`${Math.min(s+1,12)} / 12`,De("front-name").textContent=r.name,De("front-detail").textContent=El(e,r),De("weather-meters").innerHTML=[["Dryness",r.dry],["Wind",r.wind],["Rain",r.rain]].map(([a,o])=>`<div class="weather-meter"><span>${a}<b>${Math.round(o*100)}%</b></span><i><b style="width:${o*100}%"></b></i></div>`).join(""),De("integrity").textContent=Math.round(e.integrity),De("integrity-bar").style.width=`${e.integrity}%`,De("integrity-bar").style.background=e.integrity<60?"var(--accent)":"var(--mint)",De("supplies").textContent=e.supplies,De("crews").textContent=`${hi(e)}/${e.crewTotal}`,De("contained").textContent=e.contained,De("crew-status").textContent=n?.crew?i?"Crew assigned":`Crew returns in ${n.crew} front${n.crew===1?"":"s"}`:"",De("advance").disabled=!i&&!ki(e),De("advance").querySelector("span").textContent=i?"Season report":e.turn===11?"Close season":"Advance front",De("incident-name").textContent=n?.name||"All clear for now",n){let{pressure:a,loss:o}=bl(e,n);De("incident-readout").innerHTML=`<div><strong>${Vi(n.size)}</strong>pressure</div><div><strong>${a===null?"—":Vi(a)}</strong>${i?"season ended":"after front"}</div><div><strong id="incident-risk">${o===null?"—":Vi(o)}</strong>reserve loss</div>`,De("incident-readout").title=`${pu[n.cover]}. Toy fuel ${Vi(n.fuel)}, exposure ${Vi(n.exposure)}. Reserve loss is this fire's projected contribution after the current front. These are fictional game units, not hectares.`,De("incident-readout").setAttribute("aria-description",De("incident-readout").title)}else De("incident-readout").textContent="Advance to the next weather front.",De("incident-readout").removeAttribute("title"),De("incident-readout").removeAttribute("aria-description");for(let a of document.querySelectorAll("[data-action]")){let o=a.dataset.action,c={crew:2,water:4}[o],l="";if(!ki(e))l="Choose an upgrade or begin a new season.";else if(!n||n.status!=="burning")l="Select an active fire.";else if(e.supplies<c)l="Not enough supplies.";else if(o==="crew"&&n.crew)l="A crew is already assigned.";else if(o==="crew"&&hi(e)===0)l="All crews are occupied. Advance a front to bring them back.";else if(o==="water"&&n.dropTurn===e.turn)l="One drop per fire per front.";a.disabled=!!l,a.title=l,a.querySelector("small").textContent=i?"":o==="crew"?`Suppression over ${e.turn===5?3:2} fronts`:"Reduce pressure immediately"}if(De("action-feedback").textContent=t,this.incidents.render(zn(e).sort((a,o)=>o.size-a.size),e.selected,i),this.progression.render(e),e.upgradePending&&!De("upgrade").open)this.showUpgrade(e);if(i&&this.lastStatus!==e.status&&!De("debrief").open)this.showDebrief(e);return this.lastStatus=e.status,n}showUpgrade(e){De("upgrade-options").replaceChildren();for(let t of Tr(e)){let n=document.createElement("button");n.dataset.upgrade=t.id,n.innerHTML=`<b>${t.name}</b><span>${t.branch}</span><small>${t.description}</small>`,n.onclick=()=>{this.onUpgrade(t.id),De("upgrade").close()},De("upgrade-options").append(n)}De("upgrade").showModal()}showDebrief(e){De("debrief-kicker").textContent=`Seed ${e.seed} / ${e.turn} fronts`,De("debrief-title").textContent=e.status==="won"?"The season held.":"The line broke.",De("debrief-chart").innerHTML=yl(e);let t=xl(e);De("debrief-impact").innerHTML=vl(t),De("debrief-impact").setAttribute("aria-label",`Largest contributors to ${t.total.toFixed(1)} cumulative simulated pressure impact, before reserve is floored at zero. These are recorded impacts, not effects prevented by interventions.`),De("debrief-peak").textContent=t.total&&t.peak?`Hardest front ${t.peak.front} · ${t.peak.weather} · ${t.peak.impact.toFixed(1)} impact`:"No pressure impact this season.",De("debrief-stats").innerHTML=[[Math.round(e.integrity),"reserve"],[e.contained,"contained"],[e.score,"score"]].map(([n,i])=>`<div><strong>${n}</strong><span>${i}</span></div>`).join(""),De("debrief-stats").lastElementChild.title="Score = 10 × final reserve + 18 × contained fires + 2 × remaining supplies, rounded.",De("debrief-thought").textContent=e.status==="won"?`You combined ${e.deployments} crew dispatches and ${e.drops} water drops. Try the same weather with a different approach.`:"Pressure outran your response. Crews need time; water reduces pressure immediately. Replay this weather and try a different response.",De("debrief").showModal()}}var Yl="186";var Zl=0,ia=1,Jl=2;var Ki=1,Kl=2,Ci=3,Ri=0,Bt=1,ln=2,cn=0,ji=1,sa=2,ra=3,aa=4,jl=5;var Ii=100,Ql=101,ec=102,tc=103,nc=104,ic=200,sc=201,rc=202,ac=203,oc=204,lc=205,cc=206,hc=207,uc=208,dc=209,fc=210,pc=211,mc=212,gc=213,_c=214,xc=0,vc=1,yc=2,oa=3,Sc=4,Mc=5,bc=6,wc=7,Ec=0,Tc=1,Ac=2,Qt=0,la=1,ca=2,ha=3,ua=4,da=5,fa=6,pa=7;var Pi=301,Xn=302,Hs=303,Vs=304,Qi=306,Cc=1000,Ws=1001,Rc=1002,Dn=1003,Ic=1004;var es=1005;var zt=1006,Xs=1007;var qn=1008;var en=1009,Pc=1010,Lc=1011,ts=1012,ma=1013,Un=1014,Sn=1015,hn=1016,ga=1017,_a=1018,Li=1020,Nc=35902,Dc=35899,Uc=1021,Fc=1022,un=1023,$n=1026,Yn=1027,Oc=1028,xa=1029,Zn=1030,va=1031;var ya=1033,qs=33776,$s=33777,Ys=33778,Zs=33779,Sa=35840,Ma=35841,ba=35842,wa=35843,Ea=36196,Ta=37492,Aa=37496,Ca=37488,Ra=37489,Js=37490,Ia=37491,Pa=37808,La=37809,Na=37810,Da=37811,Ua=37812,Fa=37813,Oa=37814,Ba=37815,za=37816,ka=37817,Ga=37818,Ha=37819,Va=37820,Wa=37821,Xa=36492,qa=36494,$a=36495,Ya=36283,Za=36284,Ks=36285,Ja=36286;var Ka=0,Bc=1,Jn="",zc="srgb",ja="srgb-linear",Qa="linear",nt="srgb";var kc=512,Gc=513,Hc=514,js=515,Vc=516,Wc=517,Qs=518,Xc=519;var eo="300 es",to=2000;function mu(e){for(let t=e.length-1;t>=0;--t)if(e[t]>=65535)return!0;return!1}function gu(e){return ArrayBuffer.isView(e)&&!(e instanceof DataView)}function Ji(e){return document.createElementNS("http://www.w3.org/1999/xhtml",e)}function qc(){let e=Ji("canvas");return e.style.display="block",e}var Tl={},Ai=null;function no(...e){let t="THREE."+e.shift();if(Ai)Ai("log",t,...e);else console.log(t,...e)}function $c(e){let t=e[0];if(typeof t==="string"&&t.startsWith("TSL:")){let n=e[1];if(n&&n.isStackTrace)e[0]+=" "+n.getLocation();else e[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return e}function Ce(...e){e=$c(e);let t="THREE."+e.shift();if(Ai)Ai("warn",t,...e);else{let n=e[0];if(n&&n.isStackTrace)console.warn(n.getError(t));else console.warn(t,...e)}}function Pe(...e){e=$c(e);let t="THREE."+e.shift();if(Ai)Ai("error",t,...e);else{let n=e[0];if(n&&n.isStackTrace)console.error(n.getError(t));else console.error(t,...e)}}function Wn(...e){let t=e.join(" ");if(t in Tl)return;Tl[t]=!0,Ce(...e)}function Yc(e,t,n){return new Promise(function(i,s){function r(){switch(e.clientWaitSync(t,e.SYNC_FLUSH_COMMANDS_BIT,0)){case e.WAIT_FAILED:s();break;case e.TIMEOUT_EXPIRED:setTimeout(r,n);break;default:i()}}setTimeout(r,n)})}var Zc={[0]:1,[2]:6,[4]:7,[3]:5,[1]:0,[6]:2,[7]:4,[5]:3};class Mn{addEventListener(e,t){if(this._listeners===void 0)this._listeners={};let n=this._listeners;if(n[e]===void 0)n[e]=[];if(n[e].indexOf(t)===-1)n[e].push(t)}hasEventListener(e,t){let n=this._listeners;if(n===void 0)return!1;return n[e]!==void 0&&n[e].indexOf(t)!==-1}removeEventListener(e,t){let n=this._listeners;if(n===void 0)return;let i=n[e];if(i!==void 0){let s=i.indexOf(t);if(s!==-1)i.splice(s,1)}}dispatchEvent(e){let t=this._listeners;if(t===void 0)return;let n=t[e.type];if(n!==void 0){e.target=this;let i=n.slice(0);for(let s=0,r=i.length;s<r;s++)i[s].call(this,e);e.target=null}}}var At=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"];var Nr=Math.PI/180,zs=180/Math.PI;function ns(){let e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,n=Math.random()*4294967295|0,i=Math.random()*4294967295|0;return(At[e&255]+At[e>>8&255]+At[e>>16&255]+At[e>>24&255]+"-"+At[t&255]+At[t>>8&255]+"-"+At[t>>16&15|64]+At[t>>24&255]+"-"+At[n&63|128]+At[n>>8&255]+"-"+At[n>>16&255]+At[n>>24&255]+At[i&255]+At[i>>8&255]+At[i>>16&255]+At[i>>24&255]).toLowerCase()}function Ge(e,t,n){return Math.max(t,Math.min(n,e))}function _u(e,t){return(e%t+t)%t}function Dr(e,t,n){return(1-n)*e+n*t}function Wi(e,t){switch(t.constructor){case Float32Array:return e;case Uint32Array:return e/4294967295;case Uint16Array:return e/65535;case Uint8Array:case Uint8ClampedArray:return e/255;case Int32Array:return Math.max(e/2147483647,-1);case Int16Array:return Math.max(e/32767,-1);case Int8Array:return Math.max(e/127,-1);default:throw Error("THREE.MathUtils: Invalid component type.")}}function Ot(e,t){switch(t.constructor){case Float32Array:return e;case Uint32Array:return Math.round(e*4294967295);case Uint16Array:return Math.round(e*65535);case Uint8Array:case Uint8ClampedArray:return Math.round(e*255);case Int32Array:return Math.round(e*2147483647);case Int16Array:return Math.round(e*32767);case Int8Array:return Math.round(e*127);default:throw Error("THREE.MathUtils: Invalid component type.")}}class Xe{static{Xe.prototype.isVector2=!0}constructor(e=0,t=0){this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw Error("THREE.Vector2: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw Error("THREE.Vector2: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){let t=this.x,n=this.y,i=e.elements;return this.x=i[0]*t+i[3]*n+i[6],this.y=i[1]*t+i[4]*n+i[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=Ge(this.x,e.x,t.x),this.y=Ge(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=Ge(this.x,e,t),this.y=Ge(this.y,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Ge(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(Ge(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y;return t*t+n*n}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){let n=Math.cos(t),i=Math.sin(t),s=this.x-e.x,r=this.y-e.y;return this.x=s*n-r*i+e.x,this.y=s*i+r*n+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}}class bn{constructor(e=0,t=0,n=0,i=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=n,this._w=i}static slerpFlat(e,t,n,i,s,r,a){let o=n[i+0],c=n[i+1],l=n[i+2],u=n[i+3],d=s[r+0],h=s[r+1],m=s[r+2],v=s[r+3];if(u!==v||o!==d||c!==h||l!==m){let b=o*d+c*h+l*m+u*v;if(b<0)d=-d,h=-h,m=-m,v=-v,b=-b;let p=1-a;if(b<0.9995){let f=Math.acos(b),T=Math.sin(f);p=Math.sin(p*f)/T,a=Math.sin(a*f)/T,o=o*p+d*a,c=c*p+h*a,l=l*p+m*a,u=u*p+v*a}else{o=o*p+d*a,c=c*p+h*a,l=l*p+m*a,u=u*p+v*a;let f=1/Math.sqrt(o*o+c*c+l*l+u*u);o*=f,c*=f,l*=f,u*=f}}e[t]=o,e[t+1]=c,e[t+2]=l,e[t+3]=u}static multiplyQuaternionsFlat(e,t,n,i,s,r){let a=n[i],o=n[i+1],c=n[i+2],l=n[i+3],u=s[r],d=s[r+1],h=s[r+2],m=s[r+3];return e[t]=a*m+l*u+o*h-c*d,e[t+1]=o*m+l*d+c*u-a*h,e[t+2]=c*m+l*h+a*d-o*u,e[t+3]=l*m-a*u-o*d-c*h,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,n,i){return this._x=e,this._y=t,this._z=n,this._w=i,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){let{_x:n,_y:i,_z:s,_order:r}=e,{cos:a,sin:o}=Math,c=a(n/2),l=a(i/2),u=a(s/2),d=o(n/2),h=o(i/2),m=o(s/2);switch(r){case"XYZ":this._x=d*l*u+c*h*m,this._y=c*h*u-d*l*m,this._z=c*l*m+d*h*u,this._w=c*l*u-d*h*m;break;case"YXZ":this._x=d*l*u+c*h*m,this._y=c*h*u-d*l*m,this._z=c*l*m-d*h*u,this._w=c*l*u+d*h*m;break;case"ZXY":this._x=d*l*u-c*h*m,this._y=c*h*u+d*l*m,this._z=c*l*m+d*h*u,this._w=c*l*u-d*h*m;break;case"ZYX":this._x=d*l*u-c*h*m,this._y=c*h*u+d*l*m,this._z=c*l*m-d*h*u,this._w=c*l*u+d*h*m;break;case"YZX":this._x=d*l*u+c*h*m,this._y=c*h*u+d*l*m,this._z=c*l*m-d*h*u,this._w=c*l*u-d*h*m;break;case"XZY":this._x=d*l*u-c*h*m,this._y=c*h*u-d*l*m,this._z=c*l*m+d*h*u,this._w=c*l*u+d*h*m;break;default:Ce("Quaternion: .setFromEuler() encountered an unknown order: "+r)}if(t===!0)this._onChangeCallback();return this}setFromAxisAngle(e,t){let n=t/2,i=Math.sin(n);return this._x=e.x*i,this._y=e.y*i,this._z=e.z*i,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(e){let t=e.elements,n=t[0],i=t[4],s=t[8],r=t[1],a=t[5],o=t[9],c=t[2],l=t[6],u=t[10],d=n+a+u;if(d>0){let h=0.5/Math.sqrt(d+1);this._w=0.25/h,this._x=(l-o)*h,this._y=(s-c)*h,this._z=(r-i)*h}else if(n>a&&n>u){let h=2*Math.sqrt(1+n-a-u);this._w=(l-o)/h,this._x=0.25*h,this._y=(i+r)/h,this._z=(s+c)/h}else if(a>u){let h=2*Math.sqrt(1+a-n-u);this._w=(s-c)/h,this._x=(i+r)/h,this._y=0.25*h,this._z=(o+l)/h}else{let h=2*Math.sqrt(1+u-n-a);this._w=(r-i)/h,this._x=(s+c)/h,this._y=(o+l)/h,this._z=0.25*h}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let n=e.dot(t)+1;if(n<0.00000001)if(n=0,Math.abs(e.x)>Math.abs(e.z))this._x=-e.y,this._y=e.x,this._z=0,this._w=n;else this._x=0,this._y=-e.z,this._z=e.y,this._w=n;else this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=n;return this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(Ge(this.dot(e),-1,1)))}rotateTowards(e,t){let n=this.angleTo(e);if(n===0)return this;let i=Math.min(1,t/n);return this.slerp(e,i),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();if(e===0)this._x=0,this._y=0,this._z=0,this._w=1;else e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e;return this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){let{_x:n,_y:i,_z:s,_w:r}=e,{_x:a,_y:o,_z:c,_w:l}=t;return this._x=n*l+r*a+i*c-s*o,this._y=i*l+r*o+s*a-n*c,this._z=s*l+r*c+n*o-i*a,this._w=r*l-n*a-i*o-s*c,this._onChangeCallback(),this}slerp(e,t){let{_x:n,_y:i,_z:s,_w:r}=e,a=this.dot(e);if(a<0)n=-n,i=-i,s=-s,r=-r,a=-a;let o=1-t;if(a<0.9995){let c=Math.acos(a),l=Math.sin(c);o=Math.sin(o*c)/l,t=Math.sin(t*c)/l,this._x=this._x*o+n*t,this._y=this._y*o+i*t,this._z=this._z*o+s*t,this._w=this._w*o+r*t,this._onChangeCallback()}else this._x=this._x*o+n*t,this._y=this._y*o+i*t,this._z=this._z*o+s*t,this._w=this._w*o+r*t,this.normalize();return this}slerpQuaternions(e,t,n){return this.copy(e).slerp(t,n)}random(){let e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),n=Math.random(),i=Math.sqrt(1-n),s=Math.sqrt(n);return this.set(i*Math.sin(e),i*Math.cos(e),s*Math.sin(t),s*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}class F{static{F.prototype.isVector3=!0}constructor(e=0,t=0,n=0){this.x=e,this.y=t,this.z=n}set(e,t,n){if(n===void 0)n=this.z;return this.x=e,this.y=t,this.z=n,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw Error("THREE.Vector3: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw Error("THREE.Vector3: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(Al.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(Al.setFromAxisAngle(e,t))}applyMatrix3(e){let t=this.x,n=this.y,i=this.z,s=e.elements;return this.x=s[0]*t+s[3]*n+s[6]*i,this.y=s[1]*t+s[4]*n+s[7]*i,this.z=s[2]*t+s[5]*n+s[8]*i,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){let t=this.x,n=this.y,i=this.z,s=e.elements,r=1/(s[3]*t+s[7]*n+s[11]*i+s[15]);return this.x=(s[0]*t+s[4]*n+s[8]*i+s[12])*r,this.y=(s[1]*t+s[5]*n+s[9]*i+s[13])*r,this.z=(s[2]*t+s[6]*n+s[10]*i+s[14])*r,this}applyQuaternion(e){let t=this.x,n=this.y,i=this.z,{x:s,y:r,z:a,w:o}=e,c=2*(r*i-a*n),l=2*(a*t-s*i),u=2*(s*n-r*t);return this.x=t+o*c+r*u-a*l,this.y=n+o*l+a*c-s*u,this.z=i+o*u+s*l-r*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){let t=this.x,n=this.y,i=this.z,s=e.elements;return this.x=s[0]*t+s[4]*n+s[8]*i,this.y=s[1]*t+s[5]*n+s[9]*i,this.z=s[2]*t+s[6]*n+s[10]*i,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=Ge(this.x,e.x,t.x),this.y=Ge(this.y,e.y,t.y),this.z=Ge(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=Ge(this.x,e,t),this.y=Ge(this.y,e,t),this.z=Ge(this.z,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Ge(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){let{x:n,y:i,z:s}=e,{x:r,y:a,z:o}=t;return this.x=i*o-s*a,this.y=s*r-n*o,this.z=n*a-i*r,this}projectOnVector(e){let t=e.lengthSq();if(t===0)return this.set(0,0,0);let n=e.dot(this)/t;return this.copy(e).multiplyScalar(n)}projectOnPlane(e){return Ur.copy(this).projectOnVector(e),this.sub(Ur)}reflect(e){return this.sub(Ur.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(Ge(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y,i=this.z-e.z;return t*t+n*n+i*i}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,n){let i=Math.sin(t)*e;return this.x=i*Math.sin(n),this.y=Math.cos(t)*e,this.z=i*Math.cos(n),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,n){return this.x=e*Math.sin(t),this.y=n,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){let t=this.setFromMatrixColumn(e,0).length(),n=this.setFromMatrixColumn(e,1).length(),i=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=n,this.z=i,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){let e=Math.random()*Math.PI*2,t=Math.random()*2-1,n=Math.sqrt(1-t*t);return this.x=n*Math.cos(e),this.y=t,this.z=n*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}}var Ur=new F,Al=new bn;class Le{static{Le.prototype.isMatrix3=!0}constructor(e,t,n,i,s,r,a,o,c){if(this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0)this.set(e,t,n,i,s,r,a,o,c)}set(e,t,n,i,s,r,a,o,c){let l=this.elements;return l[0]=e,l[1]=i,l[2]=a,l[3]=t,l[4]=s,l[5]=o,l[6]=n,l[7]=r,l[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],this}extractBasis(e,t,n){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(e){let t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,i=t.elements,s=this.elements,r=n[0],a=n[3],o=n[6],c=n[1],l=n[4],u=n[7],d=n[2],h=n[5],m=n[8],v=i[0],b=i[3],p=i[6],f=i[1],T=i[4],I=i[7],S=i[2],w=i[5],E=i[8];return s[0]=r*v+a*f+o*S,s[3]=r*b+a*T+o*w,s[6]=r*p+a*I+o*E,s[1]=c*v+l*f+u*S,s[4]=c*b+l*T+u*w,s[7]=c*p+l*I+u*E,s[2]=d*v+h*f+m*S,s[5]=d*b+h*T+m*w,s[8]=d*p+h*I+m*E,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[1],i=e[2],s=e[3],r=e[4],a=e[5],o=e[6],c=e[7],l=e[8];return t*r*l-t*a*c-n*s*l+n*a*o+i*s*c-i*r*o}invert(){let e=this.elements,t=e[0],n=e[1],i=e[2],s=e[3],r=e[4],a=e[5],o=e[6],c=e[7],l=e[8],u=l*r-a*c,d=a*o-l*s,h=c*s-r*o,m=t*u+n*d+i*h;if(m===0)return this.set(0,0,0,0,0,0,0,0,0);let v=1/m;return e[0]=u*v,e[1]=(i*c-l*n)*v,e[2]=(a*n-i*r)*v,e[3]=d*v,e[4]=(l*t-i*o)*v,e[5]=(i*s-a*t)*v,e[6]=h*v,e[7]=(n*o-c*t)*v,e[8]=(r*t-n*s)*v,this}transpose(){let e,t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){let t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,n,i,s,r,a){let o=Math.cos(s),c=Math.sin(s);return this.set(n*o,n*c,-n*(o*r+c*a)+r+e,-i*c,i*o,-i*(-c*r+o*a)+a+t,0,0,1),this}scale(e,t){return Wn("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply(Fr.makeScale(e,t)),this}rotate(e){return Wn("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply(Fr.makeRotation(-e)),this}translate(e,t){return Wn("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply(Fr.makeTranslation(e,t)),this}makeTranslation(e,t){if(e.isVector2)this.set(1,0,e.x,0,1,e.y,0,0,1);else this.set(1,0,e,0,1,t,0,0,1);return this}makeRotation(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,n,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){let t=this.elements,n=e.elements;for(let i=0;i<9;i++)if(t[i]!==n[i])return!1;return!0}fromArray(e,t=0){for(let n=0;n<9;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e}clone(){return new this.constructor().fromArray(this.elements)}}var Fr=new Le,Cl=new Le().set(0.4123908,0.3575843,0.1804808,0.212639,0.7151687,0.0721923,0.0193308,0.1191948,0.9505322),Rl=new Le().set(3.2409699,-1.5373832,-0.4986108,-0.9692436,1.8759675,0.0415551,0.0556301,-0.203977,1.0569715);function xu(){let e={enabled:!0,workingColorSpace:"srgb-linear",spaces:{},convert:function(s,r,a){if(this.enabled===!1||r===a||!r||!a)return s;if(this.spaces[r].transfer==="srgb")s.r=yn(s.r),s.g=yn(s.g),s.b=yn(s.b);if(this.spaces[r].primaries!==this.spaces[a].primaries)s.applyMatrix3(this.spaces[r].toXYZ),s.applyMatrix3(this.spaces[a].fromXYZ);if(this.spaces[a].transfer==="srgb")s.r=Ti(s.r),s.g=Ti(s.g),s.b=Ti(s.b);return s},workingToColorSpace:function(s,r){return this.convert(s,this.workingColorSpace,r)},colorSpaceToWorking:function(s,r){return this.convert(s,r,this.workingColorSpace)},getPrimaries:function(s){return this.spaces[s].primaries},getTransfer:function(s){if(s==="")return"linear";return this.spaces[s].transfer},getToneMappingMode:function(s){return this.spaces[s].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(s,r=this.workingColorSpace){return s.fromArray(this.spaces[r].luminanceCoefficients)},define:function(s){Object.assign(this.spaces,s)},_getMatrix:function(s,r,a){return s.copy(this.spaces[r].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(s){return this.spaces[s].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(s=this.workingColorSpace){return this.spaces[s].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(s,r){return Wn("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),e.workingToColorSpace(s,r)},toWorkingColorSpace:function(s,r){return Wn("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),e.colorSpaceToWorking(s,r)}},t=[0.64,0.33,0.3,0.6,0.15,0.06],n=[0.2126,0.7152,0.0722],i=[0.3127,0.329];return e.define({["srgb-linear"]:{primaries:t,whitePoint:i,transfer:"linear",toXYZ:Cl,fromXYZ:Rl,luminanceCoefficients:n,workingColorSpaceConfig:{unpackColorSpace:"srgb"},outputColorSpaceConfig:{drawingBufferColorSpace:"srgb"}},["srgb"]:{primaries:t,whitePoint:i,transfer:"srgb",toXYZ:Cl,fromXYZ:Rl,luminanceCoefficients:n,outputColorSpaceConfig:{drawingBufferColorSpace:"srgb"}}}),e}var ke=xu();function yn(e){return e<0.04045?e*0.0773993808:Math.pow(e*0.9478672986+0.0521327014,2.4)}function Ti(e){return e<0.0031308?e*12.92:1.055*Math.pow(e,0.41666)-0.055}var fi;class io{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src))return e.src;if(typeof HTMLCanvasElement>"u")return e.src;let n;if(e instanceof HTMLCanvasElement)n=e;else{if(fi===void 0)fi=Ji("canvas");fi.width=e.width,fi.height=e.height;let i=fi.getContext("2d");if(e instanceof ImageData)i.putImageData(e,0,0);else i.drawImage(e,0,0,e.width,e.height);n=fi}return n.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){let t=Ji("canvas");t.width=e.width,t.height=e.height;let n=t.getContext("2d");n.drawImage(e,0,0,e.width,e.height);let i=n.getImageData(0,0,e.width,e.height),s=i.data;for(let r=0;r<s.length;r++)s[r]=yn(s[r]/255)*255;return n.putImageData(i,0,0),t}else if(e.data){let t=e.data.slice(0);for(let n=0;n<t.length;n++)if(t instanceof Uint8Array||t instanceof Uint8ClampedArray)t[n]=Math.floor(yn(t[n]/255)*255);else t[n]=yn(t[n]);return{data:t,width:e.width,height:e.height}}else return Ce("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}var vu=0;class is{constructor(e=null){this.isTextureSource=!0,Object.defineProperty(this,"id",{value:vu++}),this.uuid=ns(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){let t=this.data;if(typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement)e.set(t.videoWidth,t.videoHeight,0);else if(typeof VideoFrame<"u"&&t instanceof VideoFrame)e.set(t.displayWidth,t.displayHeight,0);else if(t!==null)e.set(t.width,t.height,t.depth||0);else e.set(0,0,0);return e}set needsUpdate(e){if(e===!0)this.version++}toJSON(e){let t=e===void 0||typeof e==="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];let n={uuid:this.uuid,url:""},i=this.data;if(i!==null){let s;if(Array.isArray(i)){s=[];for(let r=0,a=i.length;r<a;r++)if(i[r].isDataTexture)s.push(Or(i[r].image));else s.push(Or(i[r]))}else s=Or(i);n.url=s}if(!t)e.images[this.uuid]=n;return n}}function Or(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap)return io.getDataURL(e);else if(e.data)return{data:Array.from(e.data),width:e.width,height:e.height,type:e.data.constructor.name};else return Ce("Texture: Unable to serialize Texture."),{}}var yu=0,Br=new F;class Rt extends Mn{constructor(e=Rt.DEFAULT_IMAGE,t=Rt.DEFAULT_MAPPING,n=1001,i=1001,s=1006,r=1008,a=1023,o=1009,c=Rt.DEFAULT_ANISOTROPY,l=""){super();this.isTexture=!0,Object.defineProperty(this,"id",{value:yu++}),this.uuid=ns(),this.name="",this.source=new is(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=n,this.wrapT=i,this.magFilter=s,this.minFilter=r,this.anisotropy=c,this.format=a,this.internalFormat=null,this.type=o,this.offset=new Xe(0,0),this.repeat=new Xe(1,1),this.center=new Xe(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new Le,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=l,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=e&&e.depth&&e.depth>1?!0:!1,this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(Br).x}get height(){return this.source.getSize(Br).y}get depth(){return this.source.getSize(Br).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(let t in e){let n=e[t];if(n===void 0){Ce(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}let i=this[t];if(i===void 0){Ce(`Texture.setValues(): property '${t}' does not exist.`);continue}if(i&&n&&(i.isVector2&&n.isVector2))i.copy(n);else if(i&&n&&(i.isVector3&&n.isVector3))i.copy(n);else if(i&&n&&(i.isMatrix3&&n.isMatrix3))i.copy(n);else this[t]=n}}toJSON(e){let t=e===void 0||typeof e==="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};if(Object.keys(this.userData).length>0)n.userData=this.userData;if(!t)e.textures[this.uuid]=n;return n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==300)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case 1000:e.x=e.x-Math.floor(e.x);break;case 1001:e.x=e.x<0?0:1;break;case 1002:if(Math.abs(Math.floor(e.x)%2)===1)e.x=Math.ceil(e.x)-e.x;else e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case 1000:e.y=e.y-Math.floor(e.y);break;case 1001:e.y=e.y<0?0:1;break;case 1002:if(Math.abs(Math.floor(e.y)%2)===1)e.y=Math.ceil(e.y)-e.y;else e.y=e.y-Math.floor(e.y);break}if(this.flipY)e.y=1-e.y;return e}set needsUpdate(e){if(e===!0)this.version++,this.source.needsUpdate=!0}set needsPMREMUpdate(e){if(e===!0)this.pmremVersion++}}Rt.DEFAULT_IMAGE=null;Rt.DEFAULT_MAPPING=300;Rt.DEFAULT_ANISOTROPY=1;class ut{static{ut.prototype.isVector4=!0}constructor(e=0,t=0,n=0,i=1){this.x=e,this.y=t,this.z=n,this.w=i}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,n,i){return this.x=e,this.y=t,this.z=n,this.w=i,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw Error("THREE.Vector4: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw Error("THREE.Vector4: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){let t=this.x,n=this.y,i=this.z,s=this.w,r=e.elements;return this.x=r[0]*t+r[4]*n+r[8]*i+r[12]*s,this.y=r[1]*t+r[5]*n+r[9]*i+r[13]*s,this.z=r[2]*t+r[6]*n+r[10]*i+r[14]*s,this.w=r[3]*t+r[7]*n+r[11]*i+r[15]*s,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);let t=Math.sqrt(1-e.w*e.w);if(t<0.0001)this.x=1,this.y=0,this.z=0;else this.x=e.x/t,this.y=e.y/t,this.z=e.z/t;return this}setAxisAngleFromRotationMatrix(e){let t,n,i,s,r=0.01,a=0.1,o=e.elements,c=o[0],l=o[4],u=o[8],d=o[1],h=o[5],m=o[9],v=o[2],b=o[6],p=o[10];if(Math.abs(l-d)<0.01&&Math.abs(u-v)<0.01&&Math.abs(m-b)<0.01){if(Math.abs(l+d)<0.1&&Math.abs(u+v)<0.1&&Math.abs(m+b)<0.1&&Math.abs(c+h+p-3)<0.1)return this.set(1,0,0,0),this;t=Math.PI;let T=(c+1)/2,I=(h+1)/2,S=(p+1)/2,w=(l+d)/4,E=(u+v)/4,A=(m+b)/4;if(T>I&&T>S)if(T<0.01)n=0,i=0.707106781,s=0.707106781;else n=Math.sqrt(T),i=w/n,s=E/n;else if(I>S)if(I<0.01)n=0.707106781,i=0,s=0.707106781;else i=Math.sqrt(I),n=w/i,s=A/i;else if(S<0.01)n=0.707106781,i=0.707106781,s=0;else s=Math.sqrt(S),n=E/s,i=A/s;return this.set(n,i,s,t),this}let f=Math.sqrt((b-m)*(b-m)+(u-v)*(u-v)+(d-l)*(d-l));if(Math.abs(f)<0.001)f=1;return this.x=(b-m)/f,this.y=(u-v)/f,this.z=(d-l)/f,this.w=Math.acos((c+h+p-1)/2),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=Ge(this.x,e.x,t.x),this.y=Ge(this.y,e.y,t.y),this.z=Ge(this.z,e.z,t.z),this.w=Ge(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=Ge(this.x,e,t),this.y=Ge(this.y,e,t),this.z=Ge(this.z,e,t),this.w=Ge(this.w,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Ge(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this.w=e.w+(t.w-e.w)*n,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}}class so extends Mn{constructor(e=1,t=1,n={}){super();n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:1006,depthBuffer:!0,stencilBuffer:!1,resolveColorBuffer:!0,resolveDepthBuffer:!0,resolveStencilBuffer:!0,storeMultisampledColorBuffer:!0,storeMultisampledDepthBuffer:!0,storeMultisampledStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1,useArrayDepthTexture:!1},n),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=n.depth,this.scissor=new ut(0,0,e,t),this.scissorTest=!1,this.viewport=new ut(0,0,e,t),this.textures=[];let i={width:e,height:t,depth:n.depth},s=new Rt(i),r=n.count;for(let a=0;a<r;a++)this.textures[a]=s.clone(),this.textures[a].isRenderTargetTexture=!0,this.textures[a].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveColorBuffer=n.resolveColorBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this.storeMultisampledColorBuffer=n.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=n.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=n.storeMultisampledStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview,this.useArrayDepthTexture=n.useArrayDepthTexture}_setTextureOptions(e={}){let t={minFilter:1006,generateMipmaps:!1,flipY:!1,internalFormat:null};if(e.mapping!==void 0)t.mapping=e.mapping;if(e.wrapS!==void 0)t.wrapS=e.wrapS;if(e.wrapT!==void 0)t.wrapT=e.wrapT;if(e.wrapR!==void 0)t.wrapR=e.wrapR;if(e.magFilter!==void 0)t.magFilter=e.magFilter;if(e.minFilter!==void 0)t.minFilter=e.minFilter;if(e.format!==void 0)t.format=e.format;if(e.type!==void 0)t.type=e.type;if(e.anisotropy!==void 0)t.anisotropy=e.anisotropy;if(e.colorSpace!==void 0)t.colorSpace=e.colorSpace;if(e.flipY!==void 0)t.flipY=e.flipY;if(e.generateMipmaps!==void 0)t.generateMipmaps=e.generateMipmaps;if(e.internalFormat!==void 0)t.internalFormat=e.internalFormat;for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){if(this._depthTexture!==null&&this._depthTexture.renderTarget===this)this._depthTexture.renderTarget=null;if(e!==null&&e.renderTarget===null)e.renderTarget=this;this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,n=1){if(this.width!==e||this.height!==t||this.depth!==n){this.width=e,this.height=t,this.depth=n;for(let i=0,s=this.textures.length;i<s;i++)if(this.textures[i].image.width=e,this.textures[i].image.height=t,this.textures[i].image.depth=n,this.textures[i].isData3DTexture!==!0)this.textures[i].isArrayTexture=this.textures[i].image.depth>1;this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,n=e.textures.length;t<n;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;let i=Object.assign({},e.textures[t].image);this.textures[t].source=new is(i)}if(this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveColorBuffer=e.resolveColorBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,this.storeMultisampledColorBuffer=e.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=e.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=e.storeMultisampledStencilBuffer,e.depthTexture!==null)if(e.depthTexture.renderTarget===e){let t=e.depthTexture.clone();t.renderTarget=null,this.depthTexture=t}else this.depthTexture=e.depthTexture;return this.samples=e.samples,this.multiview=e.multiview,this.useArrayDepthTexture=e.useArrayDepthTexture,this}dispose(){this.dispatchEvent({type:"dispose"})}}class Vt extends so{constructor(e=1,t=1,n={}){super(e,t,n);this.isWebGLRenderTarget=!0}}class er extends Rt{constructor(e=null,t=1,n=1,i=1){super(null);this.isDataArrayTexture=!0,this.image={data:e,width:t,height:n,depth:i},this.magFilter=1003,this.minFilter=1003,this.wrapR=1001,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class ro extends Rt{constructor(e=null,t=1,n=1,i=1){super(null);this.isData3DTexture=!0,this.image={data:e,width:t,height:n,depth:i},this.magFilter=1003,this.minFilter=1003,this.wrapR=1001,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}}class ht{static{ht.prototype.isMatrix4=!0}constructor(e,t,n,i,s,r,a,o,c,l,u,d,h,m,v,b){if(this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0)this.set(e,t,n,i,s,r,a,o,c,l,u,d,h,m,v,b)}set(e,t,n,i,s,r,a,o,c,l,u,d,h,m,v,b){let p=this.elements;return p[0]=e,p[4]=t,p[8]=n,p[12]=i,p[1]=s,p[5]=r,p[9]=a,p[13]=o,p[2]=c,p[6]=l,p[10]=u,p[14]=d,p[3]=h,p[7]=m,p[11]=v,p[15]=b,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new ht().fromArray(this.elements)}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],t[9]=n[9],t[10]=n[10],t[11]=n[11],t[12]=n[12],t[13]=n[13],t[14]=n[14],t[15]=n[15],this}copyPosition(e){let t=this.elements,n=e.elements;return t[12]=n[12],t[13]=n[13],t[14]=n[14],this}setFromMatrix3(e){let t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,n){if(this.determinantAffine()===0)return e.set(1,0,0),t.set(0,1,0),n.set(0,0,1),this;return e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this}makeBasis(e,t,n){return this.set(e.x,t.x,n.x,0,e.y,t.y,n.y,0,e.z,t.z,n.z,0,0,0,0,1),this}extractRotation(e){if(e.determinantAffine()===0)return this.identity();let t=this.elements,n=e.elements,i=1/pi.setFromMatrixColumn(e,0).length(),s=1/pi.setFromMatrixColumn(e,1).length(),r=1/pi.setFromMatrixColumn(e,2).length();return t[0]=n[0]*i,t[1]=n[1]*i,t[2]=n[2]*i,t[3]=0,t[4]=n[4]*s,t[5]=n[5]*s,t[6]=n[6]*s,t[7]=0,t[8]=n[8]*r,t[9]=n[9]*r,t[10]=n[10]*r,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){let t=this.elements,{x:n,y:i,z:s}=e,r=Math.cos(n),a=Math.sin(n),o=Math.cos(i),c=Math.sin(i),l=Math.cos(s),u=Math.sin(s);if(e.order==="XYZ"){let d=r*l,h=r*u,m=a*l,v=a*u;t[0]=o*l,t[4]=-o*u,t[8]=c,t[1]=h+m*c,t[5]=d-v*c,t[9]=-a*o,t[2]=v-d*c,t[6]=m+h*c,t[10]=r*o}else if(e.order==="YXZ"){let d=o*l,h=o*u,m=c*l,v=c*u;t[0]=d+v*a,t[4]=m*a-h,t[8]=r*c,t[1]=r*u,t[5]=r*l,t[9]=-a,t[2]=h*a-m,t[6]=v+d*a,t[10]=r*o}else if(e.order==="ZXY"){let d=o*l,h=o*u,m=c*l,v=c*u;t[0]=d-v*a,t[4]=-r*u,t[8]=m+h*a,t[1]=h+m*a,t[5]=r*l,t[9]=v-d*a,t[2]=-r*c,t[6]=a,t[10]=r*o}else if(e.order==="ZYX"){let d=r*l,h=r*u,m=a*l,v=a*u;t[0]=o*l,t[4]=m*c-h,t[8]=d*c+v,t[1]=o*u,t[5]=v*c+d,t[9]=h*c-m,t[2]=-c,t[6]=a*o,t[10]=r*o}else if(e.order==="YZX"){let d=r*o,h=r*c,m=a*o,v=a*c;t[0]=o*l,t[4]=v-d*u,t[8]=m*u+h,t[1]=u,t[5]=r*l,t[9]=-a*l,t[2]=-c*l,t[6]=h*u+m,t[10]=d-v*u}else if(e.order==="XZY"){let d=r*o,h=r*c,m=a*o,v=a*c;t[0]=o*l,t[4]=-u,t[8]=c*l,t[1]=d*u+v,t[5]=r*l,t[9]=h*u-m,t[2]=m*u-h,t[6]=a*l,t[10]=v*u+d}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(Su,e,Mu)}lookAt(e,t,n){let i=this.elements;if(kt.subVectors(e,t),kt.lengthSq()===0)kt.z=1;if(kt.normalize(),An.crossVectors(n,kt),An.lengthSq()===0){if(Math.abs(n.z)===1)kt.x+=0.0001;else kt.z+=0.0001;kt.normalize(),An.crossVectors(n,kt)}return An.normalize(),_s.crossVectors(kt,An),i[0]=An.x,i[4]=_s.x,i[8]=kt.x,i[1]=An.y,i[5]=_s.y,i[9]=kt.y,i[2]=An.z,i[6]=_s.z,i[10]=kt.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,i=t.elements,s=this.elements,r=n[0],a=n[4],o=n[8],c=n[12],l=n[1],u=n[5],d=n[9],h=n[13],m=n[2],v=n[6],b=n[10],p=n[14],f=n[3],T=n[7],I=n[11],S=n[15],w=i[0],E=i[4],A=i[8],x=i[12],M=i[1],H=i[5],D=i[9],U=i[13],J=i[2],C=i[6],V=i[10],K=i[14],G=i[3],ne=i[7],X=i[11],j=i[15];return s[0]=r*w+a*M+o*J+c*G,s[4]=r*E+a*H+o*C+c*ne,s[8]=r*A+a*D+o*V+c*X,s[12]=r*x+a*U+o*K+c*j,s[1]=l*w+u*M+d*J+h*G,s[5]=l*E+u*H+d*C+h*ne,s[9]=l*A+u*D+d*V+h*X,s[13]=l*x+u*U+d*K+h*j,s[2]=m*w+v*M+b*J+p*G,s[6]=m*E+v*H+b*C+p*ne,s[10]=m*A+v*D+b*V+p*X,s[14]=m*x+v*U+b*K+p*j,s[3]=f*w+T*M+I*J+S*G,s[7]=f*E+T*H+I*C+S*ne,s[11]=f*A+T*D+I*V+S*X,s[15]=f*x+T*U+I*K+S*j,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[4],i=e[8],s=e[12],r=e[1],a=e[5],o=e[9],c=e[13],l=e[2],u=e[6],d=e[10],h=e[14],m=e[3],v=e[7],b=e[11],p=e[15],f=o*h-c*d,T=a*h-c*u,I=a*d-o*u,S=r*h-c*l,w=r*d-o*l,E=r*u-a*l;return t*(v*f-b*T+p*I)-n*(m*f-b*S+p*w)+i*(m*T-v*S+p*E)-s*(m*I-v*w+b*E)}determinantAffine(){let e=this.elements,t=e[0],n=e[4],i=e[8],s=e[1],r=e[5],a=e[9],o=e[2],c=e[6],l=e[10];return t*(r*l-a*c)-n*(s*l-a*o)+i*(s*c-r*o)}transpose(){let e=this.elements,t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,n){let i=this.elements;if(e.isVector3)i[12]=e.x,i[13]=e.y,i[14]=e.z;else i[12]=e,i[13]=t,i[14]=n;return this}invert(){let e=this.elements,t=e[0],n=e[1],i=e[2],s=e[3],r=e[4],a=e[5],o=e[6],c=e[7],l=e[8],u=e[9],d=e[10],h=e[11],m=e[12],v=e[13],b=e[14],p=e[15],f=t*a-n*r,T=t*o-i*r,I=t*c-s*r,S=n*o-i*a,w=n*c-s*a,E=i*c-s*o,A=l*v-u*m,x=l*b-d*m,M=l*p-h*m,H=u*b-d*v,D=u*p-h*v,U=d*p-h*b,J=f*U-T*D+I*H+S*M-w*x+E*A;if(J===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let C=1/J;return e[0]=(a*U-o*D+c*H)*C,e[1]=(i*D-n*U-s*H)*C,e[2]=(v*E-b*w+p*S)*C,e[3]=(d*w-u*E-h*S)*C,e[4]=(o*M-r*U-c*x)*C,e[5]=(t*U-i*M+s*x)*C,e[6]=(b*I-m*E-p*T)*C,e[7]=(l*E-d*I+h*T)*C,e[8]=(r*D-a*M+c*A)*C,e[9]=(n*M-t*D-s*A)*C,e[10]=(m*w-v*I+p*f)*C,e[11]=(u*I-l*w-h*f)*C,e[12]=(a*x-r*H-o*A)*C,e[13]=(t*H-n*x+i*A)*C,e[14]=(v*T-m*S-b*f)*C,e[15]=(l*S-u*T+d*f)*C,this}scale(e){let t=this.elements,{x:n,y:i,z:s}=e;return t[0]*=n,t[4]*=i,t[8]*=s,t[1]*=n,t[5]*=i,t[9]*=s,t[2]*=n,t[6]*=i,t[10]*=s,t[3]*=n,t[7]*=i,t[11]*=s,this}getMaxScaleOnAxis(){let e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],n=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],i=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,n,i))}makeTranslation(e,t,n){if(e.isVector3)this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1);else this.set(1,0,0,e,0,1,0,t,0,0,1,n,0,0,0,1);return this}makeRotationX(e){let t=Math.cos(e),n=Math.sin(e);return this.set(1,0,0,0,0,t,-n,0,0,n,t,0,0,0,0,1),this}makeRotationY(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,0,n,0,0,1,0,0,-n,0,t,0,0,0,0,1),this}makeRotationZ(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,0,n,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){let n=Math.cos(t),i=Math.sin(t),s=1-n,{x:r,y:a,z:o}=e,c=s*r,l=s*a;return this.set(c*r+n,c*a-i*o,c*o+i*a,0,c*a+i*o,l*a+n,l*o-i*r,0,c*o-i*a,l*o+i*r,s*o*o+n,0,0,0,0,1),this}makeScale(e,t,n){return this.set(e,0,0,0,0,t,0,0,0,0,n,0,0,0,0,1),this}makeShear(e,t,n,i,s,r){return this.set(1,n,s,0,e,1,r,0,t,i,1,0,0,0,0,1),this}compose(e,t,n){let i=this.elements,{_x:s,_y:r,_z:a,_w:o}=t,c=s+s,l=r+r,u=a+a,d=s*c,h=s*l,m=s*u,v=r*l,b=r*u,p=a*u,f=o*c,T=o*l,I=o*u,{x:S,y:w,z:E}=n;return i[0]=(1-(v+p))*S,i[1]=(h+I)*S,i[2]=(m-T)*S,i[3]=0,i[4]=(h-I)*w,i[5]=(1-(d+p))*w,i[6]=(b+f)*w,i[7]=0,i[8]=(m+T)*E,i[9]=(b-f)*E,i[10]=(1-(d+v))*E,i[11]=0,i[12]=e.x,i[13]=e.y,i[14]=e.z,i[15]=1,this}decompose(e,t,n){let i=this.elements;e.x=i[12],e.y=i[13],e.z=i[14];let s=this.determinantAffine();if(s===0)return n.set(1,1,1),t.identity(),this;let r=pi.set(i[0],i[1],i[2]).length(),a=pi.set(i[4],i[5],i[6]).length(),o=pi.set(i[8],i[9],i[10]).length();if(s<0)r=-r;Jt.copy(this);let c=1/r,l=1/a,u=1/o;return Jt.elements[0]*=c,Jt.elements[1]*=c,Jt.elements[2]*=c,Jt.elements[4]*=l,Jt.elements[5]*=l,Jt.elements[6]*=l,Jt.elements[8]*=u,Jt.elements[9]*=u,Jt.elements[10]*=u,t.setFromRotationMatrix(Jt),n.x=r,n.y=a,n.z=o,this}makePerspective(e,t,n,i,s,r,a=2000,o=!1){let c=this.elements,l=2*s/(t-e),u=2*s/(n-i),d=(t+e)/(t-e),h=(n+i)/(n-i),m,v;if(o)m=s/(r-s),v=r*s/(r-s);else if(a===2000)m=-(r+s)/(r-s),v=-2*r*s/(r-s);else if(a===2001)m=-r/(r-s),v=-r*s/(r-s);else throw Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+a);return c[0]=l,c[4]=0,c[8]=d,c[12]=0,c[1]=0,c[5]=u,c[9]=h,c[13]=0,c[2]=0,c[6]=0,c[10]=m,c[14]=v,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,n,i,s,r,a=2000,o=!1){let c=this.elements,l=2/(t-e),u=2/(n-i),d=-(t+e)/(t-e),h=-(n+i)/(n-i),m,v;if(o)m=1/(r-s),v=r/(r-s);else if(a===2000)m=-2/(r-s),v=-(r+s)/(r-s);else if(a===2001)m=-1/(r-s),v=-s/(r-s);else throw Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+a);return c[0]=l,c[4]=0,c[8]=0,c[12]=d,c[1]=0,c[5]=u,c[9]=0,c[13]=h,c[2]=0,c[6]=0,c[10]=m,c[14]=v,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){let t=this.elements,n=e.elements;for(let i=0;i<16;i++)if(t[i]!==n[i])return!1;return!0}fromArray(e,t=0){for(let n=0;n<16;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e[t+9]=n[9],e[t+10]=n[10],e[t+11]=n[11],e[t+12]=n[12],e[t+13]=n[13],e[t+14]=n[14],e[t+15]=n[15],e}}var pi=new F,Jt=new ht,Su=new F(0,0,0),Mu=new F(1,1,1),An=new F,_s=new F,kt=new F,Il=new ht,Pl=new bn;class Nn{constructor(e=0,t=0,n=0,i=Nn.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=n,this._order=i}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,n,i=this._order){return this._x=e,this._y=t,this._z=n,this._order=i,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,n=!0){let i=e.elements,s=i[0],r=i[4],a=i[8],o=i[1],c=i[5],l=i[9],u=i[2],d=i[6],h=i[10];switch(t){case"XYZ":if(this._y=Math.asin(Ge(a,-1,1)),Math.abs(a)<0.9999999)this._x=Math.atan2(-l,h),this._z=Math.atan2(-r,s);else this._x=Math.atan2(d,c),this._z=0;break;case"YXZ":if(this._x=Math.asin(-Ge(l,-1,1)),Math.abs(l)<0.9999999)this._y=Math.atan2(a,h),this._z=Math.atan2(o,c);else this._y=Math.atan2(-u,s),this._z=0;break;case"ZXY":if(this._x=Math.asin(Ge(d,-1,1)),Math.abs(d)<0.9999999)this._y=Math.atan2(-u,h),this._z=Math.atan2(-r,c);else this._y=0,this._z=Math.atan2(o,s);break;case"ZYX":if(this._y=Math.asin(-Ge(u,-1,1)),Math.abs(u)<0.9999999)this._x=Math.atan2(d,h),this._z=Math.atan2(o,s);else this._x=0,this._z=Math.atan2(-r,c);break;case"YZX":if(this._z=Math.asin(Ge(o,-1,1)),Math.abs(o)<0.9999999)this._x=Math.atan2(-l,c),this._y=Math.atan2(-u,s);else this._x=0,this._y=Math.atan2(a,h);break;case"XZY":if(this._z=Math.asin(-Ge(r,-1,1)),Math.abs(r)<0.9999999)this._x=Math.atan2(d,c),this._y=Math.atan2(a,s);else this._x=Math.atan2(-l,h),this._y=0;break;default:Ce("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}if(this._order=t,n===!0)this._onChangeCallback();return this}setFromQuaternion(e,t,n){return Il.makeRotationFromQuaternion(e),this.setFromRotationMatrix(Il,t,n)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return Pl.setFromEuler(this),this.setFromQuaternion(Pl,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){if(this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0)this._order=e[3];return this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}Nn.DEFAULT_ORDER="XYZ";class tr{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}var bu=0,Ll=new F,mi=new bn,mn=new ht,xs=new F,Xi=new F,wu=new F,Eu=new bn,Nl=new F(1,0,0),Dl=new F(0,1,0),Ul=new F(0,0,1),Fl={type:"added"},Tu={type:"removed"},gi={type:"childadded",child:null},zr={type:"childremoved",child:null};class It extends Mn{constructor(){super();this.isObject3D=!0,Object.defineProperty(this,"id",{value:bu++}),this.uuid=ns(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=It.DEFAULT_UP.clone();let e=new F,t=new Nn,n=new bn,i=new F(1,1,1);function s(){n.setFromEuler(t,!1)}function r(){t.setFromQuaternion(n,void 0,!1)}t._onChange(s),n._onChange(r),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:i},modelViewMatrix:{value:new ht},normalMatrix:{value:new Le}}),this.matrix=new ht,this.matrixWorld=new ht,this.matrixAutoUpdate=It.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=It.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new tr,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){if(this.matrixAutoUpdate)this.updateMatrix();this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return mi.setFromAxisAngle(e,t),this.quaternion.multiply(mi),this}rotateOnWorldAxis(e,t){return mi.setFromAxisAngle(e,t),this.quaternion.premultiply(mi),this}rotateX(e){return this.rotateOnAxis(Nl,e)}rotateY(e){return this.rotateOnAxis(Dl,e)}rotateZ(e){return this.rotateOnAxis(Ul,e)}translateOnAxis(e,t){return Ll.copy(e).applyQuaternion(this.quaternion),this.position.add(Ll.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(Nl,e)}translateY(e){return this.translateOnAxis(Dl,e)}translateZ(e){return this.translateOnAxis(Ul,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(mn.copy(this.matrixWorld).invert())}lookAt(e,t,n){if(e.isVector3)xs.copy(e);else xs.set(e,t,n);let i=this.parent;if(this.updateWorldMatrix(!0,!1),Xi.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight)mn.lookAt(Xi,xs,this.up);else mn.lookAt(xs,Xi,this.up);if(this.quaternion.setFromRotationMatrix(mn),i)mn.extractRotation(i.matrixWorld),mi.setFromRotationMatrix(mn),this.quaternion.premultiply(mi.invert())}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}if(e===this)return Pe("Object3D.add: object can't be added as a child of itself.",e),this;if(e&&e.isObject3D)e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(Fl),gi.child=e,this.dispatchEvent(gi),gi.child=null;else Pe("Object3D.add: object not an instance of THREE.Object3D.",e);return this}remove(e){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let t=this.children.indexOf(e);if(t!==-1)e.parent=null,this.children.splice(t,1),e.dispatchEvent(Tu),zr.child=e,this.dispatchEvent(zr),zr.child=null;return this}removeFromParent(){let e=this.parent;if(e!==null)e.remove(this);return this}clear(){return this.remove(...this.children)}attach(e){if(this.updateWorldMatrix(!0,!1),mn.copy(this.matrixWorld).invert(),e.parent!==null)e.parent.updateWorldMatrix(!0,!1),mn.multiply(e.parent.matrixWorld);return e.applyMatrix4(mn),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(Fl),gi.child=e,this.dispatchEvent(gi),gi.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let n=0,i=this.children.length;n<i;n++){let r=this.children[n].getObjectByProperty(e,t);if(r!==void 0)return r}return}getObjectsByProperty(e,t,n=[]){if(this[e]===t)n.push(this);let i=this.children;for(let s=0,r=i.length;s<r;s++)i[s].getObjectsByProperty(e,t,n);return n}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Xi,e,wu),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Xi,Eu,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);let t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}intersectsFrustum(){}traverse(e){e(this);let t=this.children;for(let n=0,i=t.length;n<i;n++)t[n].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);let t=this.children;for(let n=0,i=t.length;n<i;n++)t[n].traverseVisible(e)}traverseAncestors(e){let t=this.parent;if(t!==null)e(t),t.traverseAncestors(e)}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);let e=this.pivot;if(e!==null){let{x:t,y:n,z:i}=e,s=this.matrix.elements;s[12]+=t-s[0]*t-s[4]*n-s[8]*i,s[13]+=n-s[1]*t-s[5]*n-s[9]*i,s[14]+=i-s[2]*t-s[6]*n-s[10]*i}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){if(this.matrixAutoUpdate)this.updateMatrix();if(this.matrixWorldNeedsUpdate||e){if(this.matrixWorldAutoUpdate===!0)if(this.parent===null)this.matrixWorld.copy(this.matrix);else this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix);this.matrixWorldNeedsUpdate=!1,e=!0}let t=this.children;for(let n=0,i=t.length;n<i;n++)t[n].updateMatrixWorld(e)}updateWorldMatrix(e,t,n=!1){let i=this.parent;if(e===!0&&i!==null)i.updateWorldMatrix(!0,!1);if(this.matrixAutoUpdate)this.updateMatrix();if(this.matrixWorldNeedsUpdate||n){if(this.matrixWorldAutoUpdate===!0)if(this.parent===null)this.matrixWorld.copy(this.matrix);else this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix);this.matrixWorldNeedsUpdate=!1,n=!0}if(t===!0){let s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].updateWorldMatrix(!1,!0,n)}}toJSON(e){let t=e===void 0||typeof e==="string",n={};if(t)e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"};let i={};if(i.uuid=this.uuid,i.type=this.type,i.name=this.name,i.castShadow=this.castShadow,i.receiveShadow=this.receiveShadow,i.visible=this.visible,i.frustumCulled=this.frustumCulled,i.renderOrder=this.renderOrder,i.static=this.static,i.matrixAutoUpdate=this.matrixAutoUpdate,Object.keys(this.userData).length>0)i.userData=this.userData;if(i.layers=this.layers.mask,i.matrix=this.matrix.toArray(),i.up=this.up.toArray(),this.pivot!==null)i.pivot=this.pivot.toArray();if(this.morphTargetDictionary!==void 0)i.morphTargetDictionary=Object.assign({},this.morphTargetDictionary);if(this.morphTargetInfluences!==void 0)i.morphTargetInfluences=this.morphTargetInfluences.slice();if(this.isInstancedMesh){if(i.type="InstancedMesh",i.count=this.count,i.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null)i.instanceColor=this.instanceColor.toJSON()}if(this.isBatchedMesh){if(i.type="BatchedMesh",i.perObjectFrustumCulled=this.perObjectFrustumCulled,i.sortObjects=this.sortObjects,i.drawRanges=this._drawRanges,i.reservedRanges=this._reservedRanges,i.geometryInfo=this._geometryInfo.map((a)=>({...a,boundingBox:a.boundingBox?a.boundingBox.toJSON():void 0,boundingSphere:a.boundingSphere?a.boundingSphere.toJSON():void 0})),i.instanceInfo=this._instanceInfo.map((a)=>({...a})),i.availableInstanceIds=this._availableInstanceIds.slice(),i.availableGeometryIds=this._availableGeometryIds.slice(),i.nextIndexStart=this._nextIndexStart,i.nextVertexStart=this._nextVertexStart,i.geometryCount=this._geometryCount,i.maxInstanceCount=this._maxInstanceCount,i.maxVertexCount=this._maxVertexCount,i.maxIndexCount=this._maxIndexCount,i.geometryInitialized=this._geometryInitialized,i.matricesTexture=this._matricesTexture.toJSON(e),i.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null)i.colorsTexture=this._colorsTexture.toJSON(e);if(this.boundingSphere!==null)i.boundingSphere=this.boundingSphere.toJSON();if(this.boundingBox!==null)i.boundingBox=this.boundingBox.toJSON()}function s(a,o){if(a[o.uuid]===void 0)a[o.uuid]=o.toJSON(e);return o.uuid}if(this.isScene){if(this.background){if(this.background.isColor)i.background=this.background.toJSON();else if(this.background.isTexture)i.background=this.background.toJSON(e).uuid}if(this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0)i.environment=this.environment.toJSON(e).uuid}else if(this.isMesh||this.isLine||this.isPoints){i.geometry=s(e.geometries,this.geometry);let a=this.geometry.parameters;if(a!==void 0&&a.shapes!==void 0){let o=a.shapes;if(Array.isArray(o))for(let c=0,l=o.length;c<l;c++){let u=o[c];s(e.shapes,u)}else s(e.shapes,o)}}if(this.isSkinnedMesh){if(i.bindMode=this.bindMode,i.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0)s(e.skeletons,this.skeleton),i.skeleton=this.skeleton.uuid}if(this.material!==void 0)if(Array.isArray(this.material)){let a=[];for(let o=0,c=this.material.length;o<c;o++)a.push(s(e.materials,this.material[o]));i.material=a}else i.material=s(e.materials,this.material);if(this.children.length>0){i.children=[];for(let a=0;a<this.children.length;a++)i.children.push(this.children[a].toJSON(e).object)}if(this.animations.length>0){i.animations=[];for(let a=0;a<this.animations.length;a++){let o=this.animations[a];i.animations.push(s(e.animations,o))}}if(t){let a=r(e.geometries),o=r(e.materials),c=r(e.textures),l=r(e.images),u=r(e.shapes),d=r(e.skeletons),h=r(e.animations),m=r(e.nodes);if(a.length>0)n.geometries=a;if(o.length>0)n.materials=o;if(c.length>0)n.textures=c;if(l.length>0)n.images=l;if(u.length>0)n.shapes=u;if(d.length>0)n.skeletons=d;if(h.length>0)n.animations=h;if(m.length>0)n.nodes=m}return n.object=i,n;function r(a){let o=[];for(let c in a){let l=a[c];delete l.metadata,o.push(l)}return o}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let n=0;n<e.children.length;n++){let i=e.children[n];this.add(i.clone())}return this}dispose(){this.dispatchEvent({type:"dispose"})}}It.DEFAULT_UP=new F(0,1,0);It.DEFAULT_MATRIX_AUTO_UPDATE=!0;It.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;class Ln extends It{constructor(){super();this.isGroup=!0,this.type="Group"}}var Au={type:"move"};class ss{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){if(this._hand===null)this._hand=new Ln,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1};return this._hand}getTargetRaySpace(){if(this._targetRay===null)this._targetRay=new Ln,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new F,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new F;return this._targetRay}getGripSpace(){if(this._grip===null)this._grip=new Ln,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new F,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new F,this._grip.eventsEnabled=!1;return this._grip}dispatchEvent(e){if(this._targetRay!==null)this._targetRay.dispatchEvent(e);if(this._grip!==null)this._grip.dispatchEvent(e);if(this._hand!==null)this._hand.dispatchEvent(e);return this}connect(e){if(e&&e.hand){let t=this._hand;if(t)for(let n of e.hand.values())this._getHandJoint(t,n)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){if(this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null)this._targetRay.visible=!1;if(this._grip!==null)this._grip.visible=!1;if(this._hand!==null)this._hand.visible=!1;return this}update(e,t,n){let i=null,s=null,r=null,a=this._targetRay,o=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){r=!0;for(let v of e.hand.values()){let b=t.getJointPose(v,n),p=this._getHandJoint(c,v);if(b!==null)p.matrix.fromArray(b.transform.matrix),p.matrix.decompose(p.position,p.rotation,p.scale),p.matrixWorldNeedsUpdate=!0,p.jointRadius=b.radius;p.visible=b!==null}let l=c.joints["index-finger-tip"],u=c.joints["thumb-tip"],d=l.position.distanceTo(u.position),h=0.02,m=0.005;if(c.inputState.pinching&&d>h+m)c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this});else if(!c.inputState.pinching&&d<=h-m)c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this})}else if(o!==null&&e.gripSpace){if(s=t.getPose(e.gripSpace,n),s!==null){if(o.matrix.fromArray(s.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,s.linearVelocity)o.hasLinearVelocity=!0,o.linearVelocity.copy(s.linearVelocity);else o.hasLinearVelocity=!1;if(s.angularVelocity)o.hasAngularVelocity=!0,o.angularVelocity.copy(s.angularVelocity);else o.hasAngularVelocity=!1;if(o.eventsEnabled)o.dispatchEvent({type:"gripUpdated",data:e,target:this})}}if(a!==null){if(i=t.getPose(e.targetRaySpace,n),i===null&&s!==null)i=s;if(i!==null){if(a.matrix.fromArray(i.transform.matrix),a.matrix.decompose(a.position,a.rotation,a.scale),a.matrixWorldNeedsUpdate=!0,i.linearVelocity)a.hasLinearVelocity=!0,a.linearVelocity.copy(i.linearVelocity);else a.hasLinearVelocity=!1;if(i.angularVelocity)a.hasAngularVelocity=!0,a.angularVelocity.copy(i.angularVelocity);else a.hasAngularVelocity=!1;this.dispatchEvent(Au)}}}if(a!==null)a.visible=i!==null;if(o!==null)o.visible=s!==null;if(c!==null)c.visible=r!==null;return this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){let n=new Ln;n.matrixAutoUpdate=!1,n.visible=!1,e.joints[t.jointName]=n,e.add(n)}return e.joints[t.jointName]}}var Jc={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},Cn={h:0,s:0,l:0},vs={h:0,s:0,l:0};function kr(e,t,n){if(n<0)n+=1;if(n>1)n-=1;if(n<0.16666666666666666)return e+(t-e)*6*n;if(n<0.5)return t;if(n<0.6666666666666666)return e+(t-e)*6*(0.6666666666666666-n);return e}class qe{constructor(e,t,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,n)}set(e,t,n){if(t===void 0&&n===void 0){let i=e;if(i&&i.isColor)this.copy(i);else if(typeof i==="number")this.setHex(i);else if(typeof i==="string")this.setStyle(i)}else this.setRGB(e,t,n);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t="srgb"){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,ke.colorSpaceToWorking(this,t),this}setRGB(e,t,n,i=ke.workingColorSpace){return this.r=e,this.g=t,this.b=n,ke.colorSpaceToWorking(this,i),this}setHSL(e,t,n,i=ke.workingColorSpace){if(e=_u(e,1),t=Ge(t,0,1),n=Ge(n,0,1),t===0)this.r=this.g=this.b=n;else{let s=n<=0.5?n*(1+t):n+t-n*t,r=2*n-s;this.r=kr(r,s,e+0.3333333333333333),this.g=kr(r,s,e),this.b=kr(r,s,e-0.3333333333333333)}return ke.colorSpaceToWorking(this,i),this}setStyle(e,t="srgb"){function n(s){if(s===void 0)return;if(parseFloat(s)<1)Ce("Color: Alpha component of "+e+" will be ignored.")}let i;if(i=/^(\w+)\(([^\)]*)\)/.exec(e)){let s,r=i[1],a=i[2];switch(r){case"rgb":case"rgba":if(s=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(a))return n(s[4]),this.setRGB(Math.min(255,parseInt(s[1],10))/255,Math.min(255,parseInt(s[2],10))/255,Math.min(255,parseInt(s[3],10))/255,t);if(s=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(a))return n(s[4]),this.setRGB(Math.min(100,parseInt(s[1],10))/100,Math.min(100,parseInt(s[2],10))/100,Math.min(100,parseInt(s[3],10))/100,t);break;case"hsl":case"hsla":if(s=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(a))return n(s[4]),this.setHSL(parseFloat(s[1])/360,parseFloat(s[2])/100,parseFloat(s[3])/100,t);break;default:Ce("Color: Unknown color model "+e)}}else if(i=/^\#([A-Fa-f\d]+)$/.exec(e)){let s=i[1],r=s.length;if(r===3)return this.setRGB(parseInt(s.charAt(0),16)/15,parseInt(s.charAt(1),16)/15,parseInt(s.charAt(2),16)/15,t);else if(r===6)return this.setHex(parseInt(s,16),t);else Ce("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t="srgb"){let n=Jc[e.toLowerCase()];if(n!==void 0)this.setHex(n,t);else Ce("Color: Unknown color "+e);return this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=yn(e.r),this.g=yn(e.g),this.b=yn(e.b),this}copyLinearToSRGB(e){return this.r=Ti(e.r),this.g=Ti(e.g),this.b=Ti(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e="srgb"){return ke.workingToColorSpace(Ct.copy(this),e),Math.round(Ge(Ct.r*255,0,255))*65536+Math.round(Ge(Ct.g*255,0,255))*256+Math.round(Ge(Ct.b*255,0,255))}getHexString(e="srgb"){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=ke.workingColorSpace){ke.workingToColorSpace(Ct.copy(this),t);let{r:n,g:i,b:s}=Ct,r=Math.max(n,i,s),a=Math.min(n,i,s),o,c,l=(a+r)/2;if(a===r)o=0,c=0;else{let u=r-a;switch(c=l<=0.5?u/(r+a):u/(2-r-a),r){case n:o=(i-s)/u+(i<s?6:0);break;case i:o=(s-n)/u+2;break;case s:o=(n-i)/u+4;break}o/=6}return e.h=o,e.s=c,e.l=l,e}getRGB(e,t=ke.workingColorSpace){return ke.workingToColorSpace(Ct.copy(this),t),e.r=Ct.r,e.g=Ct.g,e.b=Ct.b,e}getStyle(e="srgb"){ke.workingToColorSpace(Ct.copy(this),e);let{r:t,g:n,b:i}=Ct;if(e!=="srgb")return`color(${e} ${t.toFixed(3)} ${n.toFixed(3)} ${i.toFixed(3)})`;return`rgb(${Math.round(t*255)},${Math.round(n*255)},${Math.round(i*255)})`}offsetHSL(e,t,n){return this.getHSL(Cn),this.setHSL(Cn.h+e,Cn.s+t,Cn.l+n)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,n){return this.r=e.r+(t.r-e.r)*n,this.g=e.g+(t.g-e.g)*n,this.b=e.b+(t.b-e.b)*n,this}lerpHSL(e,t){this.getHSL(Cn),e.getHSL(vs);let n=Dr(Cn.h,vs.h,t),i=Dr(Cn.s,vs.s,t),s=Dr(Cn.l,vs.l,t);return this.setHSL(n,i,s),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){let t=this.r,n=this.g,i=this.b,s=e.elements;return this.r=s[0]*t+s[3]*n+s[6]*i,this.g=s[1]*t+s[4]*n+s[7]*i,this.b=s[2]*t+s[5]*n+s[8]*i,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}var Ct=new qe;qe.NAMES=Jc;class nr extends It{constructor(){super();if(this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new Nn,this.environmentIntensity=1,this.environmentRotation=new Nn,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){if(super.copy(e,t),e.background!==null)this.background=e.background.clone();if(e.environment!==null)this.environment=e.environment.clone();if(e.fog!==null)this.fog=e.fog.clone();if(this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null)this.overrideMaterial=e.overrideMaterial.clone();return this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){let t=super.toJSON(e);if(this.fog!==null)t.object.fog=this.fog.toJSON();return t.object.backgroundBlurriness=this.backgroundBlurriness,t.object.backgroundIntensity=this.backgroundIntensity,t.object.backgroundRotation=this.backgroundRotation.toArray(),t.object.environmentIntensity=this.environmentIntensity,t.object.environmentRotation=this.environmentRotation.toArray(),t}}var Kt=new F,gn=new F,Gr=new F,_n=new F,_i=new F,xi=new F,Ol=new F,Hr=new F,Vr=new F,Wr=new F,Xr=new ut,qr=new ut,$r=new ut;class $t{constructor(e=new F,t=new F,n=new F){this.a=e,this.b=t,this.c=n}static getNormal(e,t,n,i){i.subVectors(n,t),Kt.subVectors(e,t),i.cross(Kt);let s=i.lengthSq();if(s>0)return i.multiplyScalar(1/Math.sqrt(s));return i.set(0,0,0)}static getBarycoord(e,t,n,i,s){Kt.subVectors(i,t),gn.subVectors(n,t),Gr.subVectors(e,t);let r=Kt.dot(Kt),a=Kt.dot(gn),o=Kt.dot(Gr),c=gn.dot(gn),l=gn.dot(Gr),u=r*c-a*a;if(u===0)return s.set(0,0,0),null;let d=1/u,h=(c*o-a*l)*d,m=(r*l-a*o)*d;return s.set(1-h-m,m,h)}static containsPoint(e,t,n,i){if(this.getBarycoord(e,t,n,i,_n)===null)return!1;return _n.x>=0&&_n.y>=0&&_n.x+_n.y<=1}static getInterpolation(e,t,n,i,s,r,a,o){if(this.getBarycoord(e,t,n,i,_n)===null){if(o.x=0,o.y=0,"z"in o)o.z=0;if("w"in o)o.w=0;return null}return o.setScalar(0),o.addScaledVector(s,_n.x),o.addScaledVector(r,_n.y),o.addScaledVector(a,_n.z),o}static getInterpolatedAttribute(e,t,n,i,s,r){return Xr.setScalar(0),qr.setScalar(0),$r.setScalar(0),Xr.fromBufferAttribute(e,t),qr.fromBufferAttribute(e,n),$r.fromBufferAttribute(e,i),r.setScalar(0),r.addScaledVector(Xr,s.x),r.addScaledVector(qr,s.y),r.addScaledVector($r,s.z),r}static isFrontFacing(e,t,n,i){return Kt.subVectors(n,t),gn.subVectors(e,t),Kt.cross(gn).dot(i)<0}set(e,t,n){return this.a.copy(e),this.b.copy(t),this.c.copy(n),this}setFromPointsAndIndices(e,t,n,i){return this.a.copy(e[t]),this.b.copy(e[n]),this.c.copy(e[i]),this}setFromAttributeAndIndices(e,t,n,i){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,n),this.c.fromBufferAttribute(e,i),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return Kt.subVectors(this.c,this.b),gn.subVectors(this.a,this.b),Kt.cross(gn).length()*0.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(0.3333333333333333)}getNormal(e){return $t.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return $t.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,n,i,s){return $t.getInterpolation(e,this.a,this.b,this.c,t,n,i,s)}containsPoint(e){return $t.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return $t.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){let n=this.a,i=this.b,s=this.c,r,a;_i.subVectors(i,n),xi.subVectors(s,n),Hr.subVectors(e,n);let o=_i.dot(Hr),c=xi.dot(Hr);if(o<=0&&c<=0)return t.copy(n);Vr.subVectors(e,i);let l=_i.dot(Vr),u=xi.dot(Vr);if(l>=0&&u<=l)return t.copy(i);let d=o*u-l*c;if(d<=0&&o>=0&&l<=0)return r=o/(o-l),t.copy(n).addScaledVector(_i,r);Wr.subVectors(e,s);let h=_i.dot(Wr),m=xi.dot(Wr);if(m>=0&&h<=m)return t.copy(s);let v=h*c-o*m;if(v<=0&&c>=0&&m<=0)return a=c/(c-m),t.copy(n).addScaledVector(xi,a);let b=l*m-h*u;if(b<=0&&u-l>=0&&h-m>=0)return Ol.subVectors(s,i),a=(u-l)/(u-l+(h-m)),t.copy(i).addScaledVector(Ol,a);let p=1/(b+v+d);return r=v*p,a=d*p,t.copy(n).addScaledVector(_i,r).addScaledVector(xi,a)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}class Kn{constructor(e=new F(1/0,1/0,1/0),t=new F(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t+=3)this.expandByPoint(jt.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,n=e.count;t<n;t++)this.expandByPoint(jt.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){let n=jt.copy(t).multiplyScalar(0.5);return this.min.copy(e).sub(n),this.max.copy(e).add(n),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(0.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);let n=e.geometry;if(n!==void 0){let s=n.getAttribute("position");if(t===!0&&s!==void 0&&e.isInstancedMesh!==!0)for(let r=0,a=s.count;r<a;r++){if(e.isMesh===!0)e.getVertexPosition(r,jt);else jt.fromBufferAttribute(s,r);jt.applyMatrix4(e.matrixWorld),this.expandByPoint(jt)}else{if(e.boundingBox!==void 0){if(e.boundingBox===null)e.computeBoundingBox();ys.copy(e.boundingBox)}else{if(n.boundingBox===null)n.computeBoundingBox();ys.copy(n.boundingBox)}ys.applyMatrix4(e.matrixWorld),this.union(ys)}}let i=e.children;for(let s=0,r=i.length;s<r;s++)this.expandByObject(i[s],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,jt),jt.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,n;if(e.normal.x>0)t=e.normal.x*this.min.x,n=e.normal.x*this.max.x;else t=e.normal.x*this.max.x,n=e.normal.x*this.min.x;if(e.normal.y>0)t+=e.normal.y*this.min.y,n+=e.normal.y*this.max.y;else t+=e.normal.y*this.max.y,n+=e.normal.y*this.min.y;if(e.normal.z>0)t+=e.normal.z*this.min.z,n+=e.normal.z*this.max.z;else t+=e.normal.z*this.max.z,n+=e.normal.z*this.min.z;return t<=-e.constant&&n>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(qi),Ss.subVectors(this.max,qi),vi.subVectors(e.a,qi),yi.subVectors(e.b,qi),Si.subVectors(e.c,qi),Rn.subVectors(yi,vi),In.subVectors(Si,yi),kn.subVectors(vi,Si);let t=[0,-Rn.z,Rn.y,0,-In.z,In.y,0,-kn.z,kn.y,Rn.z,0,-Rn.x,In.z,0,-In.x,kn.z,0,-kn.x,-Rn.y,Rn.x,0,-In.y,In.x,0,-kn.y,kn.x,0];if(!Yr(t,vi,yi,Si,Ss))return!1;if(t=[1,0,0,0,1,0,0,0,1],!Yr(t,vi,yi,Si,Ss))return!1;return Ms.crossVectors(Rn,In),t=[Ms.x,Ms.y,Ms.z],Yr(t,vi,yi,Si,Ss)}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,jt).distanceTo(e)}getBoundingSphere(e){if(this.isEmpty())e.makeEmpty();else this.getCenter(e.center),e.radius=this.getSize(jt).length()*0.5;return e}intersect(e){if(this.min.max(e.min),this.max.min(e.max),this.isEmpty())this.makeEmpty();return this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){if(this.isEmpty())return this;return xn[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),xn[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),xn[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),xn[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),xn[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),xn[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),xn[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),xn[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(xn),this}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}var xn=[new F,new F,new F,new F,new F,new F,new F,new F],jt=new F,ys=new Kn,vi=new F,yi=new F,Si=new F,Rn=new F,In=new F,kn=new F,qi=new F,Ss=new F,Ms=new F,Gn=new F;function Yr(e,t,n,i,s){for(let r=0,a=e.length-3;r<=a;r+=3){Gn.fromArray(e,r);let o=s.x*Math.abs(Gn.x)+s.y*Math.abs(Gn.y)+s.z*Math.abs(Gn.z),c=t.dot(Gn),l=n.dot(Gn),u=i.dot(Gn);if(Math.max(-Math.max(c,l,u),Math.min(c,l,u))>o)return!1}return!0}var mt=new F,bs=new Xe,Cu=0;class Ht extends Mn{constructor(e,t,n=!1){super();if(Array.isArray(e))throw TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Cu++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=n,this.usage=35044,this.updateRanges=[],this.gpuType=1015,this.version=0}onUploadCallback(){}set needsUpdate(e){if(e===!0)this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,n){e*=this.itemSize,n*=t.itemSize;for(let i=0,s=this.itemSize;i<s;i++)this.array[e+i]=t.array[n+i];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,n=this.count;t<n;t++)bs.fromBufferAttribute(this,t),bs.applyMatrix3(e),this.setXY(t,bs.x,bs.y);else if(this.itemSize===3)for(let t=0,n=this.count;t<n;t++)mt.fromBufferAttribute(this,t),mt.applyMatrix3(e),this.setXYZ(t,mt.x,mt.y,mt.z);return this}applyMatrix4(e){for(let t=0,n=this.count;t<n;t++)mt.fromBufferAttribute(this,t),mt.applyMatrix4(e),this.setXYZ(t,mt.x,mt.y,mt.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)mt.fromBufferAttribute(this,t),mt.applyNormalMatrix(e),this.setXYZ(t,mt.x,mt.y,mt.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)mt.fromBufferAttribute(this,t),mt.transformDirection(e),this.setXYZ(t,mt.x,mt.y,mt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let n=this.array[e*this.itemSize+t];if(this.normalized)n=Wi(n,this.array);return n}setComponent(e,t,n){if(this.normalized)n=Ot(n,this.array);return this.array[e*this.itemSize+t]=n,this}getX(e){let t=this.array[e*this.itemSize];if(this.normalized)t=Wi(t,this.array);return t}setX(e,t){if(this.normalized)t=Ot(t,this.array);return this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];if(this.normalized)t=Wi(t,this.array);return t}setY(e,t){if(this.normalized)t=Ot(t,this.array);return this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];if(this.normalized)t=Wi(t,this.array);return t}setZ(e,t){if(this.normalized)t=Ot(t,this.array);return this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];if(this.normalized)t=Wi(t,this.array);return t}setW(e,t){if(this.normalized)t=Ot(t,this.array);return this.array[e*this.itemSize+3]=t,this}setXY(e,t,n){if(e*=this.itemSize,this.normalized)t=Ot(t,this.array),n=Ot(n,this.array);return this.array[e+0]=t,this.array[e+1]=n,this}setXYZ(e,t,n,i){if(e*=this.itemSize,this.normalized)t=Ot(t,this.array),n=Ot(n,this.array),i=Ot(i,this.array);return this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=i,this}setXYZW(e,t,n,i,s){if(e*=this.itemSize,this.normalized)t=Ot(t,this.array),n=Ot(n,this.array),i=Ot(i,this.array),s=Ot(s,this.array);return this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=i,this.array[e+3]=s,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return e.name=this.name,e.usage=this.usage,e.gpuType=this.gpuType,e}dispose(){this.dispatchEvent({type:"dispose"})}}class ir extends Ht{constructor(e,t,n){super(new Uint16Array(e),t,n)}}class sr extends Ht{constructor(e,t,n){super(new Uint32Array(e),t,n)}}class vt extends Ht{constructor(e,t,n){super(new Float32Array(e),t,n)}}var Ru=new Kn,$i=new F,Zr=new F;class Ni{constructor(e=new F,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){let n=this.center;if(t!==void 0)n.copy(t);else Ru.setFromPoints(e).getCenter(n);let i=0;for(let s=0,r=e.length;s<r;s++)i=Math.max(i,n.distanceToSquared(e[s]));return this.radius=Math.sqrt(i),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){let t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){let n=this.center.distanceToSquared(e);if(t.copy(e),n>this.radius*this.radius)t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center);return t}getBoundingBox(e){if(this.isEmpty())return e.makeEmpty(),e;return e.set(this.center,this.center),e.expandByScalar(this.radius),e}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;$i.subVectors(e,this.center);let t=$i.lengthSq();if(t>this.radius*this.radius){let n=Math.sqrt(t),i=(n-this.radius)*0.5;this.center.addScaledVector($i,i/n),this.radius+=i}return this}union(e){if(e.isEmpty())return this;if(this.isEmpty())return this.copy(e),this;if(this.center.equals(e.center)===!0)this.radius=Math.max(this.radius,e.radius);else Zr.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint($i.copy(e.center).add(Zr)),this.expandByPoint($i.copy(e.center).sub(Zr));return this}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}var Iu=0,qt=new ht,Jr=new It,Mi=new F,Gt=new Kn,Yi=new Kn,Mt=new F;class bt extends Mn{constructor(){super();this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:Iu++}),this.uuid=ns(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(e){if(Array.isArray(e))this.index=new((mu(e))?sr:ir)(e,1);else this.index=e;return this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,n=0){this.groups.push({start:e,count:t,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){let t=this.attributes.position;if(t!==void 0)t.applyMatrix4(e),t.needsUpdate=!0;let n=this.attributes.normal;if(n!==void 0){let s=new Le().getNormalMatrix(e);n.applyNormalMatrix(s),n.needsUpdate=!0}let i=this.attributes.tangent;if(i!==void 0)i.transformDirection(e),i.needsUpdate=!0;if(this.boundingBox!==null)this.computeBoundingBox();if(this.boundingSphere!==null)this.computeBoundingSphere();return this._transformed=!0,this}applyQuaternion(e){return qt.makeRotationFromQuaternion(e),this.applyMatrix4(qt),this}rotateX(e){return qt.makeRotationX(e),this.applyMatrix4(qt),this}rotateY(e){return qt.makeRotationY(e),this.applyMatrix4(qt),this}rotateZ(e){return qt.makeRotationZ(e),this.applyMatrix4(qt),this}translate(e,t,n){return qt.makeTranslation(e,t,n),this.applyMatrix4(qt),this}scale(e,t,n){return qt.makeScale(e,t,n),this.applyMatrix4(qt),this}lookAt(e){return Jr.lookAt(e),Jr.updateMatrix(),this.applyMatrix4(Jr.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(Mi).negate(),this.translate(Mi.x,Mi.y,Mi.z),this}setFromPoints(e){let t=this.getAttribute("position");if(t===void 0){let n=[];for(let i=0,s=e.length;i<s;i++){let r=e[i];n.push(r.x,r.y,r.z||0)}this.setAttribute("position",new vt(n,3))}else{let n=Math.min(e.length,t.count);for(let i=0;i<n;i++){let s=e[i];t.setXYZ(i,s.x,s.y,s.z||0)}if(e.length>t.count)Ce("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry.");t.needsUpdate=!0}return this}computeBoundingBox(){if(this.boundingBox===null)this.boundingBox=new Kn;let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Pe("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new F(-1/0,-1/0,-1/0),new F(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let n=0,i=t.length;n<i;n++){let s=t[n];if(Gt.setFromBufferAttribute(s),this.morphTargetsRelative)Mt.addVectors(this.boundingBox.min,Gt.min),this.boundingBox.expandByPoint(Mt),Mt.addVectors(this.boundingBox.max,Gt.max),this.boundingBox.expandByPoint(Mt);else this.boundingBox.expandByPoint(Gt.min),this.boundingBox.expandByPoint(Gt.max)}}else this.boundingBox.makeEmpty();if(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))Pe('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){if(this.boundingSphere===null)this.boundingSphere=new Ni;let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Pe("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new F,1/0);return}if(e){let n=this.boundingSphere.center;if(Gt.setFromBufferAttribute(e),t)for(let s=0,r=t.length;s<r;s++){let a=t[s];if(Yi.setFromBufferAttribute(a),this.morphTargetsRelative)Mt.addVectors(Gt.min,Yi.min),Gt.expandByPoint(Mt),Mt.addVectors(Gt.max,Yi.max),Gt.expandByPoint(Mt);else Gt.expandByPoint(Yi.min),Gt.expandByPoint(Yi.max)}Gt.getCenter(n);let i=0;for(let s=0,r=e.count;s<r;s++)Mt.fromBufferAttribute(e,s),i=Math.max(i,n.distanceToSquared(Mt));if(t)for(let s=0,r=t.length;s<r;s++){let a=t[s],o=this.morphTargetsRelative;for(let c=0,l=a.count;c<l;c++){if(Mt.fromBufferAttribute(a,c),o)Mi.fromBufferAttribute(e,c),Mt.add(Mi);i=Math.max(i,n.distanceToSquared(Mt))}}if(this.boundingSphere.radius=Math.sqrt(i),isNaN(this.boundingSphere.radius))Pe('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){Pe("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let{position:n,normal:i,uv:s}=t,r=this.getAttribute("tangent");if(r===void 0||r.count!==n.count)r=new Ht(new Float32Array(4*n.count),4),this.setAttribute("tangent",r);let a=[],o=[];for(let A=0;A<n.count;A++)a[A]=new F,o[A]=new F;let c=new F,l=new F,u=new F,d=new Xe,h=new Xe,m=new Xe,v=new F,b=new F;function p(A,x,M){c.fromBufferAttribute(n,A),l.fromBufferAttribute(n,x),u.fromBufferAttribute(n,M),d.fromBufferAttribute(s,A),h.fromBufferAttribute(s,x),m.fromBufferAttribute(s,M),l.sub(c),u.sub(c),h.sub(d),m.sub(d);let H=1/(h.x*m.y-m.x*h.y);if(!isFinite(H))return;v.copy(l).multiplyScalar(m.y).addScaledVector(u,-h.y).multiplyScalar(H),b.copy(u).multiplyScalar(h.x).addScaledVector(l,-m.x).multiplyScalar(H),a[A].add(v),a[x].add(v),a[M].add(v),o[A].add(b),o[x].add(b),o[M].add(b)}let f=this.groups;if(f.length===0)f=[{start:0,count:e.count}];for(let A=0,x=f.length;A<x;++A){let M=f[A],{start:H,count:D}=M;for(let U=H,J=H+D;U<J;U+=3)p(e.getX(U+0),e.getX(U+1),e.getX(U+2))}let T=new F,I=new F,S=new F,w=new F;function E(A){S.fromBufferAttribute(i,A),w.copy(S);let x=a[A];T.copy(x),T.sub(S.multiplyScalar(S.dot(x))).normalize(),I.crossVectors(w,x);let H=I.dot(o[A])<0?-1:1;r.setXYZW(A,T.x,T.y,T.z,H)}for(let A=0,x=f.length;A<x;++A){let M=f[A],{start:H,count:D}=M;for(let U=H,J=H+D;U<J;U+=3)E(e.getX(U+0)),E(e.getX(U+1)),E(e.getX(U+2))}this._transformed=!0}computeVertexNormals(){let e=this.index,t=this.getAttribute("position");if(t!==void 0){let n=this.getAttribute("normal");if(n===void 0||n.count!==t.count)n=new Ht(new Float32Array(t.count*3),3),this.setAttribute("normal",n);else for(let d=0,h=n.count;d<h;d++)n.setXYZ(d,0,0,0);let i=new F,s=new F,r=new F,a=new F,o=new F,c=new F,l=new F,u=new F;if(e)for(let d=0,h=e.count;d<h;d+=3){let m=e.getX(d+0),v=e.getX(d+1),b=e.getX(d+2);i.fromBufferAttribute(t,m),s.fromBufferAttribute(t,v),r.fromBufferAttribute(t,b),l.subVectors(r,s),u.subVectors(i,s),l.cross(u),a.fromBufferAttribute(n,m),o.fromBufferAttribute(n,v),c.fromBufferAttribute(n,b),a.add(l),o.add(l),c.add(l),n.setXYZ(m,a.x,a.y,a.z),n.setXYZ(v,o.x,o.y,o.z),n.setXYZ(b,c.x,c.y,c.z)}else for(let d=0,h=t.count;d<h;d+=3)i.fromBufferAttribute(t,d+0),s.fromBufferAttribute(t,d+1),r.fromBufferAttribute(t,d+2),l.subVectors(r,s),u.subVectors(i,s),l.cross(u),n.setXYZ(d+0,l.x,l.y,l.z),n.setXYZ(d+1,l.x,l.y,l.z),n.setXYZ(d+2,l.x,l.y,l.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let e=this.attributes.normal;for(let t=0,n=e.count;t<n;t++)Mt.fromBufferAttribute(e,t),Mt.normalize(),e.setXYZ(t,Mt.x,Mt.y,Mt.z)}toNonIndexed(){function e(a,o){let{array:c,itemSize:l,normalized:u}=a,d=new c.constructor(o.length*l),h=0,m=0;for(let v=0,b=o.length;v<b;v++){if(a.isInterleavedBufferAttribute)h=o[v]*a.data.stride+a.offset;else h=o[v]*l;for(let p=0;p<l;p++)d[m++]=c[h++]}return new Ht(d,l,u)}if(this.index===null)return Ce("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let t=new bt,n=this.index.array,i=this.attributes;for(let a in i){let o=i[a],c=e(o,n);t.setAttribute(a,c)}let s=this.morphAttributes;for(let a in s){let o=[],c=s[a];for(let l=0,u=c.length;l<u;l++){let d=c[l],h=e(d,n);o.push(h)}t.morphAttributes[a]=o}t.morphTargetsRelative=this.morphTargetsRelative;let r=this.groups;for(let a=0,o=r.length;a<o;a++){let c=r[a];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){let e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,e.name=this.name,Object.keys(this.userData).length>0)e.userData=this.userData;if(this.parameters!==void 0&&this._transformed!==!0){let o=this.parameters;for(let c in o)if(o[c]!==void 0)e[c]=o[c];return e}e.data={attributes:{}};let t=this.index;if(t!==null)e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)};let n=this.attributes;for(let o in n){let c=n[o];e.data.attributes[o]=c.toJSON(e.data)}let i={},s=!1;for(let o in this.morphAttributes){let c=this.morphAttributes[o],l=[];for(let u=0,d=c.length;u<d;u++){let h=c[u];l.push(h.toJSON(e.data))}if(l.length>0)i[o]=l,s=!0}if(s)e.data.morphAttributes=i,e.data.morphTargetsRelative=this.morphTargetsRelative;let r=this.groups;if(r.length>0)e.data.groups=JSON.parse(JSON.stringify(r));let a=this.boundingSphere;if(a!==null)e.data.boundingSphere=a.toJSON();return e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let t={};this.name=e.name;let n=e.index;if(n!==null)this.setIndex(n.clone());let i=e.attributes;for(let c in i){let l=i[c];this.setAttribute(c,l.clone(t))}let s=e.morphAttributes;for(let c in s){let l=[],u=s[c];for(let d=0,h=u.length;d<h;d++)l.push(u[d].clone(t));this.morphAttributes[c]=l}this.morphTargetsRelative=e.morphTargetsRelative;let r=e.groups;for(let c=0,l=r.length;c<l;c++){let u=r[c];this.addGroup(u.start,u.count,u.materialIndex)}let a=e.boundingBox;if(a!==null)this.boundingBox=a.clone();let o=e.boundingSphere;if(o!==null)this.boundingSphere=o.clone();return this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this._transformed=e._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}}var Kr=new F,Pu=new F,Lu=new Le;class on{constructor(e=new F(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,n,i){return this.normal.set(e,t,n),this.constant=i,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,n){let i=Kr.subVectors(n,t).cross(Pu.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(i,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){let e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t,n=!0){let i=e.delta(Kr),s=this.normal.dot(i);if(s===0){if(this.distanceToPoint(e.start)===0)return t.copy(e.start);return null}let r=-(e.start.dot(this.normal)+this.constant)/s;if(n===!0&&(r<0||r>1))return null;return t.copy(e.start).addScaledVector(i,r)}intersectsLine(e){let t=this.distanceToPoint(e.start),n=this.distanceToPoint(e.end);return t<0&&n>0||n<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){let n=t||Lu.getNormalMatrix(e),i=this.coplanarPoint(Kr).applyMatrix4(e),s=this.normal.applyMatrix3(n).normalize();return this.constant=-i.dot(s),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}toJSON(){return{normal:this.normal.toArray(),constant:this.constant}}fromJSON(e){return this.normal.fromArray(e.normal),this.constant=e.constant,this}}var Nu=0;class jn extends Mn{constructor(){super();this.isMaterial=!0,Object.defineProperty(this,"id",{value:Nu++}),this.uuid=ns(),this.name="",this.type="Material",this.blending=1,this.side=0,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=204,this.blendDst=205,this.blendEquation=100,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new qe(0,0,0),this.blendAlpha=0,this.depthFunc=3,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=519,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=7680,this.stencilZFail=7680,this.stencilZPass=7680,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){if(this._alphaTest>0!==e>0)this.version++;this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e===void 0)return;for(let t in e){let n=e[t];if(n===void 0){Ce(`Material: parameter '${t}' has value of undefined.`);continue}let i=this[t];if(i===void 0){Ce(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}if(i&&i.isColor)i.set(n);else if(i&&i.isVector2&&(n&&n.isVector2)||i&&i.isEuler&&(n&&n.isEuler)||i&&i.isVector3&&(n&&n.isVector3))i.copy(n);else this[t]=n}}toJSON(e){let t=e===void 0||typeof e==="string";if(t)e={textures:{},images:{}};let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};if(n.uuid=this.uuid,n.type=this.type,n.blending=this.blending,n.side=this.side,n.shadowSide=this.shadowSide,n.vertexColors=this.vertexColors,n.opacity=this.opacity,n.transparent=this.transparent,n.blendSrc=this.blendSrc,n.blendDst=this.blendDst,n.blendEquation=this.blendEquation,n.blendSrcAlpha=this.blendSrcAlpha,n.blendDstAlpha=this.blendDstAlpha,n.blendEquationAlpha=this.blendEquationAlpha,n.blendColor=this.blendColor.getHex(),n.blendAlpha=this.blendAlpha,n.depthFunc=this.depthFunc,n.depthTest=this.depthTest,n.depthWrite=this.depthWrite,n.colorWrite=this.colorWrite,n.clipIntersection=this.clipIntersection,n.clipShadows=this.clipShadows,n.stencilWriteMask=this.stencilWriteMask,n.stencilFunc=this.stencilFunc,n.stencilRef=this.stencilRef,n.stencilFuncMask=this.stencilFuncMask,n.stencilFail=this.stencilFail,n.stencilZFail=this.stencilZFail,n.stencilZPass=this.stencilZPass,n.stencilWrite=this.stencilWrite,n.polygonOffset=this.polygonOffset,n.polygonOffsetFactor=this.polygonOffsetFactor,n.polygonOffsetUnits=this.polygonOffsetUnits,n.dithering=this.dithering,n.alphaTest=this.alphaTest,n.alphaHash=this.alphaHash,n.alphaToCoverage=this.alphaToCoverage,n.premultipliedAlpha=this.premultipliedAlpha,n.forceSinglePass=this.forceSinglePass,n.allowOverride=this.allowOverride,n.visible=this.visible,n.toneMapped=this.toneMapped,n.name=this.name,this.color&&this.color.isColor)n.color=this.color.getHex();if(this.roughness!==void 0)n.roughness=this.roughness;if(this.metalness!==void 0)n.metalness=this.metalness;if(this.sheen!==void 0)n.sheen=this.sheen;if(this.sheenColor&&this.sheenColor.isColor)n.sheenColor=this.sheenColor.getHex();if(this.sheenRoughness!==void 0)n.sheenRoughness=this.sheenRoughness;if(this.emissive&&this.emissive.isColor)n.emissive=this.emissive.getHex();if(this.emissiveIntensity!==void 0)n.emissiveIntensity=this.emissiveIntensity;if(this.specular&&this.specular.isColor)n.specular=this.specular.getHex();if(this.specularIntensity!==void 0)n.specularIntensity=this.specularIntensity;if(this.specularColor&&this.specularColor.isColor)n.specularColor=this.specularColor.getHex();if(this.shininess!==void 0)n.shininess=this.shininess;if(this.clearcoat!==void 0)n.clearcoat=this.clearcoat;if(this.clearcoatRoughness!==void 0)n.clearcoatRoughness=this.clearcoatRoughness;if(this.clearcoatMap&&this.clearcoatMap.isTexture)n.clearcoatMap=this.clearcoatMap.toJSON(e).uuid;if(this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture)n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid;if(this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture)n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray();if(this.sheenColorMap&&this.sheenColorMap.isTexture)n.sheenColorMap=this.sheenColorMap.toJSON(e).uuid;if(this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture)n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid;if(this.dispersion!==void 0)n.dispersion=this.dispersion;if(this.retroreflectivity!==void 0)n.retroreflectivity=this.retroreflectivity;if(this.iridescence!==void 0)n.iridescence=this.iridescence;if(this.iridescenceIOR!==void 0)n.iridescenceIOR=this.iridescenceIOR;if(this.iridescenceThicknessRange!==void 0)n.iridescenceThicknessRange=this.iridescenceThicknessRange;if(this.iridescenceMap&&this.iridescenceMap.isTexture)n.iridescenceMap=this.iridescenceMap.toJSON(e).uuid;if(this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture)n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid;if(this.anisotropy!==void 0)n.anisotropy=this.anisotropy;if(this.anisotropyRotation!==void 0)n.anisotropyRotation=this.anisotropyRotation;if(this.anisotropyMap&&this.anisotropyMap.isTexture)n.anisotropyMap=this.anisotropyMap.toJSON(e).uuid;if(this.map&&this.map.isTexture)n.map=this.map.toJSON(e).uuid;if(this.matcap&&this.matcap.isTexture)n.matcap=this.matcap.toJSON(e).uuid;if(this.alphaMap&&this.alphaMap.isTexture)n.alphaMap=this.alphaMap.toJSON(e).uuid;if(this.lightMap&&this.lightMap.isTexture)n.lightMap=this.lightMap.toJSON(e).uuid,n.lightMapIntensity=this.lightMapIntensity;if(this.aoMap&&this.aoMap.isTexture)n.aoMap=this.aoMap.toJSON(e).uuid,n.aoMapIntensity=this.aoMapIntensity;if(this.bumpMap&&this.bumpMap.isTexture)n.bumpMap=this.bumpMap.toJSON(e).uuid,n.bumpScale=this.bumpScale;if(this.normalMap&&this.normalMap.isTexture)n.normalMap=this.normalMap.toJSON(e).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray();if(this.displacementMap&&this.displacementMap.isTexture)n.displacementMap=this.displacementMap.toJSON(e).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias;if(this.roughnessMap&&this.roughnessMap.isTexture)n.roughnessMap=this.roughnessMap.toJSON(e).uuid;if(this.metalnessMap&&this.metalnessMap.isTexture)n.metalnessMap=this.metalnessMap.toJSON(e).uuid;if(this.emissiveMap&&this.emissiveMap.isTexture)n.emissiveMap=this.emissiveMap.toJSON(e).uuid;if(this.specularMap&&this.specularMap.isTexture)n.specularMap=this.specularMap.toJSON(e).uuid;if(this.specularIntensityMap&&this.specularIntensityMap.isTexture)n.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid;if(this.specularColorMap&&this.specularColorMap.isTexture)n.specularColorMap=this.specularColorMap.toJSON(e).uuid;if(this.envMap&&this.envMap.isTexture){if(n.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0)n.combine=this.combine}if(this.envMapRotation!==void 0)n.envMapRotation=this.envMapRotation.toArray();if(this.envMapIntensity!==void 0)n.envMapIntensity=this.envMapIntensity;if(this.reflectivity!==void 0)n.reflectivity=this.reflectivity;if(this.refractionRatio!==void 0)n.refractionRatio=this.refractionRatio;if(this.gradientMap&&this.gradientMap.isTexture)n.gradientMap=this.gradientMap.toJSON(e).uuid;if(this.transmission!==void 0)n.transmission=this.transmission;if(this.transmissionMap&&this.transmissionMap.isTexture)n.transmissionMap=this.transmissionMap.toJSON(e).uuid;if(this.thickness!==void 0)n.thickness=this.thickness;if(this.thicknessMap&&this.thicknessMap.isTexture)n.thicknessMap=this.thicknessMap.toJSON(e).uuid;if(this.attenuationDistance!==void 0)n.attenuationDistance=this.attenuationDistance;if(this.attenuationColor!==void 0)n.attenuationColor=this.attenuationColor.getHex();if(this.size!==void 0)n.size=this.size;if(this.sizeAttenuation!==void 0)n.sizeAttenuation=this.sizeAttenuation;if(Array.isArray(this.clippingPlanes)&&this.clippingPlanes.length>0)n.clippingPlanes=this.clippingPlanes.map((s)=>s.toJSON());if(this.rotation!==void 0)n.rotation=this.rotation;if(this.depthPacking!==void 0)n.depthPacking=this.depthPacking;if(this.linewidth!==void 0)n.linewidth=this.linewidth;if(this.linecap!==void 0)n.linecap=this.linecap;if(this.linejoin!==void 0)n.linejoin=this.linejoin;if(this.dashSize!==void 0)n.dashSize=this.dashSize;if(this.gapSize!==void 0)n.gapSize=this.gapSize;if(this.scale!==void 0)n.scale=this.scale;if(this.wireframe!==void 0)n.wireframe=this.wireframe;if(this.wireframeLinewidth!==void 0)n.wireframeLinewidth=this.wireframeLinewidth;if(this.wireframeLinecap!==void 0)n.wireframeLinecap=this.wireframeLinecap;if(this.wireframeLinejoin!==void 0)n.wireframeLinejoin=this.wireframeLinejoin;if(this.flatShading!==void 0)n.flatShading=this.flatShading;if(this.fog!==void 0)n.fog=this.fog;if(Object.keys(this.userData).length>0)n.userData=this.userData;function i(s){let r=[];for(let a in s){let o=s[a];delete o.metadata,r.push(o)}return r}if(t){let s=i(e.textures),r=i(e.images);if(s.length>0)n.textures=s;if(r.length>0)n.images=r}return n}fromJSON(e,t){if(e.uuid!==void 0)this.uuid=e.uuid;if(e.name!==void 0)this.name=e.name;if(e.color!==void 0&&this.color!==void 0)this.color.setHex(e.color);if(e.roughness!==void 0)this.roughness=e.roughness;if(e.metalness!==void 0)this.metalness=e.metalness;if(e.sheen!==void 0)this.sheen=e.sheen;if(e.sheenColor!==void 0)this.sheenColor=new qe().setHex(e.sheenColor);if(e.sheenRoughness!==void 0)this.sheenRoughness=e.sheenRoughness;if(e.emissive!==void 0&&this.emissive!==void 0)this.emissive.setHex(e.emissive);if(e.specular!==void 0&&this.specular!==void 0)this.specular.setHex(e.specular);if(e.specularIntensity!==void 0)this.specularIntensity=e.specularIntensity;if(e.specularColor!==void 0&&this.specularColor!==void 0)this.specularColor.setHex(e.specularColor);if(e.shininess!==void 0)this.shininess=e.shininess;if(e.clearcoat!==void 0)this.clearcoat=e.clearcoat;if(e.clearcoatRoughness!==void 0)this.clearcoatRoughness=e.clearcoatRoughness;if(e.dispersion!==void 0)this.dispersion=e.dispersion;if(e.retroreflectivity!==void 0)this.retroreflectivity=e.retroreflectivity;if(e.iridescence!==void 0)this.iridescence=e.iridescence;if(e.iridescenceIOR!==void 0)this.iridescenceIOR=e.iridescenceIOR;if(e.iridescenceThicknessRange!==void 0)this.iridescenceThicknessRange=e.iridescenceThicknessRange;if(e.transmission!==void 0)this.transmission=e.transmission;if(e.thickness!==void 0)this.thickness=e.thickness;if(e.attenuationDistance!==void 0)this.attenuationDistance=e.attenuationDistance;if(e.attenuationColor!==void 0&&this.attenuationColor!==void 0)this.attenuationColor.setHex(e.attenuationColor);if(e.anisotropy!==void 0)this.anisotropy=e.anisotropy;if(e.anisotropyRotation!==void 0)this.anisotropyRotation=e.anisotropyRotation;if(e.fog!==void 0)this.fog=e.fog;if(e.flatShading!==void 0)this.flatShading=e.flatShading;if(e.blending!==void 0)this.blending=e.blending;if(e.combine!==void 0)this.combine=e.combine;if(e.side!==void 0)this.side=e.side;if(e.shadowSide!==void 0)this.shadowSide=e.shadowSide;if(e.opacity!==void 0)this.opacity=e.opacity;if(e.transparent!==void 0)this.transparent=e.transparent;if(e.alphaTest!==void 0)this.alphaTest=e.alphaTest;if(e.alphaHash!==void 0)this.alphaHash=e.alphaHash;if(e.depthFunc!==void 0)this.depthFunc=e.depthFunc;if(e.depthTest!==void 0)this.depthTest=e.depthTest;if(e.depthWrite!==void 0)this.depthWrite=e.depthWrite;if(e.colorWrite!==void 0)this.colorWrite=e.colorWrite;if(e.clippingPlanes!==void 0)this.clippingPlanes=e.clippingPlanes.map((n)=>new on().fromJSON(n));if(e.clipIntersection!==void 0)this.clipIntersection=e.clipIntersection;if(e.clipShadows!==void 0)this.clipShadows=e.clipShadows;if(e.depthPacking!==void 0)this.depthPacking=e.depthPacking;if(e.blendSrc!==void 0)this.blendSrc=e.blendSrc;if(e.blendDst!==void 0)this.blendDst=e.blendDst;if(e.blendEquation!==void 0)this.blendEquation=e.blendEquation;if(e.blendSrcAlpha!==void 0)this.blendSrcAlpha=e.blendSrcAlpha;if(e.blendDstAlpha!==void 0)this.blendDstAlpha=e.blendDstAlpha;if(e.blendEquationAlpha!==void 0)this.blendEquationAlpha=e.blendEquationAlpha;if(e.blendColor!==void 0&&this.blendColor!==void 0)this.blendColor.setHex(e.blendColor);if(e.blendAlpha!==void 0)this.blendAlpha=e.blendAlpha;if(e.stencilWriteMask!==void 0)this.stencilWriteMask=e.stencilWriteMask;if(e.stencilFunc!==void 0)this.stencilFunc=e.stencilFunc;if(e.stencilRef!==void 0)this.stencilRef=e.stencilRef;if(e.stencilFuncMask!==void 0)this.stencilFuncMask=e.stencilFuncMask;if(e.stencilFail!==void 0)this.stencilFail=e.stencilFail;if(e.stencilZFail!==void 0)this.stencilZFail=e.stencilZFail;if(e.stencilZPass!==void 0)this.stencilZPass=e.stencilZPass;if(e.stencilWrite!==void 0)this.stencilWrite=e.stencilWrite;if(e.wireframe!==void 0)this.wireframe=e.wireframe;if(e.wireframeLinewidth!==void 0)this.wireframeLinewidth=e.wireframeLinewidth;if(e.wireframeLinecap!==void 0)this.wireframeLinecap=e.wireframeLinecap;if(e.wireframeLinejoin!==void 0)this.wireframeLinejoin=e.wireframeLinejoin;if(e.rotation!==void 0)this.rotation=e.rotation;if(e.linewidth!==void 0)this.linewidth=e.linewidth;if(e.linecap!==void 0)this.linecap=e.linecap;if(e.linejoin!==void 0)this.linejoin=e.linejoin;if(e.dashSize!==void 0)this.dashSize=e.dashSize;if(e.gapSize!==void 0)this.gapSize=e.gapSize;if(e.scale!==void 0)this.scale=e.scale;if(e.polygonOffset!==void 0)this.polygonOffset=e.polygonOffset;if(e.polygonOffsetFactor!==void 0)this.polygonOffsetFactor=e.polygonOffsetFactor;if(e.polygonOffsetUnits!==void 0)this.polygonOffsetUnits=e.polygonOffsetUnits;if(e.dithering!==void 0)this.dithering=e.dithering;if(e.alphaToCoverage!==void 0)this.alphaToCoverage=e.alphaToCoverage;if(e.premultipliedAlpha!==void 0)this.premultipliedAlpha=e.premultipliedAlpha;if(e.forceSinglePass!==void 0)this.forceSinglePass=e.forceSinglePass;if(e.allowOverride!==void 0)this.allowOverride=e.allowOverride;if(e.visible!==void 0)this.visible=e.visible;if(e.toneMapped!==void 0)this.toneMapped=e.toneMapped;if(e.userData!==void 0)this.userData=e.userData;if(e.vertexColors!==void 0)if(typeof e.vertexColors==="number")this.vertexColors=e.vertexColors>0;else this.vertexColors=e.vertexColors;if(e.size!==void 0)this.size=e.size;if(e.sizeAttenuation!==void 0)this.sizeAttenuation=e.sizeAttenuation;if(e.map!==void 0)this.map=t[e.map]||null;if(e.matcap!==void 0)this.matcap=t[e.matcap]||null;if(e.alphaMap!==void 0)this.alphaMap=t[e.alphaMap]||null;if(e.bumpMap!==void 0)this.bumpMap=t[e.bumpMap]||null;if(e.bumpScale!==void 0)this.bumpScale=e.bumpScale;if(e.normalMap!==void 0)this.normalMap=t[e.normalMap]||null;if(e.normalMapType!==void 0)this.normalMapType=e.normalMapType;if(e.normalScale!==void 0){let n=e.normalScale;if(Array.isArray(n)===!1)n=[n,n];this.normalScale=new Xe().fromArray(n)}if(e.displacementMap!==void 0)this.displacementMap=t[e.displacementMap]||null;if(e.displacementScale!==void 0)this.displacementScale=e.displacementScale;if(e.displacementBias!==void 0)this.displacementBias=e.displacementBias;if(e.roughnessMap!==void 0)this.roughnessMap=t[e.roughnessMap]||null;if(e.metalnessMap!==void 0)this.metalnessMap=t[e.metalnessMap]||null;if(e.emissiveMap!==void 0)this.emissiveMap=t[e.emissiveMap]||null;if(e.emissiveIntensity!==void 0)this.emissiveIntensity=e.emissiveIntensity;if(e.specularMap!==void 0)this.specularMap=t[e.specularMap]||null;if(e.specularIntensityMap!==void 0)this.specularIntensityMap=t[e.specularIntensityMap]||null;if(e.specularColorMap!==void 0)this.specularColorMap=t[e.specularColorMap]||null;if(e.envMap!==void 0)this.envMap=t[e.envMap]||null;if(e.envMapRotation!==void 0)this.envMapRotation.fromArray(e.envMapRotation);if(e.envMapIntensity!==void 0)this.envMapIntensity=e.envMapIntensity;if(e.reflectivity!==void 0)this.reflectivity=e.reflectivity;if(e.refractionRatio!==void 0)this.refractionRatio=e.refractionRatio;if(e.lightMap!==void 0)this.lightMap=t[e.lightMap]||null;if(e.lightMapIntensity!==void 0)this.lightMapIntensity=e.lightMapIntensity;if(e.aoMap!==void 0)this.aoMap=t[e.aoMap]||null;if(e.aoMapIntensity!==void 0)this.aoMapIntensity=e.aoMapIntensity;if(e.gradientMap!==void 0)this.gradientMap=t[e.gradientMap]||null;if(e.clearcoatMap!==void 0)this.clearcoatMap=t[e.clearcoatMap]||null;if(e.clearcoatRoughnessMap!==void 0)this.clearcoatRoughnessMap=t[e.clearcoatRoughnessMap]||null;if(e.clearcoatNormalMap!==void 0)this.clearcoatNormalMap=t[e.clearcoatNormalMap]||null;if(e.clearcoatNormalScale!==void 0)this.clearcoatNormalScale=new Xe().fromArray(e.clearcoatNormalScale);if(e.iridescenceMap!==void 0)this.iridescenceMap=t[e.iridescenceMap]||null;if(e.iridescenceThicknessMap!==void 0)this.iridescenceThicknessMap=t[e.iridescenceThicknessMap]||null;if(e.transmissionMap!==void 0)this.transmissionMap=t[e.transmissionMap]||null;if(e.thicknessMap!==void 0)this.thicknessMap=t[e.thicknessMap]||null;if(e.anisotropyMap!==void 0)this.anisotropyMap=t[e.anisotropyMap]||null;if(e.sheenColorMap!==void 0)this.sheenColorMap=t[e.sheenColorMap]||null;if(e.sheenRoughnessMap!==void 0)this.sheenRoughnessMap=t[e.sheenRoughnessMap]||null;return this}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;let t=e.clippingPlanes,n=null;if(t!==null){let i=t.length;n=Array(i);for(let s=0;s!==i;++s)n[s]=t[s].clone()}return this.clippingPlanes=n,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){if(e===!0)this.version++}}var vn=new F,jr=new F,ws=new F,Es=new F;class rr{constructor(e=new F,t=new F(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,vn)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);let n=t.dot(this.direction);if(n<0)return t.copy(this.origin);return t.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){let t=vn.subVectors(e,this.origin).dot(this.direction);if(t<0)return this.origin.distanceToSquared(e);return vn.copy(this.origin).addScaledVector(this.direction,t),vn.distanceToSquared(e)}distanceSqToSegment(e,t,n,i){jr.copy(e).add(t).multiplyScalar(0.5),ws.copy(t).sub(e).normalize(),Es.copy(this.origin).sub(jr);let s=e.distanceTo(t)*0.5,r=-this.direction.dot(ws),a=Es.dot(this.direction),o=-Es.dot(ws),c=Es.lengthSq(),l=Math.abs(1-r*r),u,d,h,m;if(l>0)if(u=r*o-a,d=r*a-o,m=s*l,u>=0)if(d>=-m)if(d<=m){let v=1/l;u*=v,d*=v,h=u*(u+r*d+2*a)+d*(r*u+d+2*o)+c}else d=s,u=Math.max(0,-(r*d+a)),h=-u*u+d*(d+2*o)+c;else d=-s,u=Math.max(0,-(r*d+a)),h=-u*u+d*(d+2*o)+c;else if(d<=-m)u=Math.max(0,-(-r*s+a)),d=u>0?-s:Math.min(Math.max(-s,-o),s),h=-u*u+d*(d+2*o)+c;else if(d<=m)u=0,d=Math.min(Math.max(-s,-o),s),h=d*(d+2*o)+c;else u=Math.max(0,-(r*s+a)),d=u>0?s:Math.min(Math.max(-s,-o),s),h=-u*u+d*(d+2*o)+c;else d=r>0?-s:s,u=Math.max(0,-(r*d+a)),h=-u*u+d*(d+2*o)+c;if(n)n.copy(this.origin).addScaledVector(this.direction,u);if(i)i.copy(jr).addScaledVector(ws,d);return h}intersectSphere(e,t){if(e.radius<0)return null;vn.subVectors(e.center,this.origin);let n=vn.dot(this.direction),i=vn.dot(vn)-n*n,s=e.radius*e.radius;if(i>s)return null;let r=Math.sqrt(s-i),a=n-r,o=n+r;if(o<0)return null;if(a<0)return this.at(o,t);return this.at(a,t)}intersectsSphere(e){if(e.radius<0)return!1;return this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){let t=e.normal.dot(this.direction);if(t===0){if(e.distanceToPoint(this.origin)===0)return 0;return null}let n=-(this.origin.dot(e.normal)+e.constant)/t;return n>=0?n:null}intersectPlane(e,t){let n=this.distanceToPlane(e);if(n===null)return null;return this.at(n,t)}intersectsPlane(e){let t=e.distanceToPoint(this.origin);if(t===0)return!0;if(e.normal.dot(this.direction)*t<0)return!0;return!1}intersectBox(e,t){let n,i,s,r,a,o,c=1/this.direction.x,l=1/this.direction.y,u=1/this.direction.z,d=this.origin;if(c>=0)n=(e.min.x-d.x)*c,i=(e.max.x-d.x)*c;else n=(e.max.x-d.x)*c,i=(e.min.x-d.x)*c;if(l>=0)s=(e.min.y-d.y)*l,r=(e.max.y-d.y)*l;else s=(e.max.y-d.y)*l,r=(e.min.y-d.y)*l;if(n>r||s>i)return null;if(s>n||isNaN(n))n=s;if(r<i||isNaN(i))i=r;if(u>=0)a=(e.min.z-d.z)*u,o=(e.max.z-d.z)*u;else a=(e.max.z-d.z)*u,o=(e.min.z-d.z)*u;if(n>o||a>i)return null;if(a>n||n!==n)n=a;if(o<i||i!==i)i=o;if(i<0)return null;return this.at(n>=0?n:i,t)}intersectsBox(e){return this.intersectBox(e,vn)!==null}intersectTriangle(e,t,n,i,s){let r=this.origin,a=this.direction,{x:o,y:c,z:l}=a,u=e.x-r.x,d=e.y-r.y,h=e.z-r.z,m=t.x-r.x,v=t.y-r.y,b=t.z-r.z,p=n.x-r.x,f=n.y-r.y,T=n.z-r.z,I=Math.abs(o),S=Math.abs(c),w=Math.abs(l),E,A,x,M,H,D,U,J,C,V,K,G;if(I>=S&&I>=w)if(x=o,D=u,C=m,G=p,o>=0)E=c,A=l,M=d,H=h,U=v,J=b,V=f,K=T;else E=l,A=c,M=h,H=d,U=b,J=v,V=T,K=f;else if(S>=w)if(x=c,D=d,C=v,G=f,c>=0)E=l,A=o,M=h,H=u,U=b,J=m,V=T,K=p;else E=o,A=l,M=u,H=h,U=m,J=b,V=p,K=T;else if(x=l,D=h,C=b,G=T,l>=0)E=o,A=c,M=u,H=d,U=m,J=v,V=p,K=f;else E=c,A=o,M=d,H=u,U=v,J=m,V=f,K=p;if(x===0)return null;let ne=E/x,X=A/x,j=1/x,te=M-ne*D,Re=H-X*D,Ee=U-ne*C,it=J-X*C,Oe=V-ne*G,q=K-X*G,ie=Oe*it-q*Ee,re=te*q-Re*Oe,Te=Ee*Re-it*te;if(i){if(ie<0||re<0||Te<0)return null}else if((ie<0||re<0||Te<0)&&(ie>0||re>0||Te>0))return null;let Ie=ie+re+Te;if(Ie===0)return null;let be=j*(ie*D+re*C+Te*G);if(Ie>0?be<0:be>0)return null;return this.at(be/Ie,s)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class Fn extends jn{constructor(e){super();this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new qe(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Nn,this.combine=0,this.reflectivity=1,this.refractionRatio=0.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}var Bl=new ht,Hn=new rr,Ts=new Ni,zl=new F,As=new F,Cs=new F,Rs=new F,Qr=new F,Is=new F,kl=new F,Ps=new F;class Dt extends It{constructor(e=new bt,t=new Fn){super();this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){if(super.copy(e,t),e.morphTargetInfluences!==void 0)this.morphTargetInfluences=e.morphTargetInfluences.slice();if(e.morphTargetDictionary!==void 0)this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary);return this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let i=t[n[0]];if(i!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,r=i.length;s<r;s++){let a=i[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[a]=s}}}}getVertexPosition(e,t){let n=this.geometry,i=n.attributes.position,s=n.morphAttributes.position,r=n.morphTargetsRelative;t.fromBufferAttribute(i,e);let a=this.morphTargetInfluences;if(s&&a){Is.set(0,0,0);for(let o=0,c=s.length;o<c;o++){let l=a[o],u=s[o];if(l===0)continue;if(Qr.fromBufferAttribute(u,e),r)Is.addScaledVector(Qr,l);else Is.addScaledVector(Qr.sub(t),l)}t.add(Is)}return t}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,i=this.material,s=this.matrixWorld;if(i===void 0)return;if(n.boundingSphere===null)n.computeBoundingSphere();if(Ts.copy(n.boundingSphere),Ts.applyMatrix4(s),Hn.copy(e.ray).recast(e.near),Ts.containsPoint(Hn.origin)===!1){if(Hn.intersectSphere(Ts,zl)===null)return;if(Hn.origin.distanceToSquared(zl)>(e.far-e.near)**2)return}if(Bl.copy(s).invert(),Hn.copy(e.ray).applyMatrix4(Bl),n.boundingBox!==null){if(Hn.intersectsBox(n.boundingBox)===!1)return}this._computeIntersections(e,t,Hn)}_computeIntersections(e,t,n){let i,s=this.geometry,r=this.material,a=s.index,o=s.attributes.position,c=s.attributes.uv,l=s.attributes.uv1,u=s.attributes.normal,{groups:d,drawRange:h}=s;if(a!==null)if(Array.isArray(r))for(let m=0,v=d.length;m<v;m++){let b=d[m],p=r[b.materialIndex],f=Math.max(b.start,h.start),T=Math.min(a.count,Math.min(b.start+b.count,h.start+h.count));for(let I=f,S=T;I<S;I+=3){let w=a.getX(I),E=a.getX(I+1),A=a.getX(I+2);if(i=Ls(this,p,e,n,c,l,u,w,E,A),i)i.faceIndex=Math.floor(I/3),i.face.materialIndex=b.materialIndex,t.push(i)}}else{let m=Math.max(0,h.start),v=Math.min(a.count,h.start+h.count);for(let b=m,p=v;b<p;b+=3){let f=a.getX(b),T=a.getX(b+1),I=a.getX(b+2);if(i=Ls(this,r,e,n,c,l,u,f,T,I),i)i.faceIndex=Math.floor(b/3),t.push(i)}}else if(o!==void 0)if(Array.isArray(r))for(let m=0,v=d.length;m<v;m++){let b=d[m],p=r[b.materialIndex],f=Math.max(b.start,h.start),T=Math.min(o.count,Math.min(b.start+b.count,h.start+h.count));for(let I=f,S=T;I<S;I+=3){let w=I,E=I+1,A=I+2;if(i=Ls(this,p,e,n,c,l,u,w,E,A),i)i.faceIndex=Math.floor(I/3),i.face.materialIndex=b.materialIndex,t.push(i)}}else{let m=Math.max(0,h.start),v=Math.min(o.count,h.start+h.count);for(let b=m,p=v;b<p;b+=3){let f=b,T=b+1,I=b+2;if(i=Ls(this,r,e,n,c,l,u,f,T,I),i)i.faceIndex=Math.floor(b/3),t.push(i)}}}}function Du(e,t,n,i,s,r,a,o){let c;if(t.side===1)c=i.intersectTriangle(a,r,s,!0,o);else c=i.intersectTriangle(s,r,a,t.side===0,o);if(c===null)return null;Ps.copy(o),Ps.applyMatrix4(e.matrixWorld);let l=n.ray.origin.distanceTo(Ps);if(l<n.near||l>n.far)return null;return{distance:l,point:Ps.clone(),object:e}}function Ls(e,t,n,i,s,r,a,o,c,l){e.getVertexPosition(o,As),e.getVertexPosition(c,Cs),e.getVertexPosition(l,Rs);let u=Du(e,t,n,i,As,Cs,Rs,kl);if(u){let d=new F;if($t.getBarycoord(kl,As,Cs,Rs,d),s)u.uv=$t.getInterpolatedAttribute(s,o,c,l,d,new Xe);if(r)u.uv1=$t.getInterpolatedAttribute(r,o,c,l,d,new Xe);if(a){if(u.normal=$t.getInterpolatedAttribute(a,o,c,l,d,new F),u.normal.dot(i.direction)>0)u.normal.multiplyScalar(-1)}let h={a:o,b:c,c:l,normal:new F,materialIndex:0};$t.getNormal(As,Cs,Rs,h.normal),u.face=h,u.barycoord=d}return u}class ao extends Rt{constructor(e=null,t=1,n=1,i,s,r,a,o,c=1003,l=1003,u,d){super(null,r,a,o,c,l,i,s,u,d);this.isDataTexture=!0,this.image={data:e,width:t,height:n},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}var Vn=new Ni,Uu=new Xe(0.5,0.5),Ns=new F;class ar{constructor(e=new on,t=new on,n=new on,i=new on,s=new on,r=new on){this.planes=[e,t,n,i,s,r]}set(e,t,n,i,s,r){let a=this.planes;return a[0].copy(e),a[1].copy(t),a[2].copy(n),a[3].copy(i),a[4].copy(s),a[5].copy(r),this}copy(e){let t=this.planes;for(let n=0;n<6;n++)t[n].copy(e.planes[n]);return this}setFromProjectionMatrix(e,t=2000,n=!1){let i=this.planes,s=e.elements,r=s[0],a=s[1],o=s[2],c=s[3],l=s[4],u=s[5],d=s[6],h=s[7],m=s[8],v=s[9],b=s[10],p=s[11],f=s[12],T=s[13],I=s[14],S=s[15];if(i[0].setComponents(c-r,h-l,p-m,S-f).normalize(),i[1].setComponents(c+r,h+l,p+m,S+f).normalize(),i[2].setComponents(c+a,h+u,p+v,S+T).normalize(),i[3].setComponents(c-a,h-u,p-v,S-T).normalize(),n)i[4].setComponents(o,d,b,I).normalize(),i[5].setComponents(c-o,h-d,p-b,S-I).normalize();else if(i[4].setComponents(c-o,h-d,p-b,S-I).normalize(),t===2000)i[5].setComponents(c+o,h+d,p+b,S+I).normalize();else if(t===2001)i[5].setComponents(o,d,b,I).normalize();else throw Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0){if(e.boundingSphere===null)e.computeBoundingSphere();Vn.copy(e.boundingSphere).applyMatrix4(e.matrixWorld)}else{let t=e.geometry;if(t.boundingSphere===null)t.computeBoundingSphere();Vn.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Vn)}intersectsSprite(e){Vn.center.set(0,0,0);let t=Uu.distanceTo(e.center);return Vn.radius=0.7071067811865476+t,Vn.applyMatrix4(e.matrixWorld),this.intersectsSphere(Vn)}intersectsSphere(e){let t=this.planes,n=e.center,i=-e.radius;for(let s=0;s<6;s++)if(t[s].distanceToPoint(n)<i)return!1;return!0}intersectsBox(e){let t=this.planes;for(let n=0;n<6;n++){let i=t[n];if(Ns.x=i.normal.x>0?e.max.x:e.min.x,Ns.y=i.normal.y>0?e.max.y:e.min.y,Ns.z=i.normal.z>0?e.max.z:e.min.z,i.distanceToPoint(Ns)<0)return!1}return!0}containsPoint(e){let t=this.planes;for(let n=0;n<6;n++)if(t[n].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class Qn extends jn{constructor(e){super();this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new qe(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}}var ks=new F,Gs=new F,Gl=new ht,Zi=new rr,Ds=new Ni,ea=new F,Hl=new F;class ei extends It{constructor(e=new bt,t=new Qn){super();this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){let e=this.geometry;if(e.index===null){let t=e.attributes.position,n=[0];for(let i=1,s=t.count;i<s;i++)ks.fromBufferAttribute(t,i-1),Gs.fromBufferAttribute(t,i),n[i]=n[i-1],n[i]+=ks.distanceTo(Gs);e.setAttribute("lineDistance",new vt(n,1))}else Ce("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,i=this.matrixWorld,s=e.params.Line.threshold,r=n.drawRange;if(n.boundingSphere===null)n.computeBoundingSphere();if(Ds.copy(n.boundingSphere),Ds.applyMatrix4(i),Ds.radius+=s,e.ray.intersectsSphere(Ds)===!1)return;Gl.copy(i).invert(),Zi.copy(e.ray).applyMatrix4(Gl);let a=s/((this.scale.x+this.scale.y+this.scale.z)/3),o=a*a,c=this.isLineSegments?2:1,l=n.index,d=n.attributes.position;if(l!==null){let h=Math.max(0,r.start),m=Math.min(l.count,r.start+r.count);for(let v=h,b=m-1;v<b;v+=c){let p=l.getX(v),f=l.getX(v+1),T=Us(this,e,Zi,o,p,f,v);if(T)t.push(T)}if(this.isLineLoop){let v=l.getX(m-1),b=l.getX(h),p=Us(this,e,Zi,o,v,b,m-1);if(p)t.push(p)}}else{let h=Math.max(0,r.start),m=Math.min(d.count,r.start+r.count);for(let v=h,b=m-1;v<b;v+=c){let p=Us(this,e,Zi,o,v,v+1,v);if(p)t.push(p)}if(this.isLineLoop){let v=Us(this,e,Zi,o,m-1,h,m-1);if(v)t.push(v)}}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let i=t[n[0]];if(i!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,r=i.length;s<r;s++){let a=i[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[a]=s}}}}}function Us(e,t,n,i,s,r,a){let o=e.geometry.attributes.position;if(ks.fromBufferAttribute(o,s),Gs.fromBufferAttribute(o,r),n.distanceSqToSegment(ks,Gs,ea,Hl)>i)return;ea.applyMatrix4(e.matrixWorld);let l=t.ray.origin.distanceTo(ea);if(l<t.near||l>t.far)return;return{distance:l,point:Hl.clone().applyMatrix4(e.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:e}}class or extends Rt{constructor(e=[],t=301,n,i,s,r,a,o,c,l){super(e,t,n,i,s,r,a,o,c,l);this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class ti extends Rt{constructor(e,t,n=1014,i,s,r,a=1003,o=1003,c,l=1026,u=1){if(l!==1026&&l!==1027)throw Error("THREE.DepthTexture: format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let d={width:e,height:t,depth:u};super(d,i,s,r,a,o,l,n,c);this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new is(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){let t=super.toJSON(e);return t.compareFunction=this.compareFunction,t}}class oo extends ti{constructor(e,t=1014,n=301,i,s,r=1003,a=1003,o,c=1026){let l={width:e,height:e,depth:1},u=[l,l,l,l,l,l];super(e,e,t,n,i,s,r,a,o,c);this.image=u,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}}class lr extends Rt{constructor(e=null){super();this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class Di extends bt{constructor(e=1,t=1,n=1,i=1,s=1,r=1){super();this.type="BoxGeometry",this.parameters={width:e,height:t,depth:n,widthSegments:i,heightSegments:s,depthSegments:r};let a=this;i=Math.floor(i),s=Math.floor(s),r=Math.floor(r);let o=[],c=[],l=[],u=[],d=0,h=0;m("z","y","x",-1,-1,n,t,e,r,s,0),m("z","y","x",1,-1,n,t,-e,r,s,1),m("x","z","y",1,1,e,n,t,i,r,2),m("x","z","y",1,-1,e,n,-t,i,r,3),m("x","y","z",1,-1,e,t,n,i,s,4),m("x","y","z",-1,-1,e,t,-n,i,s,5),this.setIndex(o),this.setAttribute("position",new vt(c,3)),this.setAttribute("normal",new vt(l,3)),this.setAttribute("uv",new vt(u,2));function m(v,b,p,f,T,I,S,w,E,A,x){let M=I/E,H=S/A,D=I/2,U=S/2,J=w/2,C=E+1,V=A+1,K=0,G=0,ne=new F;for(let X=0;X<V;X++){let j=X*H-U;for(let te=0;te<C;te++){let Re=te*M-D;ne[v]=Re*f,ne[b]=j*T,ne[p]=J,c.push(ne.x,ne.y,ne.z),ne[v]=0,ne[b]=0,ne[p]=w>0?1:-1,l.push(ne.x,ne.y,ne.z),u.push(te/E),u.push(1-X/A),K+=1}}for(let X=0;X<A;X++)for(let j=0;j<E;j++){let te=d+j+C*X,Re=d+j+C*(X+1),Ee=d+(j+1)+C*(X+1),it=d+(j+1)+C*X;o.push(te,Re,it),o.push(Re,Ee,it),G+=6}a.addGroup(h,G,x),h+=G,d+=K}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Di(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}class cr extends bt{constructor(e=1,t=1,n=1,i=32,s=1,r=!1,a=0,o=Math.PI*2){super();this.type="CylinderGeometry",this.parameters={radiusTop:e,radiusBottom:t,height:n,radialSegments:i,heightSegments:s,openEnded:r,thetaStart:a,thetaLength:o};let c=this;i=Math.floor(i),s=Math.floor(s);let l=[],u=[],d=[],h=[],m=0,v=[],b=n/2,p=0;if(f(),r===!1){if(e>0)T(!0);if(t>0)T(!1)}this.setIndex(l),this.setAttribute("position",new vt(u,3)),this.setAttribute("normal",new vt(d,3)),this.setAttribute("uv",new vt(h,2));function f(){let I=new F,S=new F,w=0,E=(t-e)/n;for(let A=0;A<=s;A++){let x=[],M=A/s,H=M*(t-e)+e;for(let D=0;D<=i;D++){let U=D/i,J=U*o+a,C=Math.sin(J),V=Math.cos(J);S.x=H*C,S.y=-M*n+b,S.z=H*V,u.push(S.x,S.y,S.z),I.set(C,E,V).normalize(),d.push(I.x,I.y,I.z),h.push(U,1-M),x.push(m++)}v.push(x)}for(let A=0;A<i;A++)for(let x=0;x<s;x++){let M=v[x][A],H=v[x+1][A],D=v[x+1][A+1],U=v[x][A+1];if(e>0||x!==0)l.push(M,H,U),w+=3;if(t>0||x!==s-1)l.push(H,D,U),w+=3}c.addGroup(p,w,0),p+=w}function T(I){let S=m,w=new Xe,E=new F,A=0,x=I===!0?e:t,M=I===!0?1:-1;for(let D=1;D<=i;D++)u.push(0,b*M,0),d.push(0,M,0),h.push(0.5,0.5),m++;let H=m;for(let D=0;D<=i;D++){let J=D/i*o+a,C=Math.cos(J),V=Math.sin(J);E.x=x*V,E.y=b*M,E.z=x*C,u.push(E.x,E.y,E.z),d.push(0,M,0),w.x=C*0.5+0.5,w.y=V*0.5*M+0.5,h.push(w.x,w.y),m++}for(let D=0;D<i;D++){let U=S+D,J=H+D;if(I===!0)l.push(J,J+1,U);else l.push(J+1,J,U);A+=3}c.addGroup(p,A,I===!0?1:2),p+=A}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new cr(e.radiusTop,e.radiusBottom,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}}class hr extends cr{constructor(e=1,t=1,n=32,i=1,s=!1,r=0,a=Math.PI*2){super(0,e,t,n,i,s,r,a);this.type="ConeGeometry",this.parameters={radius:e,height:t,radialSegments:n,heightSegments:i,openEnded:s,thetaStart:r,thetaLength:a}}static fromJSON(e){return new hr(e.radius,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}}class rs extends bt{constructor(e=1,t=1,n=1,i=1){super();this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:n,heightSegments:i};let s=e/2,r=t/2,a=Math.floor(n),o=Math.floor(i),c=a+1,l=o+1,u=e/a,d=t/o,h=[],m=[],v=[],b=[];for(let p=0;p<l;p++){let f=p*d-r;for(let T=0;T<c;T++){let I=T*u-s;m.push(I,-f,0),v.push(0,0,1),b.push(T/a),b.push(1-p/o)}}for(let p=0;p<o;p++)for(let f=0;f<a;f++){let T=f+c*p,I=f+c*(p+1),S=f+1+c*(p+1),w=f+1+c*p;h.push(T,I,w),h.push(I,S,w)}this.setIndex(h),this.setAttribute("position",new vt(m,3)),this.setAttribute("normal",new vt(v,3)),this.setAttribute("uv",new vt(b,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new rs(e.width,e.height,e.widthSegments,e.heightSegments)}}class Ui extends bt{constructor(e=1,t=32,n=16,i=0,s=Math.PI*2,r=0,a=Math.PI){super();this.type="SphereGeometry",this.parameters={radius:e,widthSegments:t,heightSegments:n,phiStart:i,phiLength:s,thetaStart:r,thetaLength:a},t=Math.max(3,Math.floor(t)),n=Math.max(2,Math.floor(n));let o=Math.min(r+a,Math.PI),c=0,l=[],u=new F,d=new F,h=[],m=[],v=[],b=[];for(let p=0;p<=n;p++){let f=[],T=p/n,I=r+T*a,S=e*Math.cos(I),w=Math.sqrt(e*e-S*S),E=0;if(p===0&&r===0)E=0.5/t;else if(p===n&&o===Math.PI)E=-0.5/t;for(let A=0;A<=t;A++){let x=A/t,M=i+x*s;u.x=-w*Math.cos(M),u.y=S,u.z=w*Math.sin(M),m.push(u.x,u.y,u.z),d.copy(u).normalize(),v.push(d.x,d.y,d.z),b.push(x+E,1-T),f.push(c++)}l.push(f)}for(let p=0;p<n;p++)for(let f=0;f<t;f++){let T=l[p][f+1],I=l[p][f],S=l[p+1][f],w=l[p+1][f+1];if(p!==0||r>0)h.push(T,I,w);if(p!==n-1||o<Math.PI)h.push(I,S,w)}this.setIndex(h),this.setAttribute("position",new vt(m,3)),this.setAttribute("normal",new vt(v,3)),this.setAttribute("uv",new vt(b,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Ui(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}}function ni(e){let t={};for(let n in e){t[n]={};for(let i in e[n]){let s=e[n][i];if(Vl(s))if(s.isRenderTargetTexture)Ce("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),t[n][i]=null;else t[n][i]=s.clone();else if(Array.isArray(s))if(Vl(s[0])){let r=[];for(let a=0,o=s.length;a<o;a++)r[a]=s[a].clone();t[n][i]=r}else t[n][i]=s.slice();else t[n][i]=s}}return t}function Pt(e){let t={};for(let n=0;n<e.length;n++){let i=ni(e[n]);for(let s in i)t[s]=i[s]}return t}function Vl(e){return e&&(e.isColor||e.isMatrix3||e.isMatrix4||e.isVector2||e.isVector3||e.isVector4||e.isTexture||e.isQuaternion)}function Fu(e){let t=[];for(let n=0;n<e.length;n++)t.push(e[n].clone());return t}function lo(e){let t=e.getRenderTarget();if(t===null)return e.outputColorSpace;if(t.isXRRenderTarget===!0)return t.texture.colorSpace;return ke.workingColorSpace}var Kc={clone:ni,merge:Pt},Ou=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Bu=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class Yt extends jn{constructor(e){super();if(this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=Ou,this.fragmentShader=Bu,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0)this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=ni(e.uniforms),this.uniformsGroups=Fu(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){let t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(let i in this.uniforms){let r=this.uniforms[i].value;if(r&&r.isTexture)t.uniforms[i]={type:"t",value:r.toJSON(e).uuid};else if(r&&r.isColor)t.uniforms[i]={type:"c",value:r.getHex()};else if(r&&r.isVector2)t.uniforms[i]={type:"v2",value:r.toArray()};else if(r&&r.isVector3)t.uniforms[i]={type:"v3",value:r.toArray()};else if(r&&r.isVector4)t.uniforms[i]={type:"v4",value:r.toArray()};else if(r&&r.isMatrix3)t.uniforms[i]={type:"m3",value:r.toArray()};else if(r&&r.isMatrix4)t.uniforms[i]={type:"m4",value:r.toArray()};else t.uniforms[i]={value:r}}if(Object.keys(this.defines).length>0)t.defines=this.defines;t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;let n={};for(let i in this.extensions)if(this.extensions[i]===!0)n[i]=!0;if(Object.keys(n).length>0)t.extensions=n;return t}fromJSON(e,t){if(super.fromJSON(e,t),e.uniforms!==void 0)for(let n in e.uniforms){let i=e.uniforms[n];switch(this.uniforms[n]={},i.type){case"t":this.uniforms[n].value=t[i.value]||null;break;case"c":this.uniforms[n].value=new qe().setHex(i.value);break;case"v2":this.uniforms[n].value=new Xe().fromArray(i.value);break;case"v3":this.uniforms[n].value=new F().fromArray(i.value);break;case"v4":this.uniforms[n].value=new ut().fromArray(i.value);break;case"m3":this.uniforms[n].value=new Le().fromArray(i.value);break;case"m4":this.uniforms[n].value=new ht().fromArray(i.value);break;default:this.uniforms[n].value=i.value}}if(e.defines!==void 0)this.defines=e.defines;if(e.vertexShader!==void 0)this.vertexShader=e.vertexShader;if(e.fragmentShader!==void 0)this.fragmentShader=e.fragmentShader;if(e.glslVersion!==void 0)this.glslVersion=e.glslVersion;if(e.extensions!==void 0)for(let n in e.extensions)this.extensions[n]=e.extensions[n];if(e.lights!==void 0)this.lights=e.lights;if(e.clipping!==void 0)this.clipping=e.clipping;return this}}class co extends Yt{constructor(e){super(e);this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}}class ho extends jn{constructor(e){super();this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=3200,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class uo extends jn{constructor(e){super();this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}function bi(e,t){if(!e||e.constructor===t)return e;if(typeof t.BYTES_PER_ELEMENT==="number")return new t(e);return Array.prototype.slice.call(e)}function ta(e){return e!==void 0&&e.inTangents!==void 0&&e.outTangents!==void 0}class ii{constructor(e,t,n,i){this.parameterPositions=e,this._cachedIndex=0,this.resultBuffer=i!==void 0?i:new t.constructor(n),this.sampleValues=t,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(e){let t=this.parameterPositions,n=this._cachedIndex,i=t[n],s=t[n-1];n:{e:{let r;t:{i:if(!(e<i)){for(let a=n+2;;){if(i===void 0){if(e<s)break i;return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===a)break;if(s=i,i=t[++n],e<i)break e}r=t.length;break t}if(!(e>=s)){let a=t[1];if(e<a)n=2,s=a;for(let o=n-2;;){if(s===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===o)break;if(i=s,s=t[--n-1],e>=s)break e}r=n,n=0;break t}break n}while(n<r){let a=n+r>>>1;if(e<t[a])r=a;else n=a+1}if(i=t[n],s=t[n-1],s===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(i===void 0)return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,s,i)}return this.interpolate_(n,s,e,i)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(e){let t=this.resultBuffer,n=this.sampleValues,i=this.valueSize,s=e*i;for(let r=0;r!==i;++r)t[r]=n[s+r];return t}interpolate_(){throw Error("THREE.Interpolant: Call to abstract method.")}intervalChanged_(){}}class fo extends ii{constructor(e,t,n,i){super(e,t,n,i);this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:2400,endingEnd:2400}}intervalChanged_(e,t,n){let i=this.parameterPositions,s=e-2,r=e+1,a=i[s],o=i[r];if(a===void 0)switch(this.getSettings_().endingStart){case 2401:s=e,a=2*t-n;break;case 2402:s=i.length-2,a=t+i[s]-i[s+1];break;default:s=e,a=n}if(o===void 0)switch(this.getSettings_().endingEnd){case 2401:r=e,o=2*n-t;break;case 2402:r=1,o=n+i[1]-i[0];break;default:r=e-1,o=t}let c=(n-t)*0.5,l=this.valueSize;this._weightPrev=c/(t-a),this._weightNext=c/(o-n),this._offsetPrev=s*l,this._offsetNext=r*l}interpolate_(e,t,n,i){let s=this.resultBuffer,r=this.sampleValues,a=this.valueSize,o=e*a,c=o-a,l=this._offsetPrev,u=this._offsetNext,d=this._weightPrev,h=this._weightNext,m=(n-t)/(i-t),v=m*m,b=v*m,p=-d*b+2*d*v-d*m,f=(1+d)*b+(-1.5-2*d)*v+(-0.5+d)*m+1,T=(-1-h)*b+(1.5+h)*v+0.5*m,I=h*b-h*v;for(let S=0;S!==a;++S)s[S]=p*r[l+S]+f*r[c+S]+T*r[o+S]+I*r[u+S];return s}}class po extends ii{constructor(e,t,n,i){super(e,t,n,i)}interpolate_(e,t,n,i){let s=this.resultBuffer,r=this.sampleValues,a=this.valueSize,o=e*a,c=o-a,l=(n-t)/(i-t),u=1-l;for(let d=0;d!==a;++d)s[d]=r[c+d]*u+r[o+d]*l;return s}}class mo extends ii{constructor(e,t,n,i){super(e,t,n,i)}interpolate_(e){return this.copySampleValue_(e-1)}}class go extends ii{interpolate_(e,t,n,i){let s=this.resultBuffer,r=this.sampleValues,a=this.valueSize,o=e*a,c=o-a,l=this.inTangents,u=this.outTangents;if(!l||!u){let m=(n-t)/(i-t),v=1-m;for(let b=0;b!==a;++b)s[b]=r[c+b]*v+r[o+b]*m;return s}let d=a*2,h=e-1;for(let m=0;m!==a;++m){let v=r[c+m],b=r[o+m],p=h*d+m*2,f=u[p],T=u[p+1],I=e*d+m*2,S=l[I],w=l[I+1],E=ku(n,t,f,S,i);s[m]=jc(E,v,T,w,b)}return s}}function jc(e,t,n,i,s){let r=1-e;return r*r*r*t+3*r*r*e*n+3*r*e*e*i+e*e*e*s}function zu(e,t,n,i,s){let r=1-e;return 3*r*r*(n-t)+6*r*e*(i-n)+3*e*e*(s-i)}function ku(e,t,n,i,s){let r=(e-t)/(s-t);for(let a=0;a<8;a++){let o=jc(r,t,n,i,s)-e;if(Math.abs(o)<0.0000000001)break;let c=zu(r,t,n,i,s);if(Math.abs(c)<0.0000000001)break;r=Math.max(0,Math.min(1,r-o/c))}return r}class Zt{constructor(e,t,n,i){if(e===void 0)throw Error("THREE.KeyframeTrack: track name is undefined");if(t===void 0||t.length===0)throw Error("THREE.KeyframeTrack: no keyframes in track named "+e);this.name=e,this.times=bi(t,this.TimeBufferType),this.values=bi(n,this.ValueBufferType),this.setInterpolation(i||this.DefaultInterpolation)}static toJSON(e){let t=e.constructor,n;if(t.toJSON!==this.toJSON)n=t.toJSON(e);else{n={name:e.name,times:bi(e.times,Array),values:bi(e.values,Array)};let i=e.getInterpolation();if(i!==e.DefaultInterpolation)n.interpolation=i;if(ta(e.settings))n.settings={inTangents:bi(e.settings.inTangents,Array),outTangents:bi(e.settings.outTangents,Array)}}return n.type=e.ValueTypeName,n}InterpolantFactoryMethodDiscrete(e){return new mo(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodLinear(e){return new po(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodSmooth(e){return new fo(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodBezier(e){let t=new go(this.times,this.values,this.getValueSize(),e);if(this.settings)t.inTangents=this.settings.inTangents,t.outTangents=this.settings.outTangents;return t}setInterpolation(e){let t;switch(e){case 2300:t=this.InterpolantFactoryMethodDiscrete;break;case 2301:t=this.InterpolantFactoryMethodLinear;break;case 2302:t=this.InterpolantFactoryMethodSmooth;break;case 2303:t=this.InterpolantFactoryMethodBezier;break}if(t===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(e!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw Error(n);return Ce("KeyframeTrack:",n),this}return this.createInterpolant=t,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return 2300;case this.InterpolantFactoryMethodLinear:return 2301;case this.InterpolantFactoryMethodSmooth:return 2302;case this.InterpolantFactoryMethodBezier:return 2303}}getValueSize(){return this.values.length/this.times.length}shift(e){if(e!==0){let t=this.times;for(let n=0,i=t.length;n!==i;++n)t[n]+=e}return this}scale(e){if(e!==1){let t=this.times;for(let n=0,i=t.length;n!==i;++n)t[n]*=e;if(ta(this.settings))Wl(this.settings.inTangents,e),Wl(this.settings.outTangents,e)}return this}trim(e,t){let n=this.times,i=n.length,s=0,r=i-1;while(s!==i&&n[s]<e)++s;while(r!==-1&&n[r]>t)--r;if(++r,s!==0||r!==i){if(s>=r)r=Math.max(r,1),s=r-1;let a=this.getValueSize();this.times=n.slice(s,r),this.values=this.values.slice(s*a,r*a)}return this}validate(){let e=!0,t=this.getValueSize();if(t-Math.floor(t)!==0)Pe("KeyframeTrack: Invalid value size in track.",this),e=!1;let n=this.times,i=this.values,s=n.length;if(s===0)Pe("KeyframeTrack: Track is empty.",this),e=!1;let r=null;for(let a=0;a!==s;a++){let o=n[a];if(typeof o==="number"&&isNaN(o)){Pe("KeyframeTrack: Time is not a valid number.",this,a,o),e=!1;break}if(r!==null&&r>o){Pe("KeyframeTrack: Out of order keys.",this,a,o,r),e=!1;break}r=o}if(i!==void 0){if(gu(i))for(let a=0,o=i.length;a!==o;++a){let c=i[a];if(isNaN(c)){Pe("KeyframeTrack: Value is not a valid number.",this,a,c),e=!1;break}}}return e}optimize(){let e=this.times.slice(),t=this.values.slice(),n=this.getValueSize(),i=this.getInterpolation()===2302,s=e.length-1,r=1;for(let a=1;a<s;++a){let o=!1,c=e[a],l=e[a+1];if(c!==l&&(a!==1||c!==e[0]))if(!i){let u=a*n,d=u-n,h=u+n;for(let m=0;m!==n;++m){let v=t[u+m];if(v!==t[d+m]||v!==t[h+m]){o=!0;break}}}else o=!0;if(o){if(a!==r){e[r]=e[a];let u=a*n,d=r*n;for(let h=0;h!==n;++h)t[d+h]=t[u+h]}++r}}if(s>0){e[r]=e[s];for(let a=s*n,o=r*n,c=0;c!==n;++c)t[o+c]=t[a+c];++r}if(r!==e.length)this.times=e.slice(0,r),this.values=t.slice(0,r*n);else this.times=e,this.values=t;return this}clone(){let e=this.times.slice(),t=this.values.slice(),i=new this.constructor(this.name,e,t);if(i.createInterpolant=this.createInterpolant,ta(this.settings))i.settings={inTangents:this.settings.inTangents.slice(),outTangents:this.settings.outTangents.slice()};return i}}function Wl(e,t){for(let n=0,i=e.length;n!==i;n+=2)e[n]*=t}Zt.prototype.ValueTypeName="";Zt.prototype.TimeBufferType=Float32Array;Zt.prototype.ValueBufferType=Float32Array;Zt.prototype.DefaultInterpolation=2301;class si extends Zt{constructor(e,t,n){super(e,t,n)}}si.prototype.ValueTypeName="bool";si.prototype.ValueBufferType=Array;si.prototype.DefaultInterpolation=2300;si.prototype.InterpolantFactoryMethodLinear=void 0;si.prototype.InterpolantFactoryMethodSmooth=void 0;class _o extends Zt{constructor(e,t,n,i){super(e,t,n,i)}}_o.prototype.ValueTypeName="color";class xo extends Zt{constructor(e,t,n,i){super(e,t,n,i)}}xo.prototype.ValueTypeName="number";class vo extends ii{constructor(e,t,n,i){super(e,t,n,i)}interpolate_(e,t,n,i){let s=this.resultBuffer,r=this.sampleValues,a=this.valueSize,o=(n-t)/(i-t),c=e*a;for(let l=c+a;c!==l;c+=4)bn.slerpFlat(s,0,r,c-a,r,c,o);return s}}class ur extends Zt{constructor(e,t,n,i){super(e,t,n,i)}InterpolantFactoryMethodLinear(e){return new vo(this.times,this.values,this.getValueSize(),e)}}ur.prototype.ValueTypeName="quaternion";ur.prototype.InterpolantFactoryMethodSmooth=void 0;class ri extends Zt{constructor(e,t,n){super(e,t,n)}}ri.prototype.ValueTypeName="string";ri.prototype.ValueBufferType=Array;ri.prototype.DefaultInterpolation=2300;ri.prototype.InterpolantFactoryMethodLinear=void 0;ri.prototype.InterpolantFactoryMethodSmooth=void 0;class yo extends Zt{constructor(e,t,n,i){super(e,t,n,i)}}yo.prototype.ValueTypeName="vector";class So{constructor(e,t,n){let i=this,s=!1,r=0,a=0,o=void 0,c=[];this.onStart=void 0,this.onLoad=e,this.onProgress=t,this.onError=n,this._abortController=null,this.itemStart=function(l){if(a++,s===!1){if(i.onStart!==void 0)i.onStart(l,r,a)}s=!0},this.itemEnd=function(l){if(r++,i.onProgress!==void 0)i.onProgress(l,r,a);if(r===a){if(s=!1,i.onLoad!==void 0)i.onLoad()}},this.itemError=function(l){if(i.onError!==void 0)i.onError(l)},this.resolveURL=function(l){if(l=l.normalize("NFC"),o)return o(l);return l},this.setURLModifier=function(l){return o=l,this},this.addHandler=function(l,u){return c.push(l,u),this},this.removeHandler=function(l){let u=c.indexOf(l);if(u!==-1)c.splice(u,2);return this},this.getHandler=function(l){for(let u=0,d=c.length;u<d;u+=2){let h=c[u],m=c[u+1];if(h.global)h.lastIndex=0;if(h.test(l))return m}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){if(!this._abortController)this._abortController=new AbortController;return this._abortController}}var Qc=new So;class Mo{constructor(e){if(this.manager=e!==void 0?e:Qc,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={},typeof __THREE_DEVTOOLS__<"u")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}load(){}loadAsync(e,t){let n=this;return new Promise(function(i,s){n.load(e,i,t,s)})}parse(){}setCrossOrigin(e){return this.crossOrigin=e,this}setWithCredentials(e){return this.withCredentials=e,this}setPath(e){return this.path=e,this}setResourcePath(e){return this.resourcePath=e,this}setRequestHeader(e){return this.requestHeader=e,this}abort(){return this}}Mo.DEFAULT_MATERIAL_NAME="__DEFAULT";var Fs=new F,Os=new bn,an=new F;class dr extends It{constructor(){super();this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new ht,this.projectionMatrix=new ht,this.projectionMatrixInverse=new ht,this.coordinateSystem=2000,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){if(super.updateMatrixWorld(e),this.matrixWorld.decompose(Fs,Os,an),an.x===1&&an.y===1&&an.z===1)this.matrixWorldInverse.copy(this.matrixWorld).invert();else this.matrixWorldInverse.compose(Fs,Os,an.set(1,1,1)).invert()}updateWorldMatrix(e,t,n=!1){if(super.updateWorldMatrix(e,t,n),this.matrixWorld.decompose(Fs,Os,an),an.x===1&&an.y===1&&an.z===1)this.matrixWorldInverse.copy(this.matrixWorld).invert();else this.matrixWorldInverse.compose(Fs,Os,an.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}}var Pn=new F,Xl=new Xe,ql=new Xe;class Nt extends dr{constructor(e=50,t=1,n=0.1,i=2000){super();this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=n,this.far=i,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){let t=0.5*this.getFilmHeight()/e;this.fov=zs*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){let e=Math.tan(Nr*0.5*this.fov);return 0.5*this.getFilmHeight()/e}getEffectiveFOV(){return zs*2*Math.atan(Math.tan(Nr*0.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,n){Pn.set(-1,-1,0.5).applyMatrix4(this.projectionMatrixInverse),t.set(Pn.x,Pn.y).multiplyScalar(-e/Pn.z),Pn.set(1,1,0.5).applyMatrix4(this.projectionMatrixInverse),n.set(Pn.x,Pn.y).multiplyScalar(-e/Pn.z)}getViewSize(e,t){return this.getViewBounds(e,Xl,ql),t.subVectors(ql,Xl)}setViewOffset(e,t,n,i,s,r){if(this.aspect=e/t,this.view===null)this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1};this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=i,this.view.width=s,this.view.height=r,this.updateProjectionMatrix()}clearViewOffset(){if(this.view!==null)this.view.enabled=!1;this.updateProjectionMatrix()}updateProjectionMatrix(){let e=this.near,t=e*Math.tan(Nr*0.5*this.fov)/this.zoom,n=2*t,i=this.aspect*n,s=-0.5*i,r=this.view;if(this.view!==null&&this.view.enabled){let{fullWidth:o,fullHeight:c}=r;s+=r.offsetX*i/o,t-=r.offsetY*n/c,i*=r.width/o,n*=r.height/c}let a=this.filmOffset;if(a!==0)s+=e*a/this.getFilmWidth();this.projectionMatrix.makePerspective(s,s+i,t,t-n,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);if(t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null)t.object.view=Object.assign({},this.view);return t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}}class fr extends dr{constructor(e=-1,t=1,n=1,i=-1,s=0.1,r=2000){super();this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=n,this.bottom=i,this.near=s,this.far=r,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,n,i,s,r){if(this.view===null)this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1};this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=i,this.view.width=s,this.view.height=r,this.updateProjectionMatrix()}clearViewOffset(){if(this.view!==null)this.view.enabled=!1;this.updateProjectionMatrix()}updateProjectionMatrix(){let e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,i=(this.top+this.bottom)/2,s=n-e,r=n+e,a=i+t,o=i-t;if(this.view!==null&&this.view.enabled){let c=(this.right-this.left)/this.view.fullWidth/this.zoom,l=(this.top-this.bottom)/this.view.fullHeight/this.zoom;s+=c*this.view.offsetX,r=s+c*this.view.width,a-=l*this.view.offsetY,o=a-l*this.view.height}this.projectionMatrix.makeOrthographic(s,r,a,o,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);if(t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null)t.object.view=Object.assign({},this.view);return t}}var wi=-90,Ei=1;class bo extends It{constructor(e,t,n){super();this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;let i=new Nt(wi,Ei,e,t);i.layers=this.layers,this.add(i);let s=new Nt(wi,Ei,e,t);s.layers=this.layers,this.add(s);let r=new Nt(wi,Ei,e,t);r.layers=this.layers,this.add(r);let a=new Nt(wi,Ei,e,t);a.layers=this.layers,this.add(a);let o=new Nt(wi,Ei,e,t);o.layers=this.layers,this.add(o);let c=new Nt(wi,Ei,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){let e=this.coordinateSystem,t=this.children.concat(),[n,i,s,r,a,o]=t;for(let c of t)this.remove(c);if(e===2000)n.up.set(0,1,0),n.lookAt(1,0,0),i.up.set(0,1,0),i.lookAt(-1,0,0),s.up.set(0,0,-1),s.lookAt(0,1,0),r.up.set(0,0,1),r.lookAt(0,-1,0),a.up.set(0,1,0),a.lookAt(0,0,1),o.up.set(0,1,0),o.lookAt(0,0,-1);else if(e===2001)n.up.set(0,-1,0),n.lookAt(-1,0,0),i.up.set(0,-1,0),i.lookAt(1,0,0),s.up.set(0,0,1),s.lookAt(0,1,0),r.up.set(0,0,-1),r.lookAt(0,-1,0),a.up.set(0,-1,0),a.lookAt(0,0,1),o.up.set(0,-1,0),o.lookAt(0,0,-1);else throw Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(let c of t)this.add(c),c.updateMatrixWorld()}update(e,t){if(this.parent===null)this.updateMatrixWorld();let{renderTarget:n,activeMipmapLevel:i}=this;if(this.coordinateSystem!==e.coordinateSystem)this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem();let[s,r,a,o,c,l]=this.children,u=e.getRenderTarget(),d=e.getActiveCubeFace(),h=e.getActiveMipmapLevel(),m=e.xr.enabled;e.xr.enabled=!1;let v=n.texture.generateMipmaps;n.texture.generateMipmaps=!1;let b=!1;if(e.isWebGLRenderer===!0)b=e.state.buffers.depth.getReversed();else b=e.reversedDepthBuffer;if(e.setRenderTarget(n,0,i),b&&e.autoClear===!1)e.clearDepth();if(e.render(t,s),e.setRenderTarget(n,1,i),b&&e.autoClear===!1)e.clearDepth();if(e.render(t,r),e.setRenderTarget(n,2,i),b&&e.autoClear===!1)e.clearDepth();if(e.render(t,a),e.setRenderTarget(n,3,i),b&&e.autoClear===!1)e.clearDepth();if(e.render(t,o),e.setRenderTarget(n,4,i),b&&e.autoClear===!1)e.clearDepth();if(e.render(t,c),n.texture.generateMipmaps=v,e.setRenderTarget(n,5,i),b&&e.autoClear===!1)e.clearDepth();e.render(t,l),e.setRenderTarget(u,d,h),e.xr.enabled=m,n.texture.needsPMREMUpdate=!0}}class wo extends Nt{constructor(e=[]){super();this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}var Eo="\\[\\]\\.:\\/",Gu=new RegExp("["+Eo+"]","g"),To="[^"+Eo+"]",Hu="[^"+Eo.replace("\\.","")+"]",Vu=/((?:WC+[\/:])*)/.source.replace("WC",To),Wu=/(WCOD+)?/.source.replace("WCOD",Hu),Xu=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",To),qu=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",To),$u=new RegExp("^"+Vu+Wu+Xu+qu+"$"),Yu=["material","materials","bones","map"];class eh{constructor(e,t,n){let i=n||Qe.parseTrackName(t);this._targetGroup=e,this._bindings=e.subscribe_(t,i)}getValue(e,t){this.bind();let n=this._targetGroup.nCachedObjects_,i=this._bindings[n];if(i!==void 0)i.getValue(e,t)}setValue(e,t){let n=this._bindings;for(let i=this._targetGroup.nCachedObjects_,s=n.length;i!==s;++i)n[i].setValue(e,t)}bind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].bind()}unbind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].unbind()}}class Qe{constructor(e,t,n){this.path=t,this.parsedPath=n||Qe.parseTrackName(t),this.node=Qe.findNode(e,this.parsedPath.nodeName),this.rootNode=e,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(e,t,n){if(!(e&&e.isAnimationObjectGroup))return new Qe(e,t,n);else return new Qe.Composite(e,t,n)}static sanitizeNodeName(e){return e.replace(/\s/g,"_").replace(Gu,"")}static parseTrackName(e){let t=$u.exec(e);if(t===null)throw Error("THREE.PropertyBinding: Cannot parse trackName: "+e);let n={nodeName:t[2],objectName:t[3],objectIndex:t[4],propertyName:t[5],propertyIndex:t[6]},i=n.nodeName&&n.nodeName.lastIndexOf(".");if(i!==void 0&&i!==-1){let s=n.nodeName.substring(i+1);if(Yu.indexOf(s)!==-1)n.nodeName=n.nodeName.substring(0,i),n.objectName=s}if(n.propertyName===null||n.propertyName.length===0)throw Error("THREE.PropertyBinding: can not parse propertyName from trackName: "+e);return n}static findNode(e,t){if(t===void 0||t===""||t==="."||t===-1||t===e.name||t===e.uuid)return e;if(e.skeleton){let n=e.skeleton.getBoneByName(t);if(n!==void 0)return n}if(e.children){let n=function(s){for(let r=0;r<s.length;r++){let a=s[r];if(a.name===t||a.uuid===t)return a;let o=n(a.children);if(o)return o}return null},i=n(e.children);if(i)return i}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(e,t){e[t]=this.targetObject[this.propertyName]}_getValue_array(e,t){let n=this.resolvedProperty;for(let i=0,s=n.length;i!==s;++i)e[t++]=n[i]}_getValue_arrayElement(e,t){e[t]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(e,t){this.resolvedProperty.toArray(e,t)}_setValue_direct(e,t){this.targetObject[this.propertyName]=e[t]}_setValue_direct_setNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(e,t){let n=this.resolvedProperty;for(let i=0,s=n.length;i!==s;++i)n[i]=e[t++]}_setValue_array_setNeedsUpdate(e,t){let n=this.resolvedProperty;for(let i=0,s=n.length;i!==s;++i)n[i]=e[t++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(e,t){let n=this.resolvedProperty;for(let i=0,s=n.length;i!==s;++i)n[i]=e[t++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(e,t){this.resolvedProperty[this.propertyIndex]=e[t]}_setValue_arrayElement_setNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(e,t){this.resolvedProperty.fromArray(e,t)}_setValue_fromArray_setNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(e,t){this.bind(),this.getValue(e,t)}_setValue_unbound(e,t){this.bind(),this.setValue(e,t)}bind(){let e=this.node,t=this.parsedPath,{objectName:n,propertyName:i,propertyIndex:s}=t;if(!e)e=Qe.findNode(this.rootNode,t.nodeName),this.node=e;if(this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!e){Ce("PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let c=t.objectIndex;switch(n){case"materials":if(!e.material){Pe("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.materials){Pe("PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}e=e.material.materials;break;case"bones":if(!e.skeleton){Pe("PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}e=e.skeleton.bones;for(let l=0;l<e.length;l++)if(e[l].name===c){c=l;break}break;case"map":if("map"in e){e=e.map;break}if(!e.material){Pe("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.map){Pe("PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}e=e.material.map;break;default:if(e[n]===void 0){Pe("PropertyBinding: Can not bind to objectName of node undefined.",this);return}e=e[n]}if(c!==void 0){if(e[c]===void 0){Pe("PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,e);return}e=e[c]}}let r=e[i];if(r===void 0){let c=t.nodeName;Pe("PropertyBinding: Trying to update property for track: "+c+"."+i+" but it wasn't found.",e);return}let a=this.Versioning.None;if(this.targetObject=e,e.isMaterial===!0)a=this.Versioning.NeedsUpdate;else if(e.isObject3D===!0)a=this.Versioning.MatrixWorldNeedsUpdate;let o=this.BindingType.Direct;if(s!==void 0){if(i==="morphTargetInfluences"){if(!e.geometry){Pe("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!e.geometry.morphAttributes){Pe("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}if(e.morphTargetDictionary[s]!==void 0)s=e.morphTargetDictionary[s]}o=this.BindingType.ArrayElement,this.resolvedProperty=r,this.propertyIndex=s}else if(r.fromArray!==void 0&&r.toArray!==void 0)o=this.BindingType.HasFromToArray,this.resolvedProperty=r;else if(Array.isArray(r))o=this.BindingType.EntireArray,this.resolvedProperty=r;else this.propertyName=i;this.getValue=this.GetterByBindingType[o],this.setValue=this.SetterByBindingTypeAndVersioning[o][a]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}}Qe.Composite=eh;Qe.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};Qe.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};Qe.prototype.GetterByBindingType=[Qe.prototype._getValue_direct,Qe.prototype._getValue_array,Qe.prototype._getValue_arrayElement,Qe.prototype._getValue_toArray];Qe.prototype.SetterByBindingTypeAndVersioning=[[Qe.prototype._setValue_direct,Qe.prototype._setValue_direct_setNeedsUpdate,Qe.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[Qe.prototype._setValue_array,Qe.prototype._setValue_array_setNeedsUpdate,Qe.prototype._setValue_array_setMatrixWorldNeedsUpdate],[Qe.prototype._setValue_arrayElement,Qe.prototype._setValue_arrayElement_setNeedsUpdate,Qe.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[Qe.prototype._setValue_fromArray,Qe.prototype._setValue_fromArray_setNeedsUpdate,Qe.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var C0=new Float32Array(1);class Ao{static{Ao.prototype.isMatrix2=!0}constructor(e,t,n,i){if(this.elements=[1,0,0,1],e!==void 0)this.set(e,t,n,i)}identity(){return this.set(1,0,0,1),this}fromArray(e,t=0){for(let n=0;n<4;n++)this.elements[n]=e[n+t];return this}set(e,t,n,i){let s=this.elements;return s[0]=e,s[2]=t,s[1]=n,s[3]=i,this}}var $l=new F,Bs,na;class pr extends It{constructor(e=new F(0,0,1),t=new F(0,0,0),n=1,i=16776960,s=n*0.2,r=s*0.2){super();if(this.type="ArrowHelper",Bs===void 0)Bs=new bt,Bs.setAttribute("position",new vt([0,0,0,0,1,0],3)),na=new hr(0.5,1,5,1),na.translate(0,-0.5,0);this.position.copy(t),this.line=new ei(Bs,new Qn({color:i,toneMapped:!1})),this.line.matrixAutoUpdate=!1,this.add(this.line),this.cone=new Dt(na,new Fn({color:i,toneMapped:!1})),this.cone.matrixAutoUpdate=!1,this.add(this.cone),this.setDirection(e),this.setLength(n,s,r)}setDirection(e){if(e.y>0.99999)this.quaternion.set(0,0,0,1);else if(e.y<-0.99999)this.quaternion.set(1,0,0,0);else{$l.set(e.z,0,-e.x).normalize();let t=Math.acos(e.y);this.quaternion.setFromAxisAngle($l,t)}}setLength(e,t=e*0.2,n=t*0.2){this.line.scale.set(1,Math.max(0.0001,e-t),1),this.line.updateMatrix(),this.cone.scale.set(n,t,n),this.cone.position.y=e,this.cone.updateMatrix()}setColor(e){this.line.material.color.set(e),this.cone.material.color.set(e)}copy(e){return super.copy(e,!1),this.line.copy(e.line),this.cone.copy(e.cone),this}dispose(){super.dispose(),this.line.geometry.dispose(),this.line.material.dispose(),this.cone.geometry.dispose(),this.cone.material.dispose()}}function Co(e,t,n,i){let s=Zu(i);switch(n){case 1021:return e*t;case 1028:return e*t/s.components*s.byteLength;case 1029:return e*t/s.components*s.byteLength;case 1030:return e*t*2/s.components*s.byteLength;case 1031:return e*t*2/s.components*s.byteLength;case 1022:return e*t*3/s.components*s.byteLength;case 1023:return e*t*4/s.components*s.byteLength;case 1033:return e*t*4/s.components*s.byteLength;case 33776:case 33777:return Math.floor((e+3)/4)*Math.floor((t+3)/4)*8;case 33778:case 33779:return Math.floor((e+3)/4)*Math.floor((t+3)/4)*16;case 35841:case 35843:return Math.max(e,16)*Math.max(t,8)/4;case 35840:case 35842:return Math.max(e,8)*Math.max(t,8)/2;case 36196:case 37492:case 37488:case 37489:return Math.floor((e+3)/4)*Math.floor((t+3)/4)*8;case 37496:case 37490:case 37491:return Math.floor((e+3)/4)*Math.floor((t+3)/4)*16;case 37808:return Math.floor((e+3)/4)*Math.floor((t+3)/4)*16;case 37809:return Math.floor((e+4)/5)*Math.floor((t+3)/4)*16;case 37810:return Math.floor((e+4)/5)*Math.floor((t+4)/5)*16;case 37811:return Math.floor((e+5)/6)*Math.floor((t+4)/5)*16;case 37812:return Math.floor((e+5)/6)*Math.floor((t+5)/6)*16;case 37813:return Math.floor((e+7)/8)*Math.floor((t+4)/5)*16;case 37814:return Math.floor((e+7)/8)*Math.floor((t+5)/6)*16;case 37815:return Math.floor((e+7)/8)*Math.floor((t+7)/8)*16;case 37816:return Math.floor((e+9)/10)*Math.floor((t+4)/5)*16;case 37817:return Math.floor((e+9)/10)*Math.floor((t+5)/6)*16;case 37818:return Math.floor((e+9)/10)*Math.floor((t+7)/8)*16;case 37819:return Math.floor((e+9)/10)*Math.floor((t+9)/10)*16;case 37820:return Math.floor((e+11)/12)*Math.floor((t+9)/10)*16;case 37821:return Math.floor((e+11)/12)*Math.floor((t+11)/12)*16;case 36492:case 36494:case 36495:return Math.ceil(e/4)*Math.ceil(t/4)*16;case 36283:case 36284:return Math.ceil(e/4)*Math.ceil(t/4)*8;case 36285:case 36286:return Math.ceil(e/4)*Math.ceil(t/4)*16}throw Error(`Unable to determine texture byte length for ${n} format.`)}function Zu(e){switch(e){case 1009:case 1010:return{byteLength:1,components:1};case 1012:case 1011:case 1016:return{byteLength:2,components:1};case 1017:case 1018:return{byteLength:2,components:4};case 1014:case 1013:case 1015:return{byteLength:4,components:1};case 35902:case 35899:return{byteLength:4,components:3}}throw Error(`THREE.TextureUtils: Unknown texture type ${e}.`)}if(typeof __THREE_DEVTOOLS__<"u")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"186"}}));if(typeof window<"u")if(window.__THREE__)Ce("WARNING: Multiple instances of Three.js being imported.");else window.__THREE__="186";function Mh(){let e=null,t=!1,n=null,i=null;function s(r,a){i=e.requestAnimationFrame(s),n(r,a)}return{start:function(){if(t===!0)return;if(n===null)return;if(e===null)return;i=e.requestAnimationFrame(s),t=!0},stop:function(){if(e!==null)e.cancelAnimationFrame(i);t=!1},setAnimationLoop:function(r){n=r},setContext:function(r){e=r}}}function Ju(e){let t=new WeakMap;function n(o,c){let{array:l,usage:u}=o,d=l.byteLength,h=e.createBuffer();e.bindBuffer(c,h),e.bufferData(c,l,u),o.onUploadCallback();let m;if(l instanceof Float32Array)m=e.FLOAT;else if(typeof Float16Array<"u"&&l instanceof Float16Array)m=e.HALF_FLOAT;else if(l instanceof Uint16Array)if(o.isFloat16BufferAttribute)m=e.HALF_FLOAT;else m=e.UNSIGNED_SHORT;else if(l instanceof Int16Array)m=e.SHORT;else if(l instanceof Uint32Array)m=e.UNSIGNED_INT;else if(l instanceof Int32Array)m=e.INT;else if(l instanceof Int8Array)m=e.BYTE;else if(l instanceof Uint8Array)m=e.UNSIGNED_BYTE;else if(l instanceof Uint8ClampedArray)m=e.UNSIGNED_BYTE;else throw Error("THREE.WebGLAttributes: Unsupported buffer data format: "+l);return{buffer:h,type:m,bytesPerElement:l.BYTES_PER_ELEMENT,version:o.version,size:d}}function i(o,c,l){let{array:u,updateRanges:d}=c;if(e.bindBuffer(l,o),d.length===0)e.bufferSubData(l,0,u);else{d.sort((m,v)=>m.start-v.start);let h=0;for(let m=1;m<d.length;m++){let v=d[h],b=d[m];if(b.start<=v.start+v.count+1)v.count=Math.max(v.count,b.start+b.count-v.start);else++h,d[h]=b}d.length=h+1;for(let m=0,v=d.length;m<v;m++){let b=d[m];e.bufferSubData(l,b.start*u.BYTES_PER_ELEMENT,u,b.start,b.count)}c.clearUpdateRanges()}c.onUploadCallback()}function s(o){if(o.isInterleavedBufferAttribute)o=o.data;return t.get(o)}function r(o){if(o.isInterleavedBufferAttribute)o=o.data;let c=t.get(o);if(c)e.deleteBuffer(c.buffer),t.delete(o)}function a(o,c){if(o.isInterleavedBufferAttribute)o=o.data;if(o.isGLBufferAttribute){let u=t.get(o);if(!u||u.version<o.version)t.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}let l=t.get(o);if(l===void 0)t.set(o,n(o,c));else if(l.version<o.version){if(l.size!==o.array.byteLength)throw Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");i(l.buffer,o,c),l.version=o.version}}return{get:s,remove:r,update:a}}var Ku=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,ju=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,Qu=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,ed=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,td=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,nd=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,id=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,sd=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,rd=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec4 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 );
	}
#endif`,ad=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,od=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,ld=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,cd=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,hd=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,ud=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,dd=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,fd=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,pd=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,md=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,gd=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,_d=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,xd=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,vd=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec4( 1.0 );
#endif
#ifdef USE_COLOR_ALPHA
	vColor *= color;
#elif defined( USE_COLOR )
	vColor.rgb *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.rgb *= instanceColor.rgb;
#endif
#ifdef USE_BATCHING_COLOR
	vColor *= getBatchingColor( getIndirectIndex( gl_DrawID ) );
#endif`,yd=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
#define inverseTransformDirection transformDirectionByInverseViewMatrix
vec3 transformNormalByInverseViewMatrix( in vec3 normal, in mat4 viewMatrix ) {
	return normalize( ( vec4( normal, 0.0 ) * viewMatrix ).xyz );
}
vec3 transformDirectionByInverseViewMatrix( in vec3 dir, in mat4 viewMatrix ) {
	return normalize( ( vec4( dir, 0.0 ) * viewMatrix ).xyz );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,Sd=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,Md=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
#endif`,bd=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,wd=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,Ed=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,Td=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,Ad="gl_FragColor = linearToOutputTexel( gl_FragColor );",Cd=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,Rd=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * reflectVec );
		#ifdef ENVMAP_BLENDING_MULTIPLY
			outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_MIX )
			outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_ADD )
			outgoingLight += envColor.xyz * specularStrength * reflectivity;
		#endif
	#endif
#endif`,Id=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,Pd=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,Ld=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,Nd=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,Dd=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,Ud=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,Fd=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,Od=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,Bd=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,zd=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,kd=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,Gd=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,Hd=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_SUN_LIGHTS > 0
	struct SunLight {
		vec3 direction;
		vec3 color;
	};
	uniform SunLight sunLights[ NUM_SUN_LIGHTS ];
	void getSunLightInfo( const in SunLight sunLight, out IncidentLight light ) {
		light.color = sunLight.color;
		light.direction = sunLight.direction;
		light.visible = true;
	}
#endif
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif
#include <lightprobes_pars_fragment>`,Vd=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, pow4( roughness ) ) );
			reflectVec = transformDirectionByInverseViewMatrix( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_RETROREFLECTION
		vec3 getIBLRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 retroVec = normalize( mix( viewDir, normal, pow4( roughness ) ) );
				retroVec = transformDirectionByInverseViewMatrix( retroVec, viewMatrix );
				vec4 envMapColor = textureCubeUV( envMap, envMapRotation * retroVec, roughness );
				return envMapColor.rgb * envMapIntensity;
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
		#ifdef USE_RETROREFLECTION
			vec3 getIBLAnisotropyRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
				#ifdef ENVMAP_TYPE_CUBE_UV
					vec3 bentNormal = cross( bitangent, viewDir );
					bentNormal = normalize( cross( bentNormal, bitangent ) );
					bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
					return getIBLRetroRadiance( viewDir, bentNormal, roughness );
				#else
					return vec3( 0.0 );
				#endif
			}
		#endif
	#endif
#endif`,Wd=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,Xd=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,qd=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,$d=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,Yd=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.diffuseContribution = diffuseColor.rgb * ( 1.0 - metalnessFactor );
material.metalness = metalnessFactor;
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor;
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = vec3( 0.04 );
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_RETROREFLECTION
	material.retroreflectivity = retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.0001, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,Zd=`uniform sampler2D dfgLUT;
struct PhysicalMaterial {
	vec3 diffuseColor;
	vec3 diffuseContribution;
	vec3 specularColor;
	vec3 specularColorBlended;
	float roughness;
	float metalness;
	float specularF90;
	float dispersion;
	vec2 dfg;
	vec3 multiScatteringCompensation;
	#ifdef USE_RETROREFLECTION
		float retroreflectivity;
	#endif
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0Dielectric;
		vec3 iridescenceF0Metallic;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		return 0.5 / max( gv + gl, EPSILON );
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColorBlended;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transpose( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float rInv = 1.0 / ( roughness + 0.1 );
	float a = -1.9362 + 1.0678 * roughness + 0.4573 * r2 - 0.8469 * rInv;
	float b = -0.6014 + 0.5538 * roughness - 0.4670 * r2 - 0.1255 * rInv;
	float DG = exp( a * dotNV + b );
	return saturate( DG );
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec2 fab, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec2 fab, const in vec3 specularColor, const in float specularF90, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColorBlended * t2.x + ( material.specularF90 - material.specularColorBlended ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseContribution * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
		#ifdef USE_CLEARCOAT
			vec3 Ncc = geometryClearcoatNormal;
			vec2 uvClearcoat = LTC_Uv( Ncc, viewDir, material.clearcoatRoughness );
			vec4 t1Clearcoat = texture2D( ltc_1, uvClearcoat );
			vec4 t2Clearcoat = texture2D( ltc_2, uvClearcoat );
			mat3 mInvClearcoat = mat3(
				vec3( t1Clearcoat.x, 0, t1Clearcoat.y ),
				vec3(             0, 1,             0 ),
				vec3( t1Clearcoat.z, 0, t1Clearcoat.w )
			);
			vec3 fresnelClearcoat = material.clearcoatF0 * t2Clearcoat.x + ( material.clearcoatF90 - material.clearcoatF0 ) * t2Clearcoat.y;
			clearcoatSpecularDirect += lightColor * fresnelClearcoat * LTC_Evaluate( Ncc, viewDir, position, mInvClearcoat, rectCoords );
		#endif
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
 
 		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
 
 		float sheenAlbedoV = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
 		float sheenAlbedoL = IBLSheenBRDF( geometryNormal, directLight.direction, material.sheenRoughness );
 
 		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * max( sheenAlbedoV, sheenAlbedoL );
 
 		irradiance *= sheenEnergyComp;
 
 	#endif
	vec3 specularBRDF = BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	#ifdef USE_RETROREFLECTION
		vec3 retroViewDir = reflect( - geometryViewDir, geometryNormal );
		vec3 retroSpecularBRDF = BRDF_GGX( directLight.direction, retroViewDir, geometryNormal, material );
		specularBRDF = mix( specularBRDF, retroSpecularBRDF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directSpecular += irradiance * specularBRDF * material.multiScatteringCompensation;
	vec3 halfDir = normalize( directLight.direction + geometryViewDir );
	float dotVH = saturate( dot( geometryViewDir, halfDir ) );
	vec3 F = F_Schlick( material.specularColor, material.specularF90, dotVH );
	#ifdef USE_RETROREFLECTION
		vec3 retroHalfDir = normalize( directLight.direction + retroViewDir );
		float dotRetroVH = saturate( dot( retroViewDir, retroHalfDir ) );
		vec3 retroF = F_Schlick( material.specularColor, material.specularF90, dotRetroVH );
		F = mix( F, retroF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - F );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScattering, multiScattering );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScattering, multiScattering );
	#endif
	vec3 diffuse = irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - singleScattering - multiScattering );
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		sheenSpecularIndirect += irradiance * material.sheenColor * sheenAlbedo * RECIPROCAL_PI;
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		diffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectDiffuse += diffuse;
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness ) * RECIPROCAL_PI;
 	#endif
	vec3 singleScatteringDielectric = vec3( 0.0 );
	vec3 multiScatteringDielectric = vec3( 0.0 );
	vec3 singleScatteringMetallic = vec3( 0.0 );
	vec3 multiScatteringMetallic = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscatteringIridescence( material.dfg, material.diffuseColor, material.specularF90, material.iridescence, material.iridescenceF0Metallic, singleScatteringMetallic, multiScatteringMetallic );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscattering( material.dfg, material.diffuseColor, material.specularF90, singleScatteringMetallic, multiScatteringMetallic );
	#endif
	vec3 singleScattering = mix( singleScatteringDielectric, singleScatteringMetallic, material.metalness );
	vec3 multiScattering = mix( multiScatteringDielectric, multiScatteringMetallic, material.metalness );
	vec3 totalScatteringDielectric = singleScatteringDielectric + multiScatteringDielectric;
	vec3 diffuse = material.diffuseContribution * ( 1.0 - totalScatteringDielectric );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	vec3 indirectSpecular = radiance * singleScattering;
	indirectSpecular += multiScattering * cosineWeightedIrradiance;
	vec3 indirectDiffuse = diffuse * cosineWeightedIrradiance;
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		indirectSpecular *= sheenEnergyComp;
		indirectDiffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectSpecular += indirectSpecular;
	reflectedLight.indirectDiffuse += indirectDiffuse;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,Jd=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		vec3 iridescenceFresnelDielectric = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		vec3 iridescenceFresnelMetallic = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.diffuseColor );
		material.iridescenceFresnel = mix( iridescenceFresnelDielectric, iridescenceFresnelMetallic, material.metalness );
		material.iridescenceF0Dielectric = Schlick_to_F0( iridescenceFresnelDielectric, 1.0, dotNVi );
		material.iridescenceF0Metallic = Schlick_to_F0( iridescenceFresnelMetallic, 1.0, dotNVi );
	}
#endif
#ifdef STANDARD
	float dotNVms = saturate( dot( geometryNormal, geometryViewDir ) );
	material.dfg = texture2D( dfgLUT, vec2( material.roughness, dotNVms ) ).rg;
	#if ( NUM_SUN_LIGHTS > 0 || NUM_DIR_LIGHTS > 0 || NUM_POINT_LIGHTS > 0 || NUM_SPOT_LIGHTS > 0 )
		float EssMs = material.dfg.x + material.dfg.y;
		material.multiScatteringCompensation = 1.0 + material.specularColorBlended * ( 1.0 / EssMs - 1.0 );
	#endif
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS ) && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SUN_LIGHTS > 0 ) && defined( RE_Direct )
	SunLight sunLight;
	#if defined( USE_SHADOWMAP ) && NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHTS; i ++ ) {
		sunLight = sunLights[ i ];
		getSunLightInfo( sunLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SUN_LIGHT_SHADOWS )
		sunLightShadow = sunLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getSunShadow( sunShadowMap[ i ], sunLightShadow, UNROLLED_LOOP_INDEX ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
	#ifdef USE_LIGHT_PROBES_GRID
		vec3 probeWorldPos = ( ( vec4( geometryPosition, 1.0 ) - viewMatrix[ 3 ] ) * viewMatrix ).xyz;
		vec3 probeWorldNormal = transformNormalByInverseViewMatrix( geometryNormal, viewMatrix );
		irradiance += getLightProbeGridIrradiance( probeWorldPos, probeWorldNormal );
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,Kd=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( ENVMAP_TYPE_CUBE_UV )
		#if defined( STANDARD ) || defined( LAMBERT ) || defined( PHONG )
			iblIrradiance += getIBLIrradiance( geometryNormal );
		#endif
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		vec3 iblRadiance = getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		vec3 iblRadiance = getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_RETROREFLECTION
		#ifdef USE_ANISOTROPY
			vec3 retroIBLRadiance = getIBLAnisotropyRetroRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
		#else
			vec3 retroIBLRadiance = getIBLRetroRadiance( geometryViewDir, geometryNormal, material.roughness );
		#endif
		iblRadiance = mix( iblRadiance, retroIBLRadiance, saturate( material.retroreflectivity ) );
	#endif
	radiance += iblRadiance;
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,jd=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,Qd=`#ifdef USE_LIGHT_PROBES_GRID
uniform highp sampler3D probesSH;
uniform vec3 probesMin;
uniform vec3 probesMax;
uniform vec3 probesResolution;
vec3 getLightProbeGridIrradiance( vec3 worldPos, vec3 worldNormal ) {
	vec3 res = probesResolution;
	vec3 gridRange = probesMax - probesMin;
	vec3 resMinusOne = res - 1.0;
	vec3 probeSpacing = gridRange / resMinusOne;
	vec3 samplePos = worldPos + worldNormal * probeSpacing * 0.5;
	vec3 uvw = clamp( ( samplePos - probesMin ) / gridRange, 0.0, 1.0 );
	uvw = uvw * resMinusOne / res + 0.5 / res;
	float nz          = res.z;
	float paddedSlices = nz + 2.0;
	float atlasDepth  = 7.0 * paddedSlices;
	float uvZBase     = uvw.z * nz + 1.0;
	vec4 s0 = texture( probesSH, vec3( uvw.xy, ( uvZBase                       ) / atlasDepth ) );
	vec4 s1 = texture( probesSH, vec3( uvw.xy, ( uvZBase +       paddedSlices   ) / atlasDepth ) );
	vec4 s2 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 2.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s3 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 3.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s4 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 4.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s5 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 5.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s6 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 6.0 * paddedSlices   ) / atlasDepth ) );
	vec3 c0 = s0.xyz;
	vec3 c1 = vec3( s0.w, s1.xy );
	vec3 c2 = vec3( s1.zw, s2.x );
	vec3 c3 = s2.yzw;
	vec3 c4 = s3.xyz;
	vec3 c5 = vec3( s3.w, s4.xy );
	vec3 c6 = vec3( s4.zw, s5.x );
	vec3 c7 = s5.yzw;
	vec3 c8 = s6.xyz;
	float x = worldNormal.x, y = worldNormal.y, z = worldNormal.z;
	vec3 result = c0 * 0.886227;
	result += c1 * 2.0 * 0.511664 * y;
	result += c2 * 2.0 * 0.511664 * z;
	result += c3 * 2.0 * 0.511664 * x;
	result += c4 * 2.0 * 0.429043 * x * y;
	result += c5 * 2.0 * 0.429043 * y * z;
	result += c6 * ( 0.743125 * z * z - 0.247708 );
	result += c7 * 2.0 * 0.429043 * x * z;
	result += c8 * 0.429043 * ( x * x - y * y );
	return max( result, vec3( 0.0 ) );
}
#endif`,ef=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,tf=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,nf=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,sf=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,rf=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,af=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,of=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,lf=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,cf=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,hf=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,uf=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,df=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,ff=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,pf=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,mf=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,gf=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#ifdef DOUBLE_SIDED
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#ifdef DOUBLE_SIDED
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,_f=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#if defined( USE_PACKED_NORMALMAP )
		mapN = vec3( mapN.xy, sqrt( saturate( 1.0 - dot( mapN.xy, mapN.xy ) ) ) );
	#endif
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,xf=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,vf=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,yf=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
		#ifdef FLIP_SIDED
			vBitangent = - vBitangent;
		#endif
	#endif
#endif`,Sf=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,Mf=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,bf=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,wf=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,Ef=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,Tf=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,Af=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	#ifdef USE_REVERSED_DEPTH_BUFFER
	
		return depth * ( far - near ) - far;
	#else
		return depth * ( near - far ) - near;
	#endif
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	
	#ifdef USE_REVERSED_DEPTH_BUFFER
		return ( near * far ) / ( ( near - far ) * depth - near );
	#else
		return ( near * far ) / ( ( far - near ) * depth - far );
	#endif
}`,Cf=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,Rf=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,If=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,Pf=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,Lf=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,Nf=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,Df=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		#define SUN_LIGHT_CASCADES 2
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#else
			uniform sampler2D sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#endif
		uniform mat4 sunShadowMatrix[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		uniform vec4 sunShadowCascade[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
		struct SunLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SunLightShadow sunLightShadows[ NUM_SUN_LIGHT_SHADOWS ];
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#else
			uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#endif
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#else
			uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#endif
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform samplerCubeShadow pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#elif defined( SHADOWMAP_TYPE_BASIC )
			uniform samplerCube pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#endif
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float interleavedGradientNoise( vec2 position ) {
			return fract( 52.9829189 * fract( dot( position, vec2( 0.06711056, 0.00583715 ) ) ) );
		}
		vec2 vogelDiskSample( int sampleIndex, int samplesCount, float phi ) {
			const float goldenAngle = 2.399963229728653;
			float r = sqrt( ( float( sampleIndex ) + 0.5 ) / float( samplesCount ) );
			float theta = float( sampleIndex ) * goldenAngle + phi;
			return vec2( cos( theta ), sin( theta ) ) * r;
		}
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float getShadow( sampler2DShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
				float radius = shadowRadius * texelSize.x;
				float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
				shadow = (
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 0, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 1, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 2, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 3, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 4, 5, phi ) * radius, shadowCoord.z ) )
				) * 0.2;
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#elif defined( SHADOWMAP_TYPE_VSM )
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 distribution = texture2D( shadowMap, shadowCoord.xy ).rg;
				float mean = distribution.x;
				float variance = distribution.y * distribution.y;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					float hard_shadow = step( mean, shadowCoord.z );
				#else
					float hard_shadow = step( shadowCoord.z, mean );
				#endif
				
				if ( hard_shadow == 1.0 ) {
					shadow = 1.0;
				} else {
					variance = max( variance, 0.0000001 );
					float d = shadowCoord.z - mean;
					float p_max = variance / ( variance + d * d );
					p_max = clamp( ( p_max - 0.3 ) / 0.65, 0.0, 1.0 );
					shadow = max( hard_shadow, p_max );
				}
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#else
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				float depth = texture2D( shadowMap, shadowCoord.xy ).r;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					shadow = step( depth, shadowCoord.z );
				#else
					shadow = step( shadowCoord.z, depth );
				#endif
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#endif
	#if NUM_SUN_LIGHT_SHADOWS > 0
		float getSunShadow(
			#if defined( SHADOWMAP_TYPE_PCF )
				sampler2DShadow shadowMap,
			#else
				sampler2D shadowMap,
			#endif
			SunLightShadow sunLightShadow,
			int shadowIndex
		) {
			vec4 shadowWorldPosition = vec4( vSunShadowWorldPosition.xyz + vSunShadowWorldNormal * sunLightShadow.shadowNormalBias, 1.0 );
			float viewDepth = vSunShadowWorldPosition.w;
			int cascadeOffset = shadowIndex * SUN_LIGHT_CASCADES;
			float shadow = 1.0;
			for ( int i = SUN_LIGHT_CASCADES - 1; i >= 0; i -- ) {
				vec4 cascade = sunShadowCascade[ cascadeOffset + i ];
				if ( viewDepth >= cascade.x && viewDepth < cascade.y ) {
					float cascadeShadow = getShadow(
						shadowMap,
						sunLightShadow.shadowMapSize,
						sunLightShadow.shadowIntensity,
						sunLightShadow.shadowBias,
						sunLightShadow.shadowRadius,
						sunShadowMatrix[ cascadeOffset + i ] * shadowWorldPosition
					);
					shadow = mix( cascadeShadow, shadow, smoothstep( cascade.z, cascade.y, viewDepth ) );
				}
			}
			return shadow;
		}
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#if defined( SHADOWMAP_TYPE_PCF )
	float getPointShadow( samplerCubeShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			#ifdef USE_REVERSED_DEPTH_BUFFER
				float dp = ( shadowCameraNear * ( shadowCameraFar - viewSpaceZ ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp -= shadowBias;
			#else
				float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp += shadowBias;
			#endif
			float texelSize = shadowRadius / shadowMapSize.x;
			vec3 absDir = abs( bd3D );
			vec3 tangent = absDir.x > absDir.z ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 );
			tangent = normalize( cross( bd3D, tangent ) );
			vec3 bitangent = cross( bd3D, tangent );
			float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
			vec2 sample0 = vogelDiskSample( 0, 5, phi );
			vec2 sample1 = vogelDiskSample( 1, 5, phi );
			vec2 sample2 = vogelDiskSample( 2, 5, phi );
			vec2 sample3 = vogelDiskSample( 3, 5, phi );
			vec2 sample4 = vogelDiskSample( 4, 5, phi );
			shadow = (
				texture( shadowMap, vec4( bd3D + ( tangent * sample0.x + bitangent * sample0.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample1.x + bitangent * sample1.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample2.x + bitangent * sample2.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample3.x + bitangent * sample3.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample4.x + bitangent * sample4.y ) * texelSize, dp ) )
			) * 0.2;
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#elif defined( SHADOWMAP_TYPE_BASIC )
	float getPointShadow( samplerCube shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			float depth = textureCube( shadowMap, bd3D ).r;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				depth = 1.0 - depth;
			#endif
			shadow = step( dp, depth );
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#endif
	#endif
#endif`,Uf=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,Ff=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_SUN_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	#ifdef HAS_NORMAL
		vec3 shadowWorldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
	#else
		vec3 shadowWorldNormal = vec3( 0.0 );
	#endif
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_SUN_LIGHT_SHADOWS > 0
		vSunShadowWorldPosition = vec4( worldPosition.xyz, - mvPosition.z );
		vSunShadowWorldNormal = shadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,Of=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHT_SHADOWS; i ++ ) {
		sunLight = sunLightShadows[ i ];
		shadow *= receiveShadow ? getSunShadow( sunShadowMap[ i ], sunLight, UNROLLED_LOOP_INDEX ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0 && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,Bf=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,zf=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,kf=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,Gf=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,Hf=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,Vf=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,Wf=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,Xf=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,qf=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseContribution, material.specularColorBlended, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,$f=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,Yf=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,Zf=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,Jf=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`;var Kf=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,jf=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,Qf=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,ep=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,tp=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vWorldDirection );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,np=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,ip=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,sp=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,rp=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,ap=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,op=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = vec4( dist, 0.0, 0.0, 1.0 );
}`,lp=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,cp=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,hp=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,up=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,dp=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,fp=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,pp=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,mp=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,gp=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,_p=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,xp=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,vp=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( normalize( normal ) * 0.5 + 0.5, diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,yp=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Sp=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Mp=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,bp=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_RETROREFLECTION
	uniform float retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
 
		outgoingLight = outgoingLight + sheenSpecularDirect + sheenSpecularIndirect;
 
 	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,wp=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Ep=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Tp=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,Ap=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Cp=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Rp=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Ip=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,Pp=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,Fe={alphahash_fragment:Ku,alphahash_pars_fragment:ju,alphamap_fragment:Qu,alphamap_pars_fragment:ed,alphatest_fragment:td,alphatest_pars_fragment:nd,aomap_fragment:id,aomap_pars_fragment:sd,batching_pars_vertex:rd,batching_vertex:ad,begin_vertex:od,beginnormal_vertex:ld,bsdfs:cd,iridescence_fragment:hd,bumpmap_pars_fragment:ud,clipping_planes_fragment:dd,clipping_planes_pars_fragment:fd,clipping_planes_pars_vertex:pd,clipping_planes_vertex:md,color_fragment:gd,color_pars_fragment:_d,color_pars_vertex:xd,color_vertex:vd,common:yd,cube_uv_reflection_fragment:Sd,defaultnormal_vertex:Md,displacementmap_pars_vertex:bd,displacementmap_vertex:wd,emissivemap_fragment:Ed,emissivemap_pars_fragment:Td,colorspace_fragment:Ad,colorspace_pars_fragment:Cd,envmap_fragment:Rd,envmap_common_pars_fragment:Id,envmap_pars_fragment:Pd,envmap_pars_vertex:Ld,envmap_physical_pars_fragment:Vd,envmap_vertex:Nd,fog_vertex:Dd,fog_pars_vertex:Ud,fog_fragment:Fd,fog_pars_fragment:Od,gradientmap_pars_fragment:Bd,lightmap_pars_fragment:zd,lights_lambert_fragment:kd,lights_lambert_pars_fragment:Gd,lights_pars_begin:Hd,lights_toon_fragment:Wd,lights_toon_pars_fragment:Xd,lights_phong_fragment:qd,lights_phong_pars_fragment:$d,lights_physical_fragment:Yd,lights_physical_pars_fragment:Zd,lights_fragment_begin:Jd,lights_fragment_maps:Kd,lights_fragment_end:jd,lightprobes_pars_fragment:Qd,logdepthbuf_fragment:ef,logdepthbuf_pars_fragment:tf,logdepthbuf_pars_vertex:nf,logdepthbuf_vertex:sf,map_fragment:rf,map_pars_fragment:af,map_particle_fragment:of,map_particle_pars_fragment:lf,metalnessmap_fragment:cf,metalnessmap_pars_fragment:hf,morphinstance_vertex:uf,morphcolor_vertex:df,morphnormal_vertex:ff,morphtarget_pars_vertex:pf,morphtarget_vertex:mf,normal_fragment_begin:gf,normal_fragment_maps:_f,normal_pars_fragment:xf,normal_pars_vertex:vf,normal_vertex:yf,normalmap_pars_fragment:Sf,clearcoat_normal_fragment_begin:Mf,clearcoat_normal_fragment_maps:bf,clearcoat_pars_fragment:wf,iridescence_pars_fragment:Ef,opaque_fragment:Tf,packing:Af,premultiplied_alpha_fragment:Cf,project_vertex:Rf,dithering_fragment:If,dithering_pars_fragment:Pf,roughnessmap_fragment:Lf,roughnessmap_pars_fragment:Nf,shadowmap_pars_fragment:Df,shadowmap_pars_vertex:Uf,shadowmap_vertex:Ff,shadowmask_pars_fragment:Of,skinbase_vertex:Bf,skinning_pars_vertex:zf,skinning_vertex:kf,skinnormal_vertex:Gf,specularmap_fragment:Hf,specularmap_pars_fragment:Vf,tonemapping_fragment:Wf,tonemapping_pars_fragment:Xf,transmission_fragment:qf,transmission_pars_fragment:$f,uv_pars_fragment:Yf,uv_pars_vertex:Zf,uv_vertex:Jf,worldpos_vertex:Kf,background_vert:jf,background_frag:Qf,backgroundCube_vert:ep,backgroundCube_frag:tp,cube_vert:np,cube_frag:ip,depth_vert:sp,depth_frag:rp,distance_vert:ap,distance_frag:op,equirect_vert:lp,equirect_frag:cp,linedashed_vert:hp,linedashed_frag:up,meshbasic_vert:dp,meshbasic_frag:fp,meshlambert_vert:pp,meshlambert_frag:mp,meshmatcap_vert:gp,meshmatcap_frag:_p,meshnormal_vert:xp,meshnormal_frag:vp,meshphong_vert:yp,meshphong_frag:Sp,meshphysical_vert:Mp,meshphysical_frag:bp,meshtoon_vert:wp,meshtoon_frag:Ep,points_vert:Tp,points_frag:Ap,shadow_vert:Cp,shadow_frag:Rp,sprite_vert:Ip,sprite_frag:Pp},ue={common:{diffuse:{value:new qe(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new Le},alphaMap:{value:null},alphaMapTransform:{value:new Le},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new Le}},envmap:{envMap:{value:null},envMapRotation:{value:new Le},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:0.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new Le}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new Le}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new Le},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new Le},normalScale:{value:new Xe(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new Le},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new Le}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new Le}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new Le}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:0.00025},fogNear:{value:1},fogFar:{value:2000},fogColor:{value:new qe(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},sunLights:{value:[],properties:{direction:{},color:{}}},sunLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},sunShadowMatrix:{value:[]},sunShadowCascade:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new F},probesMax:{value:new F},probesResolution:{value:new F}},points:{diffuse:{value:new qe(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new Le},alphaTest:{value:0},uvTransform:{value:new Le}},sprite:{diffuse:{value:new qe(16777215)},opacity:{value:1},center:{value:new Xe(0.5,0.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new Le},alphaMap:{value:null},alphaMapTransform:{value:new Le},alphaTest:{value:0}}},fn={basic:{uniforms:Pt([ue.common,ue.specularmap,ue.envmap,ue.aomap,ue.lightmap,ue.fog]),vertexShader:Fe.meshbasic_vert,fragmentShader:Fe.meshbasic_frag},lambert:{uniforms:Pt([ue.common,ue.specularmap,ue.envmap,ue.aomap,ue.lightmap,ue.emissivemap,ue.bumpmap,ue.normalmap,ue.displacementmap,ue.fog,ue.lights,{emissive:{value:new qe(0)},envMapIntensity:{value:1}}]),vertexShader:Fe.meshlambert_vert,fragmentShader:Fe.meshlambert_frag},phong:{uniforms:Pt([ue.common,ue.specularmap,ue.envmap,ue.aomap,ue.lightmap,ue.emissivemap,ue.bumpmap,ue.normalmap,ue.displacementmap,ue.fog,ue.lights,{emissive:{value:new qe(0)},specular:{value:new qe(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:Fe.meshphong_vert,fragmentShader:Fe.meshphong_frag},standard:{uniforms:Pt([ue.common,ue.envmap,ue.aomap,ue.lightmap,ue.emissivemap,ue.bumpmap,ue.normalmap,ue.displacementmap,ue.roughnessmap,ue.metalnessmap,ue.fog,ue.lights,{emissive:{value:new qe(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:Fe.meshphysical_vert,fragmentShader:Fe.meshphysical_frag},toon:{uniforms:Pt([ue.common,ue.aomap,ue.lightmap,ue.emissivemap,ue.bumpmap,ue.normalmap,ue.displacementmap,ue.gradientmap,ue.fog,ue.lights,{emissive:{value:new qe(0)}}]),vertexShader:Fe.meshtoon_vert,fragmentShader:Fe.meshtoon_frag},matcap:{uniforms:Pt([ue.common,ue.bumpmap,ue.normalmap,ue.displacementmap,ue.fog,{matcap:{value:null}}]),vertexShader:Fe.meshmatcap_vert,fragmentShader:Fe.meshmatcap_frag},points:{uniforms:Pt([ue.points,ue.fog]),vertexShader:Fe.points_vert,fragmentShader:Fe.points_frag},dashed:{uniforms:Pt([ue.common,ue.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:Fe.linedashed_vert,fragmentShader:Fe.linedashed_frag},depth:{uniforms:Pt([ue.common,ue.displacementmap]),vertexShader:Fe.depth_vert,fragmentShader:Fe.depth_frag},normal:{uniforms:Pt([ue.common,ue.bumpmap,ue.normalmap,ue.displacementmap,{opacity:{value:1}}]),vertexShader:Fe.meshnormal_vert,fragmentShader:Fe.meshnormal_frag},sprite:{uniforms:Pt([ue.sprite,ue.fog]),vertexShader:Fe.sprite_vert,fragmentShader:Fe.sprite_frag},background:{uniforms:{uvTransform:{value:new Le},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:Fe.background_vert,fragmentShader:Fe.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new Le}},vertexShader:Fe.backgroundCube_vert,fragmentShader:Fe.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:Fe.cube_vert,fragmentShader:Fe.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:Fe.equirect_vert,fragmentShader:Fe.equirect_frag},distance:{uniforms:Pt([ue.common,ue.displacementmap,{referencePosition:{value:new F},nearDistance:{value:1},farDistance:{value:1000}}]),vertexShader:Fe.distance_vert,fragmentShader:Fe.distance_frag},shadow:{uniforms:Pt([ue.lights,ue.fog,{color:{value:new qe(0)},opacity:{value:1}}]),vertexShader:Fe.shadow_vert,fragmentShader:Fe.shadow_frag}};fn.physical={uniforms:Pt([fn.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new Le},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new Le},clearcoatNormalScale:{value:new Xe(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new Le},dispersion:{value:0},retroreflectivity:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new Le},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new Le},sheen:{value:0},sheenColor:{value:new qe(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new Le},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new Le},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new Le},transmissionSamplerSize:{value:new Xe},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new Le},attenuationDistance:{value:0},attenuationColor:{value:new qe(0)},specularColor:{value:new qe(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new Le},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new Le},anisotropyVector:{value:new Xe},anisotropyMap:{value:null},anisotropyMapTransform:{value:new Le}}]),vertexShader:Fe.meshphysical_vert,fragmentShader:Fe.meshphysical_frag};var mr={r:0,b:0,g:0},Lp=new ht,bh=new Le;bh.set(-1,0,0,0,1,0,0,0,1);function Np(e,t,n,i,s,r){let a=new qe(0),o=s===!0?0:1,c,l,u=null,d=0,h=null;function m(T){let I=T.isScene===!0?T.background:null;if(I&&I.isTexture){let S=T.backgroundBlurriness>0;I=t.get(I,S)}return I}function v(T){let I=!1,S=m(T);if(S===null)p(a,o);else if(S&&S.isColor)p(S,1),I=!0;let w=e.xr.getEnvironmentBlendMode();if(w==="additive")n.buffers.color.setClear(0,0,0,1,r);else if(w==="alpha-blend")n.buffers.color.setClear(0,0,0,0,r);if(e.autoClear||I)n.buffers.depth.setTest(!0),n.buffers.depth.setMask(!0),n.buffers.color.setMask(!0),e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil)}function b(T,I){let S=m(I);if(S&&(S.isCubeTexture||S.mapping===Qi)){if(l===void 0)l=new Dt(new Di(1,1,1),new Yt({name:"BackgroundCubeMaterial",uniforms:ni(fn.backgroundCube.uniforms),vertexShader:fn.backgroundCube.vertexShader,fragmentShader:fn.backgroundCube.fragmentShader,side:Bt,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),l.geometry.deleteAttribute("uv"),l.onBeforeRender=function(w,E,A){this.matrixWorld.copyPosition(A.matrixWorld)},Object.defineProperty(l.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),i.update(l);if(l.material.uniforms.envMap.value=S,l.material.uniforms.backgroundBlurriness.value=I.backgroundBlurriness,l.material.uniforms.backgroundIntensity.value=I.backgroundIntensity,l.material.uniforms.backgroundRotation.value.setFromMatrix4(Lp.makeRotationFromEuler(I.backgroundRotation)).transpose(),S.isCubeTexture&&S.isRenderTargetTexture===!1)l.material.uniforms.backgroundRotation.value.premultiply(bh);if(l.material.toneMapped=ke.getTransfer(S.colorSpace)!==nt,u!==S||d!==S.version||h!==e.toneMapping)l.material.needsUpdate=!0,u=S,d=S.version,h=e.toneMapping;l.layers.enableAll(),T.unshift(l,l.geometry,l.material,0,0,null)}else if(S&&S.isTexture){if(c===void 0)c=new Dt(new rs(2,2),new Yt({name:"BackgroundMaterial",uniforms:ni(fn.background.uniforms),vertexShader:fn.background.vertexShader,fragmentShader:fn.background.fragmentShader,side:Ri,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),Object.defineProperty(c.material,"map",{get:function(){return this.uniforms.t2D.value}}),i.update(c);if(c.material.uniforms.t2D.value=S,c.material.uniforms.backgroundIntensity.value=I.backgroundIntensity,c.material.toneMapped=ke.getTransfer(S.colorSpace)!==nt,S.matrixAutoUpdate===!0)S.updateMatrix();if(c.material.uniforms.uvTransform.value.copy(S.matrix),u!==S||d!==S.version||h!==e.toneMapping)c.material.needsUpdate=!0,u=S,d=S.version,h=e.toneMapping;c.layers.enableAll(),T.unshift(c,c.geometry,c.material,0,0,null)}}function p(T,I){T.getRGB(mr,lo(e)),n.buffers.color.setClear(mr.r,mr.g,mr.b,I,r)}function f(){if(l!==void 0)l.geometry.dispose(),l.material.dispose(),l=void 0;if(c!==void 0)c.geometry.dispose(),c.material.dispose(),c=void 0}return{getClearColor:function(){return a},setClearColor:function(T,I=1){a.set(T),o=I,p(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(T){o=T,p(a,o)},render:v,addToRenderList:b,dispose:f}}function Dp(e,t){let n=e.getParameter(e.MAX_VERTEX_ATTRIBS),i={},s=h(null),r=s,a=!1;function o(D,U,J,C,V){let K=!1,G=d(D,C,J,U);if(r!==G)r=G,l(r.object);if(K=m(D,C,J,V),K)v(D,C,J,V);if(V!==null)t.update(V,e.ELEMENT_ARRAY_BUFFER);if(K||a){if(a=!1,S(D,U,J,C),V!==null)e.bindBuffer(e.ELEMENT_ARRAY_BUFFER,t.get(V).buffer)}}function c(){return e.createVertexArray()}function l(D){return e.bindVertexArray(D)}function u(D){return e.deleteVertexArray(D)}function d(D,U,J,C){let V=C.wireframe===!0,K=i[U.id];if(K===void 0)K={},i[U.id]=K;let G=D.isInstancedMesh===!0?D.id:0,ne=K[G];if(ne===void 0)ne={},K[G]=ne;let X=ne[J.id];if(X===void 0)X={},ne[J.id]=X;let j=X[V];if(j===void 0)j=h(c()),X[V]=j;return j}function h(D){let U=[],J=[],C=[];for(let V=0;V<n;V++)U[V]=0,J[V]=0,C[V]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:U,enabledAttributes:J,attributeDivisors:C,object:D,attributes:{},index:null}}function m(D,U,J,C){let V=r.attributes,K=U.attributes,G=0,ne=J.getAttributes();for(let X in ne)if(ne[X].location>=0){let te=V[X],Re=K[X];if(Re===void 0){if(X==="instanceMatrix"&&D.instanceMatrix)Re=D.instanceMatrix;if(X==="instanceColor"&&D.instanceColor)Re=D.instanceColor}if(te===void 0)return!0;if(te.attribute!==Re)return!0;if(Re&&te.data!==Re.data)return!0;G++}if(r.attributesNum!==G)return!0;if(r.index!==C)return!0;return!1}function v(D,U,J,C){let V={},K=U.attributes,G=0,ne=J.getAttributes();for(let X in ne)if(ne[X].location>=0){let te=K[X];if(te===void 0){if(X==="instanceMatrix"&&D.instanceMatrix)te=D.instanceMatrix;if(X==="instanceColor"&&D.instanceColor)te=D.instanceColor}let Re={};if(Re.attribute=te,te&&te.data)Re.data=te.data;V[X]=Re,G++}r.attributes=V,r.attributesNum=G,r.index=C}function b(){let D=r.newAttributes;for(let U=0,J=D.length;U<J;U++)D[U]=0}function p(D){f(D,0)}function f(D,U){let J=r.newAttributes,C=r.enabledAttributes,V=r.attributeDivisors;if(J[D]=1,C[D]===0)e.enableVertexAttribArray(D),C[D]=1;if(V[D]!==U)e.vertexAttribDivisor(D,U),V[D]=U}function T(){let D=r.newAttributes,U=r.enabledAttributes;for(let J=0,C=U.length;J<C;J++)if(U[J]!==D[J])e.disableVertexAttribArray(J),U[J]=0}function I(D,U,J,C,V,K,G){if(G===!0)e.vertexAttribIPointer(D,U,J,V,K);else e.vertexAttribPointer(D,U,J,C,V,K)}function S(D,U,J,C){b();let V=C.attributes,K=J.getAttributes(),G=U.defaultAttributeValues;for(let ne in K){let X=K[ne];if(X.location>=0){let j=V[ne];if(j===void 0){if(ne==="instanceMatrix"&&D.instanceMatrix)j=D.instanceMatrix;if(ne==="instanceColor"&&D.instanceColor)j=D.instanceColor}if(j!==void 0){let te=j.normalized,Re=j.itemSize,Ee=t.get(j);if(Ee===void 0)continue;let{buffer:it,type:Oe,bytesPerElement:q}=Ee,ie=Oe===e.INT||Oe===e.UNSIGNED_INT||j.gpuType===ma;if(j.isInterleavedBufferAttribute){let re=j.data,Te=re.stride,Ie=j.offset;if(re.isInstancedInterleavedBuffer){for(let be=0;be<X.locationSize;be++)f(X.location+be,re.meshPerAttribute);if(D.isInstancedMesh!==!0&&C._maxInstanceCount===void 0)C._maxInstanceCount=re.meshPerAttribute*re.count}else for(let be=0;be<X.locationSize;be++)p(X.location+be);e.bindBuffer(e.ARRAY_BUFFER,it);for(let be=0;be<X.locationSize;be++)I(X.location+be,Re/X.locationSize,Oe,te,Te*q,(Ie+Re/X.locationSize*be)*q,ie)}else{if(j.isInstancedBufferAttribute){for(let re=0;re<X.locationSize;re++)f(X.location+re,j.meshPerAttribute);if(D.isInstancedMesh!==!0&&C._maxInstanceCount===void 0)C._maxInstanceCount=j.meshPerAttribute*j.count}else for(let re=0;re<X.locationSize;re++)p(X.location+re);e.bindBuffer(e.ARRAY_BUFFER,it);for(let re=0;re<X.locationSize;re++)I(X.location+re,Re/X.locationSize,Oe,te,Re*q,Re/X.locationSize*re*q,ie)}}else if(G!==void 0){let te=G[ne];if(te!==void 0)switch(te.length){case 2:e.vertexAttrib2fv(X.location,te);break;case 3:e.vertexAttrib3fv(X.location,te);break;case 4:e.vertexAttrib4fv(X.location,te);break;default:e.vertexAttrib1fv(X.location,te)}}}}T()}function w(){M();for(let D in i){let U=i[D];for(let J in U){let C=U[J];for(let V in C){let K=C[V];for(let G in K)u(K[G].object),delete K[G];delete C[V]}}delete i[D]}}function E(D){if(i[D.id]===void 0)return;let U=i[D.id];for(let J in U){let C=U[J];for(let V in C){let K=C[V];for(let G in K)u(K[G].object),delete K[G];delete C[V]}}delete i[D.id]}function A(D){for(let U in i){let J=i[U];for(let C in J){let V=J[C];if(V[D.id]===void 0)continue;let K=V[D.id];for(let G in K)u(K[G].object),delete K[G];delete V[D.id]}}}function x(D){for(let U in i){let J=i[U],C=D.isInstancedMesh===!0?D.id:0,V=J[C];if(V===void 0)continue;for(let K in V){let G=V[K];for(let ne in G)u(G[ne].object),delete G[ne];delete V[K]}if(delete J[C],Object.keys(J).length===0)delete i[U]}}function M(){if(H(),a=!0,r===s)return;r=s,l(r.object)}function H(){s.geometry=null,s.program=null,s.wireframe=!1}return{setup:o,reset:M,resetDefaultState:H,dispose:w,releaseStatesOfGeometry:E,releaseStatesOfObject:x,releaseStatesOfProgram:A,initAttributes:b,enableAttribute:p,disableUnusedAttributes:T}}function Up(e,t,n){let i;function s(c){i=c}function r(c,l){e.drawArrays(i,c,l),n.update(l,i,1)}function a(c,l,u){if(u===0)return;e.drawArraysInstanced(i,c,l,u),n.update(l,i,u)}function o(c,l,u){if(u===0)return;t.get("WEBGL_multi_draw").multiDrawArraysWEBGL(i,c,0,l,0,u);let h=0;for(let m=0;m<u;m++)h+=l[m];n.update(h,i,1)}this.setMode=s,this.render=r,this.renderInstances=a,this.renderMultiDraw=o}function Fp(e,t,n,i){let s;function r(){if(s!==void 0)return s;if(t.has("EXT_texture_filter_anisotropic")===!0){let A=t.get("EXT_texture_filter_anisotropic");s=e.getParameter(A.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else s=0;return s}function a(A){if(A!==un&&i.convert(A)!==e.getParameter(e.IMPLEMENTATION_COLOR_READ_FORMAT))return!1;return!0}function o(A){let x=A===hn&&(t.has("EXT_color_buffer_half_float")||t.has("EXT_color_buffer_float"));if(A!==en&&A!==Sn&&!x&&i.convert(A)!==e.getParameter(e.IMPLEMENTATION_COLOR_READ_TYPE))return!1;return!0}function c(A){if(A==="highp"){if(e.getShaderPrecisionFormat(e.VERTEX_SHADER,e.HIGH_FLOAT).precision>0&&e.getShaderPrecisionFormat(e.FRAGMENT_SHADER,e.HIGH_FLOAT).precision>0)return"highp";A="mediump"}if(A==="mediump"){if(e.getShaderPrecisionFormat(e.VERTEX_SHADER,e.MEDIUM_FLOAT).precision>0&&e.getShaderPrecisionFormat(e.FRAGMENT_SHADER,e.MEDIUM_FLOAT).precision>0)return"mediump"}return"lowp"}let l=n.precision!==void 0?n.precision:"highp",u=c(l);if(u!==l)Ce("WebGLRenderer:",l,"not supported, using",u,"instead."),l=u;let d=n.logarithmicDepthBuffer===!0,h=n.reversedDepthBuffer===!0&&t.has("EXT_clip_control");if(n.reversedDepthBuffer===!0&&h===!1)Ce("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");let m=e.getParameter(e.MAX_TEXTURE_IMAGE_UNITS),v=e.getParameter(e.MAX_VERTEX_TEXTURE_IMAGE_UNITS),b=e.getParameter(e.MAX_TEXTURE_SIZE),p=e.getParameter(e.MAX_CUBE_MAP_TEXTURE_SIZE),f=e.getParameter(e.MAX_VERTEX_ATTRIBS),T=e.getParameter(e.MAX_VERTEX_UNIFORM_VECTORS),I=e.getParameter(e.MAX_VARYING_VECTORS),S=e.getParameter(e.MAX_FRAGMENT_UNIFORM_VECTORS),w=e.getParameter(e.MAX_SAMPLES),E=e.getParameter(e.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:r,getMaxPrecision:c,textureFormatReadable:a,textureTypeReadable:o,precision:l,logarithmicDepthBuffer:d,reversedDepthBuffer:h,maxTextures:m,maxVertexTextures:v,maxTextureSize:b,maxCubemapSize:p,maxAttributes:f,maxVertexUniforms:T,maxVaryings:I,maxFragmentUniforms:S,maxSamples:w,samples:E}}function Op(e){let t=this,n=null,i=0,s=!1,r=!1,a=new on,o=new Le,c={value:null,needsUpdate:!1};this.uniform=c,this.numPlanes=0,this.numIntersection=0,this.init=function(d,h){let m=d.length!==0||h||i!==0||s;return s=h,i=d.length,m},this.beginShadows=function(){r=!0,u(null)},this.endShadows=function(){r=!1},this.setGlobalState=function(d,h){n=u(d,h,0)},this.setState=function(d,h,m){let{clippingPlanes:v,clipIntersection:b,clipShadows:p}=d,f=e.get(d);if(!s||v===null||v.length===0||r&&!p)if(r)u(null);else l();else{let T=r?0:i,I=T*4,S=f.clippingState||null;c.value=S,S=u(v,h,I,m);for(let w=0;w!==I;++w)S[w]=n[w];f.clippingState=S,this.numIntersection=b?this.numPlanes:0,this.numPlanes+=T}};function l(){if(c.value!==n)c.value=n,c.needsUpdate=i>0;t.numPlanes=i,t.numIntersection=0}function u(d,h,m,v){let b=d!==null?d.length:0,p=null;if(b!==0){if(p=c.value,v!==!0||p===null){let f=m+b*4,T=h.matrixWorldInverse;if(o.getNormalMatrix(T),p===null||p.length<f)p=new Float32Array(f);for(let I=0,S=m;I!==b;++I,S+=4)a.copy(d[I]).applyMatrix4(T,o),a.normal.toArray(p,S),p[S+3]=a.constant}c.value=p,c.needsUpdate=!0}return t.numPlanes=b,t.numIntersection=0,p}}var Oi=4,Bp=6,zp=20,kp=256,as=new fr,th=new qe,Ro=null,Io=0,Po=0,Lo=!1,Gp=new F,ai=new F;class Uo{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,n=0.1,i=100,s={}){let{size:r=256,position:a=Gp}=s;Ro=this._renderer.getRenderTarget(),Io=this._renderer.getActiveCubeFace(),Po=this._renderer.getActiveMipmapLevel(),Lo=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(r);let o=this._allocateTargets();if(o.depthBuffer=!0,this._sceneToCubeUV(e,n,i,o,a),t>0)this._blur(o,0,0,t);return this._applyPMREM(o),this._cleanup(o),o}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){if(this._cubemapMaterial===null)this._cubemapMaterial=sh(),this._compileMaterial(this._cubemapMaterial)}compileEquirectangularShader(){if(this._equirectMaterial===null)this._equirectMaterial=ih(),this._compileMaterial(this._equirectMaterial)}dispose(){if(this._dispose(),this._cubemapMaterial!==null)this._cubemapMaterial.dispose();if(this._equirectMaterial!==null)this._equirectMaterial.dispose();if(this._backgroundBox!==null)this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose()}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){if(this._blurMaterial!==null)this._blurMaterial.dispose();if(this._ggxMaterial!==null)this._ggxMaterial.dispose();if(this._pingPongRenderTarget!==null)this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(Ro,Io,Po),this._renderer.xr.enabled=Lo,e.scissorTest=!1,Fi(e,0,0,e.width,e.height)}_fromTexture(e,t){if(e.mapping===Pi||e.mapping===Xn)this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width);else this._setSize(e.image.width/4);Ro=this._renderer.getRenderTarget(),Io=this._renderer.getActiveCubeFace(),Po=this._renderer.getActiveMipmapLevel(),Lo=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let n=t||this._allocateTargets();return this._textureToCubeUV(e,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){let e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,n={magFilter:zt,minFilter:zt,generateMipmaps:!1,type:hn,format:un,colorSpace:ja,depthBuffer:!1},i=nh(e,t,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){if(this._pingPongRenderTarget!==null)this._dispose();this._pingPongRenderTarget=nh(e,t,n);let{_lodMax:s}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods}=Hp(s)),this._blurMaterial=Wp(s,e,t),this._ggxMaterial=Vp(s,e,t)}return i}_compileMaterial(e){let t=new Dt(new bt,e);this._renderer.compile(t,as)}_sceneToCubeUV(e,t,n,i,s){let o=new Nt(90,1,t,n),c=[1,-1,1,1,1,1],l=[1,1,1,-1,-1,-1],u=this._renderer,{autoClear:d,toneMapping:h}=u;if(u.getClearColor(th),u.toneMapping=Qt,u.autoClear=!1,u.state.buffers.depth.getReversed())u.setRenderTarget(i),u.clearDepth(),u.setRenderTarget(null);if(this._backgroundBox===null)this._backgroundBox=new Dt(new Di,new Fn({name:"PMREM.Background",side:Bt,depthWrite:!1,depthTest:!1}));let v=this._backgroundBox,b=v.material,p=!1,f=e.background;if(f){if(f.isColor)b.color.copy(f),e.background=null,p=!0}else b.color.copy(th),p=!0;for(let T=0;T<6;T++){let I=T%3;if(I===0)o.up.set(0,c[T],0),o.position.set(s.x,s.y,s.z),o.lookAt(s.x+l[T],s.y,s.z);else if(I===1)o.up.set(0,0,c[T]),o.position.set(s.x,s.y,s.z),o.lookAt(s.x,s.y+l[T],s.z);else o.up.set(0,c[T],0),o.position.set(s.x,s.y,s.z),o.lookAt(s.x,s.y,s.z+l[T]);let S=this._cubeSize;if(Fi(i,I*S,T>2?S:0,S,S),u.setRenderTarget(i),p)u.render(v,o);u.render(e,o)}u.toneMapping=h,u.autoClear=d,e.background=f}_textureToCubeUV(e,t){let n=this._renderer,i=e.mapping===Pi||e.mapping===Xn;if(i){if(this._cubemapMaterial===null)this._cubemapMaterial=sh();this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1}else if(this._equirectMaterial===null)this._equirectMaterial=ih();let s=i?this._cubemapMaterial:this._equirectMaterial,r=this._lodMeshes[0];r.material=s;let a=s.uniforms;a.envMap.value=e;let o=this._cubeSize;Fi(t,0,0,3*o,2*o),n.setRenderTarget(t),n.render(r,as)}_applyPMREM(e){let t=this._renderer,n=t.autoClear;t.autoClear=!1;let i=this._lodMeshes.length;for(let s=1;s<i;s++)this._applyGGXFilter(e,s-1,s);t.autoClear=n}_applyGGXFilter(e,t,n){let i=this._renderer,s=this._pingPongRenderTarget,r=this._ggxMaterial,a=this._lodMeshes[n];a.material=r;let o=r.uniforms,c=n/(this._lodMeshes.length-1),l=t/(this._lodMeshes.length-1),u=Math.sqrt(c*c-l*l),d=c*1.25,h=u*d,{_lodMax:m}=this,v=this._sizeLods[n],b=3*v*(n>m-Oi?n-m+Oi:0),p=4*(this._cubeSize-v);o.envMap.value=e.texture,o.roughness.value=h,o.mipInt.value=m-t,Fi(s,b,p,3*v,2*v),i.setRenderTarget(s),i.render(a,as),o.envMap.value=s.texture,o.roughness.value=0,o.mipInt.value=m-n,Fi(e,b,p,3*v,2*v),i.setRenderTarget(e),i.render(a,as)}_blur(e,t,n,i){let s=this._pingPongRenderTarget,r=Math.min(i,Math.PI)/Math.SQRT2;this._blurPass(e,s,t,n,r),this._blurPass(s,e,n,n,r)}_blurPass(e,t,n,i,s){let r=this._renderer,a=this._blurMaterial,o=this._lodMeshes[i];o.material=a;let c=a.uniforms;c.envMap.value=e.texture,c.sigma.value=s,c.mipInt.value=this._lodMax-n;let l=this._sizeLods[i],u=3*l*(i>this._lodMax-Oi?i-this._lodMax+Oi:0),d=4*(this._cubeSize-l);Fi(t,u,d,3*l,2*l),r.setRenderTarget(t),r.render(o,as)}}function Hp(e){let t=[],n=[],i=e,s=e-Oi+1+Bp;for(let r=0;r<s;r++){let a=Math.pow(2,i);t.push(a);let o=1/(a-2),c=-o,l=1+o,u=[c,c,l,c,l,l,c,c,l,l,c,l],d=6,h=6,m=3,v=new Float32Array(m*h*d),b=new Float32Array(m*h*d);for(let f=0;f<d;f++){let T=f%3*2/3-1,I=f>2?0:-1,S=[T,I,0,T+0.6666666666666666,I,0,T+0.6666666666666666,I+1,0,T,I,0,T+0.6666666666666666,I+1,0,T,I+1,0];v.set(S,m*h*f);for(let w=0;w<h;w++){let E=u[w*2]*2-1,A=u[w*2+1]*2-1;if(f===0)ai.set(1,A,E);else if(f===1)ai.set(-E,1,-A);else if(f===2)ai.set(-E,A,1);else if(f===3)ai.set(-1,A,-E);else if(f===4)ai.set(-E,-1,A);else ai.set(E,A,-1);ai.toArray(b,(f*h+w)*m)}}let p=new bt;if(p.setAttribute("position",new Ht(v,m)),p.setAttribute("outputDirection",new Ht(b,m)),n.push(new Dt(p,null)),i>Oi)i--}return{lodMeshes:n,sizeLods:t}}function nh(e,t,n){let i=new Vt(e,t,n);return i.texture.mapping=Qi,i.texture.name="PMREM.cubeUv",i.scissorTest=!0,i}function Fi(e,t,n,i,s){e.viewport.set(t,n,i,s),e.scissor.set(t,n,i,s)}function Vp(e,t,n){return new Yt({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:kp,CUBEUV_TEXEL_WIDTH:1/t,CUBEUV_TEXEL_HEIGHT:1/n,CUBEUV_MAX_MIP:`${e}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:_r(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float roughness;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359

			// Van der Corput radical inverse
			float radicalInverse_VdC(uint bits) {
				bits = (bits << 16u) | (bits >> 16u);
				bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
				bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
				bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
				bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);
				return float(bits) * 2.3283064365386963e-10; // / 0x100000000
			}

			// Hammersley sequence
			vec2 hammersley(uint i, uint N) {
				return vec2(float(i) / float(N), radicalInverse_VdC(i));
			}

			// GGX VNDF importance sampling (Eric Heitz 2018)
			// "Sampling the GGX Distribution of Visible Normals"
			// https://jcgt.org/published/0007/04/01/
			vec3 importanceSampleGGX_VNDF(vec2 Xi, vec3 V, float roughness) {
				float alpha = roughness * roughness;

				// Section 4.1: Orthonormal basis
				vec3 T1 = vec3(1.0, 0.0, 0.0);
				vec3 T2 = cross(V, T1);

				// Section 4.2: Parameterization of projected area
				float r = sqrt(Xi.x);
				float phi = 2.0 * PI * Xi.y;
				float t1 = r * cos(phi);
				float t2 = r * sin(phi);
				float s = 0.5 * (1.0 + V.z);
				t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;

				// Section 4.3: Reprojection onto hemisphere
				vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0.0, 1.0 - t1 * t1 - t2 * t2)) * V;

				// Section 3.4: Transform back to ellipsoid configuration
				return normalize(vec3(alpha * Nh.x, alpha * Nh.y, max(0.0, Nh.z)));
			}

			void main() {
				vec3 N = normalize(vOutputDirection);
				vec3 V = N; // Assume view direction equals normal for pre-filtering

				vec3 prefilteredColor = vec3(0.0);
				float totalWeight = 0.0;

				// For very low roughness, just sample the environment directly
				if (roughness < 0.001) {
					gl_FragColor = vec4(bilinearCubeUV(envMap, N, mipInt), 1.0);
					return;
				}

				// Tangent space basis for VNDF sampling
				vec3 up = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
				vec3 tangent = normalize(cross(up, N));
				vec3 bitangent = cross(N, tangent);

				for(uint i = 0u; i < uint(GGX_SAMPLES); i++) {
					vec2 Xi = hammersley(i, uint(GGX_SAMPLES));

					// For PMREM, V = N, so in tangent space V is always (0, 0, 1)
					vec3 H_tangent = importanceSampleGGX_VNDF(Xi, vec3(0.0, 0.0, 1.0), roughness);

					// Transform H back to world space
					vec3 H = normalize(tangent * H_tangent.x + bitangent * H_tangent.y + N * H_tangent.z);
					vec3 L = normalize(2.0 * dot(V, H) * H - V);

					float NdotL = max(dot(N, L), 0.0);

					if(NdotL > 0.0) {
						// Sample environment at fixed mip level
						// VNDF importance sampling handles the distribution filtering
						vec3 sampleColor = bilinearCubeUV(envMap, L, mipInt);

						// Weight by NdotL for the split-sum approximation
						// VNDF PDF naturally accounts for the visible microfacet distribution
						prefilteredColor += sampleColor * NdotL;
						totalWeight += NdotL;
					}
				}

				if (totalWeight > 0.0) {
					prefilteredColor = prefilteredColor / totalWeight;
				}

				gl_FragColor = vec4(prefilteredColor, 1.0);
			}
		`,blending:cn,depthTest:!1,depthWrite:!1})}function Wp(e,t,n){return new Yt({name:"SphericalGaussianBlur",defines:{SAMPLES:zp,CUBEUV_TEXEL_WIDTH:1/t,CUBEUV_TEXEL_HEIGHT:1/n,CUBEUV_MAX_MIP:`${e}.0`},uniforms:{envMap:{value:null},sigma:{value:0},mipInt:{value:0}},vertexShader:_r(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float sigma;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359
			#define GOLDEN_ANGLE 2.39996322973

			void main() {

				if ( sigma == 0.0 ) {

					gl_FragColor = vec4( bilinearCubeUV( envMap, vOutputDirection, mipInt ), 1.0 );
					return;

				}

				vec3 outputDirection = normalize( vOutputDirection );

				vec3 up = abs( outputDirection.z ) < 0.999 ? vec3( 0.0, 0.0, 1.0 ) : vec3( 1.0, 0.0, 0.0 );
				vec3 tangent = normalize( cross( up, outputDirection ) );
				vec3 bitangent = cross( outputDirection, tangent );

				// Truncate the kernel at three standard deviations or at the antipode.
				float thetaMax = min( 3.0 * sigma, PI );
				float truncation = 1.0 - exp( - 0.5 * thetaMax * thetaMax / ( sigma * sigma ) );

				vec3 accumColor = vec3( 0.0 );
				float accumWeight = 0.0;

				for ( int i = 0; i < SAMPLES; i ++ ) {

					// Stratified inverse-CDF sampling of the Gaussian, placed on a golden-angle spiral.
					float stratum = ( float( i ) + 0.5 ) / float( SAMPLES );
					float theta = sigma * sqrt( - 2.0 * log( 1.0 - stratum * truncation ) );
					float phi = float( i ) * GOLDEN_ANGLE;

					vec3 offset = cos( phi ) * tangent + sin( phi ) * bitangent;
					vec3 sampleDirection = cos( theta ) * outputDirection + sin( theta ) * offset;

					// Correct the planar sample density to solid angle.
					float weight = sin( theta ) / theta;

					accumColor += weight * bilinearCubeUV( envMap, sampleDirection, mipInt );
					accumWeight += weight;

				}

				gl_FragColor = vec4( accumColor / accumWeight, 1.0 );

			}
		`,blending:cn,depthTest:!1,depthWrite:!1})}function ih(){return new Yt({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:_r(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:cn,depthTest:!1,depthWrite:!1})}function sh(){return new Yt({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:_r(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:cn,depthTest:!1,depthWrite:!1})}function _r(){return`

		precision mediump float;
		precision mediump int;

		attribute vec3 outputDirection;

		varying vec3 vOutputDirection;

		void main() {

			vOutputDirection = outputDirection;
			gl_Position = vec4( position, 1.0 );

		}
	`}class Bo extends Vt{constructor(e=1,t={}){super(e,e,t);this.isWebGLCubeRenderTarget=!0;let n={width:e,height:e,depth:1},i=[n,n,n,n,n,n];this.texture=new or(i),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;let n={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},i=new Di(5,5,5),s=new Yt({name:"CubemapFromEquirect",uniforms:ni(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:Bt,blending:cn});s.uniforms.tEquirect.value=t;let r=new Dt(i,s),a=t.minFilter;if(t.minFilter===qn)t.minFilter=zt;return new bo(1,10,this).update(e,r),t.minFilter=a,r.geometry.dispose(),r.material.dispose(),this}clear(e,t=!0,n=!0,i=!0){let s=e.getRenderTarget();for(let r=0;r<6;r++)e.setRenderTarget(this,r),e.clear(t,n,i);e.setRenderTarget(s)}}function Xp(e){let t=new WeakMap,n=new WeakMap,i=null;function s(h,m=!1){if(h===null||h===void 0)return null;if(m)return a(h);return r(h)}function r(h){if(h&&h.isTexture){let m=h.mapping;if(m===Hs||m===Vs)if(t.has(h)){let v=t.get(h).texture;return o(v,h.mapping)}else{let v=h.image;if(v&&v.height>0){let b=new Bo(v.height);return b.fromEquirectangularTexture(e,h),t.set(h,b),h.addEventListener("dispose",l),o(b.texture,h.mapping)}else return null}}return h}function a(h){if(h&&h.isTexture){let m=h.mapping,v=m===Hs||m===Vs,b=m===Pi||m===Xn;if(v||b){let p=n.get(h),f=p!==void 0?p.texture.pmremVersion:0;if(h.isRenderTargetTexture&&h.pmremVersion!==f){if(i===null)i=new Uo(e);return p=v?i.fromEquirectangular(h,p):i.fromCubemap(h,p),p.texture.pmremVersion=h.pmremVersion,n.set(h,p),p.texture}else if(p!==void 0)return p.texture;else{let T=h.image;if(v&&T&&T.height>0||b&&T&&c(T)){if(i===null)i=new Uo(e);return p=v?i.fromEquirectangular(h):i.fromCubemap(h),p.texture.pmremVersion=h.pmremVersion,n.set(h,p),h.addEventListener("dispose",u),p.texture}else return null}}}return h}function o(h,m){if(m===Hs)h.mapping=Pi;else if(m===Vs)h.mapping=Xn;return h}function c(h){let m=0,v=6;for(let b=0;b<v;b++)if(h[b]!==void 0)m++;return m===v}function l(h){let m=h.target;m.removeEventListener("dispose",l);let v=t.get(m);if(v!==void 0)t.delete(m),v.dispose()}function u(h){let m=h.target;m.removeEventListener("dispose",u);let v=n.get(m);if(v!==void 0)n.delete(m),v.dispose()}function d(){if(t=new WeakMap,n=new WeakMap,i!==null)i.dispose(),i=null}return{get:s,dispose:d}}function qp(e){let t={};function n(i){if(t[i]!==void 0)return t[i];let s=e.getExtension(i);return t[i]=s,s}return{has:function(i){return n(i)!==null},init:function(){n("EXT_color_buffer_float"),n("WEBGL_clip_cull_distance"),n("OES_texture_float_linear"),n("EXT_color_buffer_half_float"),n("WEBGL_multisampled_render_to_texture"),n("WEBGL_render_shared_exponent")},get:function(i){let s=n(i);if(s===null)Wn("WebGLRenderer: "+i+" extension not supported.");return s}}}function $p(e,t,n,i){let s={},r=new WeakMap;function a(d){let h=d.target;if(h.index!==null)t.remove(h.index);for(let v in h.attributes)t.remove(h.attributes[v]);h.removeEventListener("dispose",a),delete s[h.id];let m=r.get(h);if(m)t.remove(m),r.delete(h);if(i.releaseStatesOfGeometry(h),h.isInstancedBufferGeometry===!0)delete h._maxInstanceCount;n.memory.geometries--}function o(d,h){if(s[h.id]===!0)return h;return h.addEventListener("dispose",a),s[h.id]=!0,n.memory.geometries++,h}function c(d){let h=d.attributes;for(let m in h)t.update(h[m],e.ARRAY_BUFFER)}function l(d){let h=[],m=d.index,v=d.attributes.position,b=0;if(v===void 0)return;if(m!==null){let T=m.array;b=m.version;for(let I=0,S=T.length;I<S;I+=3){let w=T[I+0],E=T[I+1],A=T[I+2];h.push(w,E,E,A,A,w)}}else{let T=v.array;b=v.version;for(let I=0,S=T.length/3-1;I<S;I+=3){let w=I+0,E=I+1,A=I+2;h.push(w,E,E,A,A,w)}}let p=new(v.count>=65535?sr:ir)(h,1);p.version=b;let f=r.get(d);if(f)t.remove(f);r.set(d,p)}function u(d){let h=r.get(d);if(h){let m=d.index;if(m!==null){if(h.version<m.version)l(d)}}else l(d);return r.get(d)}return{get:o,update:c,getWireframeAttribute:u}}function Yp(e,t,n){let i;function s(d){i=d}let r,a;function o(d){r=d.type,a=d.bytesPerElement}function c(d,h){e.drawElements(i,h,r,d*a),n.update(h,i,1)}function l(d,h,m){if(m===0)return;e.drawElementsInstanced(i,h,r,d*a,m),n.update(h,i,m)}function u(d,h,m){if(m===0)return;t.get("WEBGL_multi_draw").multiDrawElementsWEBGL(i,h,0,r,d,0,m);let b=0;for(let p=0;p<m;p++)b+=h[p];n.update(b,i,1)}this.setMode=s,this.setIndex=o,this.render=c,this.renderInstances=l,this.renderMultiDraw=u}function Zp(e){let t={geometries:0,textures:0},n={frame:0,calls:0,triangles:0,points:0,lines:0};function i(r,a,o){switch(n.calls++,a){case e.TRIANGLES:n.triangles+=o*(r/3);break;case e.LINES:n.lines+=o*(r/2);break;case e.LINE_STRIP:n.lines+=o*(r-1);break;case e.LINE_LOOP:n.lines+=o*r;break;case e.POINTS:n.points+=o*r;break;default:Pe("WebGLInfo: Unknown draw mode:",a);break}}function s(){n.calls=0,n.triangles=0,n.points=0,n.lines=0}return{memory:t,render:n,programs:null,autoReset:!0,reset:s,update:i}}function Jp(e,t,n){let i=new WeakMap,s=new ut;function r(a,o,c){let l=a.morphTargetInfluences,u=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,d=u!==void 0?u.length:0,h=i.get(o);if(h===void 0||h.count!==d){let M=function(){A.dispose(),i.delete(o),o.removeEventListener("dispose",M)};if(h!==void 0)h.texture.dispose();let m=o.morphAttributes.position!==void 0,v=o.morphAttributes.normal!==void 0,b=o.morphAttributes.color!==void 0,p=o.morphAttributes.position||[],f=o.morphAttributes.normal||[],T=o.morphAttributes.color||[],I=0;if(m===!0)I=1;if(v===!0)I=2;if(b===!0)I=3;let S=o.attributes.position.count*I,w=1;if(S>t.maxTextureSize)w=Math.ceil(S/t.maxTextureSize),S=t.maxTextureSize;let E=new Float32Array(S*w*4*d),A=new er(E,S,w,d);A.type=Sn,A.needsUpdate=!0;let x=I*4;for(let H=0;H<d;H++){let D=p[H],U=f[H],J=T[H],C=S*w*4*H;for(let V=0;V<D.count;V++){let K=V*x;if(m===!0)s.fromBufferAttribute(D,V),E[C+K+0]=s.x,E[C+K+1]=s.y,E[C+K+2]=s.z,E[C+K+3]=0;if(v===!0)s.fromBufferAttribute(U,V),E[C+K+4]=s.x,E[C+K+5]=s.y,E[C+K+6]=s.z,E[C+K+7]=0;if(b===!0)s.fromBufferAttribute(J,V),E[C+K+8]=s.x,E[C+K+9]=s.y,E[C+K+10]=s.z,E[C+K+11]=J.itemSize===4?s.w:1}}h={count:d,texture:A,size:new Xe(S,w)},i.set(o,h),o.addEventListener("dispose",M)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)c.getUniforms().setValue(e,"morphTexture",a.morphTexture,n);else{let m=0;for(let b=0;b<l.length;b++)m+=l[b];let v=o.morphTargetsRelative?1:1-m;c.getUniforms().setValue(e,"morphTargetBaseInfluence",v),c.getUniforms().setValue(e,"morphTargetInfluences",l)}c.getUniforms().setValue(e,"morphTargetsTexture",h.texture,n),c.getUniforms().setValue(e,"morphTargetsTextureSize",h.size)}return{update:r}}function Kp(e,t,n,i,s){let r=new WeakMap;function a(l){let u=s.render.frame,d=l.geometry,h=t.get(l,d);if(r.get(h)!==u)t.update(h),r.set(h,u);if(l.isInstancedMesh){if(l.hasEventListener("dispose",c)===!1)l.addEventListener("dispose",c);if(r.get(l)!==u){if(n.update(l.instanceMatrix,e.ARRAY_BUFFER),l.instanceColor!==null)n.update(l.instanceColor,e.ARRAY_BUFFER);r.set(l,u)}}if(l.isSkinnedMesh){let m=l.skeleton;if(r.get(m)!==u)m.update(),r.set(m,u)}return h}function o(){r=new WeakMap}function c(l){let u=l.target;if(u.removeEventListener("dispose",c),i.releaseStatesOfObject(u),n.remove(u.instanceMatrix),u.instanceColor!==null)n.remove(u.instanceColor)}return{update:a,dispose:o}}var jp={[la]:"LINEAR_TONE_MAPPING",[ca]:"REINHARD_TONE_MAPPING",[ha]:"CINEON_TONE_MAPPING",[ua]:"ACES_FILMIC_TONE_MAPPING",[fa]:"AGX_TONE_MAPPING",[pa]:"NEUTRAL_TONE_MAPPING",[da]:"CUSTOM_TONE_MAPPING"};function Qp(e,t,n,i,s,r){let a=new Vt(t,n,{type:e,depthBuffer:s,stencilBuffer:r,samples:i?4:0,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,resolveDepthBuffer:!1,resolveStencilBuffer:!1}),o=null,c=null,l=new bt;l.setAttribute("position",new vt([-1,3,0,-1,-1,0,3,-1,0],3)),l.setAttribute("uv",new vt([0,2,0,0,2,0],2));let u=new co({uniforms:{tDiffuse:{value:null}},vertexShader:`
			precision highp float;

			uniform mat4 modelViewMatrix;
			uniform mat4 projectionMatrix;

			attribute vec3 position;
			attribute vec2 uv;

			varying vec2 vUv;

			void main() {
				vUv = uv;
				gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
			}`,fragmentShader:`
			precision highp float;

			uniform sampler2D tDiffuse;

			varying vec2 vUv;

			#include <tonemapping_pars_fragment>
			#include <colorspace_pars_fragment>

			void main() {
				gl_FragColor = texture2D( tDiffuse, vUv );

				#ifdef LINEAR_TONE_MAPPING
					gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );
				#elif defined( REINHARD_TONE_MAPPING )
					gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );
				#elif defined( CINEON_TONE_MAPPING )
					gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );
				#elif defined( ACES_FILMIC_TONE_MAPPING )
					gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );
				#elif defined( AGX_TONE_MAPPING )
					gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );
				#elif defined( NEUTRAL_TONE_MAPPING )
					gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );
				#elif defined( CUSTOM_TONE_MAPPING )
					gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );
				#endif

				#ifdef SRGB_TRANSFER
					gl_FragColor = sRGBTransferOETF( gl_FragColor );
				#endif
			}`,depthTest:!1,depthWrite:!1}),d=new Dt(l,u),h=new fr(-1,1,1,-1,0,1),m=null,v=null,b=!1,p,f=null,T=[],I=!1;this.setSize=function(S,w){if(a.setSize(S,w),o!==null)o.setSize(S,w);if(c!==null)c.setSize(S,w);for(let E=0;E<T.length;E++){let A=T[E];if(A.setSize)A.setSize(S,w)}},this.setEffects=function(S){T=S,I=T.length>0&&T[0].isRenderPass===!0;let{width:w,height:E}=a;if(T.length>0&&o===null)o=new Vt(w,E,{type:hn,depthBuffer:!1,stencilBuffer:!1}),c=new Vt(w,E,{type:hn,depthBuffer:!1,stencilBuffer:!1});for(let A=0;A<T.length;A++){let x=T[A];if(x.setSize)x.setSize(w,E)}},this.begin=function(S,w){if(b)return!1;if(S.toneMapping===Qt&&T.length===0)return!1;if(f=w,w!==null){let{width:E,height:A}=w;if(a.width!==E||a.height!==A)this.setSize(E,A)}if(I===!1)S.setRenderTarget(a);return p=S.toneMapping,S.toneMapping=Qt,!0},this.hasRenderPass=function(){return I},this.end=function(S,w){S.toneMapping=p,b=!0;let E=a,A=o;for(let x=0;x<T.length;x++){let M=T[x];if(M.enabled===!1)continue;if(M.render(S,A,E,w),M.needsSwap!==!1)E=A,A=A===o?c:o}if(m!==S.outputColorSpace||v!==S.toneMapping){if(m=S.outputColorSpace,v=S.toneMapping,u.defines={},ke.getTransfer(m)===nt)u.defines.SRGB_TRANSFER="";let x=jp[v];if(x)u.defines[x]="";u.needsUpdate=!0}u.uniforms.tDiffuse.value=E.texture,S.setRenderTarget(f),S.render(d,h),f=null,b=!1},this.isCompositing=function(){return b},this.dispose=function(){if(a.dispose(),o!==null)o.dispose();if(c!==null)c.dispose();l.dispose(),u.dispose()}}var wh=new Rt,Fo=new ti(1,1),Eh=new er,Th=new ro,Ah=new or,rh=[],ah=[],oh=new Float32Array(16),lh=new Float32Array(9),ch=new Float32Array(4);function Bi(e,t,n){let i=e[0];if(i<=0||i>0)return e;let s=t*n,r=rh[s];if(r===void 0)r=new Float32Array(s),rh[s]=r;if(t!==0){i.toArray(r,0);for(let a=1,o=0;a!==t;++a)o+=n,e[a].toArray(r,o)}return r}function yt(e,t){if(e.length!==t.length)return!1;for(let n=0,i=e.length;n<i;n++)if(e[n]!==t[n])return!1;return!0}function St(e,t){for(let n=0,i=t.length;n<i;n++)e[n]=t[n]}function xr(e,t){let n=ah[t];if(n===void 0)n=new Int32Array(t),ah[t]=n;for(let i=0;i!==t;++i)n[i]=e.allocateTextureUnit();return n}function em(e,t){let n=this.cache;if(n[0]===t)return;e.uniform1f(this.addr,t),n[0]=t}function tm(e,t){let n=this.cache;if(t.x!==void 0){if(n[0]!==t.x||n[1]!==t.y)e.uniform2f(this.addr,t.x,t.y),n[0]=t.x,n[1]=t.y}else{if(yt(n,t))return;e.uniform2fv(this.addr,t),St(n,t)}}function nm(e,t){let n=this.cache;if(t.x!==void 0){if(n[0]!==t.x||n[1]!==t.y||n[2]!==t.z)e.uniform3f(this.addr,t.x,t.y,t.z),n[0]=t.x,n[1]=t.y,n[2]=t.z}else if(t.r!==void 0){if(n[0]!==t.r||n[1]!==t.g||n[2]!==t.b)e.uniform3f(this.addr,t.r,t.g,t.b),n[0]=t.r,n[1]=t.g,n[2]=t.b}else{if(yt(n,t))return;e.uniform3fv(this.addr,t),St(n,t)}}function im(e,t){let n=this.cache;if(t.x!==void 0){if(n[0]!==t.x||n[1]!==t.y||n[2]!==t.z||n[3]!==t.w)e.uniform4f(this.addr,t.x,t.y,t.z,t.w),n[0]=t.x,n[1]=t.y,n[2]=t.z,n[3]=t.w}else{if(yt(n,t))return;e.uniform4fv(this.addr,t),St(n,t)}}function sm(e,t){let n=this.cache,i=t.elements;if(i===void 0){if(yt(n,t))return;e.uniformMatrix2fv(this.addr,!1,t),St(n,t)}else{if(yt(n,i))return;ch.set(i),e.uniformMatrix2fv(this.addr,!1,ch),St(n,i)}}function rm(e,t){let n=this.cache,i=t.elements;if(i===void 0){if(yt(n,t))return;e.uniformMatrix3fv(this.addr,!1,t),St(n,t)}else{if(yt(n,i))return;lh.set(i),e.uniformMatrix3fv(this.addr,!1,lh),St(n,i)}}function am(e,t){let n=this.cache,i=t.elements;if(i===void 0){if(yt(n,t))return;e.uniformMatrix4fv(this.addr,!1,t),St(n,t)}else{if(yt(n,i))return;oh.set(i),e.uniformMatrix4fv(this.addr,!1,oh),St(n,i)}}function om(e,t){let n=this.cache;if(n[0]===t)return;e.uniform1i(this.addr,t),n[0]=t}function lm(e,t){let n=this.cache;if(t.x!==void 0){if(n[0]!==t.x||n[1]!==t.y)e.uniform2i(this.addr,t.x,t.y),n[0]=t.x,n[1]=t.y}else{if(yt(n,t))return;e.uniform2iv(this.addr,t),St(n,t)}}function cm(e,t){let n=this.cache;if(t.x!==void 0){if(n[0]!==t.x||n[1]!==t.y||n[2]!==t.z)e.uniform3i(this.addr,t.x,t.y,t.z),n[0]=t.x,n[1]=t.y,n[2]=t.z}else{if(yt(n,t))return;e.uniform3iv(this.addr,t),St(n,t)}}function hm(e,t){let n=this.cache;if(t.x!==void 0){if(n[0]!==t.x||n[1]!==t.y||n[2]!==t.z||n[3]!==t.w)e.uniform4i(this.addr,t.x,t.y,t.z,t.w),n[0]=t.x,n[1]=t.y,n[2]=t.z,n[3]=t.w}else{if(yt(n,t))return;e.uniform4iv(this.addr,t),St(n,t)}}function um(e,t){let n=this.cache;if(n[0]===t)return;e.uniform1ui(this.addr,t),n[0]=t}function dm(e,t){let n=this.cache;if(t.x!==void 0){if(n[0]!==t.x||n[1]!==t.y)e.uniform2ui(this.addr,t.x,t.y),n[0]=t.x,n[1]=t.y}else{if(yt(n,t))return;e.uniform2uiv(this.addr,t),St(n,t)}}function fm(e,t){let n=this.cache;if(t.x!==void 0){if(n[0]!==t.x||n[1]!==t.y||n[2]!==t.z)e.uniform3ui(this.addr,t.x,t.y,t.z),n[0]=t.x,n[1]=t.y,n[2]=t.z}else{if(yt(n,t))return;e.uniform3uiv(this.addr,t),St(n,t)}}function pm(e,t){let n=this.cache;if(t.x!==void 0){if(n[0]!==t.x||n[1]!==t.y||n[2]!==t.z||n[3]!==t.w)e.uniform4ui(this.addr,t.x,t.y,t.z,t.w),n[0]=t.x,n[1]=t.y,n[2]=t.z,n[3]=t.w}else{if(yt(n,t))return;e.uniform4uiv(this.addr,t),St(n,t)}}function mm(e,t,n){let i=this.cache,s=n.allocateTextureUnit();if(i[0]!==s)e.uniform1i(this.addr,s),i[0]=s;let r;if(this.type===e.SAMPLER_2D_SHADOW)Fo.compareFunction=n.isReversedDepthBuffer()?Qs:js,r=Fo;else r=wh;n.setTexture2D(t||r,s)}function gm(e,t,n){let i=this.cache,s=n.allocateTextureUnit();if(i[0]!==s)e.uniform1i(this.addr,s),i[0]=s;n.setTexture3D(t||Th,s)}function _m(e,t,n){let i=this.cache,s=n.allocateTextureUnit();if(i[0]!==s)e.uniform1i(this.addr,s),i[0]=s;n.setTextureCube(t||Ah,s)}function xm(e,t,n){let i=this.cache,s=n.allocateTextureUnit();if(i[0]!==s)e.uniform1i(this.addr,s),i[0]=s;n.setTexture2DArray(t||Eh,s)}function vm(e){switch(e){case 5126:return em;case 35664:return tm;case 35665:return nm;case 35666:return im;case 35674:return sm;case 35675:return rm;case 35676:return am;case 5124:case 35670:return om;case 35667:case 35671:return lm;case 35668:case 35672:return cm;case 35669:case 35673:return hm;case 5125:return um;case 36294:return dm;case 36295:return fm;case 36296:return pm;case 35678:case 36198:case 36298:case 36306:case 35682:return mm;case 35679:case 36299:case 36307:return gm;case 35680:case 36300:case 36308:case 36293:return _m;case 36289:case 36303:case 36311:case 36292:return xm}}function ym(e,t){e.uniform1fv(this.addr,t)}function Sm(e,t){let n=Bi(t,this.size,2);e.uniform2fv(this.addr,n)}function Mm(e,t){let n=Bi(t,this.size,3);e.uniform3fv(this.addr,n)}function bm(e,t){let n=Bi(t,this.size,4);e.uniform4fv(this.addr,n)}function wm(e,t){let n=Bi(t,this.size,4);e.uniformMatrix2fv(this.addr,!1,n)}function Em(e,t){let n=Bi(t,this.size,9);e.uniformMatrix3fv(this.addr,!1,n)}function Tm(e,t){let n=Bi(t,this.size,16);e.uniformMatrix4fv(this.addr,!1,n)}function Am(e,t){e.uniform1iv(this.addr,t)}function Cm(e,t){e.uniform2iv(this.addr,t)}function Rm(e,t){e.uniform3iv(this.addr,t)}function Im(e,t){e.uniform4iv(this.addr,t)}function Pm(e,t){e.uniform1uiv(this.addr,t)}function Lm(e,t){e.uniform2uiv(this.addr,t)}function Nm(e,t){e.uniform3uiv(this.addr,t)}function Dm(e,t){e.uniform4uiv(this.addr,t)}function Um(e,t,n){let i=this.cache,s=t.length,r=xr(n,s);if(!yt(i,r))e.uniform1iv(this.addr,r),St(i,r);let a;if(this.type===e.SAMPLER_2D_SHADOW)a=Fo;else a=wh;for(let o=0;o!==s;++o)n.setTexture2D(t[o]||a,r[o])}function Fm(e,t,n){let i=this.cache,s=t.length,r=xr(n,s);if(!yt(i,r))e.uniform1iv(this.addr,r),St(i,r);for(let a=0;a!==s;++a)n.setTexture3D(t[a]||Th,r[a])}function Om(e,t,n){let i=this.cache,s=t.length,r=xr(n,s);if(!yt(i,r))e.uniform1iv(this.addr,r),St(i,r);for(let a=0;a!==s;++a)n.setTextureCube(t[a]||Ah,r[a])}function Bm(e,t,n){let i=this.cache,s=t.length,r=xr(n,s);if(!yt(i,r))e.uniform1iv(this.addr,r),St(i,r);for(let a=0;a!==s;++a)n.setTexture2DArray(t[a]||Eh,r[a])}function zm(e){switch(e){case 5126:return ym;case 35664:return Sm;case 35665:return Mm;case 35666:return bm;case 35674:return wm;case 35675:return Em;case 35676:return Tm;case 5124:case 35670:return Am;case 35667:case 35671:return Cm;case 35668:case 35672:return Rm;case 35669:case 35673:return Im;case 5125:return Pm;case 36294:return Lm;case 36295:return Nm;case 36296:return Dm;case 35678:case 36198:case 36298:case 36306:case 35682:return Um;case 35679:case 36299:case 36307:return Fm;case 35680:case 36300:case 36308:case 36293:return Om;case 36289:case 36303:case 36311:case 36292:return Bm}}class Ch{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.setValue=vm(t.type)}}class Rh{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=zm(t.type)}}class Ih{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,n){let i=this.seq;for(let s=0,r=i.length;s!==r;++s){let a=i[s];a.setValue(e,t[a.id],n)}}}var No=/(\w+)(\])?(\[|\.)?/g;function hh(e,t){e.seq.push(t),e.map[t.id]=t}function km(e,t,n){let i=e.name,s=i.length;No.lastIndex=0;while(!0){let r=No.exec(i),a=No.lastIndex,o=r[1],c=r[2]==="]",l=r[3];if(c)o=o|0;if(l===void 0||l==="["&&a+2===s){hh(n,l===void 0?new Ch(o,e,t):new Rh(o,e,t));break}else{let d=n.map[o];if(d===void 0)d=new Ih(o),hh(n,d);n=d}}}class cs{constructor(e,t){this.seq=[],this.map={};let n=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let r=0;r<n;++r){let a=e.getActiveUniform(t,r),o=e.getUniformLocation(t,a.name);km(a,o,this)}let i=[],s=[];for(let r of this.seq)if(r.type===e.SAMPLER_2D_SHADOW||r.type===e.SAMPLER_CUBE_SHADOW||r.type===e.SAMPLER_2D_ARRAY_SHADOW)i.push(r);else s.push(r);if(i.length>0)this.seq=i.concat(s)}setValue(e,t,n,i){let s=this.map[t];if(s!==void 0)s.setValue(e,n,i)}setOptional(e,t,n){let i=t[n];if(i!==void 0)this.setValue(e,n,i)}static upload(e,t,n,i){for(let s=0,r=t.length;s!==r;++s){let a=t[s],o=n[a.id];if(o.needsUpdate!==!1)a.setValue(e,o.value,i)}}static seqWithValue(e,t){let n=[];for(let i=0,s=e.length;i!==s;++i){let r=e[i];if(r.id in t)n.push(r)}return n}}function uh(e,t,n){let i=e.createShader(t);return e.shaderSource(i,n),e.compileShader(i),i}var Gm=37297,Hm=0;function Vm(e,t){let n=e.split(`
`),i=[],s=Math.max(t-6,0),r=Math.min(t+6,n.length);for(let a=s;a<r;a++){let o=a+1;i.push(`${o===t?">":" "} ${o}: ${n[a]}`)}return i.join(`
`)}var dh=new Le;function Wm(e){ke._getMatrix(dh,ke.workingColorSpace,e);let t=`mat3( ${dh.elements.map((n)=>n.toFixed(4))} )`;switch(ke.getTransfer(e)){case Qa:return[t,"LinearTransferOETF"];case nt:return[t,"sRGBTransferOETF"];default:return Ce("WebGLProgram: Unsupported color space: ",e),[t,"LinearTransferOETF"]}}function fh(e,t,n){let i=e.getShaderParameter(t,e.COMPILE_STATUS),r=(e.getShaderInfoLog(t)||"").trim();if(i&&r==="")return"";let a=/ERROR: 0:(\d+)/.exec(r);if(a){let o=parseInt(a[1]);return n.toUpperCase()+`

`+r+`

`+Vm(e.getShaderSource(t),o)}else return r}function Xm(e,t){let n=Wm(t);return[`vec4 ${e}( vec4 value ) {`,`	return ${n[1]}( vec4( value.rgb * ${n[0]}, value.a ) );`,"}"].join(`
`)}var qm={[la]:"Linear",[ca]:"Reinhard",[ha]:"Cineon",[ua]:"ACESFilmic",[fa]:"AgX",[pa]:"Neutral",[da]:"Custom"};function $m(e,t){let n=qm[t];if(n===void 0)return Ce("WebGLProgram: Unsupported toneMapping:",t),"vec3 "+e+"( vec3 color ) { return LinearToneMapping( color ); }";return"vec3 "+e+"( vec3 color ) { return "+n+"ToneMapping( color ); }"}var gr=new F;function Ym(){ke.getLuminanceCoefficients(gr);let e=gr.x.toFixed(4),t=gr.y.toFixed(4),n=gr.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${e}, ${t}, ${n} );`,"\treturn dot( weights, rgb );","}"].join(`
`)}function Zm(e){return[e.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",e.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(ls).join(`
`)}function Jm(e){let t=[];for(let n in e){let i=e[n];if(i===!1)continue;t.push("#define "+n+" "+i)}return t.join(`
`)}function Km(e,t){let n={},i=e.getProgramParameter(t,e.ACTIVE_ATTRIBUTES);for(let s=0;s<i;s++){let r=e.getActiveAttrib(t,s),a=r.name,o=1;if(r.type===e.FLOAT_MAT2)o=2;if(r.type===e.FLOAT_MAT3)o=3;if(r.type===e.FLOAT_MAT4)o=4;n[a]={type:r.type,location:e.getAttribLocation(t,a),locationSize:o}}return n}function ls(e){return e!==""}function ph(e,t){let n=t.numSpotLightShadows+t.numSpotLightMaps-t.numSpotLightShadowsWithMaps;return e.replace(/NUM_SUN_LIGHTS/g,t.numSunLights).replace(/NUM_DIR_LIGHTS/g,t.numDirLights).replace(/NUM_SPOT_LIGHTS/g,t.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,t.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,n).replace(/NUM_RECT_AREA_LIGHTS/g,t.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,t.numPointLights).replace(/NUM_HEMI_LIGHTS/g,t.numHemiLights).replace(/NUM_SUN_LIGHT_SHADOWS/g,t.numSunLightShadows).replace(/NUM_DIR_LIGHT_SHADOWS/g,t.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,t.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,t.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,t.numPointLightShadows)}function mh(e,t){return e.replace(/NUM_CLIPPING_PLANES/g,t.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,t.numClippingPlanes-t.numClipIntersection)}var jm=/^[ \t]*#include +<([\w\d./]+)>/gm;function Oo(e){return e.replace(jm,eg)}var Qm=new Map;function eg(e,t){let n=Fe[t];if(n===void 0){let i=Qm.get(t);if(i!==void 0)n=Fe[i],Ce('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',t,i);else throw Error("THREE.WebGLProgram: Can not resolve #include <"+t+">")}return Oo(n)}var tg=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function gh(e){return e.replace(tg,ng)}function ng(e,t,n,i){let s="";for(let r=parseInt(t);r<parseInt(n);r++)s+=i.replace(/\[\s*i\s*\]/g,"[ "+r+" ]").replace(/UNROLLED_LOOP_INDEX/g,r);return s}function _h(e){let t=`precision ${e.precision} float;
	precision ${e.precision} int;
	precision ${e.precision} sampler2D;
	precision ${e.precision} samplerCube;
	precision ${e.precision} sampler3D;
	precision ${e.precision} sampler2DArray;
	precision ${e.precision} sampler2DShadow;
	precision ${e.precision} samplerCubeShadow;
	precision ${e.precision} sampler2DArrayShadow;
	precision ${e.precision} isampler2D;
	precision ${e.precision} isampler3D;
	precision ${e.precision} isamplerCube;
	precision ${e.precision} isampler2DArray;
	precision ${e.precision} usampler2D;
	precision ${e.precision} usampler3D;
	precision ${e.precision} usamplerCube;
	precision ${e.precision} usampler2DArray;
	`;if(e.precision==="highp")t+=`
#define HIGH_PRECISION`;else if(e.precision==="mediump")t+=`
#define MEDIUM_PRECISION`;else if(e.precision==="lowp")t+=`
#define LOW_PRECISION`;return t}var ig={[Ki]:"SHADOWMAP_TYPE_PCF",[Ci]:"SHADOWMAP_TYPE_VSM"};function sg(e){return ig[e.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}var rg={[Pi]:"ENVMAP_TYPE_CUBE",[Xn]:"ENVMAP_TYPE_CUBE",[Qi]:"ENVMAP_TYPE_CUBE_UV"};function ag(e){if(e.envMap===!1)return"ENVMAP_TYPE_CUBE";return rg[e.envMapMode]||"ENVMAP_TYPE_CUBE"}var og={[Xn]:"ENVMAP_MODE_REFRACTION"};function lg(e){if(e.envMap===!1)return"ENVMAP_MODE_REFLECTION";return og[e.envMapMode]||"ENVMAP_MODE_REFLECTION"}var cg={[Ec]:"ENVMAP_BLENDING_MULTIPLY",[Tc]:"ENVMAP_BLENDING_MIX",[Ac]:"ENVMAP_BLENDING_ADD"};function hg(e){if(e.envMap===!1)return"ENVMAP_BLENDING_NONE";return cg[e.combine]||"ENVMAP_BLENDING_NONE"}function ug(e){let t=e.envMapCubeUVHeight;if(t===null)return null;let n=Math.log2(t)-2,i=1/t;return{texelWidth:1/(3*Math.max(Math.pow(2,n),112)),texelHeight:i,maxMip:n}}function dg(e,t,n,i){let s=e.getContext(),{defines:r,vertexShader:a,fragmentShader:o}=n,c=sg(n),l=ag(n),u=lg(n),d=hg(n),h=ug(n),m=Zm(n),v=Jm(r),b=s.createProgram(),p,f,T=n.glslVersion?"#version "+n.glslVersion+`
`:"";if(n.isRawShaderMaterial){if(p=["#define SHADER_TYPE "+n.shaderType,"#define SHADER_NAME "+n.shaderName,v].filter(ls).join(`
`),p.length>0)p+=`
`;if(f=["#define SHADER_TYPE "+n.shaderType,"#define SHADER_NAME "+n.shaderName,v].filter(ls).join(`
`),f.length>0)f+=`
`}else p=[_h(n),"#define SHADER_TYPE "+n.shaderType,"#define SHADER_NAME "+n.shaderName,v,n.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",n.batching?"#define USE_BATCHING":"",n.batchingColor?"#define USE_BATCHING_COLOR":"",n.instancing?"#define USE_INSTANCING":"",n.instancingColor?"#define USE_INSTANCING_COLOR":"",n.instancingMorph?"#define USE_INSTANCING_MORPH":"",n.useFog&&n.fog?"#define USE_FOG":"",n.useFog&&n.fogExp2?"#define FOG_EXP2":"",n.map?"#define USE_MAP":"",n.envMap?"#define USE_ENVMAP":"",n.envMap?"#define "+u:"",n.lightMap?"#define USE_LIGHTMAP":"",n.aoMap?"#define USE_AOMAP":"",n.bumpMap?"#define USE_BUMPMAP":"",n.normalMap?"#define USE_NORMALMAP":"",n.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",n.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",n.displacementMap?"#define USE_DISPLACEMENTMAP":"",n.emissiveMap?"#define USE_EMISSIVEMAP":"",n.anisotropy?"#define USE_ANISOTROPY":"",n.anisotropyMap?"#define USE_ANISOTROPYMAP":"",n.clearcoatMap?"#define USE_CLEARCOATMAP":"",n.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",n.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",n.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",n.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",n.specularMap?"#define USE_SPECULARMAP":"",n.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",n.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",n.roughnessMap?"#define USE_ROUGHNESSMAP":"",n.metalnessMap?"#define USE_METALNESSMAP":"",n.alphaMap?"#define USE_ALPHAMAP":"",n.alphaHash?"#define USE_ALPHAHASH":"",n.transmission?"#define USE_TRANSMISSION":"",n.transmissionMap?"#define USE_TRANSMISSIONMAP":"",n.thicknessMap?"#define USE_THICKNESSMAP":"",n.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",n.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",n.mapUv?"#define MAP_UV "+n.mapUv:"",n.alphaMapUv?"#define ALPHAMAP_UV "+n.alphaMapUv:"",n.lightMapUv?"#define LIGHTMAP_UV "+n.lightMapUv:"",n.aoMapUv?"#define AOMAP_UV "+n.aoMapUv:"",n.emissiveMapUv?"#define EMISSIVEMAP_UV "+n.emissiveMapUv:"",n.bumpMapUv?"#define BUMPMAP_UV "+n.bumpMapUv:"",n.normalMapUv?"#define NORMALMAP_UV "+n.normalMapUv:"",n.displacementMapUv?"#define DISPLACEMENTMAP_UV "+n.displacementMapUv:"",n.metalnessMapUv?"#define METALNESSMAP_UV "+n.metalnessMapUv:"",n.roughnessMapUv?"#define ROUGHNESSMAP_UV "+n.roughnessMapUv:"",n.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+n.anisotropyMapUv:"",n.clearcoatMapUv?"#define CLEARCOATMAP_UV "+n.clearcoatMapUv:"",n.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+n.clearcoatNormalMapUv:"",n.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+n.clearcoatRoughnessMapUv:"",n.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+n.iridescenceMapUv:"",n.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+n.iridescenceThicknessMapUv:"",n.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+n.sheenColorMapUv:"",n.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+n.sheenRoughnessMapUv:"",n.specularMapUv?"#define SPECULARMAP_UV "+n.specularMapUv:"",n.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+n.specularColorMapUv:"",n.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+n.specularIntensityMapUv:"",n.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+n.transmissionMapUv:"",n.thicknessMapUv?"#define THICKNESSMAP_UV "+n.thicknessMapUv:"",n.vertexTangents&&n.flatShading===!1?"#define USE_TANGENT":"",n.vertexNormals?"#define HAS_NORMAL":"",n.vertexColors?"#define USE_COLOR":"",n.vertexAlphas?"#define USE_COLOR_ALPHA":"",n.vertexUv1s?"#define USE_UV1":"",n.vertexUv2s?"#define USE_UV2":"",n.vertexUv3s?"#define USE_UV3":"",n.pointsUvs?"#define USE_POINTS_UV":"",n.flatShading?"#define FLAT_SHADED":"",n.skinning?"#define USE_SKINNING":"",n.morphTargets?"#define USE_MORPHTARGETS":"",n.morphNormals&&n.flatShading===!1?"#define USE_MORPHNORMALS":"",n.morphColors?"#define USE_MORPHCOLORS":"",n.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+n.morphTextureStride:"",n.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+n.morphTargetsCount:"",n.doubleSided?"#define DOUBLE_SIDED":"",n.flipSided?"#define FLIP_SIDED":"",n.shadowMapEnabled?"#define USE_SHADOWMAP":"",n.shadowMapEnabled?"#define "+c:"",n.sizeAttenuation?"#define USE_SIZEATTENUATION":"",n.numLightProbes>0?"#define USE_LIGHT_PROBES":"",n.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",n.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","\tattribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","\tattribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","\tuniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","\tattribute vec2 uv1;","#endif","#ifdef USE_UV2","\tattribute vec2 uv2;","#endif","#ifdef USE_UV3","\tattribute vec2 uv3;","#endif","#ifdef USE_TANGENT","\tattribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","\tattribute vec4 color;","#elif defined( USE_COLOR )","\tattribute vec3 color;","#endif","#ifdef USE_SKINNING","\tattribute vec4 skinIndex;","\tattribute vec4 skinWeight;","#endif",`
`].filter(ls).join(`
`),f=[_h(n),"#define SHADER_TYPE "+n.shaderType,"#define SHADER_NAME "+n.shaderName,v,n.useFog&&n.fog?"#define USE_FOG":"",n.useFog&&n.fogExp2?"#define FOG_EXP2":"",n.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",n.map?"#define USE_MAP":"",n.matcap?"#define USE_MATCAP":"",n.envMap?"#define USE_ENVMAP":"",n.envMap?"#define "+l:"",n.envMap?"#define "+u:"",n.envMap?"#define "+d:"",h?"#define CUBEUV_TEXEL_WIDTH "+h.texelWidth:"",h?"#define CUBEUV_TEXEL_HEIGHT "+h.texelHeight:"",h?"#define CUBEUV_MAX_MIP "+h.maxMip+".0":"",n.lightMap?"#define USE_LIGHTMAP":"",n.aoMap?"#define USE_AOMAP":"",n.bumpMap?"#define USE_BUMPMAP":"",n.normalMap?"#define USE_NORMALMAP":"",n.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",n.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",n.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",n.emissiveMap?"#define USE_EMISSIVEMAP":"",n.anisotropy?"#define USE_ANISOTROPY":"",n.anisotropyMap?"#define USE_ANISOTROPYMAP":"",n.clearcoat?"#define USE_CLEARCOAT":"",n.clearcoatMap?"#define USE_CLEARCOATMAP":"",n.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",n.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",n.dispersion?"#define USE_DISPERSION":"",n.retroreflection?"#define USE_RETROREFLECTION":"",n.iridescence?"#define USE_IRIDESCENCE":"",n.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",n.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",n.specularMap?"#define USE_SPECULARMAP":"",n.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",n.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",n.roughnessMap?"#define USE_ROUGHNESSMAP":"",n.metalnessMap?"#define USE_METALNESSMAP":"",n.alphaMap?"#define USE_ALPHAMAP":"",n.alphaTest?"#define USE_ALPHATEST":"",n.alphaHash?"#define USE_ALPHAHASH":"",n.sheen?"#define USE_SHEEN":"",n.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",n.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",n.transmission?"#define USE_TRANSMISSION":"",n.transmissionMap?"#define USE_TRANSMISSIONMAP":"",n.thicknessMap?"#define USE_THICKNESSMAP":"",n.vertexTangents&&n.flatShading===!1?"#define USE_TANGENT":"",n.vertexColors||n.instancingColor?"#define USE_COLOR":"",n.vertexAlphas||n.batchingColor?"#define USE_COLOR_ALPHA":"",n.vertexUv1s?"#define USE_UV1":"",n.vertexUv2s?"#define USE_UV2":"",n.vertexUv3s?"#define USE_UV3":"",n.pointsUvs?"#define USE_POINTS_UV":"",n.gradientMap?"#define USE_GRADIENTMAP":"",n.flatShading?"#define FLAT_SHADED":"",n.doubleSided?"#define DOUBLE_SIDED":"",n.flipSided?"#define FLIP_SIDED":"",n.shadowMapEnabled?"#define USE_SHADOWMAP":"",n.shadowMapEnabled?"#define "+c:"",n.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",n.numLightProbes>0?"#define USE_LIGHT_PROBES":"",n.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",n.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",n.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",n.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",n.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",n.toneMapping!==Qt?"#define TONE_MAPPING":"",n.toneMapping!==Qt?Fe.tonemapping_pars_fragment:"",n.toneMapping!==Qt?$m("toneMapping",n.toneMapping):"",n.dithering?"#define DITHERING":"",n.opaque?"#define OPAQUE":"",Fe.colorspace_pars_fragment,Xm("linearToOutputTexel",n.outputColorSpace),Ym(),n.useDepthPacking?"#define DEPTH_PACKING "+n.depthPacking:"",`
`].filter(ls).join(`
`);if(a=Oo(a),a=ph(a,n),a=mh(a,n),o=Oo(o),o=ph(o,n),o=mh(o,n),a=gh(a),o=gh(o),n.isRawShaderMaterial!==!0)T=`#version 300 es
`,p=[m,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+p,f=["#define varying in",n.glslVersion===eo?"":"layout(location = 0) out highp vec4 pc_fragColor;",n.glslVersion===eo?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+f;let I=T+p+a,S=T+f+o,w=uh(s,s.VERTEX_SHADER,I),E=uh(s,s.FRAGMENT_SHADER,S);if(s.attachShader(b,w),s.attachShader(b,E),n.index0AttributeName!==void 0)s.bindAttribLocation(b,0,n.index0AttributeName);else if(n.hasPositionAttribute===!0)s.bindAttribLocation(b,0,"position");s.linkProgram(b);function A(D){if(e.debug.checkShaderErrors){let U=s.getProgramInfoLog(b)||"",J=s.getShaderInfoLog(w)||"",C=s.getShaderInfoLog(E)||"",V=U.trim(),K=J.trim(),G=C.trim(),ne=!0,X=!0;if(s.getProgramParameter(b,s.LINK_STATUS)===!1)if(ne=!1,typeof e.debug.onShaderError==="function")e.debug.onShaderError(s,b,w,E);else{let j=fh(s,w,"vertex"),te=fh(s,E,"fragment");Pe("WebGLProgram: Shader Error "+s.getError()+" - VALIDATE_STATUS "+s.getProgramParameter(b,s.VALIDATE_STATUS)+`

Material Name: `+D.name+`
Material Type: `+D.type+`

Program Info Log: `+V+`
`+j+`
`+te)}else if(V!=="")Ce("WebGLProgram: Program Info Log:",V);else if(K===""||G==="")X=!1;if(X)D.diagnostics={runnable:ne,programLog:V,vertexShader:{log:K,prefix:p},fragmentShader:{log:G,prefix:f}}}s.deleteShader(w),s.deleteShader(E),x=new cs(s,b),M=Km(s,b)}let x;this.getUniforms=function(){if(x===void 0)A(this);return x};let M;this.getAttributes=function(){if(M===void 0)A(this);return M};let H=n.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){if(H===!1)H=s.getProgramParameter(b,Gm);return H},this.destroy=function(){i.releaseStatesOfProgram(this),s.deleteProgram(b),this.program=void 0},this.type=n.shaderType,this.name=n.shaderName,this.id=Hm++,this.cacheKey=t,this.usedTimes=1,this.program=b,this.vertexShader=w,this.fragmentShader=E,this}var fg=0;class Ph{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e,t,n){let i=this._getShaderCacheForMaterial(e);if(i.has(t)===!1)i.add(t),t.usedTimes++;if(i.has(n)===!1)i.add(n),n.usedTimes++;return this}remove(e){let t=this.materialCache.get(e);for(let n of t)if(n.usedTimes--,n.usedTimes===0)this.shaderCache.delete(n.code);return this.materialCache.delete(e),this}getVertexShaderStage(e){return this._getShaderStage(e.vertexShader)}getFragmentShaderStage(e){return this._getShaderStage(e.fragmentShader)}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){let t=this.materialCache,n=t.get(e);if(n===void 0)n=new Set,t.set(e,n);return n}_getShaderStage(e){let t=this.shaderCache,n=t.get(e);if(n===void 0)n=new Lh(e),t.set(e,n);return n}}class Lh{constructor(e){this.id=fg++,this.code=e,this.usedTimes=0}}function pg(e){return e===Zn||e===Js||e===Ks}function mg(e,t,n,i,s,r){let a=new tr,o=new Ph,c=new Set,l=[],u=new Map,{logarithmicDepthBuffer:d,precision:h}=i,m={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function v(x){if(c.add(x),x===0)return"uv";return`uv${x}`}function b(x,M,H,D,U,J){let C=D.fog,V=U.geometry,K=x.isMeshStandardMaterial||x.isMeshLambertMaterial||x.isMeshPhongMaterial?D.environment:null,G=x.isMeshStandardMaterial||x.isMeshLambertMaterial&&!x.envMap||x.isMeshPhongMaterial&&!x.envMap,ne=t.get(x.envMap||K,G),X=!!ne&&ne.mapping===Qi?ne.image.height:null,j=m[x.type];if(x.precision!==null){if(h=i.getMaxPrecision(x.precision),h!==x.precision)Ce("WebGLProgram.getParameters:",x.precision,"not supported, using",h,"instead.")}let te=V.morphAttributes.position||V.morphAttributes.normal||V.morphAttributes.color,Re=te!==void 0?te.length:0,Ee=0;if(V.morphAttributes.position!==void 0)Ee=1;if(V.morphAttributes.normal!==void 0)Ee=2;if(V.morphAttributes.color!==void 0)Ee=3;let it,Oe,q,ie;if(j){let st=fn[j];it=st.vertexShader,Oe=st.fragmentShader}else{it=x.vertexShader,Oe=x.fragmentShader;let st=o.getVertexShaderStage(x),Je=o.getFragmentShaderStage(x);o.update(x,st,Je),q=st.id,ie=Je.id}let re=e.getRenderTarget(),Te=e.state.buffers.depth.getReversed(),Ie=U.isInstancedMesh===!0,be=U.isBatchedMesh===!0,gt=!!x.map,ze=!!x.matcap,He=!!ne,je=!!x.aoMap,Ve=!!x.lightMap,Et=!!x.bumpMap&&x.wireframe===!1,at=!!x.normalMap,Ut=!!x.displacementMap,_t=!!x.emissiveMap,xt=!!x.metalnessMap,P=!!x.roughnessMap,Ft=x.anisotropy>0,Ze=x.clearcoat>0,ct=x.dispersion>0,y=x.retroreflectivity>0,g=x.iridescence>0,R=x.sheen>0,z=x.transmission>0,ee=Ft&&!!x.anisotropyMap,ae=Ze&&!!x.clearcoatMap,ce=Ze&&!!x.clearcoatNormalMap,W=Ze&&!!x.clearcoatRoughnessMap,Z=g&&!!x.iridescenceMap,me=g&&!!x.iridescenceThicknessMap,Me=R&&!!x.sheenColorMap,he=R&&!!x.sheenRoughnessMap,se=!!x.specularMap,we=!!x.specularColorMap,Ae=!!x.specularIntensityMap,$e=z&&!!x.transmissionMap,N=z&&!!x.thicknessMap,oe=!!x.gradientMap,Y=!!x.alphaMap,le=x.alphaTest>0,ge=!!x.alphaHash,Q=!!x.extensions,de=Qt;if(x.toneMapped){if(re===null||re.isXRRenderTarget===!0)de=e.toneMapping}let Ne={shaderID:j,shaderType:x.type,shaderName:x.name,vertexShader:it,fragmentShader:Oe,defines:x.defines,customVertexShaderID:q,customFragmentShaderID:ie,isRawShaderMaterial:x.isRawShaderMaterial===!0,glslVersion:x.glslVersion,precision:h,batching:be,batchingColor:be&&U._colorsTexture!==null,instancing:Ie,instancingColor:Ie&&U.instanceColor!==null,instancingMorph:Ie&&U.morphTexture!==null,outputColorSpace:re===null?e.outputColorSpace:re.isXRRenderTarget===!0?re.texture.colorSpace:ke.workingColorSpace,alphaToCoverage:!!x.alphaToCoverage,map:gt,matcap:ze,envMap:He,envMapMode:He&&ne.mapping,envMapCubeUVHeight:X,aoMap:je,lightMap:Ve,bumpMap:Et,normalMap:at,displacementMap:Ut,emissiveMap:_t,normalMapObjectSpace:at&&x.normalMapType===Bc,normalMapTangentSpace:at&&x.normalMapType===Ka,packedNormalMap:at&&x.normalMapType===Ka&&pg(x.normalMap.format),metalnessMap:xt,roughnessMap:P,anisotropy:Ft,anisotropyMap:ee,clearcoat:Ze,clearcoatMap:ae,clearcoatNormalMap:ce,clearcoatRoughnessMap:W,dispersion:ct,retroreflection:y,iridescence:g,iridescenceMap:Z,iridescenceThicknessMap:me,sheen:R,sheenColorMap:Me,sheenRoughnessMap:he,specularMap:se,specularColorMap:we,specularIntensityMap:Ae,transmission:z,transmissionMap:$e,thicknessMap:N,gradientMap:oe,opaque:x.transparent===!1&&x.blending===ji&&x.alphaToCoverage===!1,alphaMap:Y,alphaTest:le,alphaHash:ge,combine:x.combine,mapUv:gt&&v(x.map.channel),aoMapUv:je&&v(x.aoMap.channel),lightMapUv:Ve&&v(x.lightMap.channel),bumpMapUv:Et&&v(x.bumpMap.channel),normalMapUv:at&&v(x.normalMap.channel),displacementMapUv:Ut&&v(x.displacementMap.channel),emissiveMapUv:_t&&v(x.emissiveMap.channel),metalnessMapUv:xt&&v(x.metalnessMap.channel),roughnessMapUv:P&&v(x.roughnessMap.channel),anisotropyMapUv:ee&&v(x.anisotropyMap.channel),clearcoatMapUv:ae&&v(x.clearcoatMap.channel),clearcoatNormalMapUv:ce&&v(x.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:W&&v(x.clearcoatRoughnessMap.channel),iridescenceMapUv:Z&&v(x.iridescenceMap.channel),iridescenceThicknessMapUv:me&&v(x.iridescenceThicknessMap.channel),sheenColorMapUv:Me&&v(x.sheenColorMap.channel),sheenRoughnessMapUv:he&&v(x.sheenRoughnessMap.channel),specularMapUv:se&&v(x.specularMap.channel),specularColorMapUv:we&&v(x.specularColorMap.channel),specularIntensityMapUv:Ae&&v(x.specularIntensityMap.channel),transmissionMapUv:$e&&v(x.transmissionMap.channel),thicknessMapUv:N&&v(x.thicknessMap.channel),alphaMapUv:Y&&v(x.alphaMap.channel),vertexTangents:!!V.attributes.tangent&&(at||Ft),vertexNormals:!!V.attributes.normal,vertexColors:x.vertexColors,vertexAlphas:x.vertexColors===!0&&!!V.attributes.color&&V.attributes.color.itemSize===4,pointsUvs:U.isPoints===!0&&!!V.attributes.uv&&(gt||Y),fog:!!C,useFog:x.fog===!0,fogExp2:!!C&&C.isFogExp2,flatShading:x.wireframe===!1&&(x.flatShading===!0||V.attributes.normal===void 0&&at===!1&&(x.isMeshLambertMaterial||x.isMeshPhongMaterial||x.isMeshStandardMaterial||x.isMeshPhysicalMaterial)),sizeAttenuation:x.sizeAttenuation===!0,logarithmicDepthBuffer:d,reversedDepthBuffer:Te,skinning:U.isSkinnedMesh===!0,hasPositionAttribute:V.attributes.position!==void 0,morphTargets:V.morphAttributes.position!==void 0,morphNormals:V.morphAttributes.normal!==void 0,morphColors:V.morphAttributes.color!==void 0,morphTargetsCount:Re,morphTextureStride:Ee,numSunLights:M.sun.length,numDirLights:M.directional.length,numPointLights:M.point.length,numSpotLights:M.spot.length,numSpotLightMaps:M.spotLightMap.length,numRectAreaLights:M.rectArea.length,numHemiLights:M.hemi.length,numSunLightShadows:M.sunShadowMap.length,numDirLightShadows:M.directionalShadowMap.length,numPointLightShadows:M.pointShadowMap.length,numSpotLightShadows:M.spotShadowMap.length,numSpotLightShadowsWithMaps:M.numSpotLightShadowsWithMaps,numLightProbes:M.numLightProbes,numLightProbeGrids:J.length,numClippingPlanes:r.numPlanes,numClipIntersection:r.numIntersection,dithering:x.dithering,shadowMapEnabled:e.shadowMap.enabled&&H.length>0,shadowMapType:e.shadowMap.type,toneMapping:de,decodeVideoTexture:gt&&x.map.isVideoTexture===!0&&ke.getTransfer(x.map.colorSpace)===nt,decodeVideoTextureEmissive:_t&&x.emissiveMap.isVideoTexture===!0&&ke.getTransfer(x.emissiveMap.colorSpace)===nt,premultipliedAlpha:x.premultipliedAlpha,doubleSided:x.side===ln,flipSided:x.side===Bt,useDepthPacking:x.depthPacking>=0,depthPacking:x.depthPacking||0,index0AttributeName:x.index0AttributeName,extensionClipCullDistance:Q&&x.extensions.clipCullDistance===!0&&n.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(Q&&x.extensions.multiDraw===!0||be)&&n.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:n.has("KHR_parallel_shader_compile"),customProgramCacheKey:x.customProgramCacheKey()};return Ne.vertexUv1s=c.has(1),Ne.vertexUv2s=c.has(2),Ne.vertexUv3s=c.has(3),c.clear(),Ne}function p(x){let M=[];if(x.shaderID)M.push(x.shaderID);else M.push(x.customVertexShaderID),M.push(x.customFragmentShaderID);if(x.defines!==void 0)for(let H in x.defines)M.push(H),M.push(x.defines[H]);if(x.isRawShaderMaterial===!1)f(M,x),T(M,x),M.push(e.outputColorSpace);return M.push(x.customProgramCacheKey),M.join()}function f(x,M){x.push(M.precision),x.push(M.outputColorSpace),x.push(M.envMapMode),x.push(M.envMapCubeUVHeight),x.push(M.mapUv),x.push(M.alphaMapUv),x.push(M.lightMapUv),x.push(M.aoMapUv),x.push(M.bumpMapUv),x.push(M.normalMapUv),x.push(M.displacementMapUv),x.push(M.emissiveMapUv),x.push(M.metalnessMapUv),x.push(M.roughnessMapUv),x.push(M.anisotropyMapUv),x.push(M.clearcoatMapUv),x.push(M.clearcoatNormalMapUv),x.push(M.clearcoatRoughnessMapUv),x.push(M.iridescenceMapUv),x.push(M.iridescenceThicknessMapUv),x.push(M.sheenColorMapUv),x.push(M.sheenRoughnessMapUv),x.push(M.specularMapUv),x.push(M.specularColorMapUv),x.push(M.specularIntensityMapUv),x.push(M.transmissionMapUv),x.push(M.thicknessMapUv),x.push(M.combine),x.push(M.fogExp2),x.push(M.sizeAttenuation),x.push(M.morphTargetsCount),x.push(M.morphAttributeCount),x.push(M.numSunLights),x.push(M.numDirLights),x.push(M.numPointLights),x.push(M.numSpotLights),x.push(M.numSpotLightMaps),x.push(M.numHemiLights),x.push(M.numRectAreaLights),x.push(M.numSunLightShadows),x.push(M.numDirLightShadows),x.push(M.numPointLightShadows),x.push(M.numSpotLightShadows),x.push(M.numSpotLightShadowsWithMaps),x.push(M.numLightProbes),x.push(M.shadowMapType),x.push(M.toneMapping),x.push(M.numClippingPlanes),x.push(M.numClipIntersection),x.push(M.depthPacking)}function T(x,M){if(a.disableAll(),M.instancing)a.enable(0);if(M.instancingColor)a.enable(1);if(M.instancingMorph)a.enable(2);if(M.matcap)a.enable(3);if(M.envMap)a.enable(4);if(M.normalMapObjectSpace)a.enable(5);if(M.normalMapTangentSpace)a.enable(6);if(M.clearcoat)a.enable(7);if(M.iridescence)a.enable(8);if(M.alphaTest)a.enable(9);if(M.vertexColors)a.enable(10);if(M.vertexAlphas)a.enable(11);if(M.vertexUv1s)a.enable(12);if(M.vertexUv2s)a.enable(13);if(M.vertexUv3s)a.enable(14);if(M.vertexTangents)a.enable(15);if(M.anisotropy)a.enable(16);if(M.alphaHash)a.enable(17);if(M.batching)a.enable(18);if(M.dispersion)a.enable(19);if(M.retroreflection)a.enable(24);if(M.batchingColor)a.enable(20);if(M.gradientMap)a.enable(21);if(M.packedNormalMap)a.enable(22);if(M.vertexNormals)a.enable(23);if(x.push(a.mask),a.disableAll(),M.fog)a.enable(0);if(M.useFog)a.enable(1);if(M.flatShading)a.enable(2);if(M.logarithmicDepthBuffer)a.enable(3);if(M.reversedDepthBuffer)a.enable(4);if(M.skinning)a.enable(5);if(M.morphTargets)a.enable(6);if(M.morphNormals)a.enable(7);if(M.morphColors)a.enable(8);if(M.premultipliedAlpha)a.enable(9);if(M.shadowMapEnabled)a.enable(10);if(M.doubleSided)a.enable(11);if(M.flipSided)a.enable(12);if(M.useDepthPacking)a.enable(13);if(M.dithering)a.enable(14);if(M.transmission)a.enable(15);if(M.sheen)a.enable(16);if(M.opaque)a.enable(17);if(M.pointsUvs)a.enable(18);if(M.decodeVideoTexture)a.enable(19);if(M.decodeVideoTextureEmissive)a.enable(20);if(M.alphaToCoverage)a.enable(21);if(M.numLightProbeGrids>0)a.enable(22);if(M.hasPositionAttribute)a.enable(23);x.push(a.mask)}function I(x){let M=m[x.type],H;if(M){let D=fn[M];H=Kc.clone(D.uniforms)}else H=x.uniforms;return H}function S(x,M){let H=u.get(M);if(H!==void 0)++H.usedTimes;else H=new dg(e,M,x,s),l.push(H),u.set(M,H);return H}function w(x){if(--x.usedTimes===0){let M=l.indexOf(x);l[M]=l[l.length-1],l.pop(),u.delete(x.cacheKey),x.destroy()}}function E(x){o.remove(x)}function A(){o.dispose()}return{getParameters:b,getProgramCacheKey:p,getUniforms:I,acquireProgram:S,releaseProgram:w,releaseShaderCache:E,programs:l,dispose:A}}function gg(){let e=new WeakMap;function t(a){return e.has(a)}function n(a){let o=e.get(a);if(o===void 0)o={},e.set(a,o);return o}function i(a){e.delete(a)}function s(a,o,c){e.get(a)[o]=c}function r(){e=new WeakMap}return{has:t,get:n,remove:i,update:s,dispose:r}}function _g(e,t){if(e.groupOrder!==t.groupOrder)return e.groupOrder-t.groupOrder;else if(e.renderOrder!==t.renderOrder)return e.renderOrder-t.renderOrder;else if(e.material.id!==t.material.id)return e.material.id-t.material.id;else if(e.materialVariant!==t.materialVariant)return e.materialVariant-t.materialVariant;else if(e.z!==t.z)return e.z-t.z;else return e.id-t.id}function xh(e,t){if(e.groupOrder!==t.groupOrder)return e.groupOrder-t.groupOrder;else if(e.renderOrder!==t.renderOrder)return e.renderOrder-t.renderOrder;else if(e.z!==t.z)return t.z-e.z;else return e.id-t.id}function vh(){let e=[],t=0,n=[],i=[],s=[];function r(){t=0,n.length=0,i.length=0,s.length=0}function a(h){let m=0;if(h.isInstancedMesh)m+=2;if(h.isSkinnedMesh)m+=1;return m}function o(h,m,v,b,p,f){let T=e[t];if(T===void 0)T={id:h.id,object:h,geometry:m,material:v,materialVariant:a(h),groupOrder:b,renderOrder:h.renderOrder,z:p,group:f},e[t]=T;else T.id=h.id,T.object=h,T.geometry=m,T.material=v,T.materialVariant=a(h),T.groupOrder=b,T.renderOrder=h.renderOrder,T.z=p,T.group=f;return t++,T}function c(h,m,v,b,p,f,T){if(T.reversedDepth===!0)p=-p;let I=o(h,m,v,b,p,f);if(v.transmission>0)i.push(I);else if(v.transparent===!0)s.push(I);else n.push(I)}function l(h,m,v,b,p,f){let T=o(h,m,v,b,p,f);if(v.transmission>0)i.unshift(T);else if(v.transparent===!0)s.unshift(T);else n.unshift(T)}function u(h,m){if(n.length>1)n.sort(h||_g);if(i.length>1)i.sort(m||xh);if(s.length>1)s.sort(m||xh)}function d(){for(let h=t,m=e.length;h<m;h++){let v=e[h];if(v.id===null)break;v.id=null,v.object=null,v.geometry=null,v.material=null,v.group=null}}return{opaque:n,transmissive:i,transparent:s,init:r,push:c,unshift:l,finish:d,sort:u}}function xg(){let e=new WeakMap;function t(i,s){let r=e.get(i),a;if(r===void 0)a=new vh,e.set(i,[a]);else if(s>=r.length)a=new vh,r.push(a);else a=r[s];return a}function n(){e=new WeakMap}return{get:t,dispose:n}}function vg(){let e={};return{get:function(t){if(e[t.id]!==void 0)return e[t.id];let n;switch(t.type){case"SunLight":case"DirectionalLight":n={direction:new F,color:new qe};break;case"SpotLight":n={position:new F,direction:new F,color:new qe,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":n={position:new F,color:new qe,distance:0,decay:0};break;case"HemisphereLight":n={direction:new F,skyColor:new qe,groundColor:new qe};break;case"RectAreaLight":n={color:new qe,position:new F,halfWidth:new F,halfHeight:new F};break}return e[t.id]=n,n}}}function yg(){let e={};return{get:function(t){if(e[t.id]!==void 0)return e[t.id];let n;switch(t.type){case"SunLight":case"DirectionalLight":n={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe};break;case"SpotLight":n={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe};break;case"PointLight":n={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe,shadowCameraNear:1,shadowCameraFar:1000};break}return e[t.id]=n,n}}}var Sg=0;function Mg(e,t){return(t.castShadow?2:0)-(e.castShadow?2:0)+(t.map?1:0)-(e.map?1:0)}function bg(e){let t=new vg,n=yg(),i={version:0,hash:{sunLength:-1,directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numSunShadows:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],sun:[],sunShadow:[],sunShadowMap:[],sunShadowMatrix:[],sunShadowCascade:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let l=0;l<9;l++)i.probe.push(new F);let s=new F,r=new ht,a=new ht;function o(l){let u=0,d=0,h=0;for(let U=0;U<9;U++)i.probe[U].set(0,0,0);let m=0,v=0,b=0,p=0,f=0,T=0,I=0,S=0,w=0,E=0,A=0,x=0,M=0,H=0;l.sort(Mg);for(let U=0,J=l.length;U<J;U++){let C=l[U],{color:V,intensity:K,distance:G}=C,ne=null;if(C.shadow&&C.shadow.map)if(C.shadow.map.texture.format===Zn)ne=C.shadow.map.texture;else ne=C.shadow.map.depthTexture||C.shadow.map.texture;if(C.isAmbientLight)u+=V.r*K,d+=V.g*K,h+=V.b*K;else if(C.isLightProbe){for(let X=0;X<9;X++)i.probe[X].addScaledVector(C.sh.coefficients[X],K);H++}else if(C.isSunLight){let X=t.get(C);if(X.color.copy(C.color).multiplyScalar(C.intensity),C.castShadow){let j=C.shadow,te=n.get(C);te.shadowIntensity=j.intensity,te.shadowBias=j.bias,te.shadowNormalBias=j.normalBias,te.shadowRadius=j.radius,te.shadowMapSize.copy(j.mapSize).multiply(j.getFrameExtents()),i.sunShadow[v]=te,i.sunShadowMap[v]=ne;let Re=j.getViewportCount();for(let Ee=0;Ee<Re;Ee++)i.sunShadowMatrix[b+Ee]=j.getMatrix(Ee),i.sunShadowCascade[b+Ee]=j._cascadeData[Ee];b+=Re,v++}i.sun[m]=X,m++}else if(C.isDirectionalLight){let X=t.get(C);if(X.color.copy(C.color).multiplyScalar(C.intensity),C.castShadow){let j=C.shadow,te=n.get(C);te.shadowIntensity=j.intensity,te.shadowBias=j.bias,te.shadowNormalBias=j.normalBias,te.shadowRadius=j.radius,te.shadowMapSize=j.mapSize,i.directionalShadow[p]=te,i.directionalShadowMap[p]=ne,i.directionalShadowMatrix[p]=C.shadow.matrix,w++}i.directional[p]=X,p++}else if(C.isSpotLight){let X=t.get(C);X.position.setFromMatrixPosition(C.matrixWorld),X.color.copy(V).multiplyScalar(K),X.distance=G,X.coneCos=Math.cos(C.angle),X.penumbraCos=Math.cos(C.angle*(1-C.penumbra)),X.decay=C.decay,i.spot[T]=X;let j=C.shadow;if(C.map){if(i.spotLightMap[x]=C.map,x++,j.updateMatrices(C),C.castShadow)M++}if(i.spotLightMatrix[T]=j.matrix,C.castShadow){let te=n.get(C);te.shadowIntensity=j.intensity,te.shadowBias=j.bias,te.shadowNormalBias=j.normalBias,te.shadowRadius=j.radius,te.shadowMapSize=j.mapSize,i.spotShadow[T]=te,i.spotShadowMap[T]=ne,A++}T++}else if(C.isRectAreaLight){let X=t.get(C);X.color.copy(V).multiplyScalar(K),X.halfWidth.set(C.width*0.5,0,0),X.halfHeight.set(0,C.height*0.5,0),i.rectArea[I]=X,I++}else if(C.isPointLight){let X=t.get(C);if(X.color.copy(C.color).multiplyScalar(C.intensity),X.distance=C.distance,X.decay=C.decay,C.castShadow){let j=C.shadow,te=n.get(C);te.shadowIntensity=j.intensity,te.shadowBias=j.bias,te.shadowNormalBias=j.normalBias,te.shadowRadius=j.radius,te.shadowMapSize=j.mapSize,te.shadowCameraNear=j.camera.near,te.shadowCameraFar=j.camera.far,i.pointShadow[f]=te,i.pointShadowMap[f]=ne,i.pointShadowMatrix[f]=C.shadow.matrix,E++}i.point[f]=X,f++}else if(C.isHemisphereLight){let X=t.get(C);X.skyColor.copy(C.color).multiplyScalar(K),X.groundColor.copy(C.groundColor).multiplyScalar(K),i.hemi[S]=X,S++}}if(I>0)if(e.has("OES_texture_float_linear")===!0)i.rectAreaLTC1=ue.LTC_FLOAT_1,i.rectAreaLTC2=ue.LTC_FLOAT_2;else i.rectAreaLTC1=ue.LTC_HALF_1,i.rectAreaLTC2=ue.LTC_HALF_2;i.ambient[0]=u,i.ambient[1]=d,i.ambient[2]=h;let D=i.hash;if(D.sunLength!==m||D.directionalLength!==p||D.pointLength!==f||D.spotLength!==T||D.rectAreaLength!==I||D.hemiLength!==S||D.numSunShadows!==v||D.numDirectionalShadows!==w||D.numPointShadows!==E||D.numSpotShadows!==A||D.numSpotMaps!==x||D.numLightProbes!==H)i.sun.length=m,i.directional.length=p,i.spot.length=T,i.rectArea.length=I,i.point.length=f,i.hemi.length=S,i.sunShadow.length=v,i.sunShadowMap.length=v,i.sunShadowMatrix.length=b,i.sunShadowCascade.length=b,i.directionalShadow.length=w,i.directionalShadowMap.length=w,i.directionalShadowMatrix.length=w,i.pointShadow.length=E,i.pointShadowMap.length=E,i.pointShadowMatrix.length=E,i.spotShadow.length=A,i.spotShadowMap.length=A,i.spotLightMatrix.length=A+x-M,i.spotLightMap.length=x,i.numSpotLightShadowsWithMaps=M,i.numLightProbes=H,D.sunLength=m,D.directionalLength=p,D.pointLength=f,D.spotLength=T,D.rectAreaLength=I,D.hemiLength=S,D.numSunShadows=v,D.numDirectionalShadows=w,D.numPointShadows=E,D.numSpotShadows=A,D.numSpotMaps=x,D.numLightProbes=H,i.version=Sg++}function c(l,u){let d=0,h=0,m=0,v=0,b=0,p=0,f=u.matrixWorldInverse;for(let T=0,I=l.length;T<I;T++){let S=l[T];if(S.isSunLight){let w=i.sun[d];w.direction.setFromMatrixPosition(S.matrixWorld),w.direction.transformDirection(f),d++}else if(S.isDirectionalLight){let w=i.directional[h];w.direction.setFromMatrixPosition(S.matrixWorld),s.setFromMatrixPosition(S.target.matrixWorld),w.direction.sub(s),w.direction.transformDirection(f),h++}else if(S.isSpotLight){let w=i.spot[v];w.position.setFromMatrixPosition(S.matrixWorld),w.position.applyMatrix4(f),w.direction.setFromMatrixPosition(S.matrixWorld),s.setFromMatrixPosition(S.target.matrixWorld),w.direction.sub(s),w.direction.transformDirection(f),v++}else if(S.isRectAreaLight){let w=i.rectArea[b];w.position.setFromMatrixPosition(S.matrixWorld),w.position.applyMatrix4(f),a.identity(),r.copy(S.matrixWorld),r.premultiply(f),a.extractRotation(r),w.halfWidth.set(S.width*0.5,0,0),w.halfHeight.set(0,S.height*0.5,0),w.halfWidth.applyMatrix4(a),w.halfHeight.applyMatrix4(a),b++}else if(S.isPointLight){let w=i.point[m];w.position.setFromMatrixPosition(S.matrixWorld),w.position.applyMatrix4(f),m++}else if(S.isHemisphereLight){let w=i.hemi[p];w.direction.setFromMatrixPosition(S.matrixWorld),w.direction.transformDirection(f),p++}}}return{setup:o,setupView:c,state:i}}function yh(e){let t=new bg(e),n=[],i=[],s=[];function r(h){d.camera=h,n.length=0,i.length=0,s.length=0}function a(h){n.push(h)}function o(h){i.push(h)}function c(h){s.push(h)}function l(){t.setup(n)}function u(h){t.setupView(n,h)}let d={lightsArray:n,shadowsArray:i,lightProbeGridArray:s,camera:null,lights:t,transmissionRenderTarget:{},textureUnits:0};return{init:r,state:d,setupLights:l,setupLightsView:u,pushLight:a,pushShadow:o,pushLightProbeGrid:c}}function wg(e){let t=new WeakMap;function n(s,r=0){let a=t.get(s),o;if(a===void 0)o=new yh(e),t.set(s,[o]);else if(r>=a.length)o=new yh(e),a.push(o);else o=a[r];return o}function i(){t=new WeakMap}return{get:n,dispose:i}}var Eg=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,Tg=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ).rg;
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ).r;
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( max( 0.0, squared_mean - mean * mean ) );
	gl_FragColor = vec4( mean, std_dev, 0.0, 1.0 );
}`,Ag=[new F(1,0,0),new F(-1,0,0),new F(0,1,0),new F(0,-1,0),new F(0,0,1),new F(0,0,-1)],Cg=[new F(0,-1,0),new F(0,-1,0),new F(0,0,1),new F(0,0,-1),new F(0,-1,0),new F(0,-1,0)],Sh=new ht,os=new F,Do=new F;function Rg(e,t,n){let i=new ar,s=new Xe,r=new Xe,a=new ut,o=new ho,c=new uo,l={},u=n.maxTextureSize,d={[Ri]:Bt,[Bt]:Ri,[ln]:ln},h=new Yt({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Xe},radius:{value:4}},vertexShader:Eg,fragmentShader:Tg}),m=h.clone();m.defines.HORIZONTAL_PASS=1;let v=new bt;v.setAttribute("position",new Ht(new Float32Array([-1,-1,0.5,3,-1,0.5,-1,3,0.5]),3));let b=new Dt(v,h),p=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Ki;let f=this.type;this.render=function(E,A,x){if(p.enabled===!1)return;if(p.autoUpdate===!1&&p.needsUpdate===!1)return;if(E.length===0)return;if(this.type===Kl)Ce("WebGLShadowMap: PCFSoftShadowMap has been removed. Using PCFShadowMap instead."),this.type=Ki;let M=e.getRenderTarget(),H=e.getActiveCubeFace(),D=e.getActiveMipmapLevel(),U=e.state;if(U.setBlending(cn),U.buffers.depth.getReversed()===!0)U.buffers.color.setClear(0,0,0,0);else U.buffers.color.setClear(1,1,1,1);U.buffers.depth.setTest(!0),U.setScissorTest(!1);let J=f!==this.type;if(J)A.traverse(function(C){if(C.material)if(Array.isArray(C.material))C.material.forEach((V)=>V.needsUpdate=!0);else C.material.needsUpdate=!0});for(let C=0,V=E.length;C<V;C++){let K=E[C],G=K.shadow;if(G===void 0){Ce("WebGLShadowMap:",K,"has no shadow.");continue}if(G.autoUpdate===!1&&G.needsUpdate===!1)continue;s.copy(G.mapSize);let ne=G.getFrameExtents();if(s.multiply(ne),r.copy(G.mapSize),s.x>u||s.y>u){if(s.x>u)r.x=Math.floor(u/ne.x),s.x=r.x*ne.x,G.mapSize.x=r.x;if(s.y>u)r.y=Math.floor(u/ne.y),s.y=r.y*ne.y,G.mapSize.y=r.y}let X=e.state.buffers.depth.getReversed();if(G.camera._reversedDepth=X,G.map===null||J===!0){if(G.map!==null){if(G.map.depthTexture!==null)G.map.depthTexture.dispose(),G.map.depthTexture=null;G.map.dispose()}if(this.type===Ci){if(K.isPointLight){Ce("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}G.map=new Vt(s.x,s.y,{format:Zn,type:hn,minFilter:zt,magFilter:zt,generateMipmaps:!1}),G.map.texture.name=K.name+".shadowMap",G.map.depthTexture=new ti(s.x,s.y,Sn),G.map.depthTexture.name=K.name+".shadowMapDepth",G.map.depthTexture.format=$n,G.map.depthTexture.compareFunction=null,G.map.depthTexture.minFilter=Dn,G.map.depthTexture.magFilter=Dn}else{if(K.isPointLight)G.map=new Bo(s.x),G.map.depthTexture=new oo(s.x,Un);else G.map=new Vt(s.x,s.y),G.map.depthTexture=new ti(s.x,s.y,Un);if(G.map.depthTexture.name=K.name+".shadowMap",G.map.depthTexture.format=$n,this.type===Ki)G.map.depthTexture.compareFunction=X?Qs:js,G.map.depthTexture.minFilter=zt,G.map.depthTexture.magFilter=zt;else G.map.depthTexture.compareFunction=null,G.map.depthTexture.minFilter=Dn,G.map.depthTexture.magFilter=Dn}G.camera.updateProjectionMatrix()}if(G.map.isWebGLCubeRenderTarget!==!0&&(G.map.width!==s.x||G.map.height!==s.y))G.map.setSize(s.x,s.y);let j=G.map.isWebGLCubeRenderTarget?6:G.getViewportCount();if(K.isPointLight!==!0)G.updateMatrices(K,x);for(let te=0;te<j;te++){let Re=G.getCamera(te);if(K.isPointLight){let{camera:Ee,matrix:it}=G,Oe=K.distance||Ee.far;if(Oe!==Ee.far)Ee.far=Oe,Ee.updateProjectionMatrix();os.setFromMatrixPosition(K.matrixWorld),Ee.position.copy(os),Do.copy(Ee.position),Do.add(Ag[te]),Ee.up.copy(Cg[te]),Ee.lookAt(Do),Ee.updateMatrixWorld(),it.makeTranslation(-os.x,-os.y,-os.z),Sh.multiplyMatrices(Ee.projectionMatrix,Ee.matrixWorldInverse),G._frustum.setFromProjectionMatrix(Sh,Ee.coordinateSystem,Ee.reversedDepth)}if(G.map.isWebGLCubeRenderTarget)e.setRenderTarget(G.map,te),e.clear();else{if(te===0)e.setRenderTarget(G.map),e.clear();let Ee=G.getViewport(te);a.set(r.x*Ee.x,r.y*Ee.y,r.x*Ee.z,r.y*Ee.w),U.viewport(a)}i=G.getFrustum(te),S(A,x,Re,K,this.type)}if(G.isPointLightShadow!==!0&&this.type===Ci)T(G,x);G.needsUpdate=!1}f=this.type,p.needsUpdate=!1,e.setRenderTarget(M,H,D)};function T(E,A){let x=t.update(b);if(h.defines.VSM_SAMPLES!==E.blurSamples)h.defines.VSM_SAMPLES=E.blurSamples,m.defines.VSM_SAMPLES=E.blurSamples,h.needsUpdate=!0,m.needsUpdate=!0;if(E.mapPass===null)E.mapPass=new Vt(s.x,s.y,{format:Zn,type:hn});else if(E.mapPass.width!==E.map.width||E.mapPass.height!==E.map.height)E.mapPass.setSize(E.map.width,E.map.height);h.uniforms.shadow_pass.value=E.map.depthTexture,h.uniforms.resolution.value.set(E.map.width,E.map.height),h.uniforms.radius.value=E.radius,e.setRenderTarget(E.mapPass),e.clear(),e.renderBufferDirect(A,null,x,h,b,null),m.uniforms.shadow_pass.value=E.mapPass.texture,m.uniforms.resolution.value.set(E.map.width,E.map.height),m.uniforms.radius.value=E.radius,e.setRenderTarget(E.map),e.clear(),e.renderBufferDirect(A,null,x,m,b,null)}function I(E,A,x,M){let H=null,D=x.isPointLight===!0?E.customDistanceMaterial:E.customDepthMaterial;if(D!==void 0)H=D;else if(H=x.isPointLight===!0?c:o,e.localClippingEnabled&&A.clipShadows===!0&&Array.isArray(A.clippingPlanes)&&A.clippingPlanes.length!==0||A.displacementMap&&A.displacementScale!==0||A.alphaMap&&A.alphaTest>0||A.map&&A.alphaTest>0||A.alphaToCoverage===!0){let U=H.uuid,J=A.uuid,C=l[U];if(C===void 0)C={},l[U]=C;let V=C[J];if(V===void 0)V=H.clone(),C[J]=V,A.addEventListener("dispose",w);H=V}if(H.visible=A.visible,H.wireframe=A.wireframe,M===Ci)H.side=A.shadowSide!==null?A.shadowSide:A.side;else H.side=A.shadowSide!==null?A.shadowSide:d[A.side];if(H.alphaMap=A.alphaMap,H.alphaTest=A.alphaToCoverage===!0?0.5:A.alphaTest,H.map=A.map,H.clipShadows=A.clipShadows,H.clippingPlanes=A.clippingPlanes,H.clipIntersection=A.clipIntersection,H.displacementMap=A.displacementMap,H.displacementScale=A.displacementScale,H.displacementBias=A.displacementBias,H.wireframeLinewidth=A.wireframeLinewidth,H.linewidth=A.linewidth,x.isPointLight===!0&&H.isMeshDistanceMaterial===!0){let U=e.properties.get(H);U.light=x}return H}function S(E,A,x,M,H){if(E.visible===!1)return;if(E.layers.test(A.layers)&&(E.isMesh||E.isLine||E.isPoints)){if((E.castShadow||E.receiveShadow&&H===Ci)&&(!E.frustumCulled||E.intersectsFrustum(i))){E.modelViewMatrix.multiplyMatrices(x.matrixWorldInverse,E.matrixWorld);let J=t.update(E),C=E.material;if(Array.isArray(C)){let V=J.groups;for(let K=0,G=V.length;K<G;K++){let ne=V[K],X=C[ne.materialIndex];if(X&&X.visible){let j=I(E,X,M,H);E.onBeforeShadow(e,E,A,x,J,j,ne),e.renderBufferDirect(x,null,J,j,E,ne),E.onAfterShadow(e,E,A,x,J,j,ne)}}}else if(C.visible){let V=I(E,C,M,H);E.onBeforeShadow(e,E,A,x,J,V,null),e.renderBufferDirect(x,null,J,V,E,null),E.onAfterShadow(e,E,A,x,J,V,null)}}}let U=E.children;for(let J=0,C=U.length;J<C;J++)S(U[J],A,x,M,H)}function w(E){E.target.removeEventListener("dispose",w);for(let x in l){let M=l[x],H=E.target.uuid;if(H in M)M[H].dispose(),delete M[H]}}}function Ig(e,t){function n(){let N=!1,oe=new ut,Y=null,le=new ut(0,0,0,0);return{setMask:function(ge){if(Y!==ge&&!N)e.colorMask(ge,ge,ge,ge),Y=ge},setLocked:function(ge){N=ge},setClear:function(ge,Q,de,Ne,st){if(st===!0)ge*=Ne,Q*=Ne,de*=Ne;if(oe.set(ge,Q,de,Ne),le.equals(oe)===!1)e.clearColor(ge,Q,de,Ne),le.copy(oe)},reset:function(){N=!1,Y=null,le.set(-1,0,0,0)}}}function i(){let N=!1,oe=!1,Y=null,le=null,ge=null;return{setReversed:function(Q){if(oe!==Q){let de=t.get("EXT_clip_control");if(Q)de.clipControlEXT(de.LOWER_LEFT_EXT,de.ZERO_TO_ONE_EXT);else de.clipControlEXT(de.LOWER_LEFT_EXT,de.NEGATIVE_ONE_TO_ONE_EXT);oe=Q;let Ne=ge;ge=null,this.setClear(Ne)}},getReversed:function(){return oe},setTest:function(Q){if(Q)re(e.DEPTH_TEST);else Te(e.DEPTH_TEST)},setMask:function(Q){if(Y!==Q&&!N)e.depthMask(Q),Y=Q},setFunc:function(Q){if(oe)Q=Zc[Q];if(le!==Q){switch(Q){case xc:e.depthFunc(e.NEVER);break;case vc:e.depthFunc(e.ALWAYS);break;case yc:e.depthFunc(e.LESS);break;case oa:e.depthFunc(e.LEQUAL);break;case Sc:e.depthFunc(e.EQUAL);break;case Mc:e.depthFunc(e.GEQUAL);break;case bc:e.depthFunc(e.GREATER);break;case wc:e.depthFunc(e.NOTEQUAL);break;default:e.depthFunc(e.LEQUAL)}le=Q}},setLocked:function(Q){N=Q},setClear:function(Q){if(ge!==Q){if(ge=Q,oe)Q=1-Q;e.clearDepth(Q)}},reset:function(){N=!1,Y=null,le=null,ge=null,oe=!1}}}function s(){let N=!1,oe=null,Y=null,le=null,ge=null,Q=null,de=null,Ne=null,st=null;return{setTest:function(Je){if(!N)if(Je)re(e.STENCIL_TEST);else Te(e.STENCIL_TEST)},setMask:function(Je){if(oe!==Je&&!N)e.stencilMask(Je),oe=Je},setFunc:function(Je,nn,pn){if(Y!==Je||le!==nn||ge!==pn)e.stencilFunc(Je,nn,pn),Y=Je,le=nn,ge=pn},setOp:function(Je,nn,pn){if(Q!==Je||de!==nn||Ne!==pn)e.stencilOp(Je,nn,pn),Q=Je,de=nn,Ne=pn},setLocked:function(Je){N=Je},setClear:function(Je){if(st!==Je)e.clearStencil(Je),st=Je},reset:function(){N=!1,oe=null,Y=null,le=null,ge=null,Q=null,de=null,Ne=null,st=null}}}let r=new n,a=new i,o=new s,c=new WeakMap,l=new WeakMap,u={},d={},h={},m=new WeakMap,v=[],b=null,p=!1,f=null,T=null,I=null,S=null,w=null,E=null,A=null,x=new qe(0,0,0),M=0,H=!1,D=null,U=null,J=null,C=null,V=null,K=e.getParameter(e.MAX_COMBINED_TEXTURE_IMAGE_UNITS),G=!1,ne=0,X=e.getParameter(e.VERSION);if(X.indexOf("WebGL")!==-1)ne=parseFloat(/^WebGL (\d)/.exec(X)[1]),G=ne>=1;else if(X.indexOf("OpenGL ES")!==-1)ne=parseFloat(/^OpenGL ES (\d)/.exec(X)[1]),G=ne>=2;let j=null,te={},Re=e.getParameter(e.SCISSOR_BOX),Ee=e.getParameter(e.VIEWPORT),it=new ut().fromArray(Re),Oe=new ut().fromArray(Ee);function q(N,oe,Y,le){let ge=new Uint8Array(4),Q=e.createTexture();e.bindTexture(N,Q),e.texParameteri(N,e.TEXTURE_MIN_FILTER,e.NEAREST),e.texParameteri(N,e.TEXTURE_MAG_FILTER,e.NEAREST);for(let de=0;de<Y;de++)if(N===e.TEXTURE_3D||N===e.TEXTURE_2D_ARRAY)e.texImage3D(oe,0,e.RGBA,1,1,le,0,e.RGBA,e.UNSIGNED_BYTE,ge);else e.texImage2D(oe+de,0,e.RGBA,1,1,0,e.RGBA,e.UNSIGNED_BYTE,ge);return Q}let ie={};ie[e.TEXTURE_2D]=q(e.TEXTURE_2D,e.TEXTURE_2D,1),ie[e.TEXTURE_CUBE_MAP]=q(e.TEXTURE_CUBE_MAP,e.TEXTURE_CUBE_MAP_POSITIVE_X,6),ie[e.TEXTURE_2D_ARRAY]=q(e.TEXTURE_2D_ARRAY,e.TEXTURE_2D_ARRAY,1,1),ie[e.TEXTURE_3D]=q(e.TEXTURE_3D,e.TEXTURE_3D,1,1),r.setClear(0,0,0,1),a.setClear(1),o.setClear(0),re(e.DEPTH_TEST),a.setFunc(oa),Et(!1),at(ia),re(e.CULL_FACE),je(cn);function re(N){if(u[N]!==!0)e.enable(N),u[N]=!0}function Te(N){if(u[N]!==!1)e.disable(N),u[N]=!1}function Ie(N,oe){if(h[N]!==oe){if(e.bindFramebuffer(N,oe),h[N]=oe,N===e.DRAW_FRAMEBUFFER)h[e.FRAMEBUFFER]=oe;if(N===e.FRAMEBUFFER)h[e.DRAW_FRAMEBUFFER]=oe;return!0}return!1}function be(N,oe){let Y=v,le=!1;if(N){if(Y=m.get(oe),Y===void 0)Y=[],m.set(oe,Y);let ge=N.textures;if(Y.length!==ge.length||Y[0]!==e.COLOR_ATTACHMENT0){for(let Q=0,de=ge.length;Q<de;Q++)Y[Q]=e.COLOR_ATTACHMENT0+Q;Y.length=ge.length,le=!0}}else if(Y[0]!==e.BACK)Y[0]=e.BACK,le=!0;if(le)e.drawBuffers(Y)}function gt(N){if(b!==N)return e.useProgram(N),b=N,!0;return!1}let ze={[Ii]:e.FUNC_ADD,[Ql]:e.FUNC_SUBTRACT,[ec]:e.FUNC_REVERSE_SUBTRACT};ze[tc]=e.MIN,ze[nc]=e.MAX;let He={[ic]:e.ZERO,[sc]:e.ONE,[rc]:e.SRC_COLOR,[oc]:e.SRC_ALPHA,[fc]:e.SRC_ALPHA_SATURATE,[uc]:e.DST_COLOR,[cc]:e.DST_ALPHA,[ac]:e.ONE_MINUS_SRC_COLOR,[lc]:e.ONE_MINUS_SRC_ALPHA,[dc]:e.ONE_MINUS_DST_COLOR,[hc]:e.ONE_MINUS_DST_ALPHA,[pc]:e.CONSTANT_COLOR,[mc]:e.ONE_MINUS_CONSTANT_COLOR,[gc]:e.CONSTANT_ALPHA,[_c]:e.ONE_MINUS_CONSTANT_ALPHA};function je(N,oe,Y,le,ge,Q,de,Ne,st,Je){if(N===cn){if(p===!0)Te(e.BLEND),p=!1;return}if(p===!1)re(e.BLEND),p=!0;if(N!==jl){if(N!==f||Je!==H){if(T!==Ii||w!==Ii)e.blendEquation(e.FUNC_ADD),T=Ii,w=Ii;if(Je)switch(N){case ji:e.blendFuncSeparate(e.ONE,e.ONE_MINUS_SRC_ALPHA,e.ONE,e.ONE_MINUS_SRC_ALPHA);break;case sa:e.blendFunc(e.ONE,e.ONE);break;case ra:e.blendFuncSeparate(e.ZERO,e.ONE_MINUS_SRC_COLOR,e.ZERO,e.ONE);break;case aa:e.blendFuncSeparate(e.DST_COLOR,e.ONE_MINUS_SRC_ALPHA,e.ZERO,e.ONE);break;default:Pe("WebGLState: Invalid blending: ",N);break}else switch(N){case ji:e.blendFuncSeparate(e.SRC_ALPHA,e.ONE_MINUS_SRC_ALPHA,e.ONE,e.ONE_MINUS_SRC_ALPHA);break;case sa:e.blendFuncSeparate(e.SRC_ALPHA,e.ONE,e.ONE,e.ONE);break;case ra:Pe("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case aa:Pe("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:Pe("WebGLState: Invalid blending: ",N);break}I=null,S=null,E=null,A=null,x.set(0,0,0),M=0,f=N,H=Je}return}if(ge=ge||oe,Q=Q||Y,de=de||le,oe!==T||ge!==w)e.blendEquationSeparate(ze[oe],ze[ge]),T=oe,w=ge;if(Y!==I||le!==S||Q!==E||de!==A)e.blendFuncSeparate(He[Y],He[le],He[Q],He[de]),I=Y,S=le,E=Q,A=de;if(Ne.equals(x)===!1||st!==M)e.blendColor(Ne.r,Ne.g,Ne.b,st),x.copy(Ne),M=st;f=N,H=!1}function Ve(N,oe){N.side===ln?Te(e.CULL_FACE):re(e.CULL_FACE);let Y=N.side===Bt;if(oe)Y=!Y;Et(Y),N.blending===ji&&N.transparent===!1?je(cn):je(N.blending,N.blendEquation,N.blendSrc,N.blendDst,N.blendEquationAlpha,N.blendSrcAlpha,N.blendDstAlpha,N.blendColor,N.blendAlpha,N.premultipliedAlpha),a.setFunc(N.depthFunc),a.setTest(N.depthTest),a.setMask(N.depthWrite),r.setMask(N.colorWrite);let le=N.stencilWrite;if(o.setTest(le),le)o.setMask(N.stencilWriteMask),o.setFunc(N.stencilFunc,N.stencilRef,N.stencilFuncMask),o.setOp(N.stencilFail,N.stencilZFail,N.stencilZPass);_t(N.polygonOffset,N.polygonOffsetFactor,N.polygonOffsetUnits),N.alphaToCoverage===!0?re(e.SAMPLE_ALPHA_TO_COVERAGE):Te(e.SAMPLE_ALPHA_TO_COVERAGE)}function Et(N){if(D!==N){if(N)e.frontFace(e.CW);else e.frontFace(e.CCW);D=N}}function at(N){if(N!==Zl){if(re(e.CULL_FACE),N!==U)if(N===ia)e.cullFace(e.BACK);else if(N===Jl)e.cullFace(e.FRONT);else e.cullFace(e.FRONT_AND_BACK)}else Te(e.CULL_FACE);U=N}function Ut(N){if(N!==J){if(G)e.lineWidth(N);J=N}}function _t(N,oe,Y){if(N){if(re(e.POLYGON_OFFSET_FILL),C!==oe||V!==Y){if(C=oe,V=Y,a.getReversed())oe=-oe;e.polygonOffset(oe,Y)}}else Te(e.POLYGON_OFFSET_FILL)}function xt(N){if(N)re(e.SCISSOR_TEST);else Te(e.SCISSOR_TEST)}function P(N){if(N===void 0)N=e.TEXTURE0+K-1;if(j!==N)e.activeTexture(N),j=N}function Ft(N,oe,Y){if(Y===void 0)if(j===null)Y=e.TEXTURE0+K-1;else Y=j;let le=te[Y];if(le===void 0)le={type:void 0,texture:void 0},te[Y]=le;if(le.type!==N||le.texture!==oe){if(j!==Y)e.activeTexture(Y),j=Y;e.bindTexture(N,oe||ie[N]),le.type=N,le.texture=oe}}function Ze(){let N=te[j];if(N!==void 0&&N.type!==void 0)e.bindTexture(N.type,null),N.type=void 0,N.texture=void 0}function ct(){try{e.compressedTexImage2D(...arguments)}catch(N){Pe("WebGLState:",N)}}function y(){try{e.compressedTexImage3D(...arguments)}catch(N){Pe("WebGLState:",N)}}function g(){try{e.texSubImage2D(...arguments)}catch(N){Pe("WebGLState:",N)}}function R(){try{e.texSubImage3D(...arguments)}catch(N){Pe("WebGLState:",N)}}function z(){try{e.compressedTexSubImage2D(...arguments)}catch(N){Pe("WebGLState:",N)}}function ee(){try{e.compressedTexSubImage3D(...arguments)}catch(N){Pe("WebGLState:",N)}}function ae(){try{e.texStorage2D(...arguments)}catch(N){Pe("WebGLState:",N)}}function ce(){try{e.texStorage3D(...arguments)}catch(N){Pe("WebGLState:",N)}}function W(){try{e.texImage2D(...arguments)}catch(N){Pe("WebGLState:",N)}}function Z(){try{e.texImage3D(...arguments)}catch(N){Pe("WebGLState:",N)}}function me(N){if(d[N]!==void 0)return d[N];else return e.getParameter(N)}function Me(N,oe){if(d[N]!==oe)e.pixelStorei(N,oe),d[N]=oe}function he(N){if(it.equals(N)===!1)e.scissor(N.x,N.y,N.z,N.w),it.copy(N)}function se(N){if(Oe.equals(N)===!1)e.viewport(N.x,N.y,N.z,N.w),Oe.copy(N)}function we(N,oe){let Y=l.get(oe);if(Y===void 0)Y=new WeakMap,l.set(oe,Y);let le=Y.get(N);if(le===void 0)le=e.getUniformBlockIndex(oe,N.name),Y.set(N,le)}function Ae(N,oe){let le=l.get(oe).get(N);if(c.get(oe)!==le)e.uniformBlockBinding(oe,le,N.__bindingPointIndex),c.set(oe,le)}function $e(){e.disable(e.BLEND),e.disable(e.CULL_FACE),e.disable(e.DEPTH_TEST),e.disable(e.POLYGON_OFFSET_FILL),e.disable(e.SCISSOR_TEST),e.disable(e.STENCIL_TEST),e.disable(e.SAMPLE_ALPHA_TO_COVERAGE),e.blendEquation(e.FUNC_ADD),e.blendFunc(e.ONE,e.ZERO),e.blendFuncSeparate(e.ONE,e.ZERO,e.ONE,e.ZERO),e.blendColor(0,0,0,0),e.colorMask(!0,!0,!0,!0),e.clearColor(0,0,0,0),e.depthMask(!0),e.depthFunc(e.LESS),a.setReversed(!1),e.clearDepth(1),e.stencilMask(4294967295),e.stencilFunc(e.ALWAYS,0,4294967295),e.stencilOp(e.KEEP,e.KEEP,e.KEEP),e.clearStencil(0),e.cullFace(e.BACK),e.frontFace(e.CCW),e.polygonOffset(0,0),e.activeTexture(e.TEXTURE0),e.bindFramebuffer(e.FRAMEBUFFER,null),e.bindFramebuffer(e.DRAW_FRAMEBUFFER,null),e.bindFramebuffer(e.READ_FRAMEBUFFER,null),e.useProgram(null),e.lineWidth(1),e.scissor(0,0,e.canvas.width,e.canvas.height),e.viewport(0,0,e.canvas.width,e.canvas.height),e.pixelStorei(e.PACK_ALIGNMENT,4),e.pixelStorei(e.UNPACK_ALIGNMENT,4),e.pixelStorei(e.UNPACK_FLIP_Y_WEBGL,!1),e.pixelStorei(e.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),e.pixelStorei(e.UNPACK_COLORSPACE_CONVERSION_WEBGL,e.BROWSER_DEFAULT_WEBGL),e.pixelStorei(e.PACK_ROW_LENGTH,0),e.pixelStorei(e.PACK_SKIP_PIXELS,0),e.pixelStorei(e.PACK_SKIP_ROWS,0),e.pixelStorei(e.UNPACK_ROW_LENGTH,0),e.pixelStorei(e.UNPACK_IMAGE_HEIGHT,0),e.pixelStorei(e.UNPACK_SKIP_PIXELS,0),e.pixelStorei(e.UNPACK_SKIP_ROWS,0),e.pixelStorei(e.UNPACK_SKIP_IMAGES,0),u={},d={},j=null,te={},h={},m=new WeakMap,v=[],b=null,p=!1,f=null,T=null,I=null,S=null,w=null,E=null,A=null,x=new qe(0,0,0),M=0,H=!1,D=null,U=null,J=null,C=null,V=null,it.set(0,0,e.canvas.width,e.canvas.height),Oe.set(0,0,e.canvas.width,e.canvas.height),r.reset(),a.reset(),o.reset()}return{buffers:{color:r,depth:a,stencil:o},enable:re,disable:Te,bindFramebuffer:Ie,drawBuffers:be,useProgram:gt,setBlending:je,setMaterial:Ve,setFlipSided:Et,setCullFace:at,setLineWidth:Ut,setPolygonOffset:_t,setScissorTest:xt,activeTexture:P,bindTexture:Ft,unbindTexture:Ze,compressedTexImage2D:ct,compressedTexImage3D:y,texImage2D:W,texImage3D:Z,pixelStorei:Me,getParameter:me,updateUBOMapping:we,uniformBlockBinding:Ae,texStorage2D:ae,texStorage3D:ce,texSubImage2D:g,texSubImage3D:R,compressedTexSubImage2D:z,compressedTexSubImage3D:ee,scissor:he,viewport:se,reset:$e}}function Pg(e,t,n,i,s,r,a){let o=t.has("WEBGL_multisampled_render_to_texture")?t.get("WEBGL_multisampled_render_to_texture"):null,c=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),l=new Xe,u=new WeakMap,d=new Set,h,m=new WeakMap,v=!1;try{v=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch(y){}function b(y,g){return v?new OffscreenCanvas(y,g):Ji("canvas")}function p(y,g,R){let z=1,ee=ct(y);if(ee.width>R||ee.height>R)z=R/Math.max(ee.width,ee.height);if(z<1)if(typeof HTMLImageElement<"u"&&y instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&y instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&y instanceof ImageBitmap||typeof VideoFrame<"u"&&y instanceof VideoFrame){let ae=Math.floor(z*ee.width),ce=Math.floor(z*ee.height);if(h===void 0)h=b(ae,ce);let W=g?b(ae,ce):h;return W.width=ae,W.height=ce,W.getContext("2d").drawImage(y,0,0,ae,ce),Ce("WebGLRenderer: Texture has been resized from ("+ee.width+"x"+ee.height+") to ("+ae+"x"+ce+")."),W}else{if("data"in y)Ce("WebGLRenderer: Image in DataTexture is too big ("+ee.width+"x"+ee.height+").");return y}return y}function f(y){return y.generateMipmaps}function T(y){e.generateMipmap(y)}function I(y){if(y.isWebGLCubeRenderTarget)return e.TEXTURE_CUBE_MAP;if(y.isWebGL3DRenderTarget)return e.TEXTURE_3D;if(y.isWebGLArrayRenderTarget||y.isCompressedArrayTexture)return e.TEXTURE_2D_ARRAY;return e.TEXTURE_2D}function S(y,g,R,z,ee,ae=!1){if(y!==null){if(e[y]!==void 0)return e[y];Ce("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+y+"'")}let ce;if(z){if(ce=t.get("EXT_texture_norm16"),!ce)Ce("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension")}let W=g;if(g===e.RED){if(R===e.FLOAT)W=e.R32F;if(R===e.HALF_FLOAT)W=e.R16F;if(R===e.UNSIGNED_BYTE)W=e.R8;if(R===e.UNSIGNED_SHORT&&ce)W=ce.R16_EXT;if(R===e.SHORT&&ce)W=ce.R16_SNORM_EXT}if(g===e.RED_INTEGER){if(R===e.UNSIGNED_BYTE)W=e.R8UI;if(R===e.UNSIGNED_SHORT)W=e.R16UI;if(R===e.UNSIGNED_INT)W=e.R32UI;if(R===e.BYTE)W=e.R8I;if(R===e.SHORT)W=e.R16I;if(R===e.INT)W=e.R32I}if(g===e.RG){if(R===e.FLOAT)W=e.RG32F;if(R===e.HALF_FLOAT)W=e.RG16F;if(R===e.UNSIGNED_BYTE)W=e.RG8;if(R===e.UNSIGNED_SHORT&&ce)W=ce.RG16_EXT;if(R===e.SHORT&&ce)W=ce.RG16_SNORM_EXT}if(g===e.RG_INTEGER){if(R===e.UNSIGNED_BYTE)W=e.RG8UI;if(R===e.UNSIGNED_SHORT)W=e.RG16UI;if(R===e.UNSIGNED_INT)W=e.RG32UI;if(R===e.BYTE)W=e.RG8I;if(R===e.SHORT)W=e.RG16I;if(R===e.INT)W=e.RG32I}if(g===e.RGB_INTEGER){if(R===e.UNSIGNED_BYTE)W=e.RGB8UI;if(R===e.UNSIGNED_SHORT)W=e.RGB16UI;if(R===e.UNSIGNED_INT)W=e.RGB32UI;if(R===e.BYTE)W=e.RGB8I;if(R===e.SHORT)W=e.RGB16I;if(R===e.INT)W=e.RGB32I}if(g===e.RGBA_INTEGER){if(R===e.UNSIGNED_BYTE)W=e.RGBA8UI;if(R===e.UNSIGNED_SHORT)W=e.RGBA16UI;if(R===e.UNSIGNED_INT)W=e.RGBA32UI;if(R===e.BYTE)W=e.RGBA8I;if(R===e.SHORT)W=e.RGBA16I;if(R===e.INT)W=e.RGBA32I}if(g===e.RGB){if(R===e.UNSIGNED_SHORT&&ce)W=ce.RGB16_EXT;if(R===e.SHORT&&ce)W=ce.RGB16_SNORM_EXT;if(R===e.UNSIGNED_INT_5_9_9_9_REV)W=e.RGB9_E5;if(R===e.UNSIGNED_INT_10F_11F_11F_REV)W=e.R11F_G11F_B10F}if(g===e.RGBA){let Z=ae?Qa:ke.getTransfer(ee);if(R===e.FLOAT)W=e.RGBA32F;if(R===e.HALF_FLOAT)W=e.RGBA16F;if(R===e.UNSIGNED_BYTE)W=Z===nt?e.SRGB8_ALPHA8:e.RGBA8;if(R===e.UNSIGNED_SHORT&&ce)W=ce.RGBA16_EXT;if(R===e.SHORT&&ce)W=ce.RGBA16_SNORM_EXT;if(R===e.UNSIGNED_SHORT_4_4_4_4)W=e.RGBA4;if(R===e.UNSIGNED_SHORT_5_5_5_1)W=e.RGB5_A1}if(W===e.R16F||W===e.R32F||W===e.RG16F||W===e.RG32F||W===e.RGBA16F||W===e.RGBA32F)t.get("EXT_color_buffer_float");return W}function w(y,g){let R;if(y){if(g===null||g===Un||g===Li)R=e.DEPTH24_STENCIL8;else if(g===Sn)R=e.DEPTH32F_STENCIL8;else if(g===ts)R=e.DEPTH24_STENCIL8,Ce("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")}else if(g===null||g===Un||g===Li)R=e.DEPTH_COMPONENT24;else if(g===Sn)R=e.DEPTH_COMPONENT32F;else if(g===ts)R=e.DEPTH_COMPONENT16;return R}function E(y,g){if(f(y)===!0||y.isFramebufferTexture&&y.minFilter!==Dn&&y.minFilter!==zt)return Math.log2(Math.max(g.width,g.height))+1;else if(y.mipmaps!==void 0&&y.mipmaps.length>0)return y.mipmaps.length;else if(y.isCompressedTexture&&Array.isArray(y.image))return g.mipmaps.length;else return 1}function A(y){let g=y.target;if(g.removeEventListener("dispose",A),M(g),g.isVideoTexture)u.delete(g);if(g.isHTMLTexture)d.delete(g)}function x(y){let g=y.target;g.removeEventListener("dispose",x),D(g)}function M(y){let g=i.get(y);if(g.__webglInit===void 0)return;let R=y.source,z=m.get(R);if(z){let ee=z[g.__cacheKey];if(ee.usedTimes--,ee.usedTimes===0)H(y);if(Object.keys(z).length===0)m.delete(R)}i.remove(y)}function H(y){let g=i.get(y);e.deleteTexture(g.__webglTexture);let R=y.source,z=m.get(R);delete z[g.__cacheKey],a.memory.textures--}function D(y){let g=i.get(y);if(y.depthTexture)y.depthTexture.dispose(),i.remove(y.depthTexture);if(y.isWebGLCubeRenderTarget)for(let z=0;z<6;z++){if(Array.isArray(g.__webglFramebuffer[z]))for(let ee=0;ee<g.__webglFramebuffer[z].length;ee++)e.deleteFramebuffer(g.__webglFramebuffer[z][ee]);else e.deleteFramebuffer(g.__webglFramebuffer[z]);if(g.__webglDepthbuffer)e.deleteRenderbuffer(g.__webglDepthbuffer[z])}else{if(Array.isArray(g.__webglFramebuffer))for(let z=0;z<g.__webglFramebuffer.length;z++)e.deleteFramebuffer(g.__webglFramebuffer[z]);else e.deleteFramebuffer(g.__webglFramebuffer);if(g.__webglDepthbuffer)e.deleteRenderbuffer(g.__webglDepthbuffer);if(g.__webglMultisampledFramebuffer)e.deleteFramebuffer(g.__webglMultisampledFramebuffer);if(g.__webglColorRenderbuffer){for(let z=0;z<g.__webglColorRenderbuffer.length;z++)if(g.__webglColorRenderbuffer[z])e.deleteRenderbuffer(g.__webglColorRenderbuffer[z])}if(g.__webglDepthRenderbuffer)e.deleteRenderbuffer(g.__webglDepthRenderbuffer)}let R=y.textures;for(let z=0,ee=R.length;z<ee;z++){let ae=i.get(R[z]);if(ae.__webglTexture)e.deleteTexture(ae.__webglTexture),a.memory.textures--;i.remove(R[z])}i.remove(y)}let U=0;function J(){U=0}function C(){return U}function V(y){U=y}function K(){let y=U;if(y>=s.maxTextures)Ce("WebGLTextures: Trying to use "+(y+1)+" texture units while this GPU supports only "+s.maxTextures);return U+=1,y}function G(y){let g=[];return g.push(y.wrapS),g.push(y.wrapT),g.push(y.wrapR||0),g.push(y.magFilter),g.push(y.minFilter),g.push(y.anisotropy),g.push(y.internalFormat),g.push(y.format),g.push(y.type),g.push(y.generateMipmaps),g.push(y.premultiplyAlpha),g.push(y.flipY),g.push(y.unpackAlignment),g.push(y.colorSpace),g.join()}function ne(y,g){let R=i.get(y);if(y.isVideoTexture)Ft(y);if(y.isRenderTargetTexture===!1&&y.isExternalTexture!==!0&&y.version>0&&R.__version!==y.version){let z=y.image;if(z===null)Ce("WebGLRenderer: Texture marked for update but no image data found.");else if(z.complete===!1)Ce("WebGLRenderer: Texture marked for update but image is incomplete");else{Te(R,y,g);return}}else if(y.isExternalTexture)R.__webglTexture=y.sourceTexture?y.sourceTexture:null;n.bindTexture(e.TEXTURE_2D,R.__webglTexture,e.TEXTURE0+g)}function X(y,g){let R=i.get(y);if(y.isRenderTargetTexture===!1&&y.version>0&&R.__version!==y.version){Te(R,y,g);return}else if(y.isExternalTexture)R.__webglTexture=y.sourceTexture?y.sourceTexture:null;n.bindTexture(e.TEXTURE_2D_ARRAY,R.__webglTexture,e.TEXTURE0+g)}function j(y,g){let R=i.get(y);if(y.isRenderTargetTexture===!1&&y.version>0&&R.__version!==y.version){Te(R,y,g);return}n.bindTexture(e.TEXTURE_3D,R.__webglTexture,e.TEXTURE0+g)}function te(y,g){let R=i.get(y);if(y.isCubeDepthTexture!==!0&&y.version>0&&R.__version!==y.version){Ie(R,y,g);return}n.bindTexture(e.TEXTURE_CUBE_MAP,R.__webglTexture,e.TEXTURE0+g)}let Re={[Cc]:e.REPEAT,[Ws]:e.CLAMP_TO_EDGE,[Rc]:e.MIRRORED_REPEAT},Ee={[Dn]:e.NEAREST,[Ic]:e.NEAREST_MIPMAP_NEAREST,[es]:e.NEAREST_MIPMAP_LINEAR,[zt]:e.LINEAR,[Xs]:e.LINEAR_MIPMAP_NEAREST,[qn]:e.LINEAR_MIPMAP_LINEAR},it={[kc]:e.NEVER,[Xc]:e.ALWAYS,[Gc]:e.LESS,[js]:e.LEQUAL,[Hc]:e.EQUAL,[Qs]:e.GEQUAL,[Vc]:e.GREATER,[Wc]:e.NOTEQUAL};function Oe(y,g){if(g.type===Sn&&t.has("OES_texture_float_linear")===!1&&(g.magFilter===zt||g.magFilter===Xs||g.magFilter===es||g.magFilter===qn||g.minFilter===zt||g.minFilter===Xs||g.minFilter===es||g.minFilter===qn))Ce("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device.");if(e.texParameteri(y,e.TEXTURE_WRAP_S,Re[g.wrapS]),e.texParameteri(y,e.TEXTURE_WRAP_T,Re[g.wrapT]),y===e.TEXTURE_3D||y===e.TEXTURE_2D_ARRAY)e.texParameteri(y,e.TEXTURE_WRAP_R,Re[g.wrapR]);if(e.texParameteri(y,e.TEXTURE_MAG_FILTER,Ee[g.magFilter]),e.texParameteri(y,e.TEXTURE_MIN_FILTER,Ee[g.minFilter]),g.compareFunction)e.texParameteri(y,e.TEXTURE_COMPARE_MODE,e.COMPARE_REF_TO_TEXTURE),e.texParameteri(y,e.TEXTURE_COMPARE_FUNC,it[g.compareFunction]);if(t.has("EXT_texture_filter_anisotropic")===!0){if(g.magFilter===Dn)return;if(g.minFilter!==es&&g.minFilter!==qn)return;if(g.type===Sn&&t.has("OES_texture_float_linear")===!1)return;if(g.anisotropy>1||i.get(g).__currentAnisotropy){let R=t.get("EXT_texture_filter_anisotropic");e.texParameterf(y,R.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(g.anisotropy,s.getMaxAnisotropy())),i.get(g).__currentAnisotropy=g.anisotropy}}}function q(y,g){let R=!1;if(y.__webglInit===void 0)y.__webglInit=!0,g.addEventListener("dispose",A);let z=g.source,ee=m.get(z);if(ee===void 0)ee={},m.set(z,ee);let ae=G(g);if(ae!==y.__cacheKey){if(ee[ae]===void 0)ee[ae]={texture:e.createTexture(),usedTimes:0},a.memory.textures++,R=!0;ee[ae].usedTimes++;let ce=ee[y.__cacheKey];if(ce!==void 0){if(ee[y.__cacheKey].usedTimes--,ce.usedTimes===0)H(g)}y.__cacheKey=ae,y.__webglTexture=ee[ae].texture}return R}function ie(y,g,R){return Math.floor(Math.floor(y/R)/g)}function re(y,g,R,z){let ae=y.updateRanges;if(ae.length===0)n.texSubImage2D(e.TEXTURE_2D,0,0,0,g.width,g.height,R,z,g.data);else{ae.sort((Me,he)=>Me.start-he.start);let ce=0;for(let Me=1;Me<ae.length;Me++){let he=ae[ce],se=ae[Me],we=he.start+he.count,Ae=ie(se.start,g.width,4),$e=ie(he.start,g.width,4);if(se.start<=we+1&&Ae===$e&&ie(se.start+se.count-1,g.width,4)===Ae)he.count=Math.max(he.count,se.start+se.count-he.start);else++ce,ae[ce]=se}ae.length=ce+1;let W=n.getParameter(e.UNPACK_ROW_LENGTH),Z=n.getParameter(e.UNPACK_SKIP_PIXELS),me=n.getParameter(e.UNPACK_SKIP_ROWS);n.pixelStorei(e.UNPACK_ROW_LENGTH,g.width);for(let Me=0,he=ae.length;Me<he;Me++){let se=ae[Me],we=Math.floor(se.start/4),Ae=Math.ceil(se.count/4),$e=we%g.width,N=Math.floor(we/g.width),oe=Ae,Y=1;n.pixelStorei(e.UNPACK_SKIP_PIXELS,$e),n.pixelStorei(e.UNPACK_SKIP_ROWS,N),n.texSubImage2D(e.TEXTURE_2D,0,$e,N,oe,1,R,z,g.data)}y.clearUpdateRanges(),n.pixelStorei(e.UNPACK_ROW_LENGTH,W),n.pixelStorei(e.UNPACK_SKIP_PIXELS,Z),n.pixelStorei(e.UNPACK_SKIP_ROWS,me)}}function Te(y,g,R){let z=e.TEXTURE_2D;if(g.isDataArrayTexture||g.isCompressedArrayTexture)z=e.TEXTURE_2D_ARRAY;if(g.isData3DTexture)z=e.TEXTURE_3D;let ee=q(y,g),ae=g.source;n.bindTexture(z,y.__webglTexture,e.TEXTURE0+R);let ce=i.get(ae);if(ae.version!==ce.__version||ee===!0){if(n.activeTexture(e.TEXTURE0+R),(typeof ImageBitmap<"u"&&g.image instanceof ImageBitmap)===!1){let Y=ke.getPrimaries(ke.workingColorSpace),le=g.colorSpace===Jn?null:ke.getPrimaries(g.colorSpace),ge=g.colorSpace===Jn||Y===le?e.NONE:e.BROWSER_DEFAULT_WEBGL;n.pixelStorei(e.UNPACK_FLIP_Y_WEBGL,g.flipY),n.pixelStorei(e.UNPACK_PREMULTIPLY_ALPHA_WEBGL,g.premultiplyAlpha),n.pixelStorei(e.UNPACK_COLORSPACE_CONVERSION_WEBGL,ge)}n.pixelStorei(e.UNPACK_ALIGNMENT,g.unpackAlignment);let Z=p(g.image,!1,s.maxTextureSize);Z=Ze(g,Z);let me=r.convert(g.format,g.colorSpace),Me=r.convert(g.type),he=S(g.internalFormat,me,Me,g.normalized,g.colorSpace,g.isVideoTexture);Oe(z,g);let se,we=g.mipmaps,Ae=g.isVideoTexture!==!0,$e=ce.__version===void 0||ee===!0,N=ae.dataReady,oe=E(g,Z);if(g.isDepthTexture){if(he=w(g.format===Yn,g.type),$e)if(Ae)n.texStorage2D(e.TEXTURE_2D,1,he,Z.width,Z.height);else n.texImage2D(e.TEXTURE_2D,0,he,Z.width,Z.height,0,me,Me,null)}else if(g.isDataTexture)if(we.length>0){if(Ae&&$e)n.texStorage2D(e.TEXTURE_2D,oe,he,we[0].width,we[0].height);for(let Y=0,le=we.length;Y<le;Y++)if(se=we[Y],Ae){if(N)n.texSubImage2D(e.TEXTURE_2D,Y,0,0,se.width,se.height,me,Me,se.data)}else n.texImage2D(e.TEXTURE_2D,Y,he,se.width,se.height,0,me,Me,se.data);g.generateMipmaps=!1}else if(Ae){if($e)n.texStorage2D(e.TEXTURE_2D,oe,he,Z.width,Z.height);if(N)re(g,Z,me,Me)}else n.texImage2D(e.TEXTURE_2D,0,he,Z.width,Z.height,0,me,Me,Z.data);else if(g.isCompressedTexture)if(g.isCompressedArrayTexture){if(Ae&&$e)n.texStorage3D(e.TEXTURE_2D_ARRAY,oe,he,we[0].width,we[0].height,Z.depth);for(let Y=0,le=we.length;Y<le;Y++)if(se=we[Y],g.format!==un)if(me!==null)if(Ae){if(N)if(g.layerUpdates.size>0){let ge=Co(se.width,se.height,g.format,g.type);for(let Q of g.layerUpdates){let de=se.data.subarray(Q*ge/se.data.BYTES_PER_ELEMENT,(Q+1)*ge/se.data.BYTES_PER_ELEMENT);n.compressedTexSubImage3D(e.TEXTURE_2D_ARRAY,Y,0,0,Q,se.width,se.height,1,me,de)}}else n.compressedTexSubImage3D(e.TEXTURE_2D_ARRAY,Y,0,0,0,se.width,se.height,Z.depth,me,se.data)}else n.compressedTexImage3D(e.TEXTURE_2D_ARRAY,Y,he,se.width,se.height,Z.depth,0,se.data,0,0);else Ce("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else if(Ae){if(N)n.texSubImage3D(e.TEXTURE_2D_ARRAY,Y,0,0,0,se.width,se.height,Z.depth,me,Me,se.data)}else n.texImage3D(e.TEXTURE_2D_ARRAY,Y,he,se.width,se.height,Z.depth,0,me,Me,se.data);if(g.layerUpdates.size>0)g.clearLayerUpdates()}else{if(Ae&&$e)n.texStorage2D(e.TEXTURE_2D,oe,he,we[0].width,we[0].height);for(let Y=0,le=we.length;Y<le;Y++)if(se=we[Y],g.format!==un)if(me!==null)if(Ae){if(N)n.compressedTexSubImage2D(e.TEXTURE_2D,Y,0,0,se.width,se.height,me,se.data)}else n.compressedTexImage2D(e.TEXTURE_2D,Y,he,se.width,se.height,0,se.data);else Ce("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else if(Ae){if(N)n.texSubImage2D(e.TEXTURE_2D,Y,0,0,se.width,se.height,me,Me,se.data)}else n.texImage2D(e.TEXTURE_2D,Y,he,se.width,se.height,0,me,Me,se.data)}else if(g.isDataArrayTexture)if(Ae){if($e)n.texStorage3D(e.TEXTURE_2D_ARRAY,oe,he,Z.width,Z.height,Z.depth);if(N)if(g.layerUpdates.size>0){let Y=Co(Z.width,Z.height,g.format,g.type);for(let le of g.layerUpdates){let ge=Z.data.subarray(le*Y/Z.data.BYTES_PER_ELEMENT,(le+1)*Y/Z.data.BYTES_PER_ELEMENT);n.texSubImage3D(e.TEXTURE_2D_ARRAY,0,0,0,le,Z.width,Z.height,1,me,Me,ge)}g.clearLayerUpdates()}else n.texSubImage3D(e.TEXTURE_2D_ARRAY,0,0,0,0,Z.width,Z.height,Z.depth,me,Me,Z.data)}else n.texImage3D(e.TEXTURE_2D_ARRAY,0,he,Z.width,Z.height,Z.depth,0,me,Me,Z.data);else if(g.isData3DTexture)if(Ae){if($e)n.texStorage3D(e.TEXTURE_3D,oe,he,Z.width,Z.height,Z.depth);if(N)n.texSubImage3D(e.TEXTURE_3D,0,0,0,0,Z.width,Z.height,Z.depth,me,Me,Z.data)}else n.texImage3D(e.TEXTURE_3D,0,he,Z.width,Z.height,Z.depth,0,me,Me,Z.data);else if(g.isFramebufferTexture){if($e)if(Ae)n.texStorage2D(e.TEXTURE_2D,oe,he,Z.width,Z.height);else{let Y=Z.width,le=Z.height;for(let ge=0;ge<oe;ge++)n.texImage2D(e.TEXTURE_2D,ge,he,Y,le,0,me,Me,null),Y>>=1,le>>=1}}else if(g.isHTMLTexture){if("texElementImage2D"in e){let Y=e.canvas;if(!Y.hasAttribute("layoutsubtree"))Y.setAttribute("layoutsubtree","true");if(Z.parentNode!==Y){Y.appendChild(Z),d.add(g),Y.onpaint=(le)=>{let ge=le.changedElements;for(let Q of d)if(ge.includes(Q.image))Q.needsUpdate=!0},Y.requestPaint();return}if(e.texElementImage2D.length===3)e.texElementImage2D(e.TEXTURE_2D,e.RGBA8,Z);else{let{RGBA:ge,RGBA:Q,UNSIGNED_BYTE:de}=e;e.texElementImage2D(e.TEXTURE_2D,0,ge,Q,de,Z)}e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MIN_FILTER,e.LINEAR),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_WRAP_S,e.CLAMP_TO_EDGE),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_WRAP_T,e.CLAMP_TO_EDGE)}}else if(we.length>0){if(Ae&&$e){let Y=ct(we[0]);n.texStorage2D(e.TEXTURE_2D,oe,he,Y.width,Y.height)}for(let Y=0,le=we.length;Y<le;Y++)if(se=we[Y],Ae){if(N)n.texSubImage2D(e.TEXTURE_2D,Y,0,0,me,Me,se)}else n.texImage2D(e.TEXTURE_2D,Y,he,me,Me,se);g.generateMipmaps=!1}else if(Ae){if($e){let Y=ct(Z);n.texStorage2D(e.TEXTURE_2D,oe,he,Y.width,Y.height)}if(N)n.texSubImage2D(e.TEXTURE_2D,0,0,0,me,Me,Z)}else n.texImage2D(e.TEXTURE_2D,0,he,me,Me,Z);if(f(g))T(z);if(ce.__version=ae.version,g.onUpdate)g.onUpdate(g)}y.__version=g.version}function Ie(y,g,R){if(g.image.length!==6)return;let z=q(y,g),ee=g.source;n.bindTexture(e.TEXTURE_CUBE_MAP,y.__webglTexture,e.TEXTURE0+R);let ae=i.get(ee);if(ee.version!==ae.__version||z===!0){n.activeTexture(e.TEXTURE0+R);let ce=ke.getPrimaries(ke.workingColorSpace),W=g.colorSpace===Jn?null:ke.getPrimaries(g.colorSpace),Z=g.colorSpace===Jn||ce===W?e.NONE:e.BROWSER_DEFAULT_WEBGL;n.pixelStorei(e.UNPACK_FLIP_Y_WEBGL,g.flipY),n.pixelStorei(e.UNPACK_PREMULTIPLY_ALPHA_WEBGL,g.premultiplyAlpha),n.pixelStorei(e.UNPACK_ALIGNMENT,g.unpackAlignment),n.pixelStorei(e.UNPACK_COLORSPACE_CONVERSION_WEBGL,Z);let me=g.isCompressedTexture||g.image[0].isCompressedTexture,Me=g.image[0]&&g.image[0].isDataTexture,he=[];for(let Q=0;Q<6;Q++){if(!me&&!Me)he[Q]=p(g.image[Q],!0,s.maxCubemapSize);else he[Q]=Me?g.image[Q].image:g.image[Q];he[Q]=Ze(g,he[Q])}let se=he[0],we=r.convert(g.format,g.colorSpace),Ae=r.convert(g.type),$e=S(g.internalFormat,we,Ae,g.normalized,g.colorSpace),N=g.isVideoTexture!==!0,oe=ae.__version===void 0||z===!0,Y=ee.dataReady,le=E(g,se);Oe(e.TEXTURE_CUBE_MAP,g);let ge;if(me){if(N&&oe)n.texStorage2D(e.TEXTURE_CUBE_MAP,le,$e,se.width,se.height);for(let Q=0;Q<6;Q++){ge=he[Q].mipmaps;for(let de=0;de<ge.length;de++){let Ne=ge[de];if(g.format!==un)if(we!==null)if(N){if(Y)n.compressedTexSubImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,de,0,0,Ne.width,Ne.height,we,Ne.data)}else n.compressedTexImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,de,$e,Ne.width,Ne.height,0,Ne.data);else Ce("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()");else if(N){if(Y)n.texSubImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,de,0,0,Ne.width,Ne.height,we,Ae,Ne.data)}else n.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,de,$e,Ne.width,Ne.height,0,we,Ae,Ne.data)}}}else{if(ge=g.mipmaps,N&&oe){if(ge.length>0)le++;let Q=ct(he[0]);n.texStorage2D(e.TEXTURE_CUBE_MAP,le,$e,Q.width,Q.height)}for(let Q=0;Q<6;Q++)if(Me){if(N){if(Y)n.texSubImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,0,0,0,he[Q].width,he[Q].height,we,Ae,he[Q].data)}else n.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,0,$e,he[Q].width,he[Q].height,0,we,Ae,he[Q].data);for(let de=0;de<ge.length;de++){let st=ge[de].image[Q].image;if(N){if(Y)n.texSubImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,de+1,0,0,st.width,st.height,we,Ae,st.data)}else n.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,de+1,$e,st.width,st.height,0,we,Ae,st.data)}}else{if(N){if(Y)n.texSubImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,0,0,0,we,Ae,he[Q])}else n.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,0,$e,we,Ae,he[Q]);for(let de=0;de<ge.length;de++){let Ne=ge[de];if(N){if(Y)n.texSubImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,de+1,0,0,we,Ae,Ne.image[Q])}else n.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+Q,de+1,$e,we,Ae,Ne.image[Q])}}}if(f(g))T(e.TEXTURE_CUBE_MAP);if(ae.__version=ee.version,g.onUpdate)g.onUpdate(g)}y.__version=g.version}function be(y,g,R,z,ee,ae){let ce=r.convert(R.format,R.colorSpace),W=r.convert(R.type),Z=S(R.internalFormat,ce,W,R.normalized,R.colorSpace),me=i.get(g),Me=i.get(R);if(Me.__renderTarget=g,!me.__hasExternalTextures){let he=Math.max(1,g.width>>ae),se=Math.max(1,g.height>>ae);if(ee===e.TEXTURE_3D||ee===e.TEXTURE_2D_ARRAY)n.texImage3D(ee,ae,Z,he,se,g.depth,0,ce,W,null);else n.texImage2D(ee,ae,Z,he,se,0,ce,W,null)}if(n.bindFramebuffer(e.FRAMEBUFFER,y),P(g))o.framebufferTexture2DMultisampleEXT(e.FRAMEBUFFER,z,ee,Me.__webglTexture,0,xt(g));else if(ee===e.TEXTURE_2D||ee>=e.TEXTURE_CUBE_MAP_POSITIVE_X&&ee<=e.TEXTURE_CUBE_MAP_NEGATIVE_Z)e.framebufferTexture2D(e.FRAMEBUFFER,z,ee,Me.__webglTexture,ae);n.bindFramebuffer(e.FRAMEBUFFER,null)}function gt(y,g,R){if(e.bindRenderbuffer(e.RENDERBUFFER,y),g.depthBuffer){let z=g.depthTexture,ee=z&&z.isDepthTexture?z.type:null,ae=w(g.stencilBuffer,ee),ce=g.stencilBuffer?e.DEPTH_STENCIL_ATTACHMENT:e.DEPTH_ATTACHMENT;if(P(g))o.renderbufferStorageMultisampleEXT(e.RENDERBUFFER,xt(g),ae,g.width,g.height);else if(R)e.renderbufferStorageMultisample(e.RENDERBUFFER,xt(g),ae,g.width,g.height);else e.renderbufferStorage(e.RENDERBUFFER,ae,g.width,g.height);e.framebufferRenderbuffer(e.FRAMEBUFFER,ce,e.RENDERBUFFER,y)}else{let z=g.textures;for(let ee=0;ee<z.length;ee++){let ae=z[ee],ce=r.convert(ae.format,ae.colorSpace),W=r.convert(ae.type),Z=S(ae.internalFormat,ce,W,ae.normalized,ae.colorSpace);if(P(g))o.renderbufferStorageMultisampleEXT(e.RENDERBUFFER,xt(g),Z,g.width,g.height);else if(R)e.renderbufferStorageMultisample(e.RENDERBUFFER,xt(g),Z,g.width,g.height);else e.renderbufferStorage(e.RENDERBUFFER,Z,g.width,g.height)}}e.bindRenderbuffer(e.RENDERBUFFER,null)}function ze(y,g,R){let z=g.isWebGLCubeRenderTarget===!0;if(n.bindFramebuffer(e.FRAMEBUFFER,y),!(g.depthTexture&&g.depthTexture.isDepthTexture))throw Error("THREE.WebGLTextures: renderTarget.depthTexture must be an instance of THREE.DepthTexture.");let ee=i.get(g.depthTexture);if(ee.__renderTarget=g,!ee.__webglTexture||g.depthTexture.image.width!==g.width||g.depthTexture.image.height!==g.height)g.depthTexture.image.width=g.width,g.depthTexture.image.height=g.height,g.depthTexture.needsUpdate=!0;if(z){if(ee.__webglInit===void 0)ee.__webglInit=!0,g.depthTexture.addEventListener("dispose",A);if(ee.__webglTexture===void 0){ee.__webglTexture=e.createTexture(),n.bindTexture(e.TEXTURE_CUBE_MAP,ee.__webglTexture),Oe(e.TEXTURE_CUBE_MAP,g.depthTexture);let me=r.convert(g.depthTexture.format),Me=r.convert(g.depthTexture.type),he;if(g.depthTexture.format===$n)he=e.DEPTH_COMPONENT24;else if(g.depthTexture.format===Yn)he=e.DEPTH24_STENCIL8;for(let se=0;se<6;se++)e.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+se,0,he,g.width,g.height,0,me,Me,null)}}else ne(g.depthTexture,0);let ae=ee.__webglTexture,ce=xt(g),W=z?e.TEXTURE_CUBE_MAP_POSITIVE_X+R:e.TEXTURE_2D,Z=g.depthTexture.format===Yn?e.DEPTH_STENCIL_ATTACHMENT:e.DEPTH_ATTACHMENT;if(g.depthTexture.format===$n)if(P(g))o.framebufferTexture2DMultisampleEXT(e.FRAMEBUFFER,Z,W,ae,0,ce);else e.framebufferTexture2D(e.FRAMEBUFFER,Z,W,ae,0);else if(g.depthTexture.format===Yn)if(P(g))o.framebufferTexture2DMultisampleEXT(e.FRAMEBUFFER,Z,W,ae,0,ce);else e.framebufferTexture2D(e.FRAMEBUFFER,Z,W,ae,0);else throw Error("THREE.WebGLTextures: Unknown depthTexture format.")}function He(y){let g=i.get(y),R=y.isWebGLCubeRenderTarget===!0;if(g.__boundDepthTexture!==y.depthTexture){let z=y.depthTexture;if(g.__depthDisposeCallback)g.__depthDisposeCallback();if(z){let ee=()=>{delete g.__boundDepthTexture,delete g.__depthDisposeCallback,z.removeEventListener("dispose",ee)};z.addEventListener("dispose",ee),g.__depthDisposeCallback=ee}g.__boundDepthTexture=z}if(y.depthTexture&&!g.__autoAllocateDepthBuffer)if(R)for(let z=0;z<6;z++)ze(g.__webglFramebuffer[z],y,z);else{let z=y.texture.mipmaps;if(z&&z.length>0)ze(g.__webglFramebuffer[0],y,0);else ze(g.__webglFramebuffer,y,0)}else if(R){g.__webglDepthbuffer=[];for(let z=0;z<6;z++)if(n.bindFramebuffer(e.FRAMEBUFFER,g.__webglFramebuffer[z]),g.__webglDepthbuffer[z]===void 0)g.__webglDepthbuffer[z]=e.createRenderbuffer(),gt(g.__webglDepthbuffer[z],y,!1);else{let ee=y.stencilBuffer?e.DEPTH_STENCIL_ATTACHMENT:e.DEPTH_ATTACHMENT,ae=g.__webglDepthbuffer[z];e.bindRenderbuffer(e.RENDERBUFFER,ae),e.framebufferRenderbuffer(e.FRAMEBUFFER,ee,e.RENDERBUFFER,ae)}}else{let z=y.texture.mipmaps;if(z&&z.length>0)n.bindFramebuffer(e.FRAMEBUFFER,g.__webglFramebuffer[0]);else n.bindFramebuffer(e.FRAMEBUFFER,g.__webglFramebuffer);if(g.__webglDepthbuffer===void 0)g.__webglDepthbuffer=e.createRenderbuffer(),gt(g.__webglDepthbuffer,y,!1);else{let ee=y.stencilBuffer?e.DEPTH_STENCIL_ATTACHMENT:e.DEPTH_ATTACHMENT,ae=g.__webglDepthbuffer;e.bindRenderbuffer(e.RENDERBUFFER,ae),e.framebufferRenderbuffer(e.FRAMEBUFFER,ee,e.RENDERBUFFER,ae)}}n.bindFramebuffer(e.FRAMEBUFFER,null)}function je(y,g,R){let z=i.get(y);if(g!==void 0)be(z.__webglFramebuffer,y,y.texture,e.COLOR_ATTACHMENT0,e.TEXTURE_2D,0);if(R!==void 0)He(y)}function Ve(y){let g=y.texture,R=i.get(y),z=i.get(g);y.addEventListener("dispose",x);let ee=y.textures,ae=y.isWebGLCubeRenderTarget===!0,ce=ee.length>1;if(!ce){if(z.__webglTexture===void 0)z.__webglTexture=e.createTexture();z.__version=g.version,a.memory.textures++}if(ae){R.__webglFramebuffer=[];for(let W=0;W<6;W++)if(g.mipmaps&&g.mipmaps.length>0){R.__webglFramebuffer[W]=[];for(let Z=0;Z<g.mipmaps.length;Z++)R.__webglFramebuffer[W][Z]=e.createFramebuffer()}else R.__webglFramebuffer[W]=e.createFramebuffer()}else{if(g.mipmaps&&g.mipmaps.length>0){R.__webglFramebuffer=[];for(let W=0;W<g.mipmaps.length;W++)R.__webglFramebuffer[W]=e.createFramebuffer()}else R.__webglFramebuffer=e.createFramebuffer();if(ce)for(let W=0,Z=ee.length;W<Z;W++){let me=i.get(ee[W]);if(me.__webglTexture===void 0)me.__webglTexture=e.createTexture(),a.memory.textures++}if(y.samples>0&&P(y)===!1){R.__webglMultisampledFramebuffer=e.createFramebuffer(),R.__webglColorRenderbuffer=[],n.bindFramebuffer(e.FRAMEBUFFER,R.__webglMultisampledFramebuffer);for(let W=0;W<ee.length;W++){let Z=ee[W];R.__webglColorRenderbuffer[W]=e.createRenderbuffer(),e.bindRenderbuffer(e.RENDERBUFFER,R.__webglColorRenderbuffer[W]);let me=r.convert(Z.format,Z.colorSpace),Me=r.convert(Z.type),he=S(Z.internalFormat,me,Me,Z.normalized,Z.colorSpace,y.isXRRenderTarget===!0),se=xt(y);e.renderbufferStorageMultisample(e.RENDERBUFFER,se,he,y.width,y.height),e.framebufferRenderbuffer(e.FRAMEBUFFER,e.COLOR_ATTACHMENT0+W,e.RENDERBUFFER,R.__webglColorRenderbuffer[W])}if(e.bindRenderbuffer(e.RENDERBUFFER,null),y.depthBuffer)R.__webglDepthRenderbuffer=e.createRenderbuffer(),gt(R.__webglDepthRenderbuffer,y,!0);n.bindFramebuffer(e.FRAMEBUFFER,null)}}if(ae){n.bindTexture(e.TEXTURE_CUBE_MAP,z.__webglTexture),Oe(e.TEXTURE_CUBE_MAP,g);for(let W=0;W<6;W++)if(g.mipmaps&&g.mipmaps.length>0)for(let Z=0;Z<g.mipmaps.length;Z++)be(R.__webglFramebuffer[W][Z],y,g,e.COLOR_ATTACHMENT0,e.TEXTURE_CUBE_MAP_POSITIVE_X+W,Z);else be(R.__webglFramebuffer[W],y,g,e.COLOR_ATTACHMENT0,e.TEXTURE_CUBE_MAP_POSITIVE_X+W,0);if(f(g))T(e.TEXTURE_CUBE_MAP);n.unbindTexture()}else if(ce){for(let W=0,Z=ee.length;W<Z;W++){let me=ee[W],Me=i.get(me),he=e.TEXTURE_2D;if(y.isWebGL3DRenderTarget||y.isWebGLArrayRenderTarget)he=y.isWebGL3DRenderTarget?e.TEXTURE_3D:e.TEXTURE_2D_ARRAY;if(n.bindTexture(he,Me.__webglTexture),Oe(he,me),be(R.__webglFramebuffer,y,me,e.COLOR_ATTACHMENT0+W,he,0),f(me))T(he)}n.unbindTexture()}else{let W=e.TEXTURE_2D;if(y.isWebGL3DRenderTarget||y.isWebGLArrayRenderTarget)W=y.isWebGL3DRenderTarget?e.TEXTURE_3D:e.TEXTURE_2D_ARRAY;if(n.bindTexture(W,z.__webglTexture),Oe(W,g),g.mipmaps&&g.mipmaps.length>0)for(let Z=0;Z<g.mipmaps.length;Z++)be(R.__webglFramebuffer[Z],y,g,e.COLOR_ATTACHMENT0,W,Z);else be(R.__webglFramebuffer,y,g,e.COLOR_ATTACHMENT0,W,0);if(f(g))T(W);n.unbindTexture()}if(y.depthBuffer)He(y)}function Et(y){let g=y.textures;for(let R=0,z=g.length;R<z;R++){let ee=g[R];if(f(ee)){let ae=I(y),ce=i.get(ee).__webglTexture;n.bindTexture(ae,ce),T(ae),n.unbindTexture()}}}let at=[],Ut=[];function _t(y){if(y.samples>0){if(P(y)===!1){let{textures:g,width:R,height:z}=y,ee=e.COLOR_BUFFER_BIT,ae=y.stencilBuffer?e.DEPTH_STENCIL_ATTACHMENT:e.DEPTH_ATTACHMENT,ce=i.get(y),W=g.length>1;if(W)for(let me=0;me<g.length;me++)n.bindFramebuffer(e.FRAMEBUFFER,ce.__webglMultisampledFramebuffer),e.framebufferRenderbuffer(e.FRAMEBUFFER,e.COLOR_ATTACHMENT0+me,e.RENDERBUFFER,null),n.bindFramebuffer(e.FRAMEBUFFER,ce.__webglFramebuffer),e.framebufferTexture2D(e.DRAW_FRAMEBUFFER,e.COLOR_ATTACHMENT0+me,e.TEXTURE_2D,null,0);n.bindFramebuffer(e.READ_FRAMEBUFFER,ce.__webglMultisampledFramebuffer);let Z=y.texture.mipmaps;if(Z&&Z.length>0)n.bindFramebuffer(e.DRAW_FRAMEBUFFER,ce.__webglFramebuffer[0]);else n.bindFramebuffer(e.DRAW_FRAMEBUFFER,ce.__webglFramebuffer);for(let me=0;me<g.length;me++){if(y.resolveDepthBuffer){if(y.depthBuffer)ee|=e.DEPTH_BUFFER_BIT;if(y.stencilBuffer&&y.resolveStencilBuffer)ee|=e.STENCIL_BUFFER_BIT}if(W){e.framebufferRenderbuffer(e.READ_FRAMEBUFFER,e.COLOR_ATTACHMENT0,e.RENDERBUFFER,ce.__webglColorRenderbuffer[me]);let Me=i.get(g[me]).__webglTexture;e.framebufferTexture2D(e.DRAW_FRAMEBUFFER,e.COLOR_ATTACHMENT0,e.TEXTURE_2D,Me,0)}if(e.blitFramebuffer(0,0,R,z,0,0,R,z,ee,e.NEAREST),c===!0){if(at.length=0,Ut.length=0,at.push(e.COLOR_ATTACHMENT0+me),y.depthBuffer&&y.storeMultisampledDepthBuffer===!1)at.push(ae),Ut.push(ae),e.invalidateFramebuffer(e.DRAW_FRAMEBUFFER,Ut);e.invalidateFramebuffer(e.READ_FRAMEBUFFER,at)}}if(n.bindFramebuffer(e.READ_FRAMEBUFFER,null),n.bindFramebuffer(e.DRAW_FRAMEBUFFER,null),W)for(let me=0;me<g.length;me++){n.bindFramebuffer(e.FRAMEBUFFER,ce.__webglMultisampledFramebuffer),e.framebufferRenderbuffer(e.FRAMEBUFFER,e.COLOR_ATTACHMENT0+me,e.RENDERBUFFER,ce.__webglColorRenderbuffer[me]);let Me=i.get(g[me]).__webglTexture;n.bindFramebuffer(e.FRAMEBUFFER,ce.__webglFramebuffer),e.framebufferTexture2D(e.DRAW_FRAMEBUFFER,e.COLOR_ATTACHMENT0+me,e.TEXTURE_2D,Me,0)}n.bindFramebuffer(e.DRAW_FRAMEBUFFER,ce.__webglMultisampledFramebuffer)}else if(y.depthBuffer&&y.storeMultisampledDepthBuffer===!1&&c){let g=y.stencilBuffer?e.DEPTH_STENCIL_ATTACHMENT:e.DEPTH_ATTACHMENT;e.invalidateFramebuffer(e.DRAW_FRAMEBUFFER,[g])}}}function xt(y){return Math.min(s.maxSamples,y.samples)}function P(y){let g=i.get(y);return y.samples>0&&t.has("WEBGL_multisampled_render_to_texture")===!0&&g.__useRenderToTexture!==!1}function Ft(y){let g=a.render.frame;if(u.get(y)!==g)u.set(y,g),y.update()}function Ze(y,g){let{colorSpace:R,format:z,type:ee}=y;if(y.isCompressedTexture===!0||y.isVideoTexture===!0)return g;if(R!==ja&&R!==Jn)if(ke.getTransfer(R)===nt){if(z!==un||ee!==en)Ce("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType.")}else Pe("WebGLTextures: Unsupported texture color space:",R);return g}function ct(y){if(typeof HTMLImageElement<"u"&&y instanceof HTMLImageElement)l.width=y.naturalWidth||y.width,l.height=y.naturalHeight||y.height;else if(typeof VideoFrame<"u"&&y instanceof VideoFrame)l.width=y.displayWidth,l.height=y.displayHeight;else l.width=y.width,l.height=y.height;return l}this.allocateTextureUnit=K,this.resetTextureUnits=J,this.getTextureUnits=C,this.setTextureUnits=V,this.setTexture2D=ne,this.setTexture2DArray=X,this.setTexture3D=j,this.setTextureCube=te,this.rebindTextures=je,this.setupRenderTarget=Ve,this.updateRenderTargetMipmap=Et,this.updateMultisampleRenderTarget=_t,this.setupDepthRenderbuffer=He,this.setupFrameBufferTexture=be,this.useMultisampledRTT=P,this.isReversedDepthBuffer=function(){return n.buffers.depth.getReversed()}}function Lg(e,t){function n(i,s=Jn){let r,a=ke.getTransfer(s);if(i===en)return e.UNSIGNED_BYTE;if(i===ga)return e.UNSIGNED_SHORT_4_4_4_4;if(i===_a)return e.UNSIGNED_SHORT_5_5_5_1;if(i===Nc)return e.UNSIGNED_INT_5_9_9_9_REV;if(i===Dc)return e.UNSIGNED_INT_10F_11F_11F_REV;if(i===Pc)return e.BYTE;if(i===Lc)return e.SHORT;if(i===ts)return e.UNSIGNED_SHORT;if(i===ma)return e.INT;if(i===Un)return e.UNSIGNED_INT;if(i===Sn)return e.FLOAT;if(i===hn)return e.HALF_FLOAT;if(i===Uc)return e.ALPHA;if(i===Fc)return e.RGB;if(i===un)return e.RGBA;if(i===$n)return e.DEPTH_COMPONENT;if(i===Yn)return e.DEPTH_STENCIL;if(i===Oc)return e.RED;if(i===xa)return e.RED_INTEGER;if(i===Zn)return e.RG;if(i===va)return e.RG_INTEGER;if(i===ya)return e.RGBA_INTEGER;if(i===qs||i===$s||i===Ys||i===Zs)if(a===nt)if(r=t.get("WEBGL_compressed_texture_s3tc_srgb"),r!==null){if(i===qs)return r.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(i===$s)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(i===Ys)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(i===Zs)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(r=t.get("WEBGL_compressed_texture_s3tc"),r!==null){if(i===qs)return r.COMPRESSED_RGB_S3TC_DXT1_EXT;if(i===$s)return r.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(i===Ys)return r.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(i===Zs)return r.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(i===Sa||i===Ma||i===ba||i===wa)if(r=t.get("WEBGL_compressed_texture_pvrtc"),r!==null){if(i===Sa)return r.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(i===Ma)return r.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(i===ba)return r.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(i===wa)return r.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(i===Ea||i===Ta||i===Aa||i===Ca||i===Ra||i===Js||i===Ia)if(r=t.get("WEBGL_compressed_texture_etc"),r!==null){if(i===Ea||i===Ta)return a===nt?r.COMPRESSED_SRGB8_ETC2:r.COMPRESSED_RGB8_ETC2;if(i===Aa)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:r.COMPRESSED_RGBA8_ETC2_EAC;if(i===Ca)return r.COMPRESSED_R11_EAC;if(i===Ra)return r.COMPRESSED_SIGNED_R11_EAC;if(i===Js)return r.COMPRESSED_RG11_EAC;if(i===Ia)return r.COMPRESSED_SIGNED_RG11_EAC}else return null;if(i===Pa||i===La||i===Na||i===Da||i===Ua||i===Fa||i===Oa||i===Ba||i===za||i===ka||i===Ga||i===Ha||i===Va||i===Wa)if(r=t.get("WEBGL_compressed_texture_astc"),r!==null){if(i===Pa)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:r.COMPRESSED_RGBA_ASTC_4x4_KHR;if(i===La)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:r.COMPRESSED_RGBA_ASTC_5x4_KHR;if(i===Na)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:r.COMPRESSED_RGBA_ASTC_5x5_KHR;if(i===Da)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:r.COMPRESSED_RGBA_ASTC_6x5_KHR;if(i===Ua)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:r.COMPRESSED_RGBA_ASTC_6x6_KHR;if(i===Fa)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:r.COMPRESSED_RGBA_ASTC_8x5_KHR;if(i===Oa)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:r.COMPRESSED_RGBA_ASTC_8x6_KHR;if(i===Ba)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:r.COMPRESSED_RGBA_ASTC_8x8_KHR;if(i===za)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:r.COMPRESSED_RGBA_ASTC_10x5_KHR;if(i===ka)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:r.COMPRESSED_RGBA_ASTC_10x6_KHR;if(i===Ga)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:r.COMPRESSED_RGBA_ASTC_10x8_KHR;if(i===Ha)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:r.COMPRESSED_RGBA_ASTC_10x10_KHR;if(i===Va)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:r.COMPRESSED_RGBA_ASTC_12x10_KHR;if(i===Wa)return a===nt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:r.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(i===Xa||i===qa||i===$a)if(r=t.get("EXT_texture_compression_bptc"),r!==null){if(i===Xa)return a===nt?r.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:r.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(i===qa)return r.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(i===$a)return r.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(i===Ya||i===Za||i===Ks||i===Ja)if(r=t.get("EXT_texture_compression_rgtc"),r!==null){if(i===Ya)return r.COMPRESSED_RED_RGTC1_EXT;if(i===Za)return r.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(i===Ks)return r.COMPRESSED_RED_GREEN_RGTC2_EXT;if(i===Ja)return r.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;if(i===Li)return e.UNSIGNED_INT_24_8;return e[i]!==void 0?e[i]:null}return{convert:n}}var Ng=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,Dg=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`;class Nh{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){let n=new lr(e.texture);if(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)this.depthNear=e.depthNear,this.depthFar=e.depthFar;this.texture=n}}getMesh(e){if(this.texture!==null){if(this.mesh===null){let t=e.cameras[0].viewport,n=new Yt({vertexShader:Ng,fragmentShader:Dg,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new Dt(new rs(20,20),n)}}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class Dh extends Mn{constructor(e,t){super();let n=this,i=null,s=1,r=null,a="local-floor",o=1,c=null,l=null,u=null,d=null,h=null,m=null,v=typeof XRWebGLBinding<"u",b=new Nh,p={},f=t.getContextAttributes(),T=null,I=null,S=[],w=[],E=new Xe,A=null,x=null,M=new Nt;M.viewport=new ut;let H=new Nt;H.viewport=new ut;let D=[M,H],U=new wo,J=null,C=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(q){let ie=S[q];if(ie===void 0)ie=new ss,S[q]=ie;return ie.getTargetRaySpace()},this.getControllerGrip=function(q){let ie=S[q];if(ie===void 0)ie=new ss,S[q]=ie;return ie.getGripSpace()},this.getHand=function(q){let ie=S[q];if(ie===void 0)ie=new ss,S[q]=ie;return ie.getHandSpace()};function V(q){let ie=w.indexOf(q.inputSource);if(ie===-1)return;let re=S[ie];if(re!==void 0)re.update(q.inputSource,q.frame,c||r),re.dispatchEvent({type:q.type,data:q.inputSource})}function K(){i.removeEventListener("select",V),i.removeEventListener("selectstart",V),i.removeEventListener("selectend",V),i.removeEventListener("squeeze",V),i.removeEventListener("squeezestart",V),i.removeEventListener("squeezeend",V),i.removeEventListener("end",K),i.removeEventListener("inputsourceschange",G);for(let q=0;q<S.length;q++){let ie=w[q];if(ie===null)continue;w[q]=null,S[q].disconnect(ie)}J=null,C=null,b.reset();for(let q in p)delete p[q];if(e.setRenderTarget(T),h=null,d=null,u=null,i=null,I=null,Oe.stop(),n.isPresenting=!1,e.setPixelRatio(A),e.setSize(E.width,E.height,!1),x!==null){let q=x.camera;q.fov=x.fov,q.zoom=x.zoom,q.updateProjectionMatrix(),x=null}n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(q){if(s=q,n.isPresenting===!0)Ce("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(q){if(a=q,n.isPresenting===!0)Ce("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||r},this.setReferenceSpace=function(q){c=q},this.getBaseLayer=function(){return d!==null?d:h},this.getBinding=function(){if(u===null&&v)u=new XRWebGLBinding(i,t);return u},this.getFrame=function(){return m},this.getSession=function(){return i},this.setSession=async function(q){if(i=q,i!==null){if(T=e.getRenderTarget(),i.addEventListener("select",V),i.addEventListener("selectstart",V),i.addEventListener("selectend",V),i.addEventListener("squeeze",V),i.addEventListener("squeezestart",V),i.addEventListener("squeezeend",V),i.addEventListener("end",K),i.addEventListener("inputsourceschange",G),f.xrCompatible!==!0)await t.makeXRCompatible();if(A=e.getPixelRatio(),e.getSize(E),!(v&&("createProjectionLayer"in XRWebGLBinding.prototype))){let re={antialias:f.antialias,alpha:!0,depth:f.depth,stencil:f.stencil,framebufferScaleFactor:s};h=new XRWebGLLayer(i,t,re),i.updateRenderState({baseLayer:h}),e.setPixelRatio(1),e.setSize(h.framebufferWidth,h.framebufferHeight,!1),I=new Vt(h.framebufferWidth,h.framebufferHeight,{format:un,type:en,colorSpace:e.outputColorSpace,stencilBuffer:f.stencil,resolveDepthBuffer:h.ignoreDepthValues===!1,resolveStencilBuffer:h.ignoreDepthValues===!1,storeMultisampledDepthBuffer:h.ignoreDepthValues===!1,storeMultisampledStencilBuffer:h.ignoreDepthValues===!1})}else{let re=null,Te=null,Ie=null;if(f.depth)Ie=f.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,re=f.stencil?Yn:$n,Te=f.stencil?Li:Un;let be={colorFormat:t.RGBA8,depthFormat:Ie,scaleFactor:s};u=this.getBinding(),d=u.createProjectionLayer(be),i.updateRenderState({layers:[d]}),e.setPixelRatio(1),e.setSize(d.textureWidth,d.textureHeight,!1),I=new Vt(d.textureWidth,d.textureHeight,{format:un,type:en,depthTexture:new ti(d.textureWidth,d.textureHeight,Te,void 0,void 0,void 0,void 0,void 0,void 0,re),stencilBuffer:f.stencil,colorSpace:e.outputColorSpace,samples:f.antialias?4:0,resolveDepthBuffer:d.ignoreDepthValues===!1,resolveStencilBuffer:d.ignoreDepthValues===!1,storeMultisampledDepthBuffer:d.ignoreDepthValues===!1,storeMultisampledStencilBuffer:d.ignoreDepthValues===!1})}I.isXRRenderTarget=!0,this.setFoveation(o),c=null,r=await i.requestReferenceSpace(a),Oe.setContext(i),Oe.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(i!==null)return i.environmentBlendMode},this.getDepthTexture=function(){return b.getDepthTexture()};function G(q){for(let ie=0;ie<q.removed.length;ie++){let re=q.removed[ie],Te=w.indexOf(re);if(Te>=0)w[Te]=null,S[Te].disconnect(re)}for(let ie=0;ie<q.added.length;ie++){let re=q.added[ie],Te=w.indexOf(re);if(Te===-1){for(let be=0;be<S.length;be++)if(be>=w.length){w.push(re),Te=be;break}else if(w[be]===null){w[be]=re,Te=be;break}if(Te===-1)break}let Ie=S[Te];if(Ie)Ie.connect(re)}}let ne=new F,X=new F;function j(q,ie,re){ne.setFromMatrixPosition(ie.matrixWorld),X.setFromMatrixPosition(re.matrixWorld);let Te=ne.distanceTo(X),Ie=ie.projectionMatrix.elements,be=re.projectionMatrix.elements,gt=Ie[14]/(Ie[10]-1),ze=Ie[14]/(Ie[10]+1),He=(Ie[9]+1)/Ie[5],je=(Ie[9]-1)/Ie[5],Ve=(Ie[8]-1)/Ie[0],Et=(be[8]+1)/be[0],at=gt*Ve,Ut=gt*Et,_t=Te/(-Ve+Et),xt=_t*-Ve;if(ie.matrixWorld.decompose(q.position,q.quaternion,q.scale),q.translateX(xt),q.translateZ(_t),q.matrixWorld.compose(q.position,q.quaternion,q.scale),q.matrixWorldInverse.copy(q.matrixWorld).invert(),Ie[10]===-1)q.projectionMatrix.copy(ie.projectionMatrix),q.projectionMatrixInverse.copy(ie.projectionMatrixInverse);else{let P=gt+_t,Ft=ze+_t,Ze=at-xt,ct=Ut+(Te-xt),y=He*ze/Ft*P,g=je*ze/Ft*P;q.projectionMatrix.makePerspective(Ze,ct,y,g,P,Ft),q.projectionMatrixInverse.copy(q.projectionMatrix).invert()}}function te(q,ie){if(ie===null)q.matrixWorld.copy(q.matrix);else q.matrixWorld.multiplyMatrices(ie.matrixWorld,q.matrix);q.matrixWorldInverse.copy(q.matrixWorld).invert()}this.updateCamera=function(q){if(i===null)return;let{near:ie,far:re}=q;if(b.texture!==null){if(b.depthNear>0)ie=b.depthNear;if(b.depthFar>0)re=b.depthFar}if(U.near=H.near=M.near=ie,U.far=H.far=M.far=re,J!==U.near||C!==U.far)i.updateRenderState({depthNear:U.near,depthFar:U.far}),J=U.near,C=U.far;U.layers.mask=q.layers.mask|6,M.layers.mask=U.layers.mask&-5,H.layers.mask=U.layers.mask&-3;let Te=q.parent,Ie=U.cameras;te(U,Te);for(let be=0;be<Ie.length;be++)te(Ie[be],Te);if(Ie.length===2)j(U,M,H);else U.projectionMatrix.copy(M.projectionMatrix);if(x===null&&q.isPerspectiveCamera)x={camera:q,fov:q.fov,zoom:q.zoom};Re(q,U,Te)};function Re(q,ie,re){if(re===null)q.matrix.copy(ie.matrixWorld);else q.matrix.copy(re.matrixWorld),q.matrix.invert(),q.matrix.multiply(ie.matrixWorld);if(q.matrix.decompose(q.position,q.quaternion,q.scale),q.updateMatrixWorld(!0),q.projectionMatrix.copy(ie.projectionMatrix),q.projectionMatrixInverse.copy(ie.projectionMatrixInverse),q.isPerspectiveCamera)q.fov=zs*2*Math.atan(1/q.projectionMatrix.elements[5]),q.zoom=1}this.getCamera=function(){return U},this.getFoveation=function(){if(d===null&&h===null)return;return o},this.setFoveation=function(q){if(o=q,d!==null)d.fixedFoveation=q;if(h!==null&&h.fixedFoveation!==void 0)h.fixedFoveation=q},this.hasDepthSensing=function(){return b.texture!==null},this.getDepthSensingMesh=function(){return b.getMesh(U)},this.getCameraTexture=function(q){return p[q]};let Ee=null;function it(q,ie){if(l=ie.getViewerPose(c||r),m=ie,l!==null){let re=l.views;if(h!==null)e.setRenderTargetFramebuffer(I,h.framebuffer),e.setRenderTarget(I);let Te=!1;if(re.length!==U.cameras.length)U.cameras.length=0,Te=!0;for(let ze=0;ze<re.length;ze++){let He=re[ze],je=null;if(h!==null)je=h.getViewport(He);else{let Et=u.getViewSubImage(d,He);if(je=Et.viewport,ze===0)e.setRenderTargetTextures(I,Et.colorTexture,Et.depthStencilTexture),e.setRenderTarget(I)}let Ve=D[ze];if(Ve===void 0)Ve=new Nt,Ve.layers.enable(ze),Ve.viewport=new ut,D[ze]=Ve;if(Ve.matrix.fromArray(He.transform.matrix),Ve.matrix.decompose(Ve.position,Ve.quaternion,Ve.scale),Ve.projectionMatrix.fromArray(He.projectionMatrix),Ve.projectionMatrixInverse.copy(Ve.projectionMatrix).invert(),Ve.viewport.set(je.x,je.y,je.width,je.height),ze===0)U.matrix.copy(Ve.matrix),U.matrix.decompose(U.position,U.quaternion,U.scale);if(Te===!0)U.cameras.push(Ve)}let Ie=i.enabledFeatures;if(Ie&&Ie.includes("depth-sensing")&&i.depthUsage=="gpu-optimized"&&v){u=n.getBinding();let ze=u.getDepthInformation(re[0]);if(ze&&ze.isValid&&ze.texture)b.init(ze,i.renderState)}if(Ie&&Ie.includes("camera-access")&&v){e.state.unbindTexture(),u=n.getBinding();for(let ze=0;ze<re.length;ze++){let He=re[ze].camera;if(He){let je=p[He];if(!je)je=new lr,p[He]=je;let Ve=u.getCameraImage(He);je.sourceTexture=Ve}}}}for(let re=0;re<S.length;re++){let Te=w[re],Ie=S[re];if(Te!==null&&Ie!==void 0)Ie.update(Te,ie,c||r)}if(Ee)Ee(q,ie);if(ie.detectedPlanes)n.dispatchEvent({type:"planesdetected",data:ie});m=null}let Oe=new Mh;Oe.setAnimationLoop(it),this.setAnimationLoop=function(q){Ee=q},this.dispose=function(){}}}var Ug=new ht,Uh=new Le;Uh.set(-1,0,0,0,1,0,0,0,1);function Fg(e,t){function n(p,f){if(p.matrixAutoUpdate===!0)p.updateMatrix();f.value.copy(p.matrix)}function i(p,f){if(f.color.getRGB(p.fogColor.value,lo(e)),f.isFog)p.fogNear.value=f.near,p.fogFar.value=f.far;else if(f.isFogExp2)p.fogDensity.value=f.density}function s(p,f,T,I,S){if(f.isNodeMaterial)f.uniformsNeedUpdate=!1;else if(f.isMeshBasicMaterial)r(p,f);else if(f.isMeshLambertMaterial){if(r(p,f),f.envMap)p.envMapIntensity.value=f.envMapIntensity}else if(f.isMeshToonMaterial)r(p,f),d(p,f);else if(f.isMeshPhongMaterial){if(r(p,f),u(p,f),f.envMap)p.envMapIntensity.value=f.envMapIntensity}else if(f.isMeshStandardMaterial){if(r(p,f),h(p,f),f.isMeshPhysicalMaterial)m(p,f,S)}else if(f.isMeshMatcapMaterial)r(p,f),v(p,f);else if(f.isMeshDepthMaterial)r(p,f);else if(f.isMeshDistanceMaterial)r(p,f),b(p,f);else if(f.isMeshNormalMaterial)r(p,f);else if(f.isLineBasicMaterial){if(a(p,f),f.isLineDashedMaterial)o(p,f)}else if(f.isPointsMaterial)c(p,f,T,I);else if(f.isSpriteMaterial)l(p,f);else if(f.isShadowMaterial)p.color.value.copy(f.color),p.opacity.value=f.opacity;else if(f.isShaderMaterial)f.uniformsNeedUpdate=!1}function r(p,f){if(p.opacity.value=f.opacity,f.color)p.diffuse.value.copy(f.color);if(f.emissive)p.emissive.value.copy(f.emissive).multiplyScalar(f.emissiveIntensity);if(f.map)p.map.value=f.map,n(f.map,p.mapTransform);if(f.alphaMap)p.alphaMap.value=f.alphaMap,n(f.alphaMap,p.alphaMapTransform);if(f.bumpMap){if(p.bumpMap.value=f.bumpMap,n(f.bumpMap,p.bumpMapTransform),p.bumpScale.value=f.bumpScale,f.side===Bt)p.bumpScale.value*=-1}if(f.normalMap){if(p.normalMap.value=f.normalMap,n(f.normalMap,p.normalMapTransform),p.normalScale.value.copy(f.normalScale),f.side===Bt)p.normalScale.value.negate()}if(f.displacementMap)p.displacementMap.value=f.displacementMap,n(f.displacementMap,p.displacementMapTransform),p.displacementScale.value=f.displacementScale,p.displacementBias.value=f.displacementBias;if(f.emissiveMap)p.emissiveMap.value=f.emissiveMap,n(f.emissiveMap,p.emissiveMapTransform);if(f.specularMap)p.specularMap.value=f.specularMap,n(f.specularMap,p.specularMapTransform);if(f.alphaTest>0)p.alphaTest.value=f.alphaTest;let T=t.get(f),{envMap:I,envMapRotation:S}=T;if(I){if(p.envMap.value=I,p.envMapRotation.value.setFromMatrix4(Ug.makeRotationFromEuler(S)).transpose(),I.isCubeTexture&&I.isRenderTargetTexture===!1)p.envMapRotation.value.premultiply(Uh);p.reflectivity.value=f.reflectivity,p.ior.value=f.ior,p.refractionRatio.value=f.refractionRatio}if(f.lightMap)p.lightMap.value=f.lightMap,p.lightMapIntensity.value=f.lightMapIntensity,n(f.lightMap,p.lightMapTransform);if(f.aoMap)p.aoMap.value=f.aoMap,p.aoMapIntensity.value=f.aoMapIntensity,n(f.aoMap,p.aoMapTransform)}function a(p,f){if(p.diffuse.value.copy(f.color),p.opacity.value=f.opacity,f.map)p.map.value=f.map,n(f.map,p.mapTransform)}function o(p,f){p.dashSize.value=f.dashSize,p.totalSize.value=f.dashSize+f.gapSize,p.scale.value=f.scale}function c(p,f,T,I){if(p.diffuse.value.copy(f.color),p.opacity.value=f.opacity,p.size.value=f.size*T,p.scale.value=I*0.5,f.map)p.map.value=f.map,n(f.map,p.uvTransform);if(f.alphaMap)p.alphaMap.value=f.alphaMap,n(f.alphaMap,p.alphaMapTransform);if(f.alphaTest>0)p.alphaTest.value=f.alphaTest}function l(p,f){if(p.diffuse.value.copy(f.color),p.opacity.value=f.opacity,p.rotation.value=f.rotation,f.map)p.map.value=f.map,n(f.map,p.mapTransform);if(f.alphaMap)p.alphaMap.value=f.alphaMap,n(f.alphaMap,p.alphaMapTransform);if(f.alphaTest>0)p.alphaTest.value=f.alphaTest}function u(p,f){p.specular.value.copy(f.specular),p.shininess.value=Math.max(f.shininess,0.0001)}function d(p,f){if(f.gradientMap)p.gradientMap.value=f.gradientMap}function h(p,f){if(p.metalness.value=f.metalness,f.metalnessMap)p.metalnessMap.value=f.metalnessMap,n(f.metalnessMap,p.metalnessMapTransform);if(p.roughness.value=f.roughness,f.roughnessMap)p.roughnessMap.value=f.roughnessMap,n(f.roughnessMap,p.roughnessMapTransform);if(f.envMap)p.envMapIntensity.value=f.envMapIntensity}function m(p,f,T){if(p.ior.value=f.ior,f.sheen>0){if(p.sheenColor.value.copy(f.sheenColor).multiplyScalar(f.sheen),p.sheenRoughness.value=f.sheenRoughness,f.sheenColorMap)p.sheenColorMap.value=f.sheenColorMap,n(f.sheenColorMap,p.sheenColorMapTransform);if(f.sheenRoughnessMap)p.sheenRoughnessMap.value=f.sheenRoughnessMap,n(f.sheenRoughnessMap,p.sheenRoughnessMapTransform)}if(f.clearcoat>0){if(p.clearcoat.value=f.clearcoat,p.clearcoatRoughness.value=f.clearcoatRoughness,f.clearcoatMap)p.clearcoatMap.value=f.clearcoatMap,n(f.clearcoatMap,p.clearcoatMapTransform);if(f.clearcoatRoughnessMap)p.clearcoatRoughnessMap.value=f.clearcoatRoughnessMap,n(f.clearcoatRoughnessMap,p.clearcoatRoughnessMapTransform);if(f.clearcoatNormalMap){if(p.clearcoatNormalMap.value=f.clearcoatNormalMap,n(f.clearcoatNormalMap,p.clearcoatNormalMapTransform),p.clearcoatNormalScale.value.copy(f.clearcoatNormalScale),f.side===Bt)p.clearcoatNormalScale.value.negate()}}if(f.dispersion>0)p.dispersion.value=f.dispersion;if(f.retroreflectivity>0)p.retroreflectivity.value=f.retroreflectivity;if(f.iridescence>0){if(p.iridescence.value=f.iridescence,p.iridescenceIOR.value=f.iridescenceIOR,p.iridescenceThicknessMinimum.value=f.iridescenceThicknessRange[0],p.iridescenceThicknessMaximum.value=f.iridescenceThicknessRange[1],f.iridescenceMap)p.iridescenceMap.value=f.iridescenceMap,n(f.iridescenceMap,p.iridescenceMapTransform);if(f.iridescenceThicknessMap)p.iridescenceThicknessMap.value=f.iridescenceThicknessMap,n(f.iridescenceThicknessMap,p.iridescenceThicknessMapTransform)}if(f.transmission>0){if(p.transmission.value=f.transmission,p.transmissionSamplerMap.value=T.texture,p.transmissionSamplerSize.value.set(T.width,T.height),f.transmissionMap)p.transmissionMap.value=f.transmissionMap,n(f.transmissionMap,p.transmissionMapTransform);if(p.thickness.value=f.thickness,f.thicknessMap)p.thicknessMap.value=f.thicknessMap,n(f.thicknessMap,p.thicknessMapTransform);p.attenuationDistance.value=f.attenuationDistance,p.attenuationColor.value.copy(f.attenuationColor)}if(f.anisotropy>0){if(p.anisotropyVector.value.set(f.anisotropy*Math.cos(f.anisotropyRotation),f.anisotropy*Math.sin(f.anisotropyRotation)),f.anisotropyMap)p.anisotropyMap.value=f.anisotropyMap,n(f.anisotropyMap,p.anisotropyMapTransform)}if(p.specularIntensity.value=f.specularIntensity,p.specularColor.value.copy(f.specularColor),f.specularColorMap)p.specularColorMap.value=f.specularColorMap,n(f.specularColorMap,p.specularColorMapTransform);if(f.specularIntensityMap)p.specularIntensityMap.value=f.specularIntensityMap,n(f.specularIntensityMap,p.specularIntensityMapTransform)}function v(p,f){if(f.matcap)p.matcap.value=f.matcap}function b(p,f){let T=t.get(f).light;p.referencePosition.value.setFromMatrixPosition(T.matrixWorld),p.nearDistance.value=T.shadow.camera.near,p.farDistance.value=T.shadow.camera.far}return{refreshFogUniforms:i,refreshMaterialUniforms:s}}function Og(e,t,n,i){let s={},r={},a=[],o=e.getParameter(e.MAX_UNIFORM_BUFFER_BINDINGS);function c(S,w){let E=w.program;i.uniformBlockBinding(S,E)}function l(S,w){let E=s[S.id];if(E===void 0)p(S),E=u(S),s[S.id]=E,S.addEventListener("dispose",T);let A=w.program;i.updateUBOMapping(S,A);let x=t.render.frame;if(r[S.id]!==x)h(S),r[S.id]=x}function u(S){let w=d();S.__bindingPointIndex=w;let E=e.createBuffer(),{__size:A,usage:x}=S;return e.bindBuffer(e.UNIFORM_BUFFER,E),e.bufferData(e.UNIFORM_BUFFER,A,x),e.bindBuffer(e.UNIFORM_BUFFER,null),e.bindBufferBase(e.UNIFORM_BUFFER,w,E),E}function d(){for(let S=0;S<o;S++)if(a.indexOf(S)===-1)return a.push(S),S;return Pe("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function h(S){let w=s[S.id],{uniforms:E,__cache:A}=S;e.bindBuffer(e.UNIFORM_BUFFER,w);for(let x=0,M=E.length;x<M;x++){let H=E[x];if(Array.isArray(H))for(let D=0,U=H.length;D<U;D++)m(H[D],x,D,A);else m(H,x,0,A)}e.bindBuffer(e.UNIFORM_BUFFER,null)}function m(S,w,E,A){if(b(S,w,E,A)===!0){let{__offset:x,value:M}=S;if(Array.isArray(M)){let H=0;for(let D=0;D<M.length;D++){let U=M[D],J=f(U);if(v(U,S.__data,H),typeof U!=="number"&&typeof U!=="boolean"&&!U.isMatrix3&&!ArrayBuffer.isView(U))H+=J.storage/Float32Array.BYTES_PER_ELEMENT}}else v(M,S.__data,0);e.bufferSubData(e.UNIFORM_BUFFER,x,S.__data)}}function v(S,w,E){if(typeof S==="number"||typeof S==="boolean")w[0]=S;else if(S.isMatrix3)w[0]=S.elements[0],w[1]=S.elements[1],w[2]=S.elements[2],w[3]=0,w[4]=S.elements[3],w[5]=S.elements[4],w[6]=S.elements[5],w[7]=0,w[8]=S.elements[6],w[9]=S.elements[7],w[10]=S.elements[8],w[11]=0;else if(ArrayBuffer.isView(S))w.set(new S.constructor(S.buffer,S.byteOffset,w.length));else S.toArray(w,E)}function b(S,w,E,A){let x=S.value,M=w+"_"+E;if(A[M]===void 0){if(typeof x==="number"||typeof x==="boolean")A[M]=x;else if(ArrayBuffer.isView(x))A[M]=x.slice();else A[M]=x.clone();return!0}else{let H=A[M];if(typeof x==="number"||typeof x==="boolean"){if(H!==x)return A[M]=x,!0}else if(ArrayBuffer.isView(x))return!0;else if(H.equals(x)===!1)return H.copy(x),!0}return!1}function p(S){let w=S.uniforms,E=0,A=16;for(let M=0,H=w.length;M<H;M++){let D=Array.isArray(w[M])?w[M]:[w[M]];for(let U=0,J=D.length;U<J;U++){let C=D[U],V=Array.isArray(C.value)?C.value:[C.value];for(let K=0,G=V.length;K<G;K++){let ne=V[K],X=f(ne),j=E%A,te=j%X.boundary,Re=j+te;if(E+=te,Re!==0&&A-Re<X.storage)E+=A-Re;C.__data=new Float32Array(X.storage/Float32Array.BYTES_PER_ELEMENT),C.__offset=E,E+=X.storage}}}let x=E%A;if(x>0)E+=A-x;return S.__size=E,S.__cache={},this}function f(S){let w={boundary:0,storage:0};if(typeof S==="number"||typeof S==="boolean")w.boundary=4,w.storage=4;else if(S.isVector2)w.boundary=8,w.storage=8;else if(S.isVector3||S.isColor)w.boundary=16,w.storage=12;else if(S.isVector4)w.boundary=16,w.storage=16;else if(S.isMatrix3)w.boundary=48,w.storage=48;else if(S.isMatrix4)w.boundary=64,w.storage=64;else if(S.isTexture)Ce("WebGLRenderer: Texture samplers can not be part of an uniforms group.");else if(ArrayBuffer.isView(S))w.boundary=16,w.storage=S.byteLength;else Ce("WebGLRenderer: Unsupported uniform value type.",S);return w}function T(S){let w=S.target;w.removeEventListener("dispose",T);let E=a.indexOf(w.__bindingPointIndex);a.splice(E,1),e.deleteBuffer(s[w.id]),delete s[w.id],delete r[w.id]}function I(){for(let S in s)e.deleteBuffer(s[S]);a=[],s={},r={}}return{bind:c,update:l,dispose:I}}var Bg=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]),dn=null;function zg(){if(dn===null)dn=new ao(Bg,16,16,Zn,hn),dn.name="DFG_LUT",dn.minFilter=zt,dn.magFilter=zt,dn.wrapS=Ws,dn.wrapT=Ws,dn.generateMipmaps=!1,dn.needsUpdate=!0;return dn}class zo{constructor(e={}){let{canvas:t=qc(),context:n=null,depth:i=!0,stencil:s=!1,alpha:r=!1,antialias:a=!1,premultipliedAlpha:o=!0,preserveDrawingBuffer:c=!1,powerPreference:l="default",failIfMajorPerformanceCaveat:u=!1,reversedDepthBuffer:d=!1,outputBufferType:h=en}=e;this.isWebGLRenderer=!0;let m;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");m=n.getContextAttributes().alpha}else m=r;let v=h,b=new Set([ya,va,xa]),p=new Set([en,Un,ts,Li,ga,_a]),f=new Uint32Array(4),T=new Int32Array(4),I=new F,S=null,w=null,E=[],A=[],x=null;this.domElement=t,this.debug={checkShaderErrors:!0,diagnostics:{keywords:!1},onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=Qt,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let M=this,H=!1,D=null,U=null,J=null,C=null;this._outputColorSpace=zc;let V=0,K=0,G=null,ne=-1,X=null,j=new ut,te=new ut,Re=null,Ee=new qe(0),it=0,{width:Oe,height:q}=t,ie=1,re=null,Te=null,Ie=new ut(0,0,Oe,q),be=new ut(0,0,Oe,q),gt=!1,ze=new ar,He=!1,je=!1,Ve=new ht,Et=new F,at=new ut,Ut={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},_t=!1;function xt(){return G===null?ie:1}let P=n;function Ft(_,L){return t.getContext(_,L)}let Ze,ct,y,g,R,z,ee,ae,ce,W,Z,me,Me,he,se,we,Ae,$e,N,oe,Y,le,ge;try{let _={alpha:!0,depth:i,stencil:s,antialias:a,premultipliedAlpha:o,preserveDrawingBuffer:c,powerPreference:l,failIfMajorPerformanceCaveat:u};if("setAttribute"in t)t.setAttribute("data-engine",`three.js r${Yl}`);if(t.addEventListener("webglcontextlost",Ne,!1),t.addEventListener("webglcontextrestored",st,!1),t.addEventListener("webglcontextcreationerror",Je,!1),P===null){if(P=Ft("webgl2",_),P===null)if(Ft("webgl2"))throw Error("THREE.WebGLRenderer: Error creating WebGL context with your selected attributes.");else throw Error("THREE.WebGLRenderer: Error creating WebGL context.")}Q()}catch(_){throw t.removeEventListener("webglcontextlost",Ne,!1),t.removeEventListener("webglcontextrestored",st,!1),t.removeEventListener("webglcontextcreationerror",Je,!1),Pe("WebGLRenderer: "+_.message),_}function Q(){if(Ze=new qp(P),Ze.init(),Y=new Lg(P,Ze),ct=new Fp(P,Ze,e,Y),y=new Ig(P,Ze),ct.reversedDepthBuffer&&d)y.buffers.depth.setReversed(!0);U=P.createFramebuffer(),J=P.createFramebuffer(),C=P.createFramebuffer(),g=new Zp(P),R=new gg,z=new Pg(P,Ze,y,R,ct,Y,g),ee=new Xp(M),ae=new Ju(P),le=new Dp(P,ae),ce=new $p(P,ae,g,le),W=new Kp(P,ce,ae,le,g),$e=new Jp(P,ct,z),se=new Op(R),Z=new mg(M,ee,Ze,ct,le,se),me=new Fg(M,R),Me=new xg,he=new wg(Ze),Ae=new Np(M,ee,y,W,m,o),we=new Rg(M,W,ct),ge=new Og(P,g,ct,y),N=new Up(P,Ze,g),oe=new Yp(P,Ze,g),g.programs=Z.programs,M.capabilities=ct,M.extensions=Ze,M.properties=R,M.renderLists=Me,M.shadowMap=we,M.state=y,M.info=g}if(v!==en)x=new Qp(v,t.width,t.height,a,i,s);let de=new Dh(M,P);this.xr=de,this.getContext=function(){return P},this.getContextAttributes=function(){return P.getContextAttributes()},this.forceContextLoss=function(){let _=Ze.get("WEBGL_lose_context");if(_)_.loseContext()},this.forceContextRestore=function(){let _=Ze.get("WEBGL_lose_context");if(_)_.restoreContext()},this.getPixelRatio=function(){return ie},this.setPixelRatio=function(_){if(_===void 0)return;ie=_,this.setSize(Oe,q,!1)},this.getSize=function(_){return _.set(Oe,q)},this.setSize=function(_,L,k=!0){if(de.isPresenting){Ce("WebGLRenderer: Can't change size while VR device is presenting.");return}if(Oe=_,q=L,t.width=Math.floor(_*ie),t.height=Math.floor(L*ie),k===!0)t.style.width=_+"px",t.style.height=L+"px";if(x!==null)x.setSize(t.width,t.height);this.setViewport(0,0,_,L)},this.getDrawingBufferSize=function(_){return _.set(Oe*ie,q*ie).floor()},this.setDrawingBufferSize=function(_,L,k){Oe=_,q=L,ie=k,t.width=Math.floor(_*k),t.height=Math.floor(L*k),this.setViewport(0,0,_,L)},this.setEffects=function(_){if(v===en){Pe("WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(_){for(let L=0;L<_.length;L++)if(_[L].isOutputPass===!0){Ce("WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}x.setEffects(_||[])},this.getCurrentViewport=function(_){return _.copy(j)},this.getViewport=function(_){return _.copy(Ie)},this.setViewport=function(_,L,k,O){if(_.isVector4)Ie.set(_.x,_.y,_.z,_.w);else Ie.set(_,L,k,O);y.viewport(j.copy(Ie).multiplyScalar(ie).round())},this.getScissor=function(_){return _.copy(be)},this.setScissor=function(_,L,k,O){if(_.isVector4)be.set(_.x,_.y,_.z,_.w);else be.set(_,L,k,O);y.scissor(te.copy(be).multiplyScalar(ie).round())},this.getScissorTest=function(){return gt},this.setScissorTest=function(_){y.setScissorTest(gt=_)},this.setOpaqueSort=function(_){re=_},this.setTransparentSort=function(_){Te=_},this.getClearColor=function(_){return _.copy(Ae.getClearColor())},this.setClearColor=function(){Ae.setClearColor(...arguments)},this.getClearAlpha=function(){return Ae.getClearAlpha()},this.setClearAlpha=function(){Ae.setClearAlpha(...arguments)},this.clear=function(_=!0,L=!0,k=!0){let O=0;if(_){let B=!1;if(G!==null){let pe=G.texture.format;B=b.has(pe)}if(B){let pe=G.texture.type,xe=p.has(pe),fe=Ae.getClearColor(),ve=Ae.getClearAlpha(),{r:Se,g:Ue,b:Be}=fe;if(xe)f[0]=Se,f[1]=Ue,f[2]=Be,f[3]=ve,P.clearBufferuiv(P.COLOR,0,f);else T[0]=Se,T[1]=Ue,T[2]=Be,T[3]=ve,P.clearBufferiv(P.COLOR,0,T)}else O|=P.COLOR_BUFFER_BIT}if(L)O|=P.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0);if(k)O|=P.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295);if(O!==0)P.clear(O)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(_){_.setRenderer(this),D=_},this.dispose=function(){t.removeEventListener("webglcontextlost",Ne,!1),t.removeEventListener("webglcontextrestored",st,!1),t.removeEventListener("webglcontextcreationerror",Je,!1),Ae.dispose(),Me.dispose(),he.dispose(),R.dispose(),ee.dispose(),W.dispose(),le.dispose(),ge.dispose(),Z.dispose(),de.dispose(),de.removeEventListener("sessionstart",sl),de.removeEventListener("sessionend",rl),Bn.stop()};function Ne(_){_.preventDefault(),no("WebGLRenderer: Context Lost."),H=!0}function st(){no("WebGLRenderer: Context Restored."),H=!1;let _=g.autoReset,L=we.enabled,k=we.autoUpdate,O=we.needsUpdate,B=we.type;Q(),g.autoReset=_,we.enabled=L,we.autoUpdate=k,we.needsUpdate=O,we.type=B}function Je(_){Pe("WebGLRenderer: A WebGL context could not be created. Reason: ",_.statusMessage)}function nn(_){let L=_.target;L.removeEventListener("dispose",nn),pn(L)}function pn(_){ru(_),R.remove(_)}function ru(_){let L=R.get(_).programs;if(L!==void 0){if(L.forEach(function(k){Z.releaseProgram(k)}),_.isShaderMaterial)Z.releaseShaderCache(_)}}this.renderBufferDirect=function(_,L,k,O,B,pe){if(L===null)L=Ut;let xe=B.isMesh&&B.matrixWorld.determinantAffine()<0,fe=lu(_,L,k,O,B);y.setMaterial(O,xe);let ve=k.index,Se=1;if(O.wireframe===!0){if(ve=ce.getWireframeAttribute(k),ve===void 0)return;Se=2}let Ue=k.drawRange,Be=k.attributes.position,ye=Ue.start*Se,Ke=(Ue.start+Ue.count)*Se;if(pe!==null)ye=Math.max(ye,pe.start*Se),Ke=Math.min(Ke,(pe.start+pe.count)*Se);if(ve!==null)ye=Math.max(ye,0),Ke=Math.min(Ke,ve.count);else if(Be!==void 0&&Be!==null)ye=Math.max(ye,0),Ke=Math.min(Ke,Be.count);let pt=Ke-ye;if(pt<0||pt===1/0)return;le.setup(B,O,fe,k,ve);let ot,tt=N;if(ve!==null)ot=ae.get(ve),tt=oe,tt.setIndex(ot);if(B.isMesh)if(O.wireframe===!0)y.setLineWidth(O.wireframeLinewidth*xt()),tt.setMode(P.LINES);else tt.setMode(P.TRIANGLES);else if(B.isLine){let Tt=O.linewidth;if(Tt===void 0)Tt=1;if(y.setLineWidth(Tt*xt()),B.isLineSegments)tt.setMode(P.LINES);else if(B.isLineLoop)tt.setMode(P.LINE_LOOP);else tt.setMode(P.LINE_STRIP)}else if(B.isPoints)tt.setMode(P.POINTS);else if(B.isSprite)tt.setMode(P.TRIANGLES);if(B.isBatchedMesh)if(!Ze.get("WEBGL_multi_draw")){let{_multiDrawStarts:Tt,_multiDrawCounts:_e,_multiDrawCount:Lt}=B,We=ve?ae.get(ve).bytesPerElement:1,Wt=R.get(O).currentProgram.getUniforms();for(let sn=0;sn<Lt;sn++)Wt.setValue(P,"_gl_DrawID",sn),tt.render(Tt[sn]/We,_e[sn])}else tt.renderMultiDraw(B._multiDrawStarts,B._multiDrawCounts,B._multiDrawCount);else if(B.isInstancedMesh)tt.renderInstances(ye,pt,B.count);else if(k.isInstancedBufferGeometry){let Tt=k._maxInstanceCount!==void 0?k._maxInstanceCount:1/0,_e=Math.min(k.instanceCount,Tt);tt.renderInstances(ye,pt,_e)}else tt.render(ye,pt)};function il(_,L,k,O){if(D!==null&&_.isNodeMaterial)D.setObject(O,_);if(He===!0)se.setState(_,k,!1);if(_.transparent===!0&&_.side===ln&&_.forceSinglePass===!1)_.side=Bt,_.needsUpdate=!0,fs(_,L,O),_.side=Ri,_.needsUpdate=!0,fs(_,L,O),_.side=ln;else fs(_,L,O)}this.compile=function(_,L,k=null){if(k===null)k=_;if(D!==null)D.renderStart(_,L,k);if(w=he.get(k),w.init(L),A.push(w),k.traverseVisible(function(B){if(B.isLight&&B.layers.test(L.layers)){if(w.pushLight(B),B.castShadow)w.pushShadow(B)}}),_!==k)_.traverseVisible(function(B){if(B.isLight&&B.layers.test(L.layers)){if(w.pushLight(B),B.castShadow)w.pushShadow(B)}});if(w.setupLights(),D!==null)D.updateLights(w.state.lightsArray);if(je=this.localClippingEnabled,He=se.init(this.clippingPlanes,je),He===!0)se.setGlobalState(this.clippingPlanes,L);if(D!==null)we.render(w.state.shadowsArray,k,L);let O=new Set;if(_.traverse(function(B){if(!(B.isMesh||B.isPoints||B.isLine||B.isSprite))return;let pe=B.material;if(pe)if(Array.isArray(pe))for(let xe=0;xe<pe.length;xe++){let fe=pe[xe];il(fe,k,L,B),O.add(fe)}else il(pe,k,L,B),O.add(pe)}),w=A.pop(),D!==null)D.renderEnd();return O},this.compileAsync=function(_,L,k=null){let O=this.compile(_,L,k);return new Promise((B)=>{function pe(){if(O.forEach(function(xe){let ve=R.get(xe).currentProgram;if(ve===void 0||ve.isReady())O.delete(xe)}),O.size===0){B(_);return}setTimeout(pe,10)}if(Ze.get("KHR_parallel_shader_compile")!==null)pe();else setTimeout(pe,10)})};let br=null;function au(_){if(br)br(_)}function sl(){Bn.stop()}function rl(){Bn.start()}let Bn=new Mh;if(Bn.setAnimationLoop(au),typeof self<"u")Bn.setContext(self);this.setAnimationLoop=function(_){br=_,de.setAnimationLoop(_),_===null?Bn.stop():Bn.start()},de.addEventListener("sessionstart",sl),de.addEventListener("sessionend",rl),this.render=function(_,L){if(L!==void 0&&L.isCamera!==!0){Pe("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(H===!0)return;if(D!==null)D.renderStart(_,L);let k=de.enabled===!0&&de.isPresenting===!0,O=x!==null&&(G===null||k)&&x.begin(M,G);if(_.matrixWorldAutoUpdate===!0)_.updateMatrixWorld();if(L.parent===null&&L.matrixWorldAutoUpdate===!0)L.updateMatrixWorld();if(de.enabled===!0&&de.isPresenting===!0&&(x===null||x.isCompositing()===!1)){if(de.cameraAutoUpdate===!0)de.updateCamera(L);L=de.getCamera()}if(_.isScene===!0)_.onBeforeRender(M,_,L,G);if(w=he.get(_,A.length),w.init(L),w.state.textureUnits=z.getTextureUnits(),A.push(w),Ve.multiplyMatrices(L.projectionMatrix,L.matrixWorldInverse),ze.setFromProjectionMatrix(Ve,to,L.reversedDepth),je=this.localClippingEnabled,He=se.init(this.clippingPlanes,je),S=Me.get(_,E.length),S.init(),E.push(S),de.enabled===!0&&de.isPresenting===!0){let xe=M.xr.getDepthSensingMesh();if(xe!==null)wr(xe,L,-1/0,M.sortObjects)}if(wr(_,L,0,M.sortObjects),S.finish(),D!==null)D.updateLights(w.state.lightsArray);if(M.sortObjects===!0)S.sort(re,Te);if(_t=de.enabled===!1||de.isPresenting===!1||de.hasDepthSensing()===!1,_t)Ae.addToRenderList(S,_);if(this.info.render.frame++,this.info.autoReset===!0)this.info.reset();if(He===!0)se.beginShadows();let B=w.state.shadowsArray;if(we.render(B,_,L),He===!0)se.endShadows();if((O&&x.hasRenderPass())===!1){let xe=S.opaque,fe=S.transmissive;if(w.setupLights(),L.isArrayCamera){let ve=L.cameras;if(fe.length>0)for(let Se=0,Ue=ve.length;Se<Ue;Se++){let Be=ve[Se];ol(xe,fe,_,Be)}if(_t)Ae.render(_);for(let Se=0,Ue=ve.length;Se<Ue;Se++){let Be=ve[Se];al(S,_,Be,Be.viewport)}}else{if(fe.length>0)ol(xe,fe,_,L);if(_t)Ae.render(_);al(S,_,L)}}if(G!==null&&K===0)z.updateMultisampleRenderTarget(G),z.updateRenderTargetMipmap(G);if(O)x.end(M);if(_.isScene===!0)_.onAfterRender(M,_,L);if(le.resetDefaultState(),ne=-1,X=null,A.pop(),A.length>0){if(w=A[A.length-1],z.setTextureUnits(w.state.textureUnits),He===!0)se.setGlobalState(M.clippingPlanes,w.state.camera)}else w=null;if(E.pop(),E.length>0)S=E[E.length-1];else S=null;if(D!==null)D.renderEnd()};function wr(_,L,k,O){if(_.visible===!1)return;if(_.layers.test(L.layers)){if(_.isGroup)k=_.renderOrder;else if(_.isLOD){if(_.autoUpdate===!0)_.update(L)}else if(_.isLightProbeGrid)w.pushLightProbeGrid(_);else if(_.isLight){if(w.pushLight(_),_.castShadow)w.pushShadow(_)}else if(_.isSprite){if(!_.frustumCulled||_.intersectsFrustum(ze)){if(O)at.setFromMatrixPosition(_.matrixWorld).applyMatrix4(Ve);let xe=W.update(_),fe=_.material;if(fe.visible)S.push(_,xe,fe,k,at.z,null,L)}}else if(_.isMesh||_.isLine||_.isPoints){if(!_.frustumCulled||_.intersectsFrustum(ze)){let xe=W.update(_),fe=_.material;if(O){if(_.boundingSphere!==void 0){if(_.boundingSphere===null)_.computeBoundingSphere();at.copy(_.boundingSphere.center)}else{if(xe.boundingSphere===null)xe.computeBoundingSphere();at.copy(xe.boundingSphere.center)}at.applyMatrix4(_.matrixWorld).applyMatrix4(Ve)}if(Array.isArray(fe)){let ve=xe.groups;for(let Se=0,Ue=ve.length;Se<Ue;Se++){let Be=ve[Se],ye=fe[Be.materialIndex];if(ye&&ye.visible)S.push(_,xe,ye,k,at.z,Be,L)}}else if(fe.visible)S.push(_,xe,fe,k,at.z,null,L)}}}let pe=_.children;for(let xe=0,fe=pe.length;xe<fe;xe++)wr(pe[xe],L,k,O)}function al(_,L,k,O){let{opaque:B,transmissive:pe,transparent:xe}=_;if(w.setupLightsView(k),He===!0)se.setGlobalState(M.clippingPlanes,k);if(O)y.viewport(j.copy(O));if(B.length>0)ds(B,L,k);if(pe.length>0)ds(pe,L,k);if(xe.length>0)ds(xe,L,k);y.buffers.depth.setTest(!0),y.buffers.depth.setMask(!0),y.buffers.color.setMask(!0),y.setPolygonOffset(!1)}function ol(_,L,k,O){if((k.isScene===!0?k.overrideMaterial:null)!==null)return;if(w.state.transmissionRenderTarget[O.id]===void 0){let ye=Ze.has("EXT_color_buffer_half_float")||Ze.has("EXT_color_buffer_float");w.state.transmissionRenderTarget[O.id]=new Vt(1,1,{generateMipmaps:!0,type:ye?hn:en,minFilter:qn,samples:Math.max(4,ct.samples),stencilBuffer:s,resolveDepthBuffer:!1,resolveStencilBuffer:!1,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,colorSpace:ke.workingColorSpace})}let pe=w.state.transmissionRenderTarget[O.id],xe=O.viewport||j;pe.setSize(xe.z*M.transmissionResolutionScale,xe.w*M.transmissionResolutionScale);let fe=M.getRenderTarget(),ve=M.getActiveCubeFace(),Se=M.getActiveMipmapLevel();if(M.setRenderTarget(pe),M.getClearColor(Ee),it=M.getClearAlpha(),it<1)M.setClearColor(16777215,0.5);if(M.clear(),_t)Ae.render(k);let Ue=M.toneMapping;M.toneMapping=Qt;let Be=O.viewport;if(O.viewport!==void 0)O.viewport=void 0;if(w.setupLightsView(O),He===!0)se.setGlobalState(M.clippingPlanes,O);if(ds(_,k,O),z.updateMultisampleRenderTarget(pe),z.updateRenderTargetMipmap(pe),Ze.has("WEBGL_multisampled_render_to_texture")===!1){let ye=!1;for(let Ke=0,pt=L.length;Ke<pt;Ke++){let ot=L[Ke],{object:tt,geometry:Tt,material:_e,group:Lt}=ot;if(_e.side===ln&&tt.layers.test(O.layers)){let We=_e.side;_e.side=Bt,_e.needsUpdate=!0,ll(tt,k,O,Tt,_e,Lt),_e.side=We,_e.needsUpdate=!0,ye=!0}}if(ye===!0)z.updateMultisampleRenderTarget(pe),z.updateRenderTargetMipmap(pe)}if(M.setRenderTarget(fe,ve,Se),M.setClearColor(Ee,it),Be!==void 0)O.viewport=Be;M.toneMapping=Ue}function ds(_,L,k){let O=L.isScene===!0?L.overrideMaterial:null;for(let B=0,pe=_.length;B<pe;B++){let xe=_[B],{object:fe,geometry:ve,group:Se}=xe,Ue=xe.material;if(Ue.allowOverride===!0&&O!==null)Ue=O;if(fe.layers.test(k.layers))ll(fe,L,k,ve,Ue,Se)}}function ll(_,L,k,O,B,pe){if(D!==null&&B.isNodeMaterial)D.setObject(_,B);if(_.onBeforeRender(M,L,k,O,B,pe),_.modelViewMatrix.multiplyMatrices(k.matrixWorldInverse,_.matrixWorld),_.normalMatrix.getNormalMatrix(_.modelViewMatrix),B.onBeforeRender(M,L,k,O,_,pe),B.transparent===!0&&B.side===ln&&B.forceSinglePass===!1)B.side=Bt,B.needsUpdate=!0,M.renderBufferDirect(k,L,O,B,_,pe),B.side=Ri,B.needsUpdate=!0,M.renderBufferDirect(k,L,O,B,_,pe),B.side=ln;else M.renderBufferDirect(k,L,O,B,_,pe);_.onAfterRender(M,L,k,O,B,pe)}function fs(_,L,k){if(L.isScene!==!0)L=Ut;let O=R.get(_),B=w.state.lights,pe=w.state.shadowsArray,xe=B.state.version,fe=Z.getParameters(_,B.state,pe,L,k,w.state.lightProbeGridArray),ve=Z.getProgramCacheKey(fe),Se=O.programs;O.environment=_.isMeshStandardMaterial||_.isMeshLambertMaterial||_.isMeshPhongMaterial?L.environment:null,O.fog=L.fog;let Ue=_.isMeshStandardMaterial||_.isMeshLambertMaterial&&!_.envMap||_.isMeshPhongMaterial&&!_.envMap;if(O.envMap=ee.get(_.envMap||O.environment,Ue),O.envMapRotation=O.environment!==null&&_.envMap===null?L.environmentRotation:_.envMapRotation,Se===void 0)_.addEventListener("dispose",nn),Se=new Map,O.programs=Se;let Be=Se.get(ve);if(Be!==void 0){if(O.currentProgram===Be&&O.lightsStateVersion===xe)return hl(_,fe),Be}else{if(fe.uniforms=Z.getUniforms(_),D!==null&&_.isNodeMaterial)D.build(_,k,fe);_.onBeforeCompile(fe,M),Be=Z.acquireProgram(fe,ve),Se.set(ve,Be),O.uniforms=fe.uniforms}let ye=O.uniforms;if(!_.isShaderMaterial&&!_.isRawShaderMaterial||_.clipping===!0)ye.clippingPlanes=se.uniform;if(hl(_,fe),O.needsLights=hu(_),O.lightsStateVersion=xe,O.needsLights)ye.ambientLightColor.value=B.state.ambient,ye.lightProbe.value=B.state.probe,ye.sunLights.value=B.state.sun,ye.sunLightShadows.value=B.state.sunShadow,ye.directionalLights.value=B.state.directional,ye.directionalLightShadows.value=B.state.directionalShadow,ye.spotLights.value=B.state.spot,ye.spotLightShadows.value=B.state.spotShadow,ye.rectAreaLights.value=B.state.rectArea,ye.ltc_1.value=B.state.rectAreaLTC1,ye.ltc_2.value=B.state.rectAreaLTC2,ye.pointLights.value=B.state.point,ye.pointLightShadows.value=B.state.pointShadow,ye.hemisphereLights.value=B.state.hemi,ye.sunShadowMatrix.value=B.state.sunShadowMatrix,ye.sunShadowCascade.value=B.state.sunShadowCascade,ye.directionalShadowMatrix.value=B.state.directionalShadowMatrix,ye.spotLightMatrix.value=B.state.spotLightMatrix,ye.spotLightMap.value=B.state.spotLightMap,ye.pointShadowMatrix.value=B.state.pointShadowMatrix;return O.lightProbeGrid=w.state.lightProbeGridArray.length>0,O.currentProgram=Be,O.uniformsList=null,Be}function cl(_){if(_.uniformsList===null){let L=_.currentProgram.getUniforms();_.uniformsList=cs.seqWithValue(L.seq,_.uniforms)}return _.uniformsList}function hl(_,L){let k=R.get(_);k.outputColorSpace=L.outputColorSpace,k.batching=L.batching,k.batchingColor=L.batchingColor,k.instancing=L.instancing,k.instancingColor=L.instancingColor,k.instancingMorph=L.instancingMorph,k.skinning=L.skinning,k.morphTargets=L.morphTargets,k.morphNormals=L.morphNormals,k.morphColors=L.morphColors,k.morphTargetsCount=L.morphTargetsCount,k.numClippingPlanes=L.numClippingPlanes,k.numIntersection=L.numClipIntersection,k.vertexAlphas=L.vertexAlphas,k.vertexTangents=L.vertexTangents,k.toneMapping=L.toneMapping}function ou(_,L){if(_.length===0)return null;if(_.length===1)return _[0].texture!==null?_[0]:null;I.setFromMatrixPosition(L.matrixWorld);for(let k=0,O=_.length;k<O;k++){let B=_[k];if(B.texture!==null&&B.boundingBox.containsPoint(I))return B}return null}function lu(_,L,k,O,B){if(L.isScene!==!0)L=Ut;z.resetTextureUnits();let pe=L.fog,xe=O.isMeshStandardMaterial||O.isMeshLambertMaterial||O.isMeshPhongMaterial?L.environment:null,fe=G===null?M.outputColorSpace:G.isXRRenderTarget===!0?G.texture.colorSpace:ke.workingColorSpace,ve=O.isMeshStandardMaterial||O.isMeshLambertMaterial&&!O.envMap||O.isMeshPhongMaterial&&!O.envMap,Se=ee.get(O.envMap||xe,ve),Ue=O.vertexColors===!0&&!!k.attributes.color&&k.attributes.color.itemSize===4,Be=!!k.attributes.tangent&&(!!O.normalMap||O.anisotropy>0),ye=!!k.morphAttributes.position,Ke=!!k.morphAttributes.normal,pt=!!k.morphAttributes.color,ot=Qt;if(O.toneMapped){if(G===null||G.isXRRenderTarget===!0)ot=M.toneMapping}let tt=k.morphAttributes.position||k.morphAttributes.normal||k.morphAttributes.color,Tt=tt!==void 0?tt.length:0,_e=R.get(O),Lt=w.state.lights;if(He===!0){if(je===!0||_!==X){let rt=_===X&&O.id===ne;se.setState(O,_,rt)}}let We=!1;if(O.version===_e.__version){if(_e.needsLights&&_e.lightsStateVersion!==Lt.state.version)We=!0;else if(_e.outputColorSpace!==fe)We=!0;else if(B.isBatchedMesh&&_e.batching===!1)We=!0;else if(!B.isBatchedMesh&&_e.batching===!0)We=!0;else if(B.isBatchedMesh&&_e.batchingColor===!0&&B._colorsTexture===null)We=!0;else if(B.isBatchedMesh&&_e.batchingColor===!1&&B._colorsTexture!==null)We=!0;else if(B.isInstancedMesh&&_e.instancing===!1)We=!0;else if(!B.isInstancedMesh&&_e.instancing===!0)We=!0;else if(B.isSkinnedMesh&&_e.skinning===!1)We=!0;else if(!B.isSkinnedMesh&&_e.skinning===!0)We=!0;else if(B.isInstancedMesh&&_e.instancingColor===!0&&B.instanceColor===null)We=!0;else if(B.isInstancedMesh&&_e.instancingColor===!1&&B.instanceColor!==null)We=!0;else if(B.isInstancedMesh&&_e.instancingMorph===!0&&B.morphTexture===null)We=!0;else if(B.isInstancedMesh&&_e.instancingMorph===!1&&B.morphTexture!==null)We=!0;else if(_e.envMap!==Se)We=!0;else if(O.fog===!0&&_e.fog!==pe)We=!0;else if(_e.numClippingPlanes!==void 0&&(_e.numClippingPlanes!==se.numPlanes||_e.numIntersection!==se.numIntersection))We=!0;else if(_e.vertexAlphas!==Ue)We=!0;else if(_e.vertexTangents!==Be)We=!0;else if(_e.morphTargets!==ye)We=!0;else if(_e.morphNormals!==Ke)We=!0;else if(_e.morphColors!==pt)We=!0;else if(_e.toneMapping!==ot)We=!0;else if(_e.morphTargetsCount!==Tt)We=!0;else if(!!_e.lightProbeGrid!==w.state.lightProbeGridArray.length>0)We=!0}else We=!0,_e.__version=O.version;let Wt=_e.currentProgram;if(We===!0){if(Wt=fs(O,L,B),D&&O.isNodeMaterial)D.onUpdateProgram(O,Wt,_e)}let sn=!1,wn=!1,oi=!1,et=Wt.getUniforms(),dt=_e.uniforms;if(y.useProgram(Wt.program))sn=!0,wn=!0,oi=!0;if(O.id!==ne)ne=O.id,wn=!0;if(_e.needsLights){let rt=ou(w.state.lightProbeGridArray,B);if(_e.lightProbeGrid!==rt)_e.lightProbeGrid=rt,wn=!0}if(sn||X!==_){if(y.buffers.depth.getReversed()&&_.reversedDepth!==!0)_._reversedDepth=!0,_.updateProjectionMatrix();et.setValue(P,"projectionMatrix",_.projectionMatrix),et.setValue(P,"viewMatrix",_.matrixWorldInverse);let Tn=et.map.cameraPosition;if(Tn!==void 0)Tn.setValue(P,Et.setFromMatrixPosition(_.matrixWorld));if(ct.logarithmicDepthBuffer)et.setValue(P,"logDepthBufFC",2/(Math.log(_.far+1)/Math.LN2));if(O.isMeshPhongMaterial||O.isMeshToonMaterial||O.isMeshLambertMaterial||O.isMeshBasicMaterial||O.isMeshStandardMaterial||O.isShaderMaterial)et.setValue(P,"isOrthographic",_.isOrthographicCamera===!0);if(X!==_)X=_,wn=!0,oi=!0}if(_e.needsLights){if(Lt.state.sunShadowMap.length>0)et.setValue(P,"sunShadowMap",Lt.state.sunShadowMap,z);if(Lt.state.directionalShadowMap.length>0)et.setValue(P,"directionalShadowMap",Lt.state.directionalShadowMap,z);if(Lt.state.spotShadowMap.length>0)et.setValue(P,"spotShadowMap",Lt.state.spotShadowMap,z);if(Lt.state.pointShadowMap.length>0)et.setValue(P,"pointShadowMap",Lt.state.pointShadowMap,z)}if(B.isSkinnedMesh){et.setOptional(P,B,"bindMatrix"),et.setOptional(P,B,"bindMatrixInverse");let rt=B.skeleton;if(rt){if(rt.boneTexture===null)rt.computeBoneTexture();et.setValue(P,"boneTexture",rt.boneTexture,z)}}if(B.isBatchedMesh){if(et.setOptional(P,B,"batchingTexture"),et.setValue(P,"batchingTexture",B._matricesTexture,z),et.setOptional(P,B,"batchingIdTexture"),et.setValue(P,"batchingIdTexture",B._indirectTexture,z),et.setOptional(P,B,"batchingColorTexture"),B._colorsTexture!==null)et.setValue(P,"batchingColorTexture",B._colorsTexture,z)}let En=k.morphAttributes;if(En.position!==void 0||En.normal!==void 0||En.color!==void 0)$e.update(B,k,Wt);if(wn||_e.receiveShadow!==B.receiveShadow)_e.receiveShadow=B.receiveShadow,et.setValue(P,"receiveShadow",B.receiveShadow);if((O.isMeshStandardMaterial||O.isMeshLambertMaterial||O.isMeshPhongMaterial)&&O.envMap===null&&L.environment!==null)dt.envMapIntensity.value=L.environmentIntensity;if(dt.dfgLUT!==void 0)dt.dfgLUT.value=zg();if(wn){if(et.setValue(P,"toneMappingExposure",M.toneMappingExposure),_e.needsLights)cu(dt,oi);if(pe&&O.fog===!0)me.refreshFogUniforms(dt,pe);if(me.refreshMaterialUniforms(dt,O,ie,q,w.state.transmissionRenderTarget[_.id]),_e.needsLights&&_e.lightProbeGrid){let rt=_e.lightProbeGrid;dt.probesSH.value=rt.texture,dt.probesMin.value.copy(rt.boundingBox.min),dt.probesMax.value.copy(rt.boundingBox.max),dt.probesResolution.value.copy(rt.resolution)}cs.upload(P,cl(_e),dt,z)}if(O.isShaderMaterial&&O.uniformsNeedUpdate===!0)cs.upload(P,cl(_e),dt,z),O.uniformsNeedUpdate=!1;if(O.isSpriteMaterial)et.setValue(P,"center",B.center);if(et.setValue(P,"modelViewMatrix",B.modelViewMatrix),et.setValue(P,"normalMatrix",B.normalMatrix),et.setValue(P,"modelMatrix",B.matrixWorld),O.uniformsGroups!==void 0){let rt=O.uniformsGroups;for(let Tn=0,li=rt.length;Tn<li;Tn++){let dl=rt[Tn];ge.update(dl,Wt),ge.bind(dl,Wt)}}return Wt}function cu(_,L){_.ambientLightColor.needsUpdate=L,_.lightProbe.needsUpdate=L,_.sunLights.needsUpdate=L,_.sunLightShadows.needsUpdate=L,_.directionalLights.needsUpdate=L,_.directionalLightShadows.needsUpdate=L,_.pointLights.needsUpdate=L,_.pointLightShadows.needsUpdate=L,_.spotLights.needsUpdate=L,_.spotLightShadows.needsUpdate=L,_.rectAreaLights.needsUpdate=L,_.hemisphereLights.needsUpdate=L}function hu(_){return _.isMeshLambertMaterial||_.isMeshToonMaterial||_.isMeshPhongMaterial||_.isMeshStandardMaterial||_.isShadowMaterial||_.isShaderMaterial&&_.lights===!0}this.getActiveCubeFace=function(){return V},this.getActiveMipmapLevel=function(){return K},this.getRenderTarget=function(){return G},this.setRenderTargetTextures=function(_,L,k){let O=R.get(_);if(O.__autoAllocateDepthBuffer=_.resolveDepthBuffer===!1,O.__autoAllocateDepthBuffer===!1)O.__useRenderToTexture=!1;R.get(_.texture).__webglTexture=L,R.get(_.depthTexture).__webglTexture=O.__autoAllocateDepthBuffer?void 0:k,O.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(_,L){let k=R.get(_);k.__webglFramebuffer=L,k.__useDefaultFramebuffer=L===void 0},this.setRenderTarget=function(_,L=0,k=0){G=_,V=L,K=k;let O=null,B=!1,pe=!1;if(_){let fe=R.get(_);if(fe.__useDefaultFramebuffer!==void 0){y.bindFramebuffer(P.FRAMEBUFFER,fe.__webglFramebuffer),j.copy(_.viewport),te.copy(_.scissor),Re=_.scissorTest,y.viewport(j),y.scissor(te),y.setScissorTest(Re),ne=-1;return}else if(fe.__webglFramebuffer===void 0)z.setupRenderTarget(_);else if(fe.__hasExternalTextures)z.rebindTextures(_,R.get(_.texture).__webglTexture,R.get(_.depthTexture).__webglTexture);else if(_.depthBuffer){let Ue=_.depthTexture;if(fe.__boundDepthTexture!==Ue){if(Ue!==null&&R.has(Ue)&&(_.width!==Ue.image.width||_.height!==Ue.image.height))throw Error("THREE.WebGLRenderer: Attached DepthTexture is initialized to the incorrect size.");z.setupDepthRenderbuffer(_)}}let ve=_.texture;if(ve.isData3DTexture||ve.isDataArrayTexture||ve.isCompressedArrayTexture)pe=!0;let Se=R.get(_).__webglFramebuffer;if(_.isWebGLCubeRenderTarget){if(Array.isArray(Se[L]))O=Se[L][k];else O=Se[L];B=!0}else if(_.samples>0&&z.useMultisampledRTT(_)===!1)O=R.get(_).__webglMultisampledFramebuffer;else if(Array.isArray(Se))O=Se[k];else O=Se;j.copy(_.viewport),te.copy(_.scissor),Re=_.scissorTest}else j.copy(Ie).multiplyScalar(ie).floor(),te.copy(be).multiplyScalar(ie).floor(),Re=gt;if(k!==0)O=U;if(y.bindFramebuffer(P.FRAMEBUFFER,O))y.drawBuffers(_,O);if(y.viewport(j),y.scissor(te),y.setScissorTest(Re),B){let fe=R.get(_.texture);P.framebufferTexture2D(P.FRAMEBUFFER,P.COLOR_ATTACHMENT0,P.TEXTURE_CUBE_MAP_POSITIVE_X+L,fe.__webglTexture,k)}else if(pe){let fe=L;for(let ve=0;ve<_.textures.length;ve++){let Se=R.get(_.textures[ve]);P.framebufferTextureLayer(P.FRAMEBUFFER,P.COLOR_ATTACHMENT0+ve,Se.__webglTexture,k,fe)}}else if(_!==null&&k!==0){let fe=R.get(_.texture);P.framebufferTexture2D(P.FRAMEBUFFER,P.COLOR_ATTACHMENT0,P.TEXTURE_2D,fe.__webglTexture,k)}ne=-1};function ul(_){let L=R.get(_);if(L.__readFormat!==_.format||L.__readType!==_.type)L.__readFormat=_.format,L.__readType=_.type,L.__formatReadable=ct.textureFormatReadable(_.format),L.__typeReadable=ct.textureTypeReadable(_.type);return L}if(this.readRenderTargetPixels=function(_,L,k,O,B,pe,xe,fe=0){if(!(_&&_.isWebGLRenderTarget)){Pe("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let ve=R.get(_).__webglFramebuffer;if(_.isWebGLCubeRenderTarget&&xe!==void 0)ve=ve[xe];if(ve){y.bindFramebuffer(P.FRAMEBUFFER,ve);try{let Se=_.textures[fe],{format:Ue,type:Be}=Se;if(_.textures.length>1)P.readBuffer(P.COLOR_ATTACHMENT0+fe);let ye=ul(Se);if(ye.__formatReadable===!1){Pe("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(ye.__typeReadable===!1){Pe("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}if(L>=0&&L<=_.width-O&&(k>=0&&k<=_.height-B))P.readPixels(L,k,O,B,Y.convert(Ue),Y.convert(Be),pe)}finally{let Se=G!==null?R.get(G).__webglFramebuffer:null;y.bindFramebuffer(P.FRAMEBUFFER,Se)}}},this.readRenderTargetPixelsAsync=async function(_,L,k,O,B,pe,xe,fe=0){if(!(_&&_.isWebGLRenderTarget))throw Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let ve=R.get(_).__webglFramebuffer;if(_.isWebGLCubeRenderTarget&&xe!==void 0)ve=ve[xe];if(ve)if(L>=0&&L<=_.width-O&&(k>=0&&k<=_.height-B)){y.bindFramebuffer(P.FRAMEBUFFER,ve);let Se=_.textures[fe],{format:Ue,type:Be}=Se;if(_.textures.length>1)P.readBuffer(P.COLOR_ATTACHMENT0+fe);let ye=ul(Se);if(ye.__formatReadable===!1)throw Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(ye.__typeReadable===!1)throw Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let Ke=P.createBuffer();P.bindBuffer(P.PIXEL_PACK_BUFFER,Ke),P.bufferData(P.PIXEL_PACK_BUFFER,pe.byteLength,P.STREAM_READ),P.readPixels(L,k,O,B,Y.convert(Ue),Y.convert(Be),0),P.bindBuffer(P.PIXEL_PACK_BUFFER,null);let pt=G!==null?R.get(G).__webglFramebuffer:null;y.bindFramebuffer(P.FRAMEBUFFER,pt);let ot=P.fenceSync(P.SYNC_GPU_COMMANDS_COMPLETE,0);return P.flush(),await Yc(P,ot,4),P.bindBuffer(P.PIXEL_PACK_BUFFER,Ke),P.getBufferSubData(P.PIXEL_PACK_BUFFER,0,pe),P.bindBuffer(P.PIXEL_PACK_BUFFER,null),P.deleteBuffer(Ke),P.deleteSync(ot),pe}else throw Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(_,L=null,k=0){let O=Math.pow(2,-k),B=Math.floor(_.image.width*O),pe=Math.floor(_.image.height*O),xe=L!==null?L.x:0,fe=L!==null?L.y:0;z.setTexture2D(_,0),P.copyTexSubImage2D(P.TEXTURE_2D,k,0,0,xe,fe,B,pe),y.unbindTexture()},this.copyTextureToTexture=function(_,L,k=null,O=null,B=0,pe=0){let xe,fe,ve,Se,Ue,Be,ye,Ke,pt,ot=_.isCompressedTexture?_.mipmaps[pe]:_.image;if(k!==null)xe=k.max.x-k.min.x,fe=k.max.y-k.min.y,ve=k.isBox3?k.max.z-k.min.z:1,Se=k.min.x,Ue=k.min.y,Be=k.isBox3?k.min.z:0;else{let dt=Math.pow(2,-B);if(xe=Math.floor(ot.width*dt),fe=Math.floor(ot.height*dt),_.isDataArrayTexture)ve=ot.depth;else if(_.isData3DTexture)ve=Math.floor(ot.depth*dt);else ve=1;Se=0,Ue=0,Be=0}if(O!==null)ye=O.x,Ke=O.y,pt=O.z;else ye=0,Ke=0,pt=0;let tt=Y.convert(L.format),Tt=Y.convert(L.type),_e;if(L.isData3DTexture)z.setTexture3D(L,0),_e=P.TEXTURE_3D;else if(L.isDataArrayTexture||L.isCompressedArrayTexture)z.setTexture2DArray(L,0),_e=P.TEXTURE_2D_ARRAY;else z.setTexture2D(L,0),_e=P.TEXTURE_2D;y.activeTexture(P.TEXTURE0),y.pixelStorei(P.UNPACK_FLIP_Y_WEBGL,L.flipY),y.pixelStorei(P.UNPACK_PREMULTIPLY_ALPHA_WEBGL,L.premultiplyAlpha),y.pixelStorei(P.UNPACK_ALIGNMENT,L.unpackAlignment);let Lt=y.getParameter(P.UNPACK_ROW_LENGTH),We=y.getParameter(P.UNPACK_IMAGE_HEIGHT),Wt=y.getParameter(P.UNPACK_SKIP_PIXELS),sn=y.getParameter(P.UNPACK_SKIP_ROWS),wn=y.getParameter(P.UNPACK_SKIP_IMAGES);y.pixelStorei(P.UNPACK_ROW_LENGTH,ot.width),y.pixelStorei(P.UNPACK_IMAGE_HEIGHT,ot.height),y.pixelStorei(P.UNPACK_SKIP_PIXELS,Se),y.pixelStorei(P.UNPACK_SKIP_ROWS,Ue),y.pixelStorei(P.UNPACK_SKIP_IMAGES,Be);let oi=_.isDataArrayTexture||_.isData3DTexture,et=L.isDataArrayTexture||L.isData3DTexture;if(_.isDepthTexture){let dt=R.get(_),En=R.get(L),rt=R.get(dt.__renderTarget),Tn=R.get(En.__renderTarget);y.bindFramebuffer(P.READ_FRAMEBUFFER,rt.__webglFramebuffer),y.bindFramebuffer(P.DRAW_FRAMEBUFFER,Tn.__webglFramebuffer);for(let li=0;li<ve;li++){if(oi)P.framebufferTextureLayer(P.READ_FRAMEBUFFER,P.COLOR_ATTACHMENT0,R.get(_).__webglTexture,B,Be+li),P.framebufferTextureLayer(P.DRAW_FRAMEBUFFER,P.COLOR_ATTACHMENT0,R.get(L).__webglTexture,pe,pt+li);P.blitFramebuffer(Se,Ue,xe,fe,ye,Ke,xe,fe,P.DEPTH_BUFFER_BIT,P.NEAREST)}y.bindFramebuffer(P.READ_FRAMEBUFFER,null),y.bindFramebuffer(P.DRAW_FRAMEBUFFER,null)}else if(B!==0||_.isRenderTargetTexture||R.has(_)){let dt=R.get(_),En=R.get(L);y.bindFramebuffer(P.READ_FRAMEBUFFER,J),y.bindFramebuffer(P.DRAW_FRAMEBUFFER,C);for(let rt=0;rt<ve;rt++){if(oi)P.framebufferTextureLayer(P.READ_FRAMEBUFFER,P.COLOR_ATTACHMENT0,dt.__webglTexture,B,Be+rt);else P.framebufferTexture2D(P.READ_FRAMEBUFFER,P.COLOR_ATTACHMENT0,P.TEXTURE_2D,dt.__webglTexture,B);if(et)P.framebufferTextureLayer(P.DRAW_FRAMEBUFFER,P.COLOR_ATTACHMENT0,En.__webglTexture,pe,pt+rt);else P.framebufferTexture2D(P.DRAW_FRAMEBUFFER,P.COLOR_ATTACHMENT0,P.TEXTURE_2D,En.__webglTexture,pe);if(B!==0)P.blitFramebuffer(Se,Ue,xe,fe,ye,Ke,xe,fe,P.COLOR_BUFFER_BIT,P.NEAREST);else if(et)P.copyTexSubImage3D(_e,pe,ye,Ke,pt+rt,Se,Ue,xe,fe);else P.copyTexSubImage2D(_e,pe,ye,Ke,Se,Ue,xe,fe)}y.bindFramebuffer(P.READ_FRAMEBUFFER,null),y.bindFramebuffer(P.DRAW_FRAMEBUFFER,null)}else if(et)if(_.isDataTexture||_.isData3DTexture)P.texSubImage3D(_e,pe,ye,Ke,pt,xe,fe,ve,tt,Tt,ot.data);else if(L.isCompressedArrayTexture)P.compressedTexSubImage3D(_e,pe,ye,Ke,pt,xe,fe,ve,tt,ot.data);else P.texSubImage3D(_e,pe,ye,Ke,pt,xe,fe,ve,tt,Tt,ot);else if(_.isDataTexture)P.texSubImage2D(P.TEXTURE_2D,pe,ye,Ke,xe,fe,tt,Tt,ot.data);else if(_.isCompressedTexture)P.compressedTexSubImage2D(P.TEXTURE_2D,pe,ye,Ke,ot.width,ot.height,tt,ot.data);else P.texSubImage2D(P.TEXTURE_2D,pe,ye,Ke,xe,fe,tt,Tt,ot);if(y.pixelStorei(P.UNPACK_ROW_LENGTH,Lt),y.pixelStorei(P.UNPACK_IMAGE_HEIGHT,We),y.pixelStorei(P.UNPACK_SKIP_PIXELS,Wt),y.pixelStorei(P.UNPACK_SKIP_ROWS,sn),y.pixelStorei(P.UNPACK_SKIP_IMAGES,wn),pe===0&&L.generateMipmaps)P.generateMipmap(_e);y.unbindTexture()},this.initRenderTarget=function(_){if(R.get(_).__webglFramebuffer===void 0)z.setupRenderTarget(_)},this.initTexture=function(_){if(_.isCubeTexture)z.setTextureCube(_,0);else if(_.isData3DTexture)z.setTexture3D(_,0);else if(_.isDataArrayTexture||_.isCompressedArrayTexture)z.setTexture2DArray(_,0);else z.setTexture2D(_,0);y.unbindTexture()},this.resetState=function(){V=0,K=0,G=null,y.reset(),le.reset()},typeof __THREE_DEVTOOLS__<"u")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return to}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;let t=this.getContext();t.drawingBufferColorSpace=ke._getDrawingBufferColorSpace(e),t.unpackColorSpace=ke._getUnpackColorSpace()}}function Fh(e,t){let[n,i,s]=e,r=Math.cos(t),a=Math.sin(t);return[r*n-a*i,a*n+r*i,s]}function Gg(e,t,n){let[i,s,r]=e,a=Math.sqrt(1-t)*(1-n);return[a*i,a*s,(1-t)*r+t]}function hs(e,{idle:t=0.7,gate:n=0.3,dd:i=!1,twirl:s=!1,damping:r=0,dephasing:a=0}={}){let o=Fh(e,i?0:t),c=s?[o[0]*Math.cos(n),o[1]*Math.cos(n),o[2]]:Fh(o,n);return Gg(c,r,a)}function ko(e){let t=e.length,n=e.map((s)=>s.slice()),i=Array.from({length:t},(s,r)=>Array.from({length:t},(a,o)=>+(r===o)));for(let s=0;s<100;s++){let r=0,a=1,o=0;for(let v=0;v<t;v++)for(let b=v+1;b<t;b++)if(Math.abs(n[v][b])>o)o=Math.abs(n[v][b]),r=v,a=b;if(o<0.000000000001)break;let c=0.5*Math.atan2(2*n[r][a],n[a][a]-n[r][r]),l=Math.cos(c),u=Math.sin(c),d=n[r][r],h=n[a][a],m=n[r][a];for(let v=0;v<t;v++)if(v!==r&&v!==a){let b=n[v][r],p=n[v][a];n[v][r]=n[r][v]=l*b-u*p,n[v][a]=n[a][v]=u*b+l*p}n[r][r]=l*l*d-2*u*l*m+u*u*h,n[a][a]=u*u*d+2*u*l*m+l*l*h,n[r][a]=n[a][r]=0;for(let v=0;v<t;v++){let b=i[v][r],p=i[v][a];i[v][r]=l*b-u*p,i[v][a]=u*b+l*p}}return Array.from({length:t},(s,r)=>({value:n[r][r],vector:i.map((a)=>a[r])})).sort((s,r)=>r.value-s.value)}function Oh(e,t=e.length){let n=ko(e),i=e.length;return Array.from({length:i},(s,r)=>Array.from({length:i},(a,o)=>n.slice(0,t).reduce((c,l)=>c+Math.max(0,l.value)*l.vector[r]*l.vector[o],0)))}var Go=(e,t)=>Math.sqrt(e.reduce((n,i,s)=>n+i.reduce((r,a,o)=>r+(a-t[s][o])**2,0),0));function Bh(e,t=0.08,n=0.08){return n+(1-t-n)*e}function zh(e,t=0.08,n=0.08){return(e-n)/(1-t-n)}var Ho=(e)=>e.reduce((t,n)=>t+n,0)===4;class Vo{constructor(e){e.classList.add("lens-fallback"),e.innerHTML=`<svg viewBox="0 0 220 210" role="img" aria-label="Bloch-vector x/z projection">
      <desc id="fallback-description"></desc>
      <circle cx="110" cy="100" r="70" class="fallback-grid"/>
      <ellipse cx="110" cy="100" rx="70" ry="18" class="fallback-grid"/>
      <ellipse cx="110" cy="100" rx="24" ry="70" class="fallback-grid"/>
      <path d="M40 100H180 M110 30V170" class="fallback-grid"/>
      <text x="110" y="22">|0⟩</text><text x="110" y="184">|1⟩</text>
      <line id="fallback-vector" x1="110" y1="100" x2="110" y2="100"/>
      <circle id="fallback-tip" cx="110" cy="100" r="3"/>
      <text id="fallback-readout" x="110" y="205"></text>
    </svg>`,this.host=e,this.line=e.querySelector("#fallback-vector"),this.tip=e.querySelector("#fallback-tip"),this.readout=e.querySelector("#fallback-readout"),this.description=e.querySelector("#fallback-description")}render([e,t,n]){let i=110+70*e,s=100-70*n;this.line.setAttribute("x2",i),this.line.setAttribute("y2",s),this.tip.setAttribute("cx",i),this.tip.setAttribute("cy",s);let r=Math.hypot(e,t,n);this.readout.textContent=`x/z projection · |r| ${r.toFixed(2)}`,this.description.textContent=`GPU unavailable. Same illustrative Bloch vector: x ${e.toFixed(3)}, y ${t.toFixed(3)}, z ${n.toFixed(3)}. Probability of zero ${((1+n)/2).toFixed(3)}. The y coordinate is outside this projection; projected length is not purity.`,this.host.dataset.vector=JSON.stringify([e,t,n])}}function Hg(e,t,n=0,i=0){let s=Math.sqrt(1-n)*(1-i);return[s*Math.sin(e)*Math.cos(t),(1-n)*Math.cos(e)+n,s*Math.sin(e)*Math.sin(t)]}class Wo{constructor(){this.host=document.querySelector("#sphere"),this.theta=Math.PI/2,this.phi=0,this.target=this.theta,this.damping=0,this.dephasing=0,this.reduced=matchMedia("(prefers-reduced-motion: reduce)").matches,this.animate=this.animate.bind(this);try{this.setup()}catch(t){this.fallback=new Vo(this.host),console.warn("Quantum lens WebGL unavailable")}if(this.renderer)this.host.insertAdjacentHTML("beforeend",'<span class="sphere-pole north">|0⟩</span><span class="sphere-pole south">|1⟩</span>');let e;if(this.renderer)this.host.addEventListener("pointerdown",(t)=>{e=t.clientX,this.host.setPointerCapture(t.pointerId)});this.host.addEventListener("pointermove",(t)=>{if(e!==void 0)this.group.rotation.y+=(t.clientX-e)*0.01,e=t.clientX,this.schedule()}),this.host.addEventListener("pointerup",()=>e=void 0),this.host.addEventListener("pointercancel",()=>e=void 0),new ResizeObserver(()=>this.resize()).observe(this.host),this.resize(),document.addEventListener("visibilitychange",()=>this.schedule()),matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change",(t)=>{this.reduced=t.matches,this.schedule()}),this.schedule()}setup(){this.renderer=new zo({alpha:!0,antialias:!0}),this.renderer.setPixelRatio(Math.min(devicePixelRatio,2)),this.host.append(this.renderer.domElement),this.scene=new nr,this.camera=new Nt(35,1,0.1,20),this.camera.position.set(0,0.2,4.4),this.group=new Ln,this.group.rotation.set(0.1,-0.55,0),this.scene.add(this.group);let e=new Qn({color:5665898,transparent:!0,opacity:0.55});for(let n=0;n<6;n++){let i=[];for(let r=0;r<=100;r++){let a=r/100*Math.PI*2;i.push(new F(Math.cos(a),Math.sin(a),0))}let s=new ei(new bt().setFromPoints(i),e);s.rotation.y=n*Math.PI/6,this.group.add(s)}for(let n of[-0.5,0,0.5]){let i=[],s=Math.sqrt(1-n*n);for(let r=0;r<=100;r++){let a=r/100*Math.PI*2;i.push(new F(s*Math.cos(a),n,s*Math.sin(a)))}this.group.add(new ei(new bt().setFromPoints(i),e))}let t=new Fn({color:10146743,transparent:!0,opacity:0.045});this.group.add(new Dt(new Ui(1,32,24),t)),this.arrow=new pr(new F(1,0,0),new F,1,15774591,0.13,0.075),this.group.add(this.arrow),this.tip=new Dt(new Ui(0.035,16,12),new Fn({color:16765343})),this.group.add(this.tip),this.trail=new ei(new bt().setAttribute("position",new Ht(new Float32Array(123),3)),new Qn({color:15774591,transparent:!0,opacity:0.3})),this.group.add(this.trail)}resize(){if(!this.renderer)return;let{width:e,height:t}=this.host.getBoundingClientRect();this.renderer.setSize(e,t,!1),this.camera.aspect=e/t,this.camera.updateProjectionMatrix(),this.schedule()}setNoise(e){Object.assign(this,e),this.schedule()}schedule(){if(!this.animate||this.pending||document.hidden)return;this.pending=!0,requestAnimationFrame(()=>{this.pending=!1,this.animate()})}update(e){this.target=e?Math.PI*(0.15+0.7*Math.tanh(e.size/2)):Math.PI/2,this.phi=e?e.x*Math.PI*2:0,document.querySelector("#angle-readout").textContent=`θ ${Math.round(this.target/Math.PI*180)}°`,this.schedule()}animate(){this.theta=this.reduced?this.target:this.theta+(this.target-this.theta)*0.055;let e=[Math.sin(this.theta)*Math.cos(this.phi),Math.sin(this.theta)*Math.sin(this.phi),Math.cos(this.theta)],t=hs(e,{idle:this.management?0.7:0,gate:this.management?0.3:0,dd:this.dd,twirl:this.twirl,damping:this.damping,dephasing:this.dephasing});if(this.fallback){if(this.fallback.render(t),Math.abs(this.target-this.theta)>0.0001)this.schedule();return}let n=new F(t[0],t[2],t[1]),i=n.length();this.arrow.setDirection(i>0.000001?n.clone().normalize():new F(0,1,0)),this.arrow.setLength(Math.max(i,0.001),Math.min(0.13,i*0.25),0.075),this.tip.position.copy(n);let s=this.trail.geometry.attributes.position;for(let r=0;r<=40;r++){let a=Hg(r/40*this.theta,this.phi);s.setXYZ(r,...a)}if(s.needsUpdate=!0,this.renderer.render(this.scene,this.camera),Math.abs(this.target-this.theta)>0.0001)this.schedule()}}class Xo{constructor(e,t){this.bench=e,this.names=t,this.mode="projected",this.dialog=document.createElement("dialog"),this.dialog.id="bench-dialog",this.dialog.setAttribute("aria-labelledby","bench-title"),this.dialog.innerHTML=`
      <button class="close" id="bench-close" aria-label="Close feature inspection">×</button>
      <span class="eyebrow">Sample-based feature selection</span>
      <h2 id="bench-title">Sampled Hamiltonian</h2>
      <p class="bench-scope">Selection-proxy costs, not forecast errors. Classical minimum = diagonal SQD.</p>
      <div class="bench-controls">
        <button id="bench-draw">Draw 4 subsets</button>
        <button id="bench-projected" aria-pressed="true">Sampled H</button>
        <button id="bench-redundancy" aria-pressed="false">Redundancy</button>
      </div>
      <div id="bench-visual"></div>
      <div class="bench-minima">
        <div><span>Sampled SQD minimum</span><b id="bench-sqd"></b></div>
        <div><span>Classical sampled minimum</span><b id="bench-classical"></b></div>
        <div><span>All 210 subsets</span><b id="bench-exact"></b></div>
      </div>
      <div id="bench-basis"></div>
      <p id="bench-explanation"></p>
      <small>Local browser arithmetic on saved training coefficients; no addon or hardware runs here.
        These costs measure relevance/redundancy, not predictive error. Diagonal SQD equals the best sampled cost.</small>`,document.body.append(this.dialog),this.dialog.querySelector("#bench-close").onclick=()=>this.dialog.close(),this.dialog.querySelector("#bench-draw").onclick=()=>e.sample();for(let n of["projected","redundancy"])this.dialog.querySelector(`#bench-${n}`).onclick=()=>{this.mode=n,this.render()}}open(){this.render(),this.dialog.showModal()}render(){let{bench:e,names:t,mode:n}=this;this.dialog.querySelector("#bench-title").textContent=n==="projected"?"Sampled Hamiltonian":"Feature redundancy";let i=e.retained,s=n==="projected"?i.map((u,d)=>`S${d+1}`):t.map((u,d)=>String(d+1)),r=n==="projected"?i.map((u,d)=>i.map((h,m)=>d===m?u.cost:0)):e.data.record.redundancy,a=n==="projected"?`Diagonal Hamiltonian on ${i.length} lowest-cost distinct samples`:"Absolute feature redundancy; numbered inputs listed below",o=s.map((u)=>`<th scope="col">${u}</th>`).join(""),c=r.map((u,d)=>`<tr><th scope="row">${s[d]}</th>${u.map((h,m)=>`<td class="${n==="projected"&&d===0&&m===0?"minimum":""}" style="--cell:${n==="redundancy"?h:0.08}">${h===0?"0":h.toFixed(3)}</td>`).join("")}</tr>`).join("");this.dialog.querySelector("#bench-visual").innerHTML=`<table><caption>${a}</caption><thead><tr><th></th>${o}</tr></thead><tbody>${c}</tbody></table>`;for(let u of["projected","redundancy"])this.dialog.querySelector(`#bench-${u}`).setAttribute("aria-pressed",u===n);for(let u of["sqd","classical"])this.dialog.querySelector(`#bench-${u}`).textContent=e.best.cost.toFixed(6);this.dialog.querySelector("#bench-exact").textContent=e.optimum.toFixed(6);let l=n==="projected"?i.map((u,d)=>`<div class="bench-basis-row"><b>S${d+1}</b><code>${t.map((h,m)=>u.indices.includes(m)?"1":"0").join("")}</code><span>${u.indices.map((h)=>t[h]).join(" · ")}</span></div>`):t.map((u,d)=>`<div class="bench-feature-key"><b>${d+1}</b><span>${u}</span></div>`);this.dialog.querySelector("#bench-basis").innerHTML=l.join(""),this.dialog.querySelector("#bench-explanation").textContent=`${e.subsets.length} distinct four-of-ten subsets sampled. `+(n==="projected"?"Each bit string selects four inputs. Projecting this diagonal objective keeps their costs on the diagonal; the lowest eigenvalue is simply the smallest retained cost.":"Lighter cells indicate more redundancy between inputs. The objective rewards relevance and penalizes average pairwise redundancy; it is a selection proxy, not the QSVR fidelity kernel.")}}var qo=["Annual temperature","Summer temperature","Annual rain","Summer rain","Spring rain","Snowfall","Maximum temperature","Minimum temperature","Heating days","Cooling days"];function kh(e,t){let n=e.reduce((s,r)=>s+t.relevance[r],0)/4,i=0;for(let s=0;s<4;s++)for(let r=s+1;r<4;r++)i+=t.redundancy[e[s]][e[r]];return-n+0.5*i/6}class $o{constructor(e){this.data=e,this.rng={rng:271828},this.subsets=[{indices:[0,1,2,3],cost:kh([0,1,2,3],e.record)}],this.optimum=e.record.exact_objective,this.detail=new Xo(this,qo),document.querySelector("#sample").onclick=()=>this.sample();let t=document.createElement("button");t.id="matrix-mode",t.textContent="Inspect ↗",t.setAttribute("aria-label","Inspect sampled feature space"),t.onclick=()=>this.detail.open(),document.querySelector(".matrix-panel .section-heading").append(t);let n=document.querySelector("#matrix");n.setAttribute("role","button"),n.tabIndex=0,n.onclick=()=>this.detail.open(),n.onkeydown=(i)=>{if(i.key==="Enter"||i.key===" ")i.preventDefault(),this.detail.open()},this.render()}get best(){return this.subsets.reduce((e,t)=>e.cost<t.cost?e:t)}get retained(){return[...this.subsets].sort((e,t)=>e.cost-t.cost).slice(0,8)}sample(){for(let e=0;e<4;e++){let t=ci(Array.from({length:10},(n,i)=>i),this.rng).slice(0,4).sort((n,i)=>n-i);if(!this.subsets.some((n)=>n.indices.join()===t.join()))this.subsets.push({indices:t,cost:kh(t,this.data.record)})}this.render()}render(){let e=this.best,t=this.retained,n=t.length;document.querySelector("#sample-count").textContent=this.subsets.length,document.querySelector("#energy").textContent=e.cost.toFixed(3);let i=document.querySelector("#feature-subset");i.textContent=e.indices.map((o)=>qo[o]).join(" / "),i.title=i.textContent;let s=document.querySelector("#matrix");s.setAttribute("aria-label","Inspect diagonal sampled-subspace Hamiltonian; minimum highlighted"),s.style.gridTemplateColumns=`repeat(${n},minmax(0,1fr))`,s.classList.toggle("dense-preview",n>4),s.style.setProperty("--basis-font",n<3?"20px":"9px"),s.replaceChildren();for(let o=0;o<n;o++)for(let c=0;c<n;c++){let l=document.createElement("span");if(l.className="projected-cell",l.textContent=o===c?t[o].cost.toFixed(2):"·",l.title=o===c?`S${o+1}: ${t[o].indices.map((u)=>qo[u]).join(", ")}; cost ${t[o].cost.toFixed(6)}`:"Off-diagonal exactly zero",o===c)l.classList.add("diagonal");if(o===0&&c===0)l.classList.add("minimum");s.append(l)}let r=document.querySelector("#sample");r.title="Four uniform draws on saved coefficients; duplicates do not add another basis state. Not the original QAOA stream.",r.disabled=this.subsets.length===210;let a=document.querySelector(".instrument-note");if(a.textContent=`Gap to all 210 subsets: ${(e.cost-this.optimum).toFixed(3)}. Diagonal H; inspect to compare SQD and classical minima.`,a.title=a.textContent,this.detail.dialog.open)this.detail.render()}}class Yo{enabled=!1;async enable(e){if(!e)return this.enabled=!1,this.hush(),!1;try{this.context??=new AudioContext,this.prepare(),await this.context.resume(),this.enabled=!0,this.output.gain.setValueAtTime(this.hidden?0:1,this.context.currentTime)}catch{this.enabled=!1,this.unavailable=!0,this.hush()}return this.enabled}constructor(e=null){if(this.context=e,this.sources=new Set,this.hidden=!1,this.unavailable=!1,e)this.prepare()}prepare(){if(this.output)return;this.output=this.context.createGain(),this.output.connect(this.context.destination)}hush(){this.output?.gain.setValueAtTime(0,this.context.currentTime);for(let e of this.sources)e.stop();this.sources.clear()}setHidden(e){if(this.hidden=e,e)this.hush();else if(this.enabled)this.output.gain.setValueAtTime(1,this.context.currentTime)}envelope(e,t,n,i,s=null){let r=this.context,a=r.createGain(),o=r.currentTime+n;if(a.gain.setValueAtTime(0.001,o),a.gain.exponentialRampToValueAtTime(i,o+0.015),a.gain.exponentialRampToValueAtTime(0.001,o+t),e.connect(s??a),s)s.connect(a);a.connect(this.output),this.sources.add(e),e.onended=()=>{this.sources.delete(e),e.disconnect(),s?.disconnect(),a.disconnect()},e.start(o),e.stop(o+t)}tone(e,t=0.14,n=0,i="sine",s=0.06){if(!this.enabled||this.hidden)return;let r=this.context.createOscillator();r.type=i,r.frequency.setValueAtTime(e,this.context.currentTime+n),this.envelope(r,t,n,s)}texture(e,t,n,i="bandpass"){if(!this.enabled||this.hidden)return;let s=this.context;if(!this.noise){this.noise=s.createBuffer(1,s.sampleRate,s.sampleRate);let o=this.noise.getChannelData(0),c=20261006;for(let l=0;l<o.length;l++)c=Math.imul(c,1664525)+1013904223>>>0,o[l]=2*c/4294967296-1}let r=s.createBufferSource(),a=s.createBiquadFilter();r.buffer=this.noise,a.type=i,a.frequency.value=e,a.Q.value=0.6,this.envelope(r,t,0,n,a)}play(e){if(e==="crew")this.tone(220),this.tone(330,0.18,0.06);if(e==="water")this.texture(1200,0.5,0.07),this.tone(440,0.2,0,"triangle",0.025),this.tone(220,0.25,0.08,"triangle",0.025);if(e==="inspect")this.tone(660),this.tone(990,0.16,0.07);if(e==="advance")this.texture(360,0.65,0.06,"lowpass"),this.tone(140,0.2,0,"triangle",0.025);if(e==="upgrade")[220,440,660,880].forEach((t,n)=>this.tone(t,0.22,n*0.045));if(e==="won")[523,659,784,1046].forEach((t,n)=>this.tone(t,0.25,n*0.12));if(e==="lost")this.tone(220,0.2),this.tone(110,0.35,0.2)}}function Gh(e,t){return(1+e.reduce((n,i,s)=>n+i*t[s],0))/2}function Hh(e,t){let n=hs(e,{...t,dd:!1,twirl:!1}),i=hs(e,t);return{input:e,before:n,after:i,beforeFidelity:Gh(e,n),afterFidelity:Gh(e,i)}}function Vh(e){let{input:t,before:n,after:i,beforeFidelity:s,afterFidelity:r}=e,a=(c,l)=>{let u=95+62*c[0],d=76-62*c[1];return`<line class="channel-${l}" x1="95" y1="76" x2="${u}" y2="${d}"/>`},o=(c)=>c.map((l)=>l.toFixed(3)).join(", ");return`<svg viewBox="0 0 190 162" role="img" aria-label="Equatorial x/y projection. Input vector ${o(t)}. Without techniques ${o(n)}, fidelity ${s.toFixed(4)}. With loadout ${o(i)}, fidelity ${r.toFixed(4)}. Fidelity includes the omitted z component.">
    <circle class="channel-grid" cx="95" cy="76" r="62"/>
    <path class="channel-grid" d="M25 76H165M95 6V146"/>
    <text x="171" y="79">x</text><text x="99" y="9">y</text>
    ${a(t,"input")}${a(n,"before")}${a(i,"after")}
    <text x="95" y="159" text-anchor="middle">Equatorial projection · z omitted</text>
  </svg>`}function Wh(e,t){let n=Math.max(0.04,Math.min(0.85,e*0.8)),i=[152,210,174].map((r,a)=>(r*n+t[a]*(1-n))/255).map((r)=>r<=0.04045?r/12.92:((r+0.055)/1.055)**2.4).reduce((r,a,o)=>r+a*[0.2126,0.7152,0.0722][o],0),s=(i+0.05)/0.05>=1.05/(i+0.05)?"#000":"#fff";return`background:rgba(152,210,174,${n});color:${s}`}var Zo=[{id:"dd",name:"Echo sequence",kind:"Suppression",detail:"XpXm: cancels static idle Z drift in this ideal-pulse toy. Does not undo damping."},{id:"twirl",name:"Pauli twirling",kind:"Noise tailoring",detail:"Average ± coherent Z over-rotations. Removes directional bias; does not erase the error."},{id:"postselect",name:"Cardinality filter",kind:"Error detection",detail:"Keep only four-of-ten strings. Some corrupted strings still pass; discarded shots reduce your sample."},{id:"readout",name:"Readout calibration",kind:"Mitigation",detail:"Invert a known symmetric 8% assignment error. Sampling error remains."},{id:"psd",name:"PSD repair",kind:"Classical repair",detail:"Clip negative eigenvalues of the noisy four-year kernel. Restores PSD, not ideal data."},{id:"lowrank",name:"Low-rank repair",kind:"Classical regularization",detail:"Retain two positive eigenmodes. Compression can remove noise or useful structure."}],wt=(e)=>document.getElementById(e);class Jo{constructor(e,t,n=()=>{}){this.onChange=n,this.lens=t,this.credits=1,this.unlocked=[],this.milestones=new Set;let i=e.geometry.find((a)=>a.inputs===4&&a.amplitude_pi_denominator===32),s=[0,8,16,24];this.ideal=s.map((a)=>s.map((o)=>i.matrix[a][o]));let r={rng:20261006};this.noisy=this.ideal.map((a,o)=>a.map((c,l)=>Bh(c)+(o===l?0:(rn(r)-0.5)*0.22)));for(let a=0;a<4;a++)for(let o=a+1;o<4;o++)this.noisy[o][a]=this.noisy[a][o];this.strings=Array.from({length:32},()=>[1,1,1,1,0,0,0,0,0,0].map((o)=>rn(r)<0.09?1-o:o)),this.build(),this.render()}build(){let e=document.createElement("section");e.className="research-panel",e.innerHTML='<div class="section-heading"><span class="eyebrow">Instrument upgrades</span><button id="lab-open">1 credit · Equip ↗</button></div><div id="lab-loadout"></div><p id="lab-summary"></p>',document.querySelector(".operations").append(e),document.body.insertAdjacentHTML("beforeend",'<dialog id="instrument-dialog"><button id="instrument-close" class="close" aria-label="Close instrument bench">×</button><span class="eyebrow">Separate from fire response</span><h2>Improve the instrument.</h2><p id="instrument-feedback" role="status">Choose a technique. Credits arrive at the start and after fronts 4 and 8.</p><div class="lab-comparisons"><section><h3>Channel control</h3><div id="lab-channel"></div><div id="channel-fidelity"></div><p class="channel-key"><i></i> input <i></i> without techniques <i></i> loadout</p><p class="channel-assumption">Same input · idle 0.7 rad / gate 0.3 rad.<br>Damping/dephasing follow the lens controls.</p></section><section><h3>Kernel / samples</h3><div id="lab-matrix"></div><div id="lab-metrics"></div></section></div><div id="instrument-options"></div><p id="lab-caveat"></p></dialog>'),wt("lab-open").onclick=()=>{this.render(),wt("instrument-dialog").showModal()},wt("instrument-close").onclick=()=>wt("instrument-dialog").close()}progress(e){for(let t of[4,8])if(e.turn>=t&&!this.milestones.has(t))this.milestones.add(t),this.credits++;this.render()}reset(){this.credits=1,this.unlocked=[],this.milestones.clear(),this.render()}restore(e,t){if(this.unlocked=[...e],this.milestones=new Set([4,8].filter((n)=>t>=n)),this.credits=1+this.milestones.size-e.length,e.includes("dd")||e.includes("twirl"))this.lens.setNoise({management:!0}),wt("coherent-noise").checked=!0;this.render()}equip(e){if(this.credits<1||this.unlocked.includes(e))return;if(this.credits--,this.unlocked.push(e),["dd","twirl"].includes(e))this.lens.setNoise({management:!0}),document.querySelector("#coherent-noise").checked=!0;let t=this.render(),n=Zo.find((s)=>s.id===e).name,i=["dd","twirl"].includes(e)?`Channel fidelity ${t.channel.beforeFidelity.toFixed(3)} → ${t.channel.afterFidelity.toFixed(3)}.`:e==="postselect"?`Samples kept ${t.accepted}/32; ${t.invalid} wrong-cardinality.`:`Kernel error ${Go(this.noisy,this.ideal).toFixed(3)} → ${t.error.toFixed(3)}.`;wt("instrument-feedback").textContent=`${n} equipped. ${i} Fire response unchanged.`,wt("instrument-close").focus({preventScroll:!1}),this.onChange()}render(){let e=(d)=>this.unlocked.includes(d);wt("instrument-feedback").textContent=`${this.credits} credit${this.credits===1?"":"s"} available. Techniques do not change fire response.`,this.lens.setNoise({dd:e("dd"),twirl:e("twirl")});let t=this.lens.target,n=this.lens.phi,i=[Math.sin(t)*Math.cos(n),Math.sin(t)*Math.sin(n),Math.cos(t)],s=Hh(i,{idle:0.7,gate:0.3,dd:e("dd"),twirl:e("twirl"),damping:this.lens.damping,dephasing:this.lens.dephasing});wt("lab-channel").innerHTML=Vh(s),wt("channel-fidelity").innerHTML=`<span>Fidelity to input</span><b data-fidelity="before">${s.beforeFidelity.toFixed(3)}</b><span>→</span><b data-fidelity="after">${s.afterFidelity.toFixed(3)}</b>`,wt("lab-open").textContent=`${this.credits} credit${this.credits===1?"":"s"} · Equip ↗`,wt("lab-loadout").textContent=this.unlocked.length?this.unlocked.map((d)=>Zo.find((h)=>h.id===d).name).join(" / "):"No techniques equipped";let r=this.noisy.map((d)=>d.slice());if(e("readout"))r=r.map((d)=>d.map((h)=>zh(h)));if(e("psd")||e("lowrank"))r=Oh(r,e("lowrank")?2:4);let a=ko(r),o=Go(r,this.ideal),c=e("postselect")?this.strings.filter(Ho):this.strings,l=c.filter((d)=>!Ho(d)).length;wt("lab-summary").textContent=`${c.length}/32 samples kept · ${l} wrong-cardinality · kernel error ${o.toFixed(3)}`,wt("instrument-options").innerHTML=Zo.map((d)=>`<button data-technique="${d.id}" ${e(d.id)||!this.credits?"disabled":""}><b>${d.name}</b><span>${e(d.id)?"Equipped":d.kind+" / 1 credit"}</span><small>${d.detail}</small></button>`).join("");for(let d of document.querySelectorAll("[data-technique]"))d.onclick=()=>this.equip(d.dataset.technique);let u=getComputedStyle(wt("instrument-dialog")).backgroundColor.match(/[\d.]+/g).slice(0,3).map(Number);return wt("lab-matrix").innerHTML=r.flat().map((d)=>`<span style="${Wh(d,u)}">${d.toFixed(2)}</span>`).join(""),wt("lab-metrics").textContent=`Minimum eigenvalue ${a.at(-1).value.toFixed(4)} · Frobenius error ${o.toFixed(4)} · kept ${c.length}/32 · invalid ${l}`,wt("lab-caveat").textContent="Saved ideal 4-qubit kernel, four training years; synthetic readout and entry perturbations added locally. Matrix error is not forecast error. Filtering does not detect all flips; twirling/echo are idealized, and low-rank repair can worsen this example. None of these creates a logical qubit or fault-tolerant QEC.",{channel:s,error:o,accepted:c.length,invalid:l}}}var Vg=[{codes:[210],name:"Coniferous",color:"#245e4b"},{codes:[220],name:"Broadleaf",color:"#97b77a"},{codes:[230],name:"Mixedwood",color:"#57896a"},{codes:[81],name:"Treed wetland",color:"#4d7761"},{codes:[80],name:"Wetland",color:"#667f67"},{codes:[50],name:"Shrubs",color:"#a4ad73"},{codes:[100],name:"Herbs",color:"#b6aa69"},{codes:[40],name:"Bryoids",color:"#8b9470"},{codes:[32],name:"Rock / rubble",color:"#7f8479"},{codes:[33],name:"Exposed / barren",color:"#817b67"},{codes:[31],name:"Snow / ice",color:"#c5d5dc"},{codes:[20],name:"Water",color:"#163c50"},{codes:[0,255],name:"Unclassified / missing",color:"#40545b"}];function Xh(){return`<div class="cover-legend-grid">${Vg.map(({codes:t,name:n,color:i})=>`<div class="legend-row" data-cover-codes="${t.join(",")}" title="Source code ${t.join(" / ")}"><i aria-hidden="true" style="background:${i}"></i>${n}</div>`).join("")}</div><small>Grey is unclassified or missing, not no vegetation. Categories are not tree density.</small>`}var ft=(e)=>document.getElementById(e),qh={cover:"Forest cover · 2021",canopy:"Mean canopy height · 2015",lorey:"Basal-area-weighted height · 2015",recovery:"Spectral recovery · through 2017",water:"Mapped water · 2022",fuel:"Fuel classification · 2026"};class Ko{constructor(e,t,n){this.layers=e,this.series=t,this.change=n,this.epoch=1985,ft("legend-toggle").setAttribute("aria-controls","map-legend");let i=document.createElement("option");i.value="height",i.textContent="Height history ’85–’15",ft("layer").append(i);let s=document.createElement("option");s.value="height-change",s.textContent="Height difference ’85–’15",ft("layer").append(s);let r=document.createElement("div");r.id="height-epochs",r.setAttribute("role","group"),r.setAttribute("aria-label","SCANFI height epoch");for(let a of t.records){let o=document.createElement("button");o.textContent=a.year,o.dataset.epoch=a.year,o.onclick=()=>{this.epoch=a.year,this.render()},r.append(o)}ft("incident-list").before(r),ft("layer").onchange=()=>this.render(),ft("legend-toggle").onclick=()=>{ft("map-legend").hidden=!ft("map-legend").hidden,ft("legend-toggle").setAttribute("aria-expanded",!ft("map-legend").hidden),this.legend()},this.render()}render(){let e=ft("layer").value,t=e==="height",n=e==="height-change",i=t?`Reconstructed height · ${this.epoch} · 480 m samples`:n?"Estimated height difference · 2015 − 1985 · 480 m samples":qh[e];ft("map-image").src=e==="cover"?"../presentation/assets/ontario-cover.png":t?this.series.records.find((s)=>s.year===this.epoch).image:n?this.change.map.image:`assets/context/${e}.png`,ft("cities").hidden=e==="cover",ft("map-image").alt=`Full Ontario ${i}; dated visual context, not a game predictor.`,ft("layer-caption").textContent=i,ft("height-epochs").hidden=!t;for(let s of document.querySelectorAll("[data-epoch]"))s.setAttribute("aria-pressed",Number(s.dataset.epoch)===this.epoch);this.legend()}legend(){let e=ft("layer").value;if(e==="cover")ft("map-legend").innerHTML=Xh();else if(e==="height")ft("map-legend").innerHTML='<img src="assets/context/height-legend.png" alt="Fixed height scale, zero to thirty metres or higher"><small>Nearest 480 m samples. Grey = missing. Zero can include water/nonforest. Retrospective reconstruction; game conditions do not change with epoch.</small>';else if(e==="height-change")ft("map-legend").innerHTML=`<img src="${this.change.map.legend}" alt="Estimated height difference: orange minus ten, neutral zero, teal plus ten metres">`+"<small>2015 minus 1985. Colour stops at ±10 m; numeric values are retained. Grey = missing. Estimated differences do not identify growth, disturbance or fire effects.</small>";else{let t=this.layers.layers.find((n)=>n.key===e);ft("map-legend").innerHTML=`<img src="assets/context/${e}-legend.png" alt="Official ${t.title} legend"><small>${qh[e]}. Styled WMS image; no numeric inference from colours.</small>`}}}class jo{constructor(e,t,n){this.min=Number(e.min),this.max=Number(e.max),this.step=Number(e.step),this.onChange=n,this.node=document.createElement("div"),this.node.id=e.id,this.node.className="value-slider",this.node.tabIndex=0,this.node.setAttribute("role","slider"),this.node.setAttribute("aria-label",t),this.node.setAttribute("aria-valuemin",this.min),this.node.setAttribute("aria-valuemax",this.max),this.node.innerHTML='<span class="slider-rail"><i></i><b></b></span><output></output>',e.replaceWith(this.node),this.set(Number(e.value),!1),this.node.addEventListener("pointerdown",(i)=>{if(i.button!==0)return;this.node.focus({preventScroll:!0}),this.node.setPointerCapture(i.pointerId),this.pointer(i)}),this.node.addEventListener("pointermove",(i)=>{if(this.node.hasPointerCapture(i.pointerId))this.pointer(i)}),this.node.addEventListener("pointerup",(i)=>{if(this.node.hasPointerCapture(i.pointerId))this.node.releasePointerCapture(i.pointerId)}),this.node.addEventListener("keydown",(i)=>{let s=(i.shiftKey?10:1)*this.step,r={ArrowRight:this.value+s,ArrowUp:this.value+s,ArrowLeft:this.value-s,ArrowDown:this.value-s,PageUp:this.value+this.step*10,PageDown:this.value-this.step*10,Home:this.min,End:this.max}[i.key];if(r===void 0)return;i.preventDefault(),this.set(r)})}pointer(e){let t=this.node.querySelector(".slider-rail").getBoundingClientRect();this.set(this.min+(e.clientX-t.left)/t.width*(this.max-this.min))}set(e,t=!0){this.value=Math.min(this.max,Math.max(this.min,Math.round((e-this.min)/this.step)*this.step+this.min));let n=this.value.toFixed(2);if(this.node.style.setProperty("--at",`${100*(this.value-this.min)/(this.max-this.min)}%`),this.node.setAttribute("aria-valuenow",n),this.node.setAttribute("aria-valuetext",n),this.node.querySelector("output").textContent=n,t)this.onChange(this.value)}}var $h="fireline-season-20261006-v2",Yh="fireline-season";function Wg(e,t){if(e.version!==$h||!Number.isInteger(e.seed)||e.seed<1)throw Error("Unsupported season");if(!Array.isArray(e.moves)||e.moves.length>512)throw Error("Invalid move history");let n=Gi(e.seed,t);for(let a of e.moves)if(!(a.type==="advance"?di(n):a.type==="action"?ui(n,a.id,a.kind):a.type==="upgrade"?ms(n,a.id):!1))throw Error("Move history cannot be replayed");let i=e.techniques??[],s=1+Number(n.turn>=4)+Number(n.turn>=8),r=["dd","twirl","postselect","readout","psd","lowrank"];if(!Array.isArray(i)||new Set(i).size!==i.length||i.length>s||i.some((a)=>!r.includes(a)))throw Error("Invalid instrument loadout");if(n.incidents.some((a)=>a.id===e.selected))n.selected=e.selected;return{state:n,moves:e.moves,techniques:i}}function Zh(e,t){try{let n=(t??globalThis.localStorage).getItem(Yh);return n?Wg(JSON.parse(n),e):null}catch{return null}}function Jh(e,t,n,i){let s={version:$h,seed:e.seed,selected:e.selected,moves:t,techniques:n};try{return(i??globalThis.localStorage).setItem(Yh,JSON.stringify(s)),!0}catch{return!1}}function Kh(e){let t=e.history.at(-1);if(!t)return null;let n=t.turn,s=(e.history.at(-2)?.integrity??100)-t.integrity,r=e.log.filter((u)=>u.turn===n&&u.type==="contained").length,a=e.log.filter((u)=>u.turn===e.turn&&u.type==="ignition").length,o=e.supplies-t.supplies,c=hi(e),l=[`Front ${n+1}`,`−${s.toFixed(1)} reserve`];if(r)l.push(`${r} contained`);if(a)l.push(`${a} new fires`);if(o)l.push(`+${o} supplies`);return{front:n+1,reserveLost:s,contained:r,ignitions:a,resupplied:o,ready:c,supplies:e.supplies,feedback:l.join(" · "),announcement:`Front ${n+1} complete. ${s.toFixed(1)} reserve lost. ${r} fires contained. ${a} new fires. ${c} of ${e.crewTotal} crews ready. ${e.supplies} supplies.`}}function jh(e,t){document.addEventListener("keydown",(n)=>{let i=n.target;if(n.defaultPrevented||n.repeat||n.isComposing||n.ctrlKey||n.metaKey||n.altKey||document.querySelector("dialog[open]")||i.isContentEditable||i.closest?.('[role="slider"]')||["INPUT","SELECT","TEXTAREA"].includes(i.tagName))return;if(n.key.toLowerCase()==="n"||n.code==="Space"&&!["BUTTON","A"].includes(i.tagName))n.preventDefault(),e();else if(["1","2"].includes(n.key))n.preventDefault(),t({1:"crew",2:"water"}[n.key])})}function Qo(e){let t=e+2654435769>>>0;if(t=Math.imul(t^t>>>16,2246822507),t=Math.imul(t^t>>>13,3266489909),t=(t^t>>>16)>>>0,t&&t!==e)return t;return e+1>>>0||1}var Ye=(e)=>document.getElementById(e),[yr,Xg,qg,$g,Yg,Zg]=await Promise.all(["assets/context/scenario.json","data.json","assets/context/layers.json","../presentation/evidence.json","assets/context/height-series-v2.json","assets/context/height-change.json"].map(async(e)=>{let t=await fetch(e);if(!t.ok)throw Error(`Unable to load game context: ${e}`);return t.json()})),vr=Number(new URLSearchParams(location.hash.slice(1)).get("season")),el=Number.isInteger(vr)&&vr>0&&vr<4294967296?vr:0,On=new URLSearchParams(location.search).has("qa")?null:Zh(yr.pool);if(On&&el&&On.state.seed!==el)On=null;var lt=On?.state??Gi(el||2,yr.pool),us=On?.moves??[],tn=new Yo,tl=new Cr(yr,tu),Sr=new Wo,Mr=new Jo($g,Sr,eu);if(On)Mr.restore(On.techniques,lt.turn);var Qh=new Lr(tu,(e)=>{if(ms(lt,e))us.push({type:"upgrade",id:e}),tn.play("upgrade"),zi("Upgrade installed.")});new $o(Xg);function zi(e=""){let t=Qh.render(lt,e);tl.update(lt),Sr.update(t),Mr.progress(lt),eu()}function eu(){Jh(lt,us,Mr.unlocked)}function tu(e){lt.selected=e,zi()}function nu(e){let t=lt.incidents.find((i)=>i.id===lt.selected);if(!ui(lt,lt.selected,e))return;us.push({type:"action",id:lt.selected,kind:e}),tl.effect(t,e),tn.play(e);let n={crew:`Crew dispatched. Returns in ${t.crew} fronts.`,water:`Pressure reduced to ${t.size.toFixed(1)}.`};zi(n[e]),Ye("announcement").textContent=n[e]}function iu(){if(lt.status!=="playing"){Qh.showDebrief(lt);return}if(!di(lt))return;us.push({type:"advance"}),tn.play(lt.status==="playing"?"advance":lt.status),document.body.classList.remove("front-change"),document.body.offsetWidth,document.body.classList.add("front-change");let e=Kh(lt);zi(e.feedback),Ye("announcement").textContent=e.announcement}function nl(e){Ye("debrief").close(),Ye("upgrade").close(),lt=Gi(e,yr.pool),us=[],history.replaceState(null,"",`#season=${e}`),tl.reset(),Mr.reset(),zi()}for(let e of document.querySelectorAll("[data-action]"))e.onclick=()=>nu(e.dataset.action);Ye("advance").onclick=iu;function su(){Ye("welcome").close(),window.scrollTo({top:0,behavior:"instant"}),Ye("game-title").focus({preventScroll:!0})}Ye("start").onclick=su;if(On)Ye("start").textContent=`Continue front ${Math.min(lt.turn+1,12)} →`,Ye("fresh").hidden=!1;Ye("fresh").onclick=()=>{nl(Qo(lt.seed)),su()};Ye("retry").onclick=()=>nl(lt.seed);Ye("new-season").onclick=()=>nl(Qo(lt.seed));Ye("guide-open").onclick=()=>Ye("guide").showModal();Ye("guide-close").onclick=()=>Ye("guide").close();Ye("sound").onclick=async()=>{let e=Ye("sound");e.disabled=!0,await tn.enable(!tn.enabled),e.textContent=tn.unavailable?"Sound unavailable":`Sound ${tn.enabled?"on":"off"}`,e.setAttribute("aria-pressed",tn.enabled),e.disabled=tn.unavailable,tn.play("inspect")};document.addEventListener("visibilitychange",()=>tn.setHidden(document.hidden));Ye("lens-toggle").onclick=()=>{if(Ye("lens-controls").hidden=!Ye("lens-controls").hidden,Ye("lens-toggle").setAttribute("aria-expanded",!Ye("lens-controls").hidden),!Ye("lens-controls").hidden&&matchMedia("(max-width: 760px)").matches)Ye("lens-controls").scrollIntoView({block:"center",behavior:"auto"})};for(let e of["damping","dephasing"])new jo(Ye(e),e==="damping"?"Amplitude damping":"Dephasing",(t)=>Sr.setNoise({[e]:t}));Ye("coherent-noise").onchange=()=>Sr.setNoise({management:Ye("coherent-noise").checked});new Ko(qg,Yg,Zg);jh(iu,nu);Ye("cities").hidden=!0;zi();if(lt.status==="playing")Ye("welcome").showModal();
