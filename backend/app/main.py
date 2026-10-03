from fastapi import FastAPI
from .config import Config
from .storage import Repository

def create_app(config: Config | None = None):
    config=(config or Config()).prepare()
    app=FastAPI(title='Lecture Cards')
    app.state.config=config
    app.state.repository=Repository(config.data_dir/'study.sqlite')
    @app.get('/api/health')
    def health(): return {'status':'ok','provider_configured':bool(config.openai_api_key.get_secret_value())}
    return app

app=create_app()
