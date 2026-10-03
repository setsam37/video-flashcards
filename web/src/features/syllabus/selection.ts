import type {Interval,SyllabusNode} from '../../types';
export function normalizeIntervals(items:Interval[]):Interval[]{
 const output:Interval[]=[];
 for(const item of [...items].sort((a,b)=>a.start-b.start)){
  const last=output.at(-1);
  if(last&&item.start<=last.end)last.end=Math.max(last.end,item.end);
  else output.push({...item});
 }
 return output;
}
export function subtractIntervals(selected:Interval[],covered:Interval[]):Interval[]{
 let remaining=normalizeIntervals(selected);
 for(const cut of normalizeIntervals(covered)){
  remaining=remaining.flatMap(item=>{
   if(cut.end<=item.start||cut.start>=item.end)return [item];
   const result:Interval[]=[];
   if(item.start<cut.start)result.push({start:item.start,end:cut.start});
   if(cut.end<item.end)result.push({start:cut.end,end:item.end});
   return result;
  });
 }
 return remaining;
}
export function toggleNode(selected:Interval[],node:SyllabusNode,checked:boolean){
 const span={start:node.start,end:node.end};
 return checked?normalizeIntervals([...selected,span]):subtractIntervals(selected,[span]);
}
export function selectedTime(time:number,intervals:Interval[]){return intervals.some(i=>i.start<=time&&time<i.end);}
export function timeLabel(time:number){const s=Math.floor(time);return s>=3600?`${Math.floor(s/3600)}:${String(Math.floor(s%3600/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`:`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;}
