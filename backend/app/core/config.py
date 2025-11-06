"""
config.py — Centralized Application Configuration Loader

Purpose:
- Define a single source of truth for application settings.
- Load and validate environment variables from `.env` or OS environment.
- Make configuration accessible across:
    * database.py
    * security.py
    * ingestion adapters (FMP / Yahoo / EDGAR API keys)
    * modeling parameter defaults (e.g., discount rate, projection years)
- Prevent "magic strings" scattered across code.

MVP Requirements:
- Must load:
    SUPABASE_DB_URL
    FMP_API_KEY (or Yahoo Finance free endpoint, no key required)
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

    # External APIs (MVP: FMP key; Yahoo fallback handled in adapter)
    FMP_API_KEY: str = Field(..., description="Financial Modeling Prep API key for market data") 

    # Security / Auth (optional for testing - provide defaults)
    JWT_SECRET_KEY: str = Field(
        default="dummy-secret-key-for-testing-only-change-in-production",
        description="Secret key used to sign JWT access tokens"
    )
    JWT_EXPIRE_MINUTES: int = Field(60, description="Access token lifetime in minutes")

    # Optional future config
    ENV: str = Field("development", description="'development' | 'production' environment flag")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


# Singleton pattern — settings imported anywhere will reference same object.
settings = Settings()
