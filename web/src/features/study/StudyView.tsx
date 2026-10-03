import {useEffect,useRef,useState} from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {ArrowLeft,ArrowRight,RotateCw,Play,ExternalLink,X,Layers} from 'lucide-react';
import type {Card,LectureView} from '../../types';
import type {StudySession} from './session';
import {reconcileSession} from './session';
import {timeLabel} from '../syllabus/selection';
import './study.css';

export function StudyView({session,cards,lecture,onSessionChange,onExit}:{session:StudySession;cards:Card[];lecture:LectureView;onSessionChange:(session:StudySession)=>void;onExit:()=>void}){
 const current=reconcileSession(session,cards);const card=cards.find(c=>c.id===current.cardIds[current.index]);
 const [watching,setWatching]=useState(false);const video=useRef<HTMLVideoElement>(null);
 const flip=()=>onSessionChange({...current,flipped:!current.flipped});
 const navigate=(delta:number)=>{const index=current.index+delta;if(index>=0&&index<current.cardIds.length){onSessionChange({...current,index,flipped:false});setWatching(false);}};
 useEffect(()=>{
  function keydown(event:KeyboardEvent){
   const target=event.target as HTMLElement;
   if(target?.closest('input,textarea,select,a,video,[contenteditable=true]'))return;
   if(event.key===' '){if(target?.closest('button'))return;event.preventDefault();flip();}
   if(event.key==='ArrowRight'){event.preventDefault();navigate(1);}
   if(event.key==='ArrowLeft'){event.preventDefault();navigate(-1);}
  }
  window.addEventListener('keydown',keydown);return()=>window.removeEventListener('keydown',keydown);
 },[current.index,current.flipped,current.cardIds.join(',')]);
 const topic=lecture.syllabus.find(n=>n.id===card?.topic_id)?.title||'Lecture';
 if(!card)return <div className="empty-study"><Layers size={32}/><h2>No cards in this selection yet.</h2><p>Generate cards for these topics, then start a study session.</p><button className="secondary" onClick={onExit}>Back to syllabus</button></div>;
 const seek=()=>{if(video.current)video.current.currentTime=card.source_start;};
 return <section className="study-workspace"><div className="study-topline"><button className="text-button" onClick={onExit}><ArrowLeft size={15}/>Back to syllabus</button><span>{current.index+1} of {current.cardIds.length} cards</span></div><div className="study-progress"><span style={{width:`${(current.index+1)/current.cardIds.length*100}%`}}/></div>
  <div className="topic-pill"><Layers size={13}/>{topic}</div>
  <div className={`flashcard ${current.flipped?'answer-side':''}`}><div className="card-side-label">{current.flipped?'ANSWER':'QUESTION'}<span>{current.flipped?'Check what you recalled':'Think before you flip'}</span></div>
   <div className="card-hit-area" role="button" tabIndex={0} aria-label={current.flipped?'Show question':'Reveal answer'} onClick={flip}>
    <div className="card-text"><ReactMarkdown remarkPlugins={[remarkGfm]}>{current.flipped?card.back:card.front}</ReactMarkdown></div>
   </div>
   <div className="card-bottom"><span>From your lecture</span><button className="flip-button" aria-label="Flip card" onClick={flip}><RotateCw size={16}/>Flip card</button></div>
  </div>
  <div className="study-controls"><button className="nav-card" aria-label="Previous card" disabled={current.index===0} onClick={()=>navigate(-1)}><ArrowLeft size={19}/></button><div><strong>{current.index+1}<span> / {current.cardIds.length}</span></strong><small>← → to navigate · Space to flip</small></div><button className="nav-card" aria-label="Next card" disabled={current.index===current.cardIds.length-1} onClick={()=>navigate(1)}><ArrowRight size={19}/></button></div>
  {current.flipped&&<div className="evidence-panel"><div className="evidence-heading"><span>BACK TO THE SOURCE · {timeLabel(card.source_start)}</span>{lecture.youtube_id?<a href={`https://www.youtube.com/watch?v=${lecture.youtube_id}&t=${Math.floor(card.source_start)}s`} target="_blank" rel="noreferrer"><Play size={13}/>Watch this explanation<ExternalLink size={12}/></a>:lecture.media_url&&<button className="text-button" onClick={()=>setWatching(true)}><Play size={13}/>Watch this explanation</button>}</div><details><summary>View supporting transcript</summary><blockquote>{card.source_excerpt}</blockquote></details></div>}
  {watching&&lecture.media_url&&<div className="video-panel"><button className="text-button" onClick={()=>setWatching(false)}><X size={15}/>Close video</button><video ref={video} controls src={lecture.media_url} onLoadedMetadata={seek} aria-label="Supporting lecture video"/></div>}
 </section>;
}
