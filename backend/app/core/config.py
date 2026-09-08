"""Pydantic-based application settings with environment variable support.

All configurable values are read from environment variables or a `.env` file,
falling back to safe defaults for local development. Production deployments
must supply explicit values via environment.

Never hard-code secrets here — add them to `.env` (excluded from Git).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object loaded once at startup and reused application-wide.

    Use ``from app.core.config import settings`` to access these values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application Identity
    # ------------------------------------------------------------------ #
    app_name: str = "Job Market Intelligence & Skill Gap Analyzer"
    app_version: str = "0.1.0"
    app_description: str = (
        "End-to-end platform for IT job market analysis, skill gap identification, "
        "and personalized learning roadmap generation."
    )

    # ------------------------------------------------------------------ #
    # Runtime Environment
    # ------------------------------------------------------------------ #
    environment: str = "development"          # development | staging | production
    debug: bool = True
    log_level: str = "INFO"

    # ------------------------------------------------------------------ #
    # API Configuration
    # ------------------------------------------------------------------ #
    api_v1_prefix: str = "/api/v1"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    database_url: str = "sqlite:///./skill_gap_analyzer.db"

    # ------------------------------------------------------------------ #
    # File Uploads
    # ------------------------------------------------------------------ #
    max_upload_size_bytes: int = 5 * 1024 * 1024   # 5 MB
    allowed_upload_extensions: list[str] = [".pdf", ".txt", ".docx"]
    upload_directory: str = "uploads"


# Module-level singleton — import ``settings`` directly anywhere in the app.
settings = Settings()
