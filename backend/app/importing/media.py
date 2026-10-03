from pathlib import Path
import subprocess,json,shutil
from ..config import Config
from ..models import SourceDescriptor,ChapterSeed
from ..errors import ProcessingError

def executable(name,configured):
    value=configured or name
    found=shutil.which(value) or (value if Path(value).is_file() else None)
    if not found:raise ProcessingError('tool_missing',f'{name} is not configured. Set its path in the local .env file and retry.')
    return found

def probe_media(path: Path,lecture_id: str,config: Config | None=None):
    config=config or Config()
    try:
        result=subprocess.run([executable('ffprobe',config.ffprobe_path),'-v','error','-show_format','-show_streams','-show_chapters','-of','json',str(path)],capture_output=True,text=True,check=True,timeout=60)
        data=json.loads(result.stdout)
        if not any(s.get('codec_type')=='audio' for s in data.get('streams',[])):raise ProcessingError('audio_missing','This video has no readable audio track.')
        duration=float(data['format']['duration'])
        if duration<=0:raise ValueError('Empty video')
        if not any(x in data['format'].get('format_name','') for x in ['mp4','mov','webm','matroska']):raise ValueError('Unsupported format')
        chapters=[]
        for raw in data.get('chapters',[]):
            try:chapters.append(ChapterSeed(title=raw.get('tags',{}).get('title','Chapter'),start=float(raw['start_time']),end=float(raw['end_time'])))
            except (ValueError,KeyError):continue
        return SourceDescriptor(lecture_id=lecture_id,title=path.stem,duration=duration,source_kind='upload',media_path=str(path.resolve()),chapters=chapters)
    except ProcessingError:raise
    except (OSError,subprocess.SubprocessError,ValueError,KeyError):
        raise ProcessingError('unreadable_video','The video could not be read. Use a valid MP4 or WebM with audio.') from None

def extract_audio_chunk(source,start,duration,path):
    config=Config()
    try:
        subprocess.run([executable('ffmpeg',config.ffmpeg_path),'-v','error','-y','-ss',str(start),'-i',source.media_path,'-t',str(duration),'-vn','-ac','1','-ar','16000','-b:a','64k',str(path)],capture_output=True,check=True,timeout=300)
    except ProcessingError:raise
    except (OSError,subprocess.SubprocessError):raise ProcessingError('audio_extraction_failed','Audio extraction failed. Check the video and retry.') from None
