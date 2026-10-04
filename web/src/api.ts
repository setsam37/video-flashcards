import type {Interval,LectureView,LectureSummary} from './types';
let csrfToken='';
export function setCsrfToken(value:string){csrfToken=value;}
async function request<T>(path:string,init?:RequestInit):Promise<T>{
 const headers=new Headers(init?.headers);
 if(csrfToken&&init?.method&&init.method!=='GET')headers.set('X-CSRF-Token',csrfToken);
 const response=await fetch(path.startsWith('/auth/')?path:'/api'+path,{...init,headers,cache:'no-store'});
 const content=await response.json();
 if(response.status===401)window.dispatchEvent(new Event('recall-session-expired'));
 if(!response.ok)throw new Error(typeof content.detail==='string'?content.detail:'The request could not be completed.');
 return content;
}
export const api={
 handoff:()=>request<{lecture_id:string;job_id:string}>('/handoff',{method:'POST'}),
 logout:()=>request<{signed_out:boolean}>('/auth/logout',{method:'POST'}),
 health:()=>request<{status:string;provider_configured:boolean}>('/health'),
 list:()=>request<LectureSummary[]>('/lectures'),
 lecture:(id:string)=>request<LectureView>('/lectures/'+id),
 youtube:(url:string)=>request<{lecture_id:string;job_id:string}>('/lectures/youtube',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})}),
 upload:(video:File)=>{const body=new FormData();body.append('video',video);return request<{lecture_id:string;job_id:string}>('/lectures/upload',{method:'POST',body});},
 transcript:(id:string,transcript:File,video?:File)=>{const body=new FormData();body.append('transcript',transcript);if(video)body.append('video',video);return request<{lecture_id:string;job_id:string}>(`/lectures/${id}/transcript`,{method:'POST',body});},
 generate:(id:string,intervals:Interval[],regenerate=false)=>request<{lecture_id:string;job_id:string}>(`/lectures/${id}/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({intervals,regenerate})}),
 retry:(id:string)=>request<{job_id:string}>(`/jobs/${id}/retry`,{method:'POST'})
};
