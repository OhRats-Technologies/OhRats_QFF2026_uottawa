import {shortNames,fmt,kernelRow,predictionRows} from './model.js';
import {mapGraphic,phaseGraphic,matrixGraphic,projectionGraphic,predictionGraphic} from './graphics.js';

const title=(number,heading,body)=>`<div class="scene-copy"><p class="eyebrow">${number} / Inside QSVR</p><h1>${heading}</h1><p class="description">${body}</p></div>`;
const group=(label,values,active,key)=>`<div class="choices" role="group" aria-label="${label}">${values.map(([v,name])=>`<button data-${key}="${v}" aria-pressed="${String(v)===String(active)}">${name}</button>`).join('')}</div>`;
const years=(year)=>group('Ontario year',[2019,2020,2021,2022,2023,2024].map(y=>[y,y]),year,'year');

export function dataView(e,d,s) {
  const r=e.source_review.annual.find(row=>row.year===s.year);
  return `${title('01','A whole year.<br>One observation.','Recorded fires and monthly climate become annual Ontario summaries. We estimate mean hectares per fire—not the size of a particular fire.')}
    <div class="world">${mapGraphic(e,s.map)}<p class="world-caption">2021 NRCan cover ${s.map==='cover'?'+ raw recorded locations':'· Algonquin-area pixels'}<br>Context map, not a prediction</p>${group('Map view',[['cover','Ontario'],['pixels','Forest pixels']],s.map,'map')}</div>
    <div class="data-readout">${years(s.year)}<div class="arithmetic"><div><strong>${fmt(r.total_observed_size_ha)}</strong><span>reported hectares</span></div><b>÷</b><div><strong>${fmt(r.size_observed_incidents)}</strong><span>accepted fire records</span></div><b>=</b><div class="answer"><strong>${fmt(r.mean_reported_size_ha,1)}</strong><span>ha / fire · ${s.year}</span></div></div><div class="dataset-line"><span><i></i>1988–2018 · 31 training rows</span><span><i></i>2019–2024 · 6 reused years</span></div><p class="context-note">ECCC climate joins by year. Woodland is context, not a final predictor.</p></div>`;
}

export function featuresView(e,d,s) {
  const study=s.selector!=='physical_four';
  const selected=study?d.record.sqd.find(r=>r.source==='qaoa').selected_subset:d.physical_indices;
  const methods=[['physical_four','Final QSVR inputs'],['exact_same_qubo','Separate SQD study']];
  const names=shortNames.map((name,i)=>`<div class="feature ${selected.includes(i)?'selected':''}"><span class="feature-bit">${selected.includes(i)?'1':'0'}</span><span>${name}</span></div>`).join('');
  const stages=['Sample subsets','Project objective','Lowest energy'];
  const descriptions=['QAOA and uniform controls sample four-of-ten subsets. The dots are schematic, not a replay of the draw stream.','SQD projects the Hamiltonian into sampled bitstrings. Here it is diagonal: different subsets have no coupling.','The lowest diagonal entry is already the best sampled subset. SQD adds no optimization benefit for this objective.'];
  return `${title('02',study?'What SQD<br>actually did.':'Four inputs.<br>A fair comparison.',study?'A separate training-only feature-selection study, evaluated with fixed ridge—not the tuned QSVR results.':'The kernel comparison gives classical and quantum models the same four predefined temperature and precipitation inputs.')}
    <div class="feature-stage">${group('Feature study',methods,study?'exact_same_qubo':'physical_four','selector')}<div class="feature-list">${names}</div></div>
    <div class="feature-explanation">${study?`<div class="sqd-controls" role="group" aria-label="SQD explanation stages">${stages.map((label,i)=>`<button data-sqd="${i}" aria-pressed="${i===s.sqdStage}">${label}</button>`).join('')}</div><div class="projection">${projectionGraphic(d,s.sqdStage)}</div><div class="sqd-narration"><p class="projection-caption">${descriptions[s.sqdStage]}</p><div class="sqd-receipt"><span>Saved first fold · 1988–2006 training</span><strong>83 / 89</strong><span>unique feasible subsets · uniform / QAOA</span></div></div>`:`<div class="four-nodes">${[0,1,2,3].map(i=>`<div><span>q${i}</span><i></i><small>${i<2?'Temperature':'Precipitation'}</small></div>`).join('')}</div><div class="comparison-line"><span>RBF distance → SVR</span><span>Qiskit fidelity → SVR</span></div><p class="projection-caption">Same rows, same inputs, same tuning budget. Selecting more qubits does not create more observations.</p>`}</div>`;
}

export function encodingView(e,d,s) {
  return `${title('03','Values become<br>phase angles.','Bound standardized features, then encode them in a shallow ZZ circuit. Move an input to see its illustrative single-qubit phase change.')}
    <div class="phase-stage"><div id="phase-visual">${phaseGraphic(s)}</div><p class="phase-caption">RZ(2θ) on |+〉 · illustrative equatorial phases<br>The entangled ZZ state is not shown.</p><div class="phase-formula">θ = a tanh(z / 2)</div>${group('Illustrative angle amplitude',[[32,'π/32'],[16,'π/16'],[8,'π/8'],[4,'π/4'],[2,'π/2']],s.denominator,'angle')}</div>
    <div class="input-controls">${s.z.map((z,i)=>`<div class="input-row"><div><span>${shortNames[i]}</span><output id="z-${i}">${fmt(z,2)} <small>z</small></output></div><div class="custom-slider" role="slider" tabindex="0" aria-label="Illustrative standardized ${shortNames[i].toLowerCase()}" aria-valuemin="-3" aria-valuemax="3" aria-valuenow="${z}" aria-valuetext="${fmt(z,2)} standard deviations" data-input="${i}" style="--at:${(z+3)/6*100}%"><i></i><b></b></div></div>`).join('')}<p class="context-note">These inputs explain encoding; they do not launch circuits or change saved predictions.</p></div>`;
}

