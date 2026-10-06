// Authoring uses the bundled Presentations runtime; public viewing needs only bun.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import {makeSlides} from './slides.js';

const root=process.cwd();
const {RUNTIME_NODE_MODULES,SKILL_DIR,RUNTIME_PYTHON}=process.env;
if(!RUNTIME_NODE_MODULES||!SKILL_DIR||!RUNTIME_PYTHON)throw new Error('Supply bundled presentation runtime paths');
const require=createRequire(path.join(RUNTIME_NODE_MODULES,'../package.json'));
const {Presentation,PresentationFile}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const {resolvePresentationFont,applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const font=resolvePresentationFont({fontFamily:'Arial'});
const e=JSON.parse(await fs.readFile(path.join(root,'web/presentation/evidence.json'),'utf8'));
const copy=makeSlides(e),p=Presentation.create({slideSize:{width:1280,height:720}});
const build=path.join(root,'.cache/judge-submission','pptx-'+path.basename(process.argv[2]??'ontario-wildfire.pptx'));
const output=path.join(root,'web/presentation/slides',process.argv[2]??'ontario-wildfire.pptx');
await fs.mkdir(build,{recursive:true});await fs.mkdir(path.dirname(output),{recursive:true});
const ink='#17343a',muted='#66777a',teal='#18747c',orange='#c46242',paper='#f7f6f2';
function text(s,value,x,y,w,h,size=26,color=ink,bold=false){
  const shape=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  shape.text=value;shape.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none'};return shape;
}
function foot(s,value){text(s,value,76,630,1128,62,20,muted);}
function chart(s,kind,config){
  config={...config,series:config.series.map(row=>({...row,values:row.values.map(v=>Number(v.toFixed(6))),valuesFormatCode:'0.00'}))};
  const c=s.charts.add(kind,{chartFill:paper,plotAreaFill:paper,chartLine:{fill:'none',width:0},...config});
  applyPresentationChartFont(c,{fontFamily:font});return c;
}
const axis={textStyle:{typeface:font,fontSize:20,fill:muted},line:{fill:'#cbd3d0',width:1},majorGridlines:{fill:'#dfe4e0',width:1}};
function table(s,rows,top=220,height=290){
  const t=s.tables.add({rows:rows.length,columns:2,left:76,top,width:1128,height,columnWidths:[800,328],values:rows});
  t.cells.block({row:0,column:0,rowCount:rows.length,columnCount:2}).assign({fill:paper,textStyle:{typeface:font,fontSize:25,color:ink},margins:{left:12,right:12,top:12,bottom:12}});
  t.borders.assign({fill:'#d2dbd7',width:1,style:'solid'});return t;
}
const imageBytes=await Promise.all(['ontario-records.png','algonquin-cover.png'].map(name=>fs.readFile(path.join(root,'web/presentation/assets',name))));
function mapImage(s,index,x,y,w,h){s.images.add({blob:new Uint8Array(imageBytes[index]),contentType:'image/png',alt:index?'Algonquin-area 2021 source cover pixels':'Ontario 2021 source cover and raw recorded locations',fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function ellipse(s,x,y,w,h,color=teal,fill='none'){s.shapes.add({geometry:'ellipse',position:{left:x,top:y,width:w,height:h},fill,line:{fill:color,width:1}});}
function phaseDials(s){
  [-1,.3,.8,1.4].forEach((z,j)=>{
    const x=142+j*128,y=298,phase=Math.PI/2*Math.tanh(z/2),dx=43*Math.cos(phase),dy=15*Math.sin(phase);
    ellipse(s,x-45,y-45,90,90,'#89a496');ellipse(s,x-45,y-15,90,30,'#adbbb2');
    s.shapes.add({geometry:'line',position:{left:Math.min(x,x+dx),top:Math.min(y,y+dy),width:Math.abs(dx),height:Math.abs(dy),verticalFlip:dx*dy<0},fill:'none',line:{fill:teal,width:3}});
    ellipse(s,x+dx-4,y+dy-4,8,8,teal,teal);text(s,'θ = '+(phase/2).toFixed(2),x-52,y+69,110,25,17,muted);
  });
}
for(let i=0;i<copy.length;i++){
  const item=copy[i],s=p.slides.add();s.background.fill=paper;
  if(i!==0)text(s,item.title,76,62,1128,105,46);
  const urls=[...item.notes.matchAll(/href="([^"]+)"/g)].map(m=>m[1]);
  s.speakerNotes.textFrame.setText(item.notes.replace(/<[^>]+>/g,'')+'\n\nSources:\n'+urls.join('\n'));
  if(i===0){
    s.background.fill='#071e24';mapImage(s,0,690,40,550,580);
    text(s,'Ontario · Qiskit Fall Fest',76,65,1000,30,20,'#a8bdb4');
    text(s,'Can quantum kernels\nestimate fire size?',76,160,620,195,60,'#f3f5e9');
    text(s,'Annual mean size. Four qubits.\nA matched comparison.',76,365,600,74,24,'#c2d0c5');
    text(s,'657',76,452,230,110,100,'#ddaa6c');text(s,'ha / recorded fire\nOntario, 2021',330,474,500,74,25,'#c2d0c5');
    text(s,'Full Ontario boundary · grey = unmapped woodland · 2021 records',76,642,1128,38,19,'#a8bdb4');
  }else if(i===1){
    mapImage(s,1,76,178,530,330);
    text(s,'Algonquin-area source cover pixels · 2021',76,527,540,32,20,muted);
    text(s,'NRCan · NFDB',670,181,530,30,20,muted);
    text(s,'784,447 ha ÷ 1,194 fires',670,226,534,43,30);
    text(s,'657 ha/fire',670,279,534,65,49,teal);
    text(s,'ECCC · Monthly Climate Summaries',670,374,534,36,23,muted);
    text(s,'Ten annual / seasonal climate inputs',670,427,534,42,26);
    text(s,'Join by year → one observation',670,490,534,45,25,teal);
    text(s,'31 training years · 1988–2018',76,582,600,33,24);
    text(s,'6 reused years · 2019–2024',740,582,470,33,24);
    foot(s,'Woodland = context / separate ablation. Final predictors use climate.');
  }else if(i===2){
    text(s,'Ten candidate climate features',76,206,510,36,22,muted);
    for(let j=0;j<10;j++){
      const chosen=[0,2,5,7].includes(j);ellipse(s,76+j*51,270,40,40,chosen?teal:'#b8c7be',chosen?teal:'none');
      text(s,chosen?'1':'0',87+j*51,278,24,29,21,chosen?'#ffffff':muted);
    }
    text(s,'Classical search\nQAOA samples → SQD',76,371,520,91,31);
    text(s,'Four-of-ten subset schematic\n210 possible subsets',76,508,520,77,23,muted);
    chart(s,'bar',{position:{left:650,top:204,width:560,height:367},categories:['Exact classical','Uniform + SQD','QAOA + SQD'],series:[{name:'Fixed-ridge MAE ha/fire',values:[e.selectors.exact_same_qubo,e.selectors.uniform_bitstring_budget,e.selectors.qaoa_same_qubo],fill:teal}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:100},hasLegend:false,xAxis:{...axis,min:0,max:100,majorUnit:25},yAxis:{...axis,min:0,max:100,majorUnit:25,majorGridlines:null},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:22,fill:ink}}});
    foot(s,'Fixed-ridge MAE · ha/fire · lower is better.\nDiagonal SQD returns the best sampled subset. No quantum advantage.');
  }else if(i===3){
    text(s,'Same four inputs. Same tuning budget.',76,158,1128,50,27,muted);
    chart(s,'bar',{position:{left:76,top:236,width:1128,height:350},categories:['Training mean','RBF-SVR · 4 inputs','QSVR · 4 qubits'],series:[{name:'MAE ha/fire',values:[e.development.training_mean.mae,e.development.matched_rbf_svr_4.mae,e.development.matched_fidelity_svr_4.mae],fill:teal,points:[{idx:0,fill:'#7c8988'},{idx:1,fill:'#a4b6b0'},{idx:2,fill:teal}]}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:70},hasLegend:false,xAxis:{...axis,min:0,max:110,majorUnit:20,numberFormatCode:'0.00'},yAxis:{...axis,min:0,max:110,majorUnit:20,majorGridlines:null},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:24,fill:ink}}});
    foot(s,'Qiskit encodes angles and computes overlaps; both models use classical SVR.\nEqual tuning budgets and chronological preprocessing. MAE · ha/fire · lower is better.');
  }else if(i===4){
    text(s,'Recorded mean hectares per fire—not total burned area.',76,158,1128,44,27,muted);
    text(s,'Mean fire size · hectares per recorded fire',76,208,1128,28,20,muted);
    const series=[['Recorded mean',e.final[0].actual_ha,orange],['Training mean',e.final[0].predicted_ha,'#7c8988'],['QSVR · 4',e.final.find(r=>r.id==='matched_fidelity_svr_4').predicted_ha,teal],['RBF · 4',e.final.find(r=>r.id==='matched_rbf_svr_4').predicted_ha,'#a4b6b0']].map(([name,values,color])=>({name,values,fill:color}));
    chart(s,'bar',{position:{left:76,top:245,width:1128,height:344},categories:e.final[0].years.map(String),series,hasLegend:true,legend:{position:'bottom',textStyle:{typeface:font,fontSize:18,fill:ink}},xAxis:{...axis,majorGridlines:null},yAxis:{...axis,min:0,max:700,majorUnit:200,numberFormatCode:'0'},barOptions:{direction:'column',grouping:'clustered',gapWidth:65}});
    foot(s,'Reused-year MAE · mean 276.81 · QSVR 280.68 · RBF 299.81 ha/fire\nFrozen before annual evaluation; these six years are not a pristine holdout.');
  }else if(i===5){
    text(s,'A measured scale sweep—not a newly fitted predictor.',76,158,1128,46,27,muted);
    phaseDials(s);text(s,'Illustrative phase rotations at π/4 · radians',76,415,550,36,20,muted);
    text(s,'0.000805 → 0.538897',76,501,560,65,37,teal);text(s,'Mean training fidelity · π/4 → π/32',76,569,560,34,21,muted);
    const rows=e.geometry.filter(r=>r.inputs===10);
    text(s,'Measured effective rank · maximum 31',690,206,515,30,20,muted);
    chart(s,'bar',{position:{left:690,top:235,width:515,height:340},categories:rows.map(r=>'π/'+r.amplitude_pi_denominator),series:[{name:'Measured effective rank /31',values:rows.map(r=>r.effective_rank),fill:teal}],barOptions:{direction:'column',grouping:'clustered',gapWidth:90},hasLegend:false,xAxis:{...axis,majorGridlines:null},yAxis:{...axis,min:0,max:31,numberFormatCode:'0'},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:20,fill:ink}}});
    foot(s,'Input-only diagnostic. Narrower angles can also make kernels ill-conditioned.');
  }else if(i===6){
    const rows=[['77.02 vs 86.64','RBF / QSVR development MAE · ha/fire'],['No later-year win.','The training mean beats every main model.'],['Encoding matters.','Similarity changes with angle scale; skill is not guaranteed.']];
    rows.forEach(([title,body],j)=>{text(s,title,76,218+j*125,1128,58,40);text(s,body,76,281+j*125,1128,36,24,muted);});
    foot(s,'Next: prospective targets, independent observations and raw/log-target controls.');
  }else if(i===7){
    for(let j=0;j<4;j++){
      const y=270+j*65;
      text(s,'q'+j,76,y-10,60,30,18,muted);
      s.shapes.add({geometry:'line',position:{left:115,top:y,width:545,height:0},line:{fill:'#b2bfb7',width:1.5}});
      text(s,'H',146,y-17,45,34,23,teal);text(s,'P(2θ'+j+')',227,y-17,110,34,23,teal);
      if(j<3){
        const x=411+j*85;
        s.shapes.add({geometry:'line',position:{left:x,top:y,width:0,height:65},line:{fill:teal,width:2.5}});
        ellipse(s,x-4,y-4,8,8,teal,teal);ellipse(s,x-4,y+61,8,8,teal,teal);
        text(s,'ZZ',x+10,y+20,45,28,18,teal);
      }
    }
    text(s,'Four-qubit linear ZZ map · schematic gate layout',76,524,595,37,20,muted);
    [['Bound the standardized input','θ = a tanh(z / 2)'],['Compare the encoded states','k(x,y) = |〈φ(x) | φ(y)〉|²'],['Classical prediction','Similarity matrix → SVR']].forEach(([a,b],j)=>{
      text(s,a,730,235+j*110,475,30,19,muted);text(s,b,730,274+j*110,475,44,26);
    });
    foot(s,'Actual FidelityQuantumKernel + QSVR · exact simulation · training-only preprocessing\nEntangling features does not guarantee predictive skill.');
  }else{
    text(s,'Final fit / saved-year evaluation · seconds',76,214,590,30,20,muted);
    [[e.resources.training_seconds,'Training'],[e.resources.evaluation_seconds,'Evaluation']].forEach(([v,label],j)=>{
      const y=262+j*120;
      text(s,v.toFixed(2),76,y,230,65,52);text(s,label,324,y+26,290,38,24,muted);
      s.shapes.add({geometry:'rect',position:{left:76,top:y+78,width:530*v/e.resources.training_seconds,height:5},fill:teal,line:{fill:'none',width:0}});
    });
    text(s,'267 kB',76,521,300,76,59,teal);text(s,'Frozen evidence package\nNo-fit public replay',376,536,270,66,22,muted);
    const t=s.tables.add({rows:4,columns:2,left:715,top:227,width:490,height:347,columnWidths:[245,245],values:[['Fidelity pairs','12,092 train\n2,232 evaluation'],['Scale diagnostic','4,650 pairs\n48.89 s'],['Evaluation refits','0'],['Hardware jobs','0']]});
    t.cells.block({row:0,column:0,rowCount:4,columnCount:2}).assign({fill:paper,textStyle:{typeface:font,fontSize:21,color:ink},margins:{left:8,right:8,top:12,bottom:12}});
    t.borders.assign({fill:'#d2dbd7',width:1,style:'solid'});
    foot(s,'Local analytic circuits, not physical shots. Runtime excludes installation.\nSeven main slides · 300-second plan · appendices for questions.');
  }
}
const candidate=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidate);
for(let i=0;i<p.slides.items.length;i++){
  const slide=p.slides.items[i];
  await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await(await p.export({slide,format:'png',scale:1})).arrayBuffer()));
}
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:output,pythonExecutable:RUNTIME_PYTHON,
  integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
  explicitTotalSlideCount:9,requiredNativeChartOwnerSlides:[3,4,5,6],requiredNativeTableOwnerSlides:[9],
  materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','9'],receiptPath:path.join(build,'validation.json')});
console.log(`Exported ${output}`);
