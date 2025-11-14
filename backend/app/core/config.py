"""
config.py — Centralized Application Configuration Loader

Purpose:
- Define a single source of truth for application settings.
- Load and validate environment variables from `.env` or OS environment.
- Make configuration accessible across:
    * database.py
    * security.py
    * ingestion adapters (Yahoo / EDGAR API keys)
    * modeling parameter defaults (e.g., discount rate, projection years)
- Prevent "magic strings" scattered across code.

MVP Requirements:
- Must load:
    SUPABASE_DB_URL
    Yahoo Finance free endpoint (no key required)
    JWT_SECRET_KEY
    JWT_EXPIRE_MINUTES
- Should not fail silently — fail fast if critical config missing.

This module does NOT:
- Execute any DB connections.
- Make external API calls.
- Modify runtime settings.
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings container loaded once at app startup.

    Notes:
    - `env_file` ensures `.env` is used during local dev.
    - Rename variables to match actual deployment environment names.
    """
    # Database
    SUPABASE_DB_URL: str = Field(..., description="Postgres connection string provided by Supabase")
    SUPABASE_URL: str = Field(..., description="Supabase project URL for API client")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., description="Supabase service role key for backend ingestion")

    # External APIs (MVP: Yahoo Finance - no key required) 

    # Security / Auth
    JWT_SECRET_KEY: str = Field(
        "dev-secret",
        description="Secret key used to sign JWT access tokens",
    )
    JWT_EXPIRE_MINUTES: int = Field(60, description="Access token lifetime in minutes")

    # Ingestion / EDGAR
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
    SP500_TICKER_SOURCE: str = Field(
        "",
        description="Optional path or URL to cached S&P 500 constituents CSV/JSON",
    )

    # Optional future config
    ENV: str = Field("development", description="'development' | 'production' environment flag")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Singleton pattern — settings imported anywhere will reference same object.
settings = Settings()
