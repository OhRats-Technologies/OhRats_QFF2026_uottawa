import {describe,test,expect} from 'bun:test';
import {channel,managedVector,eigensystem,repair,matrixError,readout,correctReadout,feasible} from './quantum.js';

describe('quantum teaching models',()=>{
  test('damping tends to ground, while dephasing preserves z and all vectors remain physical',()=>{
    const input=[.6,0,.8];
    expect(channel(input,1,.5)).toEqual([0,0,1]);
    expect(channel(input,0,1)).toEqual([0,0,.8]);
    for(let damping=0;damping<=1;damping+=.1)for(let phase=0;phase<=1;phase+=.1){
      const vector=channel(input,damping,phase);
      expect(vector.reduce((sum,v)=>sum+v*v,0)).toBeLessThanOrEqual(1+1e-12);
    }
  });
  test('ideal echo removes static idle drift, not damping; twirling averages signs without restoring purity',()=>{
    const input=[1,0,0];
    expect(managedVector(input,{dd:true,idle:.7,gate:0})).toEqual(input);
    const damped=managedVector(input,{dd:true,gate:0,damping:.4});
    expect(damped[2]).toBeCloseTo(.4,12);
    const tailored=managedVector(input,{idle:0,gate:.6,twirl:true});
    expect(tailored[0]).toBeCloseTo(Math.cos(.6),12);
    expect(tailored[1]).toBe(0);
    expect(tailored[0]**2).toBeLessThan(1);
  });
  test('eigendecomposition reconstructs and PSD/low-rank repairs do what their names promise',()=>{
    const input=[[1,.9,.8,.9],[.9,1,1.1,.7],[.8,1.1,1,.95],[.9,.7,.95,1]];
    const eigen=eigensystem(input);
    const reconstruction=input.map((row,i)=>row.map((_,j)=>eigen.reduce((sum,item)=>sum+item.value*item.vector[i]*item.vector[j],0)));
    expect(matrixError(input,reconstruction)).toBeLessThan(1e-10);
    expect(eigen.at(-1).value).toBeLessThan(0);
    expect(eigensystem(repair(input)).at(-1).value).toBeGreaterThan(-1e-10);
    expect(eigensystem(repair(input,2)).filter(item=>item.value>1e-9)).toHaveLength(2);
  });
  test('known readout inversion is exact without shot noise, and cardinality is only a filter',()=>{
    for(const p of [0,.13,.5,.92,1])expect(correctReadout(readout(p))).toBeCloseTo(p,12);
    expect(feasible([1,1,1,1,0,0,0,0,0,0])).toBe(true);
    expect(feasible([0,1,1,1,1,0,0,0,0,0])).toBe(true); // Two flipped bits evade detection.
    expect(feasible([0,1,1,1,0,0,0,0,0,0])).toBe(false);
  });
});
