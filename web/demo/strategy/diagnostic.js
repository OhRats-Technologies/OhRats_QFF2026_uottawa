// JSON stdin reference for cross-language local Qiskit verification.
import {managedVector} from './quantum.js';
const input=await Bun.stdin.text();
const rows=JSON.parse(input);
const output=rows.map(row=>{
  const vector=[Math.sin(row.theta)*Math.cos(row.phi),Math.sin(row.theta)*Math.sin(row.phi),Math.cos(row.theta)];
  return managedVector(vector,row.options);
});
console.log(JSON.stringify(output));
