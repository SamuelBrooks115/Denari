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

from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env file relative to backend directory
# config.py is at: backend/app/core/config.py
# .env should be at: backend/.env
_CONFIG_DIR = Path(__file__).parent  # backend/app/core
_BACKEND_DIR = _CONFIG_DIR.parent.parent  # backend
_ENV_FILE = _BACKEND_DIR / ".env"

# Use absolute path for reliability
if _ENV_FILE.exists():
    _ENV_FILE_PATH = str(_ENV_FILE.resolve())
else:
    # Fallback: use relative path (pydantic will look in CWD)
    _ENV_FILE_PATH = ".env"


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

    # S&P 500 Ticker Source - Required for ingestion
    SP500_TICKER_SOURCE: str = Field(
        "",
        description="Path or URL to S&P 500 ticker list (CSV or JSON format)",
    )

    # Database - Required for data persistence
    SUPABASE_DB_URL: str = Field(
        "",
        description="PostgreSQL connection string (format: postgresql://user:password@host:port/database)",
    )

    # LLM API - For classifying EDGAR facts
    LLM_ENABLED: bool = Field(
        True,
        description="Enable LLM classification (set False to disable for testing)",
    )
    LLM_PROVIDER: str = Field(
        "openai",
        description="LLM provider: 'openai' or 'anthropic'",
    )
    OPENAI_API_KEY_PATH: str = Field(
        "",
        description="Path to file containing OpenAI API key (alternative to OPENAI_API_KEY)",
    )
    OPENAI_API_KEY: str = Field(
        "",
        description="OpenAI API key for LLM classification (optional, can be empty if LLM_ENABLED=False or if OPENAI_API_KEY_PATH is set)",
    )
    
    @field_validator('OPENAI_API_KEY', mode='before')
    @classmethod
    def strip_api_key(cls, v: Any) -> str:
        """Strip whitespace from API key."""
        if isinstance(v, str):
            return v.strip()
        return v or ""
    
    @model_validator(mode='after')
    def load_api_key_from_file(self) -> 'Settings':
        """Load API key from file if OPENAI_API_KEY_PATH is provided."""
        if self.OPENAI_API_KEY_PATH and not self.OPENAI_API_KEY:
            key_path = Path(self.OPENAI_API_KEY_PATH).expanduser()
            if key_path.exists():
                try:
                    with key_path.open('r', encoding='utf-8') as f:
                        self.OPENAI_API_KEY = f.read().strip()
                except Exception as e:
                    raise ValueError(f"Failed to read API key from {key_path}: {e}")
            else:
                raise ValueError(f"API key file not found: {key_path}")
        return self
    OPENAI_MODEL: str = Field(
        "gpt-4o-mini",
        description="OpenAI model to use for classification",
    )
    LLM_TIMEOUT_SECONDS: int = Field(
        30,
        description="Timeout for LLM API calls (seconds)",
    )
    LLM_MAX_RETRIES: int = Field(
        3,
        description="Maximum retry attempts for LLM API calls",
    )

    # Database Configuration (Supabase)
    SUPABASE_DB_URL: str = Field(
        "",
        description="PostgreSQL connection URL for Supabase database",
    )
    SUPABASE_URL: str = Field(
        "",
        description="Supabase project URL",
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        "",
        description="Supabase service role key for admin access",
    )

    # S&P 500 Ticker Source
    SP500_TICKER_SOURCE: str = Field(
        "",
        description="Path or URL to S&P 500 ticker list (CSV or JSON)",
    )

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Singleton pattern — settings imported anywhere will reference same object.
settings = Settings()
