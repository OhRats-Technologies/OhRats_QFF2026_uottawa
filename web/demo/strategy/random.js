export function random(state) {
  let x=state.rng|0;
  x^=x<<13;x^=x>>>17;x^=x<<5;
  state.rng=x>>>0;
  return state.rng/4294967296;
}
export const clamp=(x,min=0,max=1)=>Math.min(max,Math.max(min,x));
export function shuffle(items,state) {
  const result=[...items];
  for(let i=result.length-1;i>0;i--){const j=Math.floor(random(state)*(i+1));[result[i],result[j]]=[result[j],result[i]];}
  return result;
}
