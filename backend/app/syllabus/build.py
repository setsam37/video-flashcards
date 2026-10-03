import hashlib,re
from ..models import Interval,SyllabusNode
from ..errors import ProcessingError
from ..jobs import JobQueue
from ..importing.youtube import import_youtube
from ..importing.media import probe_media
from ..importing.transcribe import transcribe_media

def node_id(lecture,start,end,parent=None):return hashlib.sha256(f'{lecture}:{start:.3f}:{end:.3f}:{parent}'.encode()).hexdigest()[:20]

def chapter_roots(source):
    roots=[];cursor=0
    for seed in sorted(source.chapters,key=lambda c:(c.start,c.end)):
        if seed.start<cursor or seed.end>source.duration:continue
        if seed.start>cursor:
            roots.append(SyllabusNode(id=node_id(source.lecture_id,cursor,seed.start),title='Additional material',start=cursor,end=seed.start,inferred=True))
        roots.append(SyllabusNode(id=node_id(source.lecture_id,seed.start,seed.end),title=seed.title,start=seed.start,end=seed.end))
        cursor=seed.end
    if roots and cursor<source.duration:roots.append(SyllabusNode(id=node_id(source.lecture_id,cursor,source.duration),title='Additional material',start=cursor,end=source.duration,inferred=True))
    return roots

def build_syllabus(source,segments,provider):
    if not segments:raise ProcessingError('transcript_missing','A timestamped transcript is needed before preparing the syllabus.')
    roots=chapter_roots(source)
    proposals=[]
    for start in range(0,max(1,int(source.duration)),600):
        window=[s for s in segments if s.end>start and s.start<start+600]
        if window:proposals.extend(provider.propose_syllabus(window,source.chapters))
    evidence={s.id:s for s in segments}
    usable=[p for p in proposals if p.end<=source.duration and p.title.strip() and p.source_segment_ids and all(id in evidence for id in p.source_segment_ids)]
    if not roots:
        tops=sorted([p for p in usable if p.parent_start is None],key=lambda p:(p.start,p.end))
        for p in tops:
            if roots and p.start<roots[-1].end:continue
            if roots and p.start<=roots[-1].end+2 and re.sub(r'\W','',p.title.casefold())==re.sub(r'\W','',roots[-1].title.casefold()):
                previous=roots.pop();p=p.model_copy(update={'start':previous.start})
            cursor=roots[-1].end if roots else 0
            if cursor<p.start:roots.append(SyllabusNode(id=node_id(source.lecture_id,cursor,p.start),title='Additional material',start=cursor,end=p.start,inferred=True))
            roots.append(SyllabusNode(id=node_id(source.lecture_id,p.start,p.end),title=p.title.strip(),start=p.start,end=p.end,inferred=True))
        if not roots:raise ProcessingError('syllabus_incomplete','No supported topics were identified. Retry syllabus preparation.')
        if roots[-1].end<source.duration:roots.append(SyllabusNode(id=node_id(source.lecture_id,roots[-1].end,source.duration),title='Additional material',start=roots[-1].end,end=source.duration,inferred=True))
    children=[]
    for p in sorted(usable,key=lambda p:(p.start,p.end)):
        parent=next((r for r in roots if r.start==p.parent_start and r.start<=p.start<p.end<=r.end),None)
        summaries={re.sub(r'\W','',x.casefold()) for x in p.point_summaries if x.strip()}
        if not parent or p.end-p.start<120 or len(summaries)<2 or p.title.strip().casefold()==parent.title.casefold():continue
        if p.start==parent.start and p.end==parent.end:continue
        if not all(evidence[id].end>p.start and evidence[id].start<p.end for id in p.source_segment_ids):continue
        if any(c.parent_id==parent.id and c.start<p.end and p.start<c.end for c in children):continue
        children.append(SyllabusNode(id=node_id(source.lecture_id,p.start,p.end,parent.id),parent_id=parent.id,title=p.title.strip(),start=p.start,end=p.end,inferred=True))
    return sorted(roots+children,key=lambda n:(n.start,n.parent_id is not None,n.end))

def prepare_lecture(job,repository,provider):
    from pathlib import Path
    queue=JobQueue(repository);source=repository.get_source(job.lecture_id);segments=repository.get_segments(job.lecture_id)
    queue.update(job.id,stage='importing')
    if source.source_kind=='youtube' and not segments:
        source,segments=import_youtube(f'https://www.youtube.com/watch?v={source.youtube_id}',source.lecture_id)
        repository.save_source(source)
        if source.chapters:repository.save_syllabus(source.lecture_id,chapter_roots(source))
        if segments:repository.save_transcript(source.lecture_id,segments)
        else:raise ProcessingError('captions_unavailable','YouTube captions are unavailable. Attach SRT/VTT captions or upload the video to continue.')
    elif source.media_path and source.duration==0:
        probed=probe_media(Path(source.media_path),source.lecture_id)
        source=probed.model_copy(update={'title':source.title,'source_kind':source.source_kind,'youtube_id':source.youtube_id})
        repository.save_source(source)
    if not segments:
        if not source.media_path:raise ProcessingError('transcript_missing','Attach captions or a video to prepare this lecture.')
        queue.update(job.id,stage='transcribing')
        segments=transcribe_media(source,provider,repository.path.parent/'jobs'/source.lecture_id/'transcription')
        repository.save_transcript(source.lecture_id,segments)
    if source.chapters:repository.save_syllabus(source.lecture_id,chapter_roots(source))
    queue.update(job.id,stage='syllabus')
    nodes=build_syllabus(source,segments,provider)
    repository.save_syllabus(source.lecture_id,nodes)
