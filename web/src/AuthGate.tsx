import {useEffect,useState,type ReactNode} from 'react';
import {Layers} from 'lucide-react';
import {api,setCsrfToken} from './api';

type Session={hosted:boolean;authenticated:boolean;email?:string;csrf_token?:string;pending?:boolean};
function clearStudy(){try{for(const key of Object.keys(sessionStorage))if(key.startsWith('recall-'))sessionStorage.removeItem(key);}catch{}}

export function AuthGate({children}:{children:(hosted:boolean)=>ReactNode}){
 const [session,setSession]=useState<Session|null>(null),[error,setError]=useState('');
 useEffect(()=>{
  let active=true;const controller=new AbortController();
  async function open(){
   try{
    const response=await fetch('/auth/session',{signal:controller.signal,cache:'no-store'});
    if(!response.ok)throw new Error('Sign-in is unavailable. Try reloading in a moment.');
    const next:Session=await response.json();if(!active)return;
    setCsrfToken(next.csrf_token||'');
    if(!next.authenticated)clearStudy();
    if(next.pending){const result=await api.handoff();if(!active)return;try{sessionStorage.setItem('recall-active-lecture',result.lecture_id);}catch{}}
    setSession(next);
   }catch(e){if(active)setError(e instanceof Error?e.message:'The library is unavailable. Reload to retry.');}
  }
  const expired=()=>{clearStudy();setCsrfToken('');setSession({hosted:true,authenticated:false});setError('Your session ended. Sign in to continue.');};
  window.addEventListener('recall-session-expired',expired);open();
  return()=>{active=false;controller.abort();window.removeEventListener('recall-session-expired',expired);};
 },[]);
 async function signOut(){try{await api.logout();clearStudy();setCsrfToken('');setSession({hosted:true,authenticated:false});}catch(e){setError(e instanceof Error?e.message:'Sign out failed. Try again.');}}
 if(session?.authenticated)return <>{session.hosted&&<div className="account-bar"><span>{session.email} · Private library</span><button className="text-button" onClick={signOut}>Sign out</button>{error&&<span role="alert">{error}</span>}</div>}{children(session.hosted)}</>;
 const failed=new URLSearchParams(window.location.search).has('signin');
 return <main className="signin-page"><span className="brand-mark"><Layers size={28}/></span><h1>Your next lesson starts here.</h1><p>Sign in to open your own videos, topics, and flashcards.</p>{error&&<p role="alert">{error}</p>}{failed&&<p role="alert">Sign-in did not finish. Use an invited Google account and try again.</p>}{session?<><a className="primary" href="/auth/login">Continue with Google</a><small>Each account has its own private library.</small></>:error?<button className="secondary" onClick={()=>window.location.reload()}>Reload</button>:<p role="status">Opening your study space…</p>}</main>;
}
