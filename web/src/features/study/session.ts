import type {Card,Interval,StudyMode} from '../../types';
import {selectedTime} from '../syllabus/selection';
export type StudySession={cardIds:string[];index:number;flipped:boolean};
export function createSession(cards:Card[],mode:StudyMode,intervals:Interval[],shuffle:boolean):StudySession{
 const unique=[...new Map(cards.filter(c=>mode==='all'||selectedTime(c.primary_time,intervals)).map(c=>[c.id,c])).values()].sort((a,b)=>a.primary_time-b.primary_time||a.id.localeCompare(b.id));
 const cardIds=unique.map(c=>c.id);
 if(shuffle)for(let i=cardIds.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[cardIds[i],cardIds[j]]=[cardIds[j],cardIds[i]];}
 return {cardIds,index:0,flipped:false};
}
export function reconcileSession(session:StudySession,cards:Card[]):StudySession{
 const available=new Set(cards.map(c=>c.id));const current=session.cardIds[session.index];
 const cardIds=[...new Set(session.cardIds)].filter(id=>available.has(id));
 const index=cardIds.includes(current)?cardIds.indexOf(current):Math.max(0,Math.min(session.index,cardIds.length-1));
 return {cardIds,index,flipped:session.flipped};
}
export function readSession(key:string):StudySession|null{
 try{const item=JSON.parse(sessionStorage.getItem(key)||'null');if(!item||!Array.isArray(item.cardIds)||!item.cardIds.every((id:unknown)=>typeof id==='string')||!Number.isInteger(item.index)||item.index<0||typeof item.flipped!=='boolean')return null;return item;}catch{return null;}
}
export function saveSession(key:string,session:StudySession){try{sessionStorage.setItem(key,JSON.stringify(session));}catch{/* Study remains usable when browser storage is disabled. */}}
