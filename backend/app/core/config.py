"""
Application configuration via environment variables.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = ""
    GEMINI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    SNOWFLAKE_ACCOUNT: str = ""
    SNOWFLAKE_USER: str = ""
    SNOWFLAKE_PASSWORD: str = ""
    SNOWFLAKE_DATABASE: str = "CODEANCESTRY"
    SNOWFLAKE_SCHEMA: str = "PUBLIC"
    SNOWFLAKE_WAREHOUSE: str = "COMPUTE_WH"
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:8080"
    CORS_ORIGINS: str = ""
    REDIS_URL: str = ""
    ENCRYPTION_KEY: str = ""

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS:
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return [self.FRONTEND_URL]

    @property
    def effective_redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def github_redirect_uri(self) -> str:
        if self.GITHUB_REDIRECT_URI:
            return self.GITHUB_REDIRECT_URI
        if self.is_production:
            raise ValueError("GITHUB_REDIRECT_URI must be set in production")
        return "http://localhost:8000/auth/github/callback"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
logger.info("📁 Using environment variables from .env file")

if settings.is_production:
    _missing = []
    if not settings.JWT_SECRET_KEY:
        _missing.append("JWT_SECRET_KEY")
    if not settings.ENCRYPTION_KEY:
        _missing.append("ENCRYPTION_KEY")
    if not settings.GITHUB_CLIENT_ID:
        _missing.append("GITHUB_CLIENT_ID")
    if not settings.GITHUB_CLIENT_SECRET:
        _missing.append("GITHUB_CLIENT_SECRET")
    if _missing:
        raise ValueError(f"Production deployment missing required secrets: {', '.join(_missing)}")
