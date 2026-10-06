// Small, deterministic teaching models. No hardware or trained predictor calls.
export function rotateZ(vector,angle) {
  const [x,y,z]=vector,c=Math.cos(angle),s=Math.sin(angle);
  return [c*x-s*y,s*x+c*y,z];
}
export function channel(vector,damping,dephasing) {
  const [x,y,z]=vector,scale=Math.sqrt(1-damping)*(1-dephasing);
  return [scale*x,scale*y,(1-damping)*z+damping];
}
export function managedVector(vector,{idle=.7,gate=.3,dd=false,twirl=false,damping=0,dephasing=0}={}) {
  // Ideal echo cancels static idle Z drift. It cannot undo damping here.
  const rotated=rotateZ(vector,dd?0:idle);
  const tailored=twirl?[rotated[0]*Math.cos(gate),rotated[1]*Math.cos(gate),rotated[2]]:rotateZ(rotated,gate);
  return channel(tailored,damping,dephasing);
}
export function eigensystem(matrix) {
  const n=matrix.length,a=matrix.map(row=>row.slice());
  const vectors=Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>+(i===j)));
  for(let sweep=0;sweep<100;sweep++){
    let p=0,q=1,maximum=0;
    for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)if(Math.abs(a[i][j])>maximum){maximum=Math.abs(a[i][j]);p=i;q=j;}
    if(maximum<1e-12)break;
    const angle=.5*Math.atan2(2*a[p][q],a[q][q]-a[p][p]);
    const c=Math.cos(angle),s=Math.sin(angle),app=a[p][p],aqq=a[q][q],apq=a[p][q];
    for(let k=0;k<n;k++)if(k!==p&&k!==q){
      const kp=a[k][p],kq=a[k][q];
      a[k][p]=a[p][k]=c*kp-s*kq;a[k][q]=a[q][k]=s*kp+c*kq;
    }
    a[p][p]=c*c*app-2*s*c*apq+s*s*aqq;
    a[q][q]=s*s*app+2*s*c*apq+c*c*aqq;a[p][q]=a[q][p]=0;
    for(let k=0;k<n;k++){
      const vp=vectors[k][p],vq=vectors[k][q];
      vectors[k][p]=c*vp-s*vq;vectors[k][q]=s*vp+c*vq;
    }
  }
  return Array.from({length:n},(_,index)=>({value:a[index][index],vector:vectors.map(row=>row[index])})).sort((a,b)=>b.value-a.value);
}
export function repair(matrix,rank=matrix.length) {
  const eigen=eigensystem(matrix),n=matrix.length;
  return Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>eigen.slice(0,rank).reduce((sum,item)=>sum+Math.max(0,item.value)*item.vector[i]*item.vector[j],0)));
}
export const matrixError=(a,b)=>Math.sqrt(a.reduce((sum,row,i)=>sum+row.reduce((subtotal,value,j)=>subtotal+(value-b[i][j])**2,0),0));
export function readout(probability,p01=.08,p10=.08) {
  return p10+(1-p01-p10)*probability;
}
export function correctReadout(observed,p01=.08,p10=.08) {
  return (observed-p10)/(1-p01-p10);
}
export const feasible=bits=>bits.reduce((sum,bit)=>sum+bit,0)===4;
