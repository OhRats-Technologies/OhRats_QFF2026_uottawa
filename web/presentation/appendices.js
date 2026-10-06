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
  return `<h2>Useful shots matter.</h2><div class="research-resource"><img src="assets/research-hardware.png" alt="Actual valid four-feature subset yields on Marrakesh and Quebec: noise remains severe at sixteen and twenty selector qubits, with mixed DD and twirling outcomes."><div class="research-receipt"><span class="mini">New training followups</span><strong>9 <small>IBM jobs</small></strong><strong>82 <small>QPU seconds</small></strong><strong>219,648 <small>shots</small></strong><p>Frozen parameters.<br>All repairs reported.</p></div></div><p class="footnote">One raw / combined pair per device · not a device ranking<br>Original final comparison stays frozen. Separate measured-kernel outcomes are in the research report.</p>`;
}
