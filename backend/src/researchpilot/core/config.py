"""Core configuration and settings management for ResearchPilot."""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings validated via Pydantic v2."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_name: str = Field(default="ResearchPilot", validation_alias="APP_NAME")
    app_secret_key: str = Field(
        default="development-insecure-secret-key-32-chars-minimum",
        validation_alias="APP_SECRET_KEY",
    )
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Networking
    port: int = Field(default=8000, validation_alias="PORT")
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    frontend_origin: str = Field(default="http://localhost:5173", validation_alias="FRONTEND_ORIGIN")

    # Database & Storage
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/researchpilot",
        validation_alias="DATABASE_URL",
    )
    local_storage_path: Path = Field(
        default=Path("./storage/documents"),
        validation_alias="LOCAL_STORAGE_PATH",
    )

    # Authentication
    access_token_ttl_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_TTL_MINUTES")
    refresh_token_ttl_days: int = Field(default=7, validation_alias="REFRESH_TOKEN_TTL_DAYS")

    # OpenAI / AI Provider
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_CHAT_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", validation_alias="OPENAI_EMBEDDING_MODEL"
    )
    embedding_dimensions: int = Field(default=1536, validation_alias="EMBEDDING_DIMENSIONS")

    # Ingestion Constraints
    max_upload_mb: int = Field(default=25, validation_alias="MAX_UPLOAD_MB")
    max_pdf_pages: int = Field(default=500, validation_alias="MAX_PDF_PAGES")
    chunk_size_tokens: int = Field(default=800, validation_alias="CHUNK_SIZE_TOKENS")
    chunk_overlap_tokens: int = Field(default=120, validation_alias="CHUNK_OVERLAP_TOKENS")

    # Agent Constraints
    max_tool_calls_per_run: int = Field(default=25, validation_alias="MAX_TOOL_CALLS_PER_RUN")
    max_retrieved_chunks_per_run: int = Field(
        default=40, validation_alias="MAX_RETRIEVED_CHUNKS_PER_RUN"
    )
    max_run_duration_seconds: int = Field(default=300, validation_alias="MAX_RUN_DURATION_SECONDS")


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton instance of validated settings."""
    return Settings()