export function kernelView(e,d,s) {
  const row=kernelRow(e,s),[i,j]=s.pair;
  return `${title('04','Similarity is<br>the interface.','Qiskit computes squared state overlaps. The SVR receives this matrix. Explore saved training kernels; narrower angles change their geometry.')}
    <div class="kernel-stage"><div class="matrix-frame">${matrixGraphic(row,s.pair)}</div><div class="matrix-endpoints"><span>1988</span><span>31 Ontario training years</span><span>2018</span></div>${group('Saved input width',[[4,'4 qubits'],[10,'10 qubits']],s.width,'width')}${group('Saved angle amplitude',[[32,'π/32'],[16,'π/16'],[8,'π/8'],[4,'π/4'],[2,'π/2']],s.denominator,'scale')}</div>
    <div class="similarity-readout"><p class="micro">Compare two saved training years</p><div class="year-pair">${[i,j].map((year,k)=>`<label>${k?'With':'Year'}<select data-pair="${k}">${Array.from({length:31},(_,n)=>`<option value="${n}" ${n===year?'selected':''}>${1988+n}</option>`).join('')}</select></label>`).join('')}</div><strong id="fidelity">${fmt(row.matrix[i][j],6)}</strong><span class="unit">state fidelity · 0 to 1</span><div class="kernel-stats"><div><strong>${fmt(row.effective_rank,2)}</strong><span>effective rank / 31</span></div><div><strong>${fmt(row.off_diagonal_mean,6)}</strong><span>mean off-diagonal fidelity</span></div></div><p class="context-note">Input-only diagnostic. A richer-looking matrix is not evidence of better prediction.</p></div>`;
}

export function predictionView(e,d,s) {
  const rows=predictionRows(e,s.year);
  return `${title('05','Predictions<br>meet reality.','Frozen QSVR and classical estimates, compared with the training mean. The SVR optimizer is classical.')}
    <div class="prediction-stage">${years(s.year)}<div class="prediction-chart">${predictionGraphic(rows,s.year)}</div><p class="context-note">Recorded mean = reported hectares ÷ accepted fire records.<br>Each bar is an annual mean, not the size of one fire.</p></div>
    <div class="final-readout"><p class="micro">MAE across six reused years · ha/fire</p>${rows.map((r,i)=>`<div class="result-row"><span>${['Training mean','QSVR · 4','RBF · 4'][i]}</span><strong>${fmt(r.mae,2)}</strong></div>`).join('')}<p class="final-verdict">No main model beats<br>the training mean.</p><p class="context-note">Same-year climate makes this retrospective. Six evaluation years were previously inspected. No quantum advantage is claimed.</p></div>`;
}

export const views=[dataView,featuresView,encodingView,kernelView,predictionView];
export function explanation(index,d) {
  const copy=[
    ['Annual data','The NFDB audit reproduces 37 annual labels. It selects Ontario agency records, quarantines ambiguous identities and excludes prescribed records. Annual mean reported size = total accepted observed hectares / accepted size-observed fire records. It does not filter the annual target by map coordinates. The 2021 map contains all 1,200 raw location records; the accepted annual target contains 1,194. Climate features use ECCC monthly summaries aggregated across eligible stations. Woodland pixels show land-cover categories, not density or final predictors.'],
    ['Features and SQD',`Final prediction uses the predefined physical four. The separate selector study ranks target relevance against feature redundancy on training years. QAOA draws are simulated; qiskit-addon-sqd projects the diagonal Hamiltonian. In the displayed first fold, uniform and QAOA both contain the exact optimum. The ${d.teaching_basis.length}-state teaching matrix uses distinct published selector outputs; it is not the original 83/89-state sampled basis. Browser projection is explanatory arithmetic, not an addon execution. Across folds, fixed-ridge MAE is exact 79.58, uniform + SQD 80.31, QAOA + SQD 81.66 ha/fire.`],
    ['Encoding','The sliders are illustrative standardized inputs. A bounded θ = a tanh(z/2) controls phase. For RZ(2θ)|+〉, phase is 2θ and the single-qubit Bloch vector stays on the equator. It changes relative phase, not the |0〉/|1〉 measurement probabilities of that isolated illustrative qubit. The real shallow ZZ circuit also has adjacent pairwise phase interactions; these four dials do not represent the full entangled state. No state or kernel is recomputed in this demo.'],
    ['Saved kernel geometry','Values are saved exact-simulation FidelityQuantumKernel matrices, rounded to six decimals for display, over training years 1988–2018. Width and angle controls select among ten saved matrices. Selected year-pair fidelity comes directly from those values. Geometry was a post-final, input-only diagnostic: no targets, model fits or improved predictor selection. Narrow angles can be ill-conditioned. It must not be read as predictive validation.'],
    ['Saved predictions','All predictions, observed outcomes and error summaries are copied from the frozen annual evaluation. Qiskit supplies similarities; the SVR solver is classical. Original tuning was chronological, with preprocessing fitted only on training folds and matched family budgets. The six 2019–2024 years are reused evaluation, not an independent pristine holdout. None of eleven main models beats the mean; a QSVR-versus-RBF gain here is not useful skill.'],
  ][index];
  return `<h2>${copy[0]}</h2><p>${copy[1]}</p><p class="note-links"><a href="https://github.com/OhRats-Technologies/OhRats_QFF2026_uottawa/blob/main/docs/REPORT.md" target="_blank" rel="noreferrer">Source report ↗</a></p>`;
}
