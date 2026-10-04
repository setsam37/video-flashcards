import re,uuid
from urllib.parse import parse_qs
from fastapi import APIRouter,Request,HTTPException
from fastapi.responses import RedirectResponse
from .importing.youtube import canonical_youtube

router=APIRouter()

def pending_handoff(request):
    value=request.session.get('handoff')
    if not isinstance(value,dict) or not re.fullmatch('[a-f0-9]{32}',str(value.get('id',''))):return None
    try:canonical_youtube(value.get('url',''))
    except (ValueError,TypeError):return None
    return value

@router.post('/start')
async def start(request:Request):
    config=request.app.state.config
    if config.app_mode!='hosted':raise HTTPException(404)
    if request.headers.get('origin')!=config.pages_origin:raise HTTPException(403,'Open this video from the Recall entry page.')
    if request.headers.get('content-type','').split(';')[0]!='application/x-www-form-urlencoded':raise HTTPException(415,'Use the video form on the entry page.')
    content=bytearray()
    async for block in request.stream():
        content.extend(block)
        if len(content)>4096:raise HTTPException(413,'The video link is too long.')
    try:
        values=parse_qs(content.decode('utf-8'),strict_parsing=True)
        if set(values)!={'url'} or len(values['url'])!=1:raise ValueError()
        _,url=canonical_youtube(values['url'][0])
    except (ValueError,UnicodeError):raise HTTPException(422,'Paste a supported YouTube video link.') from None
    request.session['handoff']={'id':uuid.uuid4().hex,'url':url}
    # SameSite=Lax app cookies are absent on the cross-site POST. Check the
    # existing session on the redirected GET, where the browser sends them.
    return RedirectResponse('/',status_code=303)

@router.post('/api/handoff')
def consume(request:Request):
    if request.app.state.config.app_mode!='hosted':raise HTTPException(404)
    pending=pending_handoff(request)
    if not pending:raise HTTPException(404,'No video is waiting. Paste a video on the entry page.')
    video_id,_=canonical_youtube(pending['url'])
    return request.state.repository.import_handoff(pending['id'],video_id)
