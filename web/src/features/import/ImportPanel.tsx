import {useState} from 'react';
import {Link,Upload,ArrowRight,LoaderCircle} from 'lucide-react';
import {api} from '../../api';
export function ImportPanel({onImported,onClose,videoUploadsEnabled=true}:{onImported:(id:string)=>void;onClose?:()=>void;videoUploadsEnabled?:boolean}){
 const [tab,setTab]=useState<'link'|'file'>('link');const [url,setUrl]=useState('https://www.youtube.com/watch?v=C842vFY5kRo');
 const [file,setFile]=useState<File>();const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 async function submit(e:React.FormEvent){
  e.preventDefault();setError('');setBusy(true);
  try{const result=tab==='link'?await api.youtube(url):await api.upload(file!);onImported(result.lecture_id);}
  catch(e){setError(e instanceof Error?e.message:'Import failed.');}finally{setBusy(false);}
 }
 return <section className="import-panel"><div className="section-heading"><div><span className="eyebrow">START WITH A LECTURE</span><h2>Bring your video.</h2></div>{onClose&&<button className="text-button" onClick={onClose}>Close</button>}</div>
  <p className="muted">Get a chapter syllabus, then choose what you want to remember.</p>
  <div className="segmented" role="group" aria-label="Import source"><button className={tab==='link'?'active':''} onClick={()=>setTab('link')}><Link size={16}/>YouTube link</button>{videoUploadsEnabled&&<button className={tab==='file'?'active':''} onClick={()=>setTab('file')}><Upload size={16}/>Upload video</button>}</div>
  {!videoUploadsEnabled&&<p className="small muted">Online study supports YouTube links and captions. Use the local app for video uploads.</p>}
  <form onSubmit={submit}>{tab==='link'?<label className="field-label">Video URL<input type="url" value={url} onChange={e=>setUrl(e.target.value)} required placeholder="https://www.youtube.com/watch?v=…"/></label>:<label className="upload-zone"><Upload size={25}/><strong>{file?.name||'Choose a lecture video'}</strong><span>MP4 or WebM · up to 4 GB</span><input aria-label="Upload video file" type="file" accept=".mp4,.webm" onChange={e=>setFile(e.target.files?.[0])}/></label>}
   <p className="small muted">Uses the video's audio or captions. Material shown only on screen may be missed.</p>
   {error&&<p role="alert" className="error-message">{error}</p>}
   <button className="primary" disabled={busy||(tab==='file'&&!file)}>{busy?<LoaderCircle size={17} className="spin"/>:<ArrowRight size={17}/>} {busy?'Importing…':'Create syllabus'}</button>
  </form>
 </section>;
}
