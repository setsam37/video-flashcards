from pathlib import Path
import uuid
from fastapi import APIRouter,Request,UploadFile,File,HTTPException
from fastapi.responses import FileResponse
from .models import Model,Interval,SourceDescriptor
from .jobs import JobQueue
from .importing.youtube import canonical_youtube
from .importing.captions import parse_captions
from .syllabus.selection import normalize

router=APIRouter(prefix='/api')
class YouTubeRequest(Model):url:str
class GenerationRequest(Model):
    intervals:list[Interval]
    regenerate:bool=False

def repository(request):return request.app.state.repository
def source_or_404(repo,id):
    try:return repo.get_source(id)
    except KeyError:raise HTTPException(404,'Lecture not found') from None

async def store_video(video,config):
    suffix=Path((video.filename or '').replace('\\','/')).suffix.lower()
    if suffix not in ['.mp4','.webm']:raise HTTPException(422,'Upload an MP4 or WebM video.')
    path=config.data_dir/'media'/f'{uuid.uuid4().hex}{suffix}'
    total=0
    try:
        with path.open('wb') as out:
            while block:=await video.read(1024**2):
                total+=len(block)
                if total>config.upload_limit_bytes:raise HTTPException(413,'The video exceeds the configured upload limit.')
                out.write(block)
        if total==0:raise HTTPException(422,'The video is empty.')
    except Exception:
        path.unlink(missing_ok=True);raise
    finally:await video.close()
    return path

@router.get('/lectures')
def list_lectures(request:Request):return repository(request).list_lectures()

@router.get('/lectures/{id}')
def get_lecture(id:str,request:Request):
    repo=repository(request);source_or_404(repo,id)
    return repo.get_lecture(id)

@router.post('/lectures/upload')
async def upload(request:Request,video:UploadFile=File()):
    path=await store_video(video,request.app.state.config);id=uuid.uuid4().hex;repo=repository(request)
    title=Path((video.filename or 'Lecture').replace('\\','/')).stem
    repo.save_source(SourceDescriptor(lecture_id=id,title=title,duration=0,source_kind='upload',media_path=str(path.resolve())))
    job=JobQueue(repo).enqueue(id,'prepare',[],False)
    return {'lecture_id':id,'job_id':job.id}

@router.post('/lectures/youtube')
def youtube(body:YouTubeRequest,request:Request):
    video_id,_=canonical_youtube(body.url);id=uuid.uuid4().hex;repo=repository(request)
    repo.save_source(SourceDescriptor(lecture_id=id,title='YouTube lecture',duration=0,source_kind='youtube',youtube_id=video_id))
    job=JobQueue(repo).enqueue(id,'prepare',[],False)
    return {'lecture_id':id,'job_id':job.id}

@router.post('/lectures/{id}/transcript')
async def transcript(id:str,request:Request,transcript:UploadFile=File(),video:UploadFile|None=File(default=None)):
    repo=repository(request);source=source_or_404(repo,id);view=repo.get_lecture(id)
    if view.cards:raise HTTPException(409,'Import a new lecture to replace a transcript with existing cards.')
    if any(j.status in ['queued','running'] for j in view.jobs):raise HTTPException(409,'Wait for current processing to finish before attaching a transcript.')
    suffix=Path(transcript.filename or '').suffix.lower()
    if suffix not in ['.srt','.vtt']:raise HTTPException(422,'Use an SRT or VTT transcript.')
    content=await transcript.read(20*1024**2+1);await transcript.close()
    if len(content)>20*1024**2:raise HTTPException(413,'The transcript exceeds 20 MB.')
    try:segments=parse_captions(content.decode('utf-8-sig'),suffix[1:])
    except UnicodeError:raise HTTPException(422,'The transcript must use UTF-8 encoding.') from None
    if video:
        path=await store_video(video,request.app.state.config)
        from .importing.media import probe_media
        probed=probe_media(path,id,request.app.state.config)
        source=source.model_copy(update={'media_path':str(path.resolve()),'duration':probed.duration,'chapters':source.chapters or probed.chapters})
    if not source.media_path and not source.youtube_id:raise HTTPException(422,'Attach a video or retain a YouTube reference for playback.')
    if source.duration==0:source=source.model_copy(update={'duration':max(s.end for s in segments)})
    if max(s.end for s in segments)>source.duration+2:raise HTTPException(422,'Transcript timestamps extend beyond this lecture.')
    repo.save_source(source);repo.save_transcript(id,segments)
    job=JobQueue(repo).enqueue(id,'prepare',[],False)
    return {'lecture_id':id,'job_id':job.id}

@router.post('/lectures/{id}/generate')
def generate(id:str,body:GenerationRequest,request:Request):
    repo=repository(request);source=source_or_404(repo,id)
    if not body.intervals:raise HTTPException(422,'Select at least one topic.')
    if any(i.end>source.duration for i in body.intervals):raise HTTPException(422,'A selected range exceeds the lecture duration.')
    if not repo.get_nodes(id) or not repo.get_segments(id):raise HTTPException(422,'Prepare the syllabus and transcript first.')
    if any(j.kind=='prepare' and j.status in ['queued','running'] for j in repo.get_lecture(id).jobs):raise HTTPException(409,'Syllabus preparation is still running.')
    job=JobQueue(repo).enqueue(id,'generate',normalize(body.intervals),body.regenerate)
    return {'lecture_id':id,'job_id':job.id}

@router.post('/jobs/{id}/retry')
def retry(id:str,request:Request):
    try:job=JobQueue(repository(request)).retry(id)
    except KeyError:raise HTTPException(404,'Job not found') from None
    except ValueError as error:raise HTTPException(409,str(error)) from None
    return {'job_id':job.id}

@router.get('/lectures/{id}/media')
def media(id:str,request:Request):
    source=source_or_404(repository(request),id)
    if not source.media_path:raise HTTPException(404,'No uploaded video is attached.')
    path=Path(source.media_path).resolve();root=(request.app.state.config.data_dir/'media').resolve()
    if not path.is_relative_to(root) or not path.is_file():raise HTTPException(404,'Uploaded video not found.')
    return FileResponse(path,media_type='video/webm' if path.suffix=='.webm' else 'video/mp4')
