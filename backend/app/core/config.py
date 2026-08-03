"""
Application configuration module.

Centralizes all environment-driven settings using Pydantic BaseSettings.
Values are loaded from environment variables and optional .env files,
ensuring type-safe configuration across all application layers.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to backend/ so settings load regardless of working directory
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All sensitive values (API keys, database URLs) must be provided via
    environment variables or a local .env file — never hardcoded.
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    app_name: str = Field(default="ProcureAI Backend", description="Service display name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Database
    database_url: str = Field(
        default="postgresql://procureai:procureai123@127.0.0.1:5433/procureai",
        description="PostgreSQL connection string for SQLAlchemy",
    )

    # Cache
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string for caching and task queues",
    )

    # Vector database (for future RAG capabilities)
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant vector database URL",
    )

    # AI provider (for future agent integrations)
    mistral_api_key: str = Field(
        default="",
        description="Mistral API key for LLM-powered agents",
    )

    # Security
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT token signing",
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration time in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="JWT refresh token expiration time in days",
    )

    # File uploads
    upload_dir: str = Field(
        default="uploads",
        description="Base directory (relative to backend/) for storing uploaded files",
    )
    max_upload_size_mb: int = Field(
        default=10,
        description="Maximum allowed file upload size in megabytes",
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins for frontend applications",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using lru_cache ensures settings are loaded once and reused
    throughout the application lifecycle.
    """
    return Settings()


# Module-level singleton for convenient imports
settings = get_settings()
