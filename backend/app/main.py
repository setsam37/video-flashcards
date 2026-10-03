from fastapi import FastAPI
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from urllib.parse import urlparse
from .config import Config
from .storage import Repository
from .routes import router
from .errors import ProcessingError

def create_app(config: Config | None = None):
    config=(config or Config()).prepare()
    app=FastAPI(title='Lecture Cards')
    app.state.config=config
    app.state.repository=Repository(config.data_dir/'study.sqlite')
    @app.middleware('http')
    async def guard_origin(request,call_next):
        origin=request.headers.get('origin')
        if request.method not in ['GET','HEAD','OPTIONS'] and origin:
            try:
                parsed=urlparse(origin)
                allowed=parsed.scheme in ['http','https'] and parsed.hostname in ['127.0.0.1','localhost','testserver'] and parsed.port in [None,8000,5173,request.url.port]
            except ValueError:allowed=False
            if not allowed:
                return JSONResponse(status_code=403,content={'detail':'This local app does not accept requests from that origin.'})
        return await call_next(request)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver'])
    @app.exception_handler(ProcessingError)
    async def processing_error(request,error):return JSONResponse(status_code=422,content={'detail':error.public_message,'code':error.code})
    app.include_router(router)
    @app.get('/api/health')
    def health(): return {'status':'ok','provider_configured':bool(config.openai_api_key.get_secret_value())}
    dist=__import__('pathlib').Path(__file__).resolve().parents[2]/'web/dist'
    if (dist/'assets').is_dir():app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
    @app.get('/')
    def index():
        if (dist/'index.html').is_file():return FileResponse(dist/'index.html')
        return {'message':'Build the web interface, or open the Vite development server.'}
    return app

app=create_app()
