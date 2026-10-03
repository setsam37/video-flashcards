import html,re
from ..models import TranscriptSegment
from ..errors import ProcessingError

def timestamp(value):
    pieces=value.replace(',','.').split(':')
    return sum(float(p)*60**i for i,p in enumerate(reversed(pieces)))

def deduplicate(segments):
    result=[]
    for segment in sorted(segments,key=lambda s:(s.start,s.end)):
        text=segment.text.strip()
        if not text:continue
        if result and segment.start<result[-1].end:
            previous=result[-1].text.split();words=text.split()
            for count in range(min(len(previous),len(words)),0,-1):
                if [w.casefold() for w in previous[-count:]]==[w.casefold() for w in words[:count]]:
                    text=' '.join(words[count:]);break
            if not text:
                result[-1]=result[-1].model_copy(update={'end':max(result[-1].end,segment.end)});continue
        result.append(segment.model_copy(update={'id':f'seg_{len(result):06d}','text':text}))
    return result

def parse_captions(text,format):
    segments=[]
    for block in re.split(r'\n\s*\n',text.replace('\r','')):
        lines=block.strip().splitlines()
        match=next(((i,re.match(r'([\d:,.]+)\s+-->\s+([\d:,.]+)',line)) for i,line in enumerate(lines) if '-->' in line),None)
        if not match or not match[1]:continue
        index,timing=match
        try:
            start=timestamp(timing.group(1));end=timestamp(timing.group(2))
            body=html.unescape(re.sub(r'<[^>]+>','', ' '.join(lines[index+1:]))).strip()
            if body and end>start>=0:segments.append(TranscriptSegment(id='cue',start=start,end=end,text=body))
        except ValueError:continue
    result=deduplicate(segments)
    if not result:raise ProcessingError('invalid_transcript','No usable timestamped captions were found. Upload an SRT or VTT file.')
    return result
