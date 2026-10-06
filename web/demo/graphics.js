import {angle,fmt} from './model.js';

export function mapGraphic(e,mode='cover') {
  const m=e.map;
  const dots=m.points.map(p=>`<circle cx="${p.x}" cy="${p.y}" r="${2+Math.min(5,Math.log1p(p.ha)/2)}"/>`).join('');
  if(mode==='pixels')return `<img class="pixel-land" src="../presentation/assets/algonquin-cover.png" alt="Actual 2021 Algonquin-area forest land-cover categories">`;
  return `<div class="province-map"><img src="../presentation/assets/ontario-cover.png" alt="Full Ontario boundary with Toronto/GTA, Ottawa and Windsor; grey = no mapped woodland class"><svg viewBox="0 0 ${m.width} ${m.height}" aria-hidden="true">${dots}</svg></div>`;
}

export function phaseGraphic(state) {
  const nodes=state.z.map((z,i)=>{
    const x=100+i*160,y=135,theta=angle(z,state.denominator),phi=2*theta;
    return `<g data-dial="${i}"><circle cx="${x}" cy="${y}" r="65" class="sphere"/><ellipse cx="${x}" cy="${y}" rx="65" ry="23" class="orbit"/><path d="M${x} ${y-80} V${y+80}" class="orbit"/><text x="${x}" y="${y-99}" text-anchor="middle">q${i}</text><path class="phase-arm" d="M${x} ${y} L${x+62*Math.cos(phi)} ${y+23*Math.sin(phi)}"/><circle class="phase-tip" cx="${x+62*Math.cos(phi)}" cy="${y+23*Math.sin(phi)}" r="6"/><text class="theta" x="${x}" y="${y+112}" text-anchor="middle">θ ${fmt(theta,2)}</text></g>`;
  }).join('');
  return `<svg viewBox="0 0 680 280" role="img" aria-label="Illustrative equatorial single-qubit phases; not full entangled states">${nodes}</svg>`;
}

export function matrixGraphic(row,pair) {
  const size=31,cell=12;
  const cells=row.matrix.flatMap((r,i)=>r.map((v,j)=>{
    const light=9+v*63;
    return `<rect x="${j*cell}" y="${i*cell}" width="12" height="12" fill="hsl(160 24% ${light}%)"/>`;
  })).join('');
  const [i,j]=pair;
  return `<svg id="matrix" viewBox="0 0 372 372" role="img" aria-label="Saved ${row.inputs}-qubit training fidelity matrix, 1988–2018; select a year pair using the controls"><g>${cells}</g><path class="matrix-guide" d="M0 ${i*cell+6} H372 M${j*cell+6} 0 V372"/><rect class="matrix-focus" x="${j*cell}" y="${i*cell}" width="12" height="12"/></svg>`;
}

export function projectionGraphic(data,stage) {
  const basis=data.teaching_basis,n=basis.length;
  if(stage===0)return `<svg viewBox="0 0 580 315" role="img" aria-label="Four-of-ten possible subsets; illustrative sampled-space view">${Array.from({length:210},(_,i)=>{
    const x=38+(i%21)*25,y=40+Math.floor(i/21)*25;
    return `<circle cx="${x}" cy="${y}" r="${i%5===0?4:2}" class="${i%5===0?'sample':'candidate'}" style="--delay:${i*2}ms"/>`;
  }).join('')}<text x="38" y="306">210 feasible subsets · schematic sampled dots</text></svg>`;
  const side=225/n;
  return `<svg viewBox="0 0 580 315" role="img" aria-label="Teaching projection of a diagonal objective onto distinct saved selector outputs">${Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>{
    const x=34+j*side,y=30+i*side;
    return `<rect x="${x}" y="${y}" width="${side-3}" height="${side-3}" class="${i===j?'diagonal':'zero'} ${stage===2&&i===0&&j===0?'minimum':''}"/><text x="${x+side/2-1}" y="${y+side/2+3}" text-anchor="middle">${i===j?fmt(data.teaching_basis[i].energy,3):'0'}</text>`;
  }).join('')).join('')}<text x="295" y="93">H in the sampled basis</text><text x="295" y="126">Off-diagonal entries = 0</text><text x="295" y="194" class="projection-energy">${stage===2?fmt(data.record.exact_objective,4):'Diagonal objective'}</text><text x="34" y="302">Teaching basis · ${n} distinct saved selector outputs</text></svg>`;
}

export function predictionGraphic(rows,year) {
  const names=['Training mean','QSVR · 4 qubits','RBF · 4 inputs'];
  const all=[...rows.map((r,i)=>({label:names[i],value:r.value,kind:i})),{label:'Recorded mean',value:rows[0].actual,kind:3}];
  const description=`${year} annual mean hectares per recorded fire. ${all.map(r=>`${r.label}: ${fmt(r.value,1)} ha/fire`).join('. ')}. Fixed 0–700 ha/fire scale; reused evaluation years.`;
  return `<svg viewBox="0 0 670 430" role="img" aria-label="${description}">${[0,200,400,600].map(t=>`<path d="M40 ${370-t/700*290} H630" class="chart-grid"/><text x="645" y="${375-t/700*290}" class="tick">${t}</text>`).join('')}${all.map((r,i)=>{
    const x=70+i*135,h=r.value/700*290;
    return `<rect x="${x}" y="${370-h}" width="58" height="${h}" class="pred-bar series-${r.kind}"/><text x="${x+29}" y="${355-h}" text-anchor="middle" class="bar-value">${fmt(r.value,1)}</text><text x="${x+29}" y="${397+i%2*21}" text-anchor="middle" class="bar-label"><tspan class="full-label">${r.label}</tspan><tspan class="compact-label">${["Baseline","QSVR","RBF","Recorded"][r.kind]}</tspan></text>`;
  }).join('')}<text x="40" y="25" class="chart-unit">Mean hectares / recorded fire</text></svg>`;
}
