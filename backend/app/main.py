import time,sqlite3
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from .auth import install_security
from .config import Config
from .storage import Repository
from .routes import router
from .handoff import router as handoff_router
from .errors import ProcessingError

def create_app(config: Config | None = None):
    config=(config or Config()).prepare()
    hosted=config.app_mode=='hosted'
    app=FastAPI(title='Lecture Cards',docs_url=None if hosted else '/docs',redoc_url=None if hosted else '/redoc',openapi_url=None if hosted else '/openapi.json')
    app.state.config=config
    app.state.repository=Repository(config.data_dir/'study.sqlite')
    install_security(app,config)
    @app.exception_handler(ProcessingError)
    async def processing_error(request,error):return JSONResponse(status_code=422,content={'detail':error.public_message,'code':error.code})
    app.include_router(router)
    app.include_router(handoff_router)
    @app.get('/api/health')
    def health(request:Request):
        if hosted:
            try:
                age=time.time()-float((config.data_dir/'worker-heartbeat').read_text())
                if not 0<=age<10:raise ValueError()
                with app.state.sessions.connection() as db:db.execute('SELECT 1 FROM sessions LIMIT 1')
                with app.state.repository.connection() as db:db.execute('SELECT 1 FROM sources LIMIT 1')
            except (OSError,ValueError,sqlite3.Error):return JSONResponse(status_code=503,content={'status':'unavailable'})
            if not request.state.user:return {'status':'ok'}
        return {'status':'ok','provider_configured':bool(config.openai_api_key.get_secret_value())}
    dist=__import__('pathlib').Path(__file__).resolve().parents[2]/'web/dist'
    if (dist/'assets').is_dir():app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
    @app.get('/')
    def index():
        if (dist/'index.html').is_file():return FileResponse(dist/'index.html')
        return {'message':'Build the web interface, or open the Vite development server.'}
    return app

app=create_app()
