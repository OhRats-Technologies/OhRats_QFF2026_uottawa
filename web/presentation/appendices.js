export function circuitDiagram() {
  const wires=[0,1,2,3].map(i=>{
    const y=45+i*65;
    return `<g><text x="8" y="${y+5}">q${i}</text><path d="M45 ${y} H615" class="wire"/><rect x="75" y="${y-17}" width="35" height="34" class="gate"/><text x="92" y="${y+5}" text-anchor="middle">H</text><rect x="165" y="${y-17}" width="110" height="34" class="gate"/><text x="220" y="${y+5}" text-anchor="middle">P(2θ${i})</text></g>`;
  }).join('');
  const pairs=[0,1,2].map(i=>{
    const x=350+i*90,y=45+i*65;
    return `<g><path d="M${x} ${y} V${y+65}" class="coupling"/><circle cx="${x}" cy="${y}" r="5" class="state-tip"/><circle cx="${x}" cy="${y+65}" r="5" class="state-tip"/><text x="${x+12}" y="${y+38}">ZZ</text></g>`;
  }).join('');
  return `<svg viewBox="0 0 640 295" role="img" aria-label="Schematic four-qubit linear ZZ feature map: Hadamard gates, feature phases and adjacent pair interactions">${wires}${pairs}<text x="75" y="286">Superposition</text><text x="180" y="286">Feature phase</text><text x="357" y="286">Pair interaction</text></svg>`;
}

export function encodingAppendix() {
  return `<h2>Measurements → phases → similarities.</h2><div class="encoding-appendix"><div class="circuit-figure">${circuitDiagram()}<p class="mini">Four-qubit linear ZZ map · schematic gate layout</p></div><div class="encoding-explanation"><div><span>Bound the standardized input</span><strong>θ = a tanh(z / 2)</strong></div><div><span>Compare the encoded states</span><strong>k(x,y) = |〈φ(x) | φ(y)〉|²</strong></div><div><span>Predict with a classical solver</span><strong>Similarity matrix → SVR</strong></div></div></div><p class="footnote">Actual FidelityQuantumKernel + QSVR · exact simulation · training-only preprocessing<br>Entangling features does not guarantee predictive skill.</p>`;
}

export function resourcesAppendix(e) {
  if (!e.shot_sweep) return `<h2>Useful shots matter.</h2><p class="subtitle">Load the saved shot-sweep asset for the updated hardware appendix.</p>`;
  const s=e.shot_sweep;
  return `<h2>More shots. More candidates.</h2><div class="research-resource">${shotSweep(s)}<div class="research-receipt"><span class="mini">10 / 16 / 20 feature pools</span><strong>${s.jobs} <small>IBM jobs</small></strong><strong>${s.charged_seconds} <small>QPU seconds</small></strong><strong>${s.physical_shots.toLocaleString('en-US')} <small>returned shots</small></strong><p>Same circuits.<br>512 → 2,048 shots.</p></div></div><p class="footnote">Chart: four valid features from twenty candidates · percentages are usable yield, not accuracy<br>Wilson 95% shot intervals · one execution per condition · not a device ranking</p>`;
}

function shotSweep(s) {
  const styles=[['raw','Raw','#ce6733'],['dd_twirl','DD + twirling','#38b2ac']];
  const groups=['marrakesh','quebec'].map(device=>{
    const left=48,top=68,width=342,height=248;
    const x=i=>left+width*i/2,y=f=>top+height*(1-f/.2);
    const grid=[0,.05,.1,.15,.2].map(f=>`<path d="M${left} ${y(f)}h${width}" stroke="#1f4444"/><text x="${left-9}" y="${y(f)+5}" text-anchor="end" font-size="14">${(f*100).toFixed(0)}</text>`).join('');
    const curves=styles.map(([arm,label,color])=>{
      const rows=s.rows.filter(r=>r.device===device&&r.arm===arm).sort((a,b)=>a.shots-b.shots);
      const points=rows.map((r,i)=>`${x(i)},${y(r.fraction)}`).join(' ');
      const bars=rows.map((r,i)=>`<path d="M${x(i)} ${y(r.wilson95[1])}V${y(r.wilson95[0])}" stroke="${color}" stroke-width="2"/><circle data-device="${device}" data-arm="${arm}" data-shots="${r.shots}" data-valid="${r.valid}" data-fraction="${r.fraction}" cx="${x(i)}" cy="${y(r.fraction)}" r="5" fill="${color}"><title>${device} ${label}: ${r.valid}/${r.shots} valid (${(r.fraction*100).toFixed(2)}%)</title></circle>`).join('');
      return `<polyline points="${points}" fill="none" stroke="${color}" stroke-width="3"/>${bars}`;
    }).join('');
    const counts=s.rows.filter(r=>r.device===device&&r.arm==='raw').sort((a,b)=>a.shots-b.shots).map(r=>r.valid).join(' → ');
    return `<svg class="shot-chart" viewBox="0 0 430 435" role="img" aria-label="${device}: measured usable four-feature yield at512,1024 and2048 shots, not prediction accuracy."><text x="48" y="57" font-size="14" fill="#aed6b6">Valid selections · %</text><g><text x="${left}" y="31" class="label" font-size="24">${device==='marrakesh'?'Marrakesh':'Quebec'}</text>${grid}${curves}${[512,1024,2048].map((n,i)=>`<text x="${x(i)}" y="${top+height+27}" text-anchor="middle" font-size="16">${n.toLocaleString('en-US')}</text>`).join('')}<text x="${left}" y="${top+height+57}" font-size="15" fill="#749b92">Raw valid counts: ${counts}</text></g><path d="M48 410h24" stroke="#ce6733" stroke-width="3"/><text x="80" y="416" font-size="16" fill="#ce6733">Raw</text><path d="M170 410h24" stroke="#38b2ac" stroke-width="3"/><text x="202" y="416" font-size="16" fill="#38b2ac">DD + twirling</text><text x="210" y="390" font-size="14" text-anchor="middle" fill="#749b92">Shots per circuit</text></svg>`;
  }).join('');
  return `<div class="shot-comparison">${groups}</div>`;
}
