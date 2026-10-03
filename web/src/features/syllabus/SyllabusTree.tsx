import {useEffect,useRef} from 'react';
import {ChevronDown,BookOpen} from 'lucide-react';
import type {Interval,SyllabusNode} from '../../types';
import {subtractIntervals,toggleNode,timeLabel} from './selection';
type Props={nodes:SyllabusNode[];selected:Interval[];onChange:(selected:Interval[])=>void;cardCounts:Record<string,number>};
function Row({node,selected,onChange,cardCounts,child=false}:Props&{node:SyllabusNode;child?:boolean}){
 const ref=useRef<HTMLInputElement>(null);
 const unchecked=subtractIntervals([{start:node.start,end:node.end}],selected);
 const checked=unchecked.length===0;
 const partial=!checked&&unchecked.reduce((sum,i)=>sum+i.end-i.start,0)<node.end-node.start;
 useEffect(()=>{if(ref.current)ref.current.indeterminate=partial;},[partial]);
 return <label className={`syllabus-row ${child?'child-row':''} ${checked?'selected-row':''}`}>
  <input ref={ref} type="checkbox" aria-label={node.title} checked={checked} onChange={e=>onChange(toggleNode(selected,node,e.target.checked))}/>
  <span className="row-content"><span className="row-title">{node.title}</span><span className="row-meta">{timeLabel(node.start)} – {timeLabel(node.end)}{node.inferred&&<span className="inferred-tag">{child?'Subtopic':'Inferred'}</span>}</span></span>
  {cardCounts[node.id]!==undefined&&<span className="card-count">{cardCounts[node.id]} cards</span>}
 </label>;
}
export function SyllabusTree(props:Props){
 return <div className="syllabus-tree">{props.nodes.filter(n=>!n.parent_id).map((node,index)=>{
  const children=props.nodes.filter(n=>n.parent_id===node.id);
  return <section className="chapter" key={node.id}><div className="chapter-number">{String(index+1).padStart(2,'0')}</div><div className="chapter-main"><Row {...props} node={node}/>{children.length>0&&<details open><summary><ChevronDown size={14}/>{children.length} subtopic{children.length===1?'':'s'}</summary>{children.map(child=><Row key={child.id} {...props} node={child} child/>)}</details>}</div></section>;
 })}{props.nodes.length===0&&<div className="empty-syllabus"><BookOpen size={26}/><p>Your chapter outline will appear here after processing.</p></div>}</div>;
}
