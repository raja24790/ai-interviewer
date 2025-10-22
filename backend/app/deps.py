from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Interviewer"
    environment: Literal["development", "staging", "production"] = "development"
    api_prefix: str = "/"
    allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    force_https: bool = False

    data_dir: Path = Path("/data")
    audio_dir: Path = Path("/data/audio")
    transcript_dir: Path = Path("/data/transcripts")
    report_dir: Path = Path("/data/reports")
    avatar_dir: Path = Path("/data/avatar")
    log_dir: Path = Path("/data/logs")

    # LLM provider configuration
    llm_provider: Literal["openai", "ollama", "mock"] = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    ollama_model: str = "llama3"
    ollama_host: str = "http://localhost:11434"

    # JWT / auth
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 120

    # Rate limiting
    rate_limit: str = "60/minute"

    # Attention / monitoring configuration
    attention_window_seconds: int = 60

    # PDF generation metadata
    company_name: str = "AI Interviewer"
    company_logo_path: Path | None = None

    # Storage retention
    retention_days: int = 30

    # Database configuration
    database_url: str = Field(default="sqlite:///data/ai_interviewer.db")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for directory in (
        settings.data_dir,
        settings.audio_dir,
        settings.transcript_dir,
        settings.report_dir,
        settings.avatar_dir,
        settings.log_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return settings


SettingsType = Settings
