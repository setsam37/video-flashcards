from pathlib import Path
from pydantic import SecretStr
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

    def prepare(self):
        self.data_dir.mkdir(parents=True,exist_ok=True)
        (self.data_dir/'media').mkdir(exist_ok=True)
        (self.data_dir/'jobs').mkdir(exist_ok=True)
        return self
