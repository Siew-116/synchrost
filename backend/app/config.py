"""Configuration settings for StudyBiz AI."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class Settings(BaseSettings):
    APP_NAME: str = "StudyBiz AI"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key"

    DATABASE_URL: str = "sqlite:///./studybiz.db"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CONNECTED: bool = False
    TELEGRAM_WEBHOOK_URL: str = ""

    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    DEMO_MODE: bool = True
    EXAM_MODE: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
