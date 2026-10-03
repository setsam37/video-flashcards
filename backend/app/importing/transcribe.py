from pathlib import Path
import json
from ..models import TranscriptSegment
from ..errors import ProcessingError
from .media import extract_audio_chunk
from .captions import deduplicate

def merge_chunks(chunks):
    segments=[]
    for offset,local in chunks:
        segments.extend(s.model_copy(update={'start':s.start+offset,'end':s.end+offset}) for s in local)
    return deduplicate(segments)

def transcribe_media(source,provider,checkpoint: Path):
    checkpoint.mkdir(parents=True,exist_ok=True)
    chunks=[]
    for index,nominal in enumerate(range(0,int(source.duration)+1,600)):
        if nominal>=source.duration:break
        start=max(0,nominal-2);duration=min(source.duration-start,602)
        saved=checkpoint/f'{index}.json';audio=checkpoint/f'{index}.mp3'
        if saved.exists():local=[TranscriptSegment.model_validate(x) for x in json.loads(saved.read_text(encoding='utf-8'))]
        else:
            extract_audio_chunk(source,start,duration,audio)
            if audio.stat().st_size>=25_000_000:raise ProcessingError('audio_chunk_too_large','An audio chunk exceeds the provider limit. Try a compressed video or transcript upload.')
            local=provider.transcribe(audio)
            if not local:raise ProcessingError('empty_transcription','No speech was transcribed. Check the audio or upload captions.')
            saved.write_text(json.dumps([s.model_dump() for s in local]),encoding='utf-8')
        chunks.append((start,local))
    result=merge_chunks(chunks)
    if not result:raise ProcessingError('empty_transcription','No speech was found in the video.')
    return result
