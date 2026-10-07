export const colors = { actual:'#ce6733', mean:'#53706e', q:'#38b2ac', rbf:'#aed6b6' };
const fmt = value => value.toFixed(2);
const svg = (width,height,body,label) => `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${label}">${body}</svg>`;
const text = (x,y,label,cls='',anchor='start') => `<text x="${x}" y="${y}" class="${cls}" text-anchor="${anchor}">${label}</text>`;

export function annualLines(evidence,compact=false) {
  const source = evidence.final.find(row=>row.id==='training_mean');
  const width=1128,height=compact?180:350;
  const pad={ left:compact?0:60, right:26, top:20, bottom:compact?20:38 };
  const x=i=>pad.left+i*(width-pad.left-pad.right)/5;
  const y=v=>height-pad.bottom-v*(height-pad.top-pad.bottom)/700;
  let body='';
  if(!compact) {
    for(const value of [0,200,400,600]) body+=`<line class="grid" x1="${pad.left}" x2="${width-pad.right}" y1="${y(value)}" y2="${y(value)}"/>`+text(pad.left-15,y(value)+6,value,'','end');
    source.years.forEach((year,i)=>{body+=text(x(i),height-7,year,'','middle');});
  }
  const series=compact?[{name:'Observed',values:source.actual_ha,color:colors.actual}]:[
    {name:'Mean',values:source.predicted_ha,color:colors.mean},
    {name:'RBF',values:evidence.final.find(r=>r.id==='matched_rbf_svr_4').predicted_ha,color:colors.rbf},
    {name:'QSVR',values:evidence.final.find(r=>r.id==='matched_fidelity_svr_4').predicted_ha,color:colors.q},
    {name:'Observed',values:source.actual_ha,color:colors.actual},
  ];
  for(const row of series) {
    const d=row.values.map((v,i)=>`${i?'L':'M'}${x(i)},${y(v)}`).join(' ');
    body+=`<path class="series draw" d="${d}" pathLength="1" stroke-dasharray="1" stroke="${row.color}"/>`;
    if(row.name==='Observed') row.values.forEach((value,i)=>{
      body+=`<circle class="dot" cx="${x(i)}" cy="${y(value)}" r="${compact?4:6}" fill="${row.color}" style="animation-delay:${i*.07}s"/>`;
      if(!compact)body+=text(x(i),y(value)-16,Math.round(value),'label','middle');
    });
  }
  return svg(width,height,body,'Reported annual mean fire size and model estimates, hectares per fire');
}

export function annualComparison(evidence) {
  const source=evidence.final.find(r=>r.id==='training_mean');
  const rows=[['Recorded',source.actual_ha,colors.actual],['Training mean',source.predicted_ha,colors.mean],
    ['QSVR',evidence.final.find(r=>r.id==='matched_fidelity_svr_4').predicted_ha,colors.q],
    ['RBF',evidence.final.find(r=>r.id==='matched_rbf_svr_4').predicted_ha,colors.rbf]];
  const width=1128,height=350,left=60,right=20,top=38,bottom=36;
  const group=(width-left-right)/source.years.length,bar=28,gap=7;
  const y=value=>height-bottom-value*(height-top-bottom)/700;
  let body=text(left,18,'Mean fire size · hectares per recorded fire');
  for(const value of [0,200,400,600])body+=`<line class="grid" x1="${left}" x2="${width-right}" y1="${y(value)}" y2="${y(value)}"/>`+text(left-15,y(value)+6,value,'','end');
  source.years.forEach((year,i)=>{
    const start=left+group*(i+.5)-(4*bar+3*gap)/2;
    rows.forEach(([name,values,color],j)=>{
      const x=start+j*(bar+gap),value=values[i];
      body+=`<rect class="annual-bar" data-series="${name}" data-year="${year}" data-value="${value}" x="${x}" y="${y(value)}" width="${bar}" height="${y(0)-y(value)}" fill="${color}"><title>${year}: ${name} ${value.toFixed(2)} ha/fire</title></rect>`;
      if(j===0)body+=text(x+bar/2,y(value)-10,Math.round(value),'label','middle');
    });
    body+=text(left+group*(i+.5),height-7,year,'','middle');
  });
  return svg(width,height,body,'Annual mean recorded fire size in hectares per fire: orange bars are recorded values; grey, teal and green bars are training-mean, QSVR and RBF estimates. Each group is a separate Ontario year.');
}

export function developmentBars(evidence) {
  const rows=[['Training mean',evidence.development.training_mean.mae,colors.mean],
    ['RBF-SVR · 4 inputs',evidence.development.matched_rbf_svr_4.mae,colors.rbf],
    ['QSVR · 4 qubits',evidence.development.matched_fidelity_svr_4.mae,colors.q]];
  let body='';const start=330,scale=6.2;
  for(let i=0;i<rows.length;i++) {
    const [label,value,color]=rows[i],y=45+i*95;
    body+=text(0,y+28,label,'label');
    body+=`<rect x="${start}" y="${y}" height="40" width="${value*scale}" fill="${color}"/>`;
    body+=text(start+value*scale+18,y+29,fmt(value),'value');
  }
  body+=text(start,330,'Mean chronological MAE · ha/fire · lower is better');
  return svg(1128,360,body,'Development MAE: training mean 92.00, RBF 77.02, QSVR 86.64 hectares per fire');
}

export function heatmap(row) {
  let body='';const cell=10;
  row.matrix.forEach((line,y)=>line.forEach((v,x)=>{
    const hue = 26;
    const lightness = (7 + v * 57).toFixed(1);
    body+=`<rect x="${x*cell}" y="${y*cell}" width="10.02" height="10.02" fill="hsl(${hue}, 75%, ${lightness}%)"/>`;
  }));
  return svg(310,310,body,`Ten-qubit training fidelity matrix, amplitude pi/${row.amplitude_pi_denominator}, 31 by 31`);
}

export function geometryMarkup(evidence,denominator=4) {
  const row=evidence.geometry.find(r=>r.inputs===10&&r.amplitude_pi_denominator===denominator);
  return `<div class="heatmap">${heatmap(row)}</div><div class="geometry-detail">
    <div class="stat teal">${row.effective_rank.toFixed(2)}<span style="font-size:30px;color:var(--muted)"> / 31</span></div>
    <p class="caption">Effective rank of the ten-qubit training kernel</p>
    <p class="geometry-insight">Mean off-diagonal fidelity <strong>${row.off_diagonal_mean.toFixed(6)}</strong><br>Condition number <strong>${row.condition_number.toFixed(2)}</strong></p>
    <div class="scale-control" role="group" aria-label="Ten-qubit angle amplitude">${[32,16,8,4,2].map(d=>`<button data-scale="${d}" aria-pressed="${d===denominator}">π/${d}</button>`).join('')}</div>
    <p class="caption" style="margin-top:13px">Angle amplitude · five measured settings</p>
  </div>`;
}
