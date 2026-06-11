# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./babycry.db"
    redis_url: str = ""
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 30  # 30 days
    anthropic_api_key: str = ""
    enable_ai_advice: bool = False
    audio_upload_dir: str = "./uploads/audio"
    noise_audio_dir: str = "./data/noise"
    min_record_seconds: int = 6
    max_record_seconds: int = 30
    model_path: str = "./models/cry_classifier.onnx"
    persist_cry_records: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
