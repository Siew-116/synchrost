"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./studybiz.db"

    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI Model
    AI_MODEL_API_BASE: str = ""
    AI_MODEL_API_KEY: str = ""
    AI_MODEL_NAME: str = "gpt-4o-mini"

    # Timezone
    TIMEZONE: str = "Asia/Kuala_Lumpur"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def use_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
