"""
config.py — Centralized Application Configuration Loader

Purpose:
- Define a single source of truth for application settings.
- Load and validate environment variables from `.env` or OS environment.
- MVP: Minimal configuration for EDGAR data fetching and model population.

MVP Requirements:
- EDGAR API settings for data fetching
- No database - models are populated directly from JSON
- No caching - direct fetch and process workflow

Core Workflow:
1. Pull from EDGAR → JSON
2. Use JSON to populate 3 models:
   - 3-Statement Model
   - DCF Model
   - Comps Model

This module does NOT:
- Execute any DB connections.
- Make external API calls.
- Modify runtime settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    MVP Settings container - minimal viable product configuration.
    
    Core workflow:
    1. Pull from EDGAR → JSON
    2. Use JSON to populate 3 models (3-statement, DCF, Comps)
    3. No database persistence - models are in-memory only
    """
    # EDGAR API - Required for data fetching
    EDGAR_USER_AGENT: str = Field(
        "Denari/1.0 (contact: ingestion@denari.ai)",
        description="SEC-compliant User-Agent string for EDGAR requests",
    )
    EDGAR_REQUEST_SLEEP_SECONDS: float = Field(
        0.45,
        description="Polite delay between EDGAR requests (seconds)",
    )
    EDGAR_REQUEST_TIMEOUT_SECONDS: int = Field(
        45,
        description="HTTP timeout for EDGAR requests (seconds)",
    )
    EDGAR_MAX_RETRIES: int = Field(
        4,
        description="Maximum retry attempts for EDGAR requests",
    )
    EDGAR_BACKOFF_BASE: float = Field(
        0.6,
        description="Exponential backoff base for retry delays",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Singleton pattern — settings imported anywhere will reference same object.
settings = Settings()
