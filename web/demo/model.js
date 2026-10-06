export const sections=['data','features','encoding','kernel','prediction'];
export const labels=['Annual data','Features + SQD','Phase encoding','Similarity','Prediction'];
export const shortNames=['Annual temperature','Summer temperature','Annual precipitation','Summer precipitation','Spring precipitation','Annual snowfall','Highest temperature','Lowest temperature','Heating degree days','Cooling degree days'];
export const initialState=()=>({section:0,year:2021,map:'cover',selector:'physical_four',sqdStage:0,width:10,denominator:4,pair:[19,20],z:[-1,.3,.8,1.4]});
export const angle=(z,denominator)=>Math.PI/denominator*Math.tanh(z/2);
export function subsetCost(indices,data) {
  let relevance=0,redundancy=0;
  indices.forEach((i,index)=>{
    relevance+=data.record.relevance[i];
    indices.slice(index+1).forEach(j=>{redundancy+=data.record.redundancy[i][j];});
  });
  return -relevance/4+data.redundancy_weight*redundancy/6;
}
export function kernelRow(e,state) {
  return e.geometry.find(r=>r.inputs===state.width&&r.amplitude_pi_denominator===state.denominator);
}
export function predictionRows(e,year) {
  const ids=['training_mean','matched_fidelity_svr_4','matched_rbf_svr_4'];
  return ids.map(id=>{
    const r=e.final.find(r=>r.id===id),i=r.years.indexOf(year);
    return {id,value:r.predicted_ha[i],actual:r.actual_ha[i],mae:r.mae_ha};
  });
}
export const fmt=(x,d=0)=>Number(x).toLocaleString('en-CA',{maximumFractionDigits:d,minimumFractionDigits:d});
