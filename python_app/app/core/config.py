from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path
import secrets

# Project root directory
ROOT_DIR = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Water Bottles API"
    
    # Database
    DATABASE_URL: str = "sqlite:///./water_bottles.db"
    
    # JWT Auth
    SECRET_KEY: str = "default_secret_key" # Should be overridden by env var
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Email (for password reset, etc.)
    EMAILS_ENABLED: bool = False
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USER: str | None = None
    SMTP_PASS: str | None = None
    EMAILS_FROM_EMAIL: str = "noreply@example.com"
    EMAILS_FROM_NAME: str = "Water Bottles App"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 