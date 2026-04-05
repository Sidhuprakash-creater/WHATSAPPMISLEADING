"""
MisLEADING — Configuration via Pydantic Settings
Loads from .env file automatically
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "MisLEADING"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Auth
    JWT_SECRET: str = "change-this-to-a-very-long-random-string"
    JWT_EXPIRE_MINUTES: int = 60
    JWT_ALGORITHM: str = "HS256"
    
    # AI Keys
    ANTHROPIC_API_KEY: str = ""
    
    # URL Security
    GOOGLE_SAFE_BROWSING_KEY: str = ""
    VIRUSTOTAL_API_KEY: str = ""
    
    # Image Analysis
    SIGHTENGINE_API_USER: str = ""
    SIGHTENGINE_API_SECRET: str = ""
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./misleading.db"  # SQLite for dev
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
