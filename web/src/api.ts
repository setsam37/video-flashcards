import type {Interval,LectureView,LectureSummary} from './types';
async function request<T>(path:string,init?:RequestInit):Promise<T>{
 const response=await fetch('/api'+path,init);
 const content=await response.json();
 if(!response.ok)throw new Error(typeof content.detail==='string'?content.detail:'The request could not be completed.');
 return content;
}
export const api={
 health:()=>request<{status:string;provider_configured:boolean}>('/health'),
 list:()=>request<LectureSummary[]>('/lectures'),
 lecture:(id:string)=>request<LectureView>('/lectures/'+id),
 youtube:(url:string)=>request<{lecture_id:string;job_id:string}>('/lectures/youtube',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})}),
 upload:(video:File)=>{const body=new FormData();body.append('video',video);return request<{lecture_id:string;job_id:string}>('/lectures/upload',{method:'POST',body});},
 transcript:(id:string,transcript:File,video?:File)=>{const body=new FormData();body.append('transcript',transcript);if(video)body.append('video',video);return request<{lecture_id:string;job_id:string}>(`/lectures/${id}/transcript`,{method:'POST',body});},
 generate:(id:string,intervals:Interval[],regenerate=false)=>request<{lecture_id:string;job_id:string}>(`/lectures/${id}/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({intervals,regenerate})}),
 retry:(id:string)=>request<{job_id:string}>(`/jobs/${id}/retry`,{method:'POST'})
};
