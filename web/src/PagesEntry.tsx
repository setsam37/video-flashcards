import {useState} from 'react';
import {ArrowRight,BookOpen,Layers,Link,Shuffle} from 'lucide-react';
import './pages.css';

export function PagesEntry({appUrl=import.meta.env.VITE_APP_URL||''}:{appUrl?:string}){
 let destination='';
 try{const parsed=new URL(appUrl);if(parsed.protocol==='https:'&&!parsed.username&&!parsed.password&&!parsed.port&&['','/'].includes(parsed.pathname)&&!parsed.search&&!parsed.hash)destination=parsed.origin;}catch{}
 const [url,setUrl]=useState(''),[message,setMessage]=useState('');
 function proceed(event:React.FormEvent){
  let supported=false;
  try{
   const parsed=new URL(url.trim());
   const host=parsed.hostname.toLowerCase();
   const video=host==='youtu.be'?parsed.pathname.slice(1):parsed.searchParams.get('v');
   supported=parsed.protocol==='https:'&&!parsed.username&&!parsed.password&&!parsed.port&&
    (host==='youtu.be'||(['youtube.com','www.youtube.com','m.youtube.com'].includes(host)&&parsed.pathname==='/watch'))&&!!video&&/^[A-Za-z0-9_-]{11}$/.test(video);
  }catch{}
  if(supported&&destination)return;
  event.preventDefault();setMessage(supported?'Video processing is not connected to this website yet. No lesson was created. Open the local app to generate your syllabus and flashcards.':'Paste a valid HTTPS YouTube video link, such as youtube.com/watch?v=… or youtu.be/….');
 }
 return <div className="pages-entry"><header className="pages-nav"><a className="brand" href="./"><span className="brand-mark"><Layers size={23}/></span><span>recall<span className="brand-dot">.</span></span></a><span className="pages-tag">YOUR VIDEO. YOUR NEXT LESSON.</span></header>
  <main className="pages-main"><span className="eyebrow">LESS WATCHING. MORE REMEMBERING.</span><h1>Turn a video into<br/><span>something you remember.</span></h1><p className="pages-intro">Start with a lecture. Find its topics. Practice what it teaches.</p><p className="pages-connection">{destination?'Sign in with Google to save this lesson in your private library.':'Online video processing is not connected yet.'}</p>
   <form className="pages-video-box" action={destination?destination+'/start':undefined} method="post" onSubmit={proceed}><label htmlFor="video-url"><Link size={18}/>Paste your video link</label><input id="video-url" name="url" type="url" autoComplete="off" required placeholder="https://www.youtube.com/watch?v=…" value={url} onChange={event=>{setUrl(event.target.value);setMessage('');}}/><button className="primary" type="submit">Proceed to lesson<ArrowRight size={18}/></button><p>YouTube lecture links · choose the topics you want to study</p>{message&&<div className="pages-feedback" role="alert">{message}</div>}</form>
   <div className="pages-steps"><div><BookOpen size={22}/><strong>Find your topics</strong><p>A syllabus shaped by what the lecture teaches.</p></div><div><Layers size={22}/><strong>Make your cards</strong><p>Choose chapters and substantial subtopics.</p></div><div><Shuffle size={22}/><strong>Practice your recall</strong><p>Flip cards. Study one topic or mix your selection.</p></div></div>
   {destination?<aside className="pages-availability"><strong>Your library, wherever you study.</strong><p>Already have lessons? Open your library and continue.</p><a href={destination}>Open your library<ArrowRight size={14}/></a></aside>:<aside className="pages-availability"><strong>Online processing is not connected yet.</strong><p>This page cannot generate lessons. The working app is currently available on your computer.</p><a href="http://127.0.0.1:8000/">Open the app on this computer<ArrowRight size={14}/></a><small>The local app must be running.</small></aside>}
  </main><footer className="page-footer">Learn it once. Recall it often.</footer></div>;
}
