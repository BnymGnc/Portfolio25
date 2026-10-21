export function periodIndices(timestamps:string[],start:string,days:number){
  if(days===366)return timestamps.map((_,i)=>i);
  const from=Date.parse(`${start}T00:00:00+03:00`);
  return timestamps.flatMap((stamp,i)=>{const t=Date.parse(stamp);return t>=from&&t<from+days*86400000?[i]:[]});
}
