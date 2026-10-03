from urllib.parse import urlparse,parse_qs
import re,urllib.request
import yt_dlp
from ..models import SourceDescriptor,ChapterSeed
from ..errors import ProcessingError
from .captions import parse_captions

def canonical_youtube(url):
    parsed=urlparse(url);host=(parsed.hostname or '').lower()
    id=None
    if parsed.scheme in ['https','http'] and host in ['youtube.com','www.youtube.com','m.youtube.com']:
        if parsed.path=='/watch':id=parse_qs(parsed.query).get('v',[None])[0]
        elif parsed.path.startswith(('/shorts/','/embed/')):id=parsed.path.split('/')[2]
    elif parsed.scheme in ['https','http'] and host=='youtu.be':id=parsed.path.strip('/')
    if not id or not re.fullmatch(r'[\w-]{11}',id):raise ProcessingError('invalid_youtube','Paste a link to one YouTube video.')
    return id,f'https://www.youtube.com/watch?v={id}'

class QuietLogger:
    def debug(self,message):pass
    def warning(self,message):pass
    def error(self,message):pass

def import_youtube(url,lecture_id):
    id,url=canonical_youtube(url)
    try:
        with yt_dlp.YoutubeDL({'skip_download':True,'quiet':True,'no_warnings':True,'logger':QuietLogger(),'socket_timeout':30,'retries':1}) as ydl:
            info=ydl.extract_info(url,download=False)
        if not info or info.get('is_live') or not info.get('duration'):raise ValueError('No finished video')
    except Exception:raise ProcessingError('youtube_unavailable','YouTube metadata could not be retrieved. Upload the video, or try the link again.') from None
    chapters=[]
    for raw in info.get('chapters') or []:
        try:chapters.append(ChapterSeed(title=raw['title'],start=raw['start_time'],end=raw['end_time']))
        except (ValueError,KeyError,TypeError):continue
    source=SourceDescriptor(lecture_id=lecture_id,title=info['title'],duration=info['duration'],source_kind='youtube',youtube_id=id,chapters=chapters)
    for collection in [info.get('subtitles') or {},info.get('automatic_captions') or {}]:
        langs=sorted((lang for lang in collection if lang=='en' or lang.startswith('en-')),key=lambda lang:(lang!='en',lang))
        for lang in langs:
            for item in collection[lang]:
                if item.get('ext') not in ['vtt','srt']:continue
                try:
                    with urllib.request.urlopen(item['url'],timeout=30) as response: text=response.read(20*1024**2).decode('utf-8-sig')
                    return source,parse_captions(text,item['ext'])
                except Exception:continue
    return source,None
