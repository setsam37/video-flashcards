from pathlib import Path
from typing import Literal
from urllib.parse import urlparse,parse_qs
from pydantic import SecretStr,model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ROOT = Path(__file__).resolve().parents[2]

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=APP_ROOT / '.env',extra='ignore')
    data_dir: Path = APP_ROOT / 'data'
    openai_api_key: SecretStr = SecretStr('')
    openai_text_model: str = 'gpt-4.1-mini-2025-04-14'
    ffmpeg_path: str = 'ffmpeg'
    ffprobe_path: str = 'ffprobe'
    upload_limit_bytes: int = 4*1024**3
    provider_timeout: float = 120
    app_mode: Literal['local','hosted'] = 'local'
    public_app_url: str = ''
    render_external_url: str = ''
    pages_origin: str = 'https://setsam37.github.io'
    google_client_id: str = ''
    google_client_secret: SecretStr = SecretStr('')
    session_secret: SecretStr = SecretStr('')
    allowed_emails: list[str] = []
    public_signup: bool = False
    database_url: SecretStr = SecretStr('')
    workspace_id: str = 'root'
    video_uploads_enabled: bool = True
    ephemeral_hosting: bool = False

    @model_validator(mode='after')
    def validate_hosting(self):
        self.allowed_emails=[email.strip().lower() for email in self.allowed_emails if email.strip()]
        if self.app_mode=='hosted':
            database_url=self.database_url.get_secret_value()
            if self.ephemeral_hosting and (not database_url or self.video_uploads_enabled):
                raise ValueError('Ephemeral hosting requires DATABASE_URL and disabled video uploads.')
            if database_url:
                parsed_db=urlparse(database_url)
                if parsed_db.scheme not in ['postgres','postgresql'] or not parsed_db.hostname or parse_qs(parsed_db.query).get('sslmode',[''])[0] not in ['require','verify-ca','verify-full']:
                    raise ValueError('Hosted database connections require encrypted TLS (sslmode=require or verify-full).')
            self.public_app_url=(self.public_app_url or self.render_external_url).rstrip('/')
            for value in [self.public_app_url,self.pages_origin]:
                parsed=urlparse(value)
                if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in [None,443] or parsed.path not in ['', '/'] or parsed.query or parsed.fragment:
                    raise ValueError('Hosted URLs must be HTTPS origins.')
            if not self.google_client_id or not self.google_client_secret.get_secret_value() or len(self.session_secret.get_secret_value())<32 or not self.openai_api_key.get_secret_value():
                raise ValueError('Hosted mode requires Google credentials, a session secret of at least 32 characters, and an OpenAI key.')
            if not self.public_signup and not self.allowed_emails:raise ValueError('Hosted mode requires invited email addresses.')
        return self

    def prepare(self):
        self.data_dir.mkdir(parents=True,exist_ok=True)
        (self.data_dir/'media').mkdir(exist_ok=True)
        (self.data_dir/'jobs').mkdir(exist_ok=True)
        (self.data_dir/'tmp').mkdir(exist_ok=True)
        return self
