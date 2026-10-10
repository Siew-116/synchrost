"""Configuration settings for StudyBiz AI."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from multiple possible locations
_env_paths = [
    Path(__file__).parent.parent / ".env",          # backend/.env
    Path(__file__).parent.parent.parent / ".env",    # root/.env
    Path.cwd() / ".env",                             # current working directory
]
for p in _env_paths:
    if p.exists():
        load_dotenv(p)
        break


class Settings(BaseSettings):
    APP_NAME: str = "Synchrost AI"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key"

    DATABASE_URL: str = "sqlite:///./studybiz.db"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CONNECTED: bool = False
    TELEGRAM_WEBHOOK_URL: str = ""

    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    LLM_MODEL: str = "gemini-3.8-flash"

    DEMO_MODE: bool = False
    # EXAM_MODE is the internal name; UI shows it as "Busy Mode"
    EXAM_MODE: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
