"""Bound multipart spooling on the free server, including chunked bodies."""
import re
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

class CaptionBodyLimit:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope['method']!='POST' or not re.fullmatch(r'/api/lectures/[^/]+/transcript',scope['path']):
            return await self.app(scope,receive,send)
        limit=21*1024**2
        headers=dict(scope['headers'])
        try:declared=int(headers.get(b'content-length',b'0'))
        except ValueError:declared=limit+1
        if declared>limit:
            return await JSONResponse(status_code=413,content={'detail':'The transcript request exceeds 21 MB. Use the local app for video uploads.'})(scope,receive,send)
        total=0
        async def bounded_receive():
            nonlocal total
            message=await receive()
            if message['type']=='http.request':
                total+=len(message.get('body',b''))
                if total>limit:raise HTTPException(413,'The transcript request exceeds 21 MB. Use the local app for video uploads.')
            return message
        await self.app(scope,bounded_receive,send)
