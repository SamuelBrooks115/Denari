"""
database.py — Database Session & Connection Management

Purpose:
- Create and provide access to the Postgres database used by the backend.
- Manage SQLAlchemy Engine + Session lifecycle.
- Expose a FastAPI dependency `get_db()` that yields a session per-request.
- Ensure all models can share a common Base metadata if needed.

Key Characteristics (MVP):
- Synchronous SQLAlchemy engine (fast + simple).
- No Alembic migrations in MVP — schema expected to already exist (created in Supabase).
- Session is opened at the start of a request and closed after the response.
- If the backend is later deployed horizontally, switch to a connection pool–aware config.

This module does NOT:
- Define ORM models (see app/models/*).
- Create schema or run migrations (no Alembic in MVP).
- Perform any queries or business logic.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# -----------------------------------------------------------------------------
# SQLAlchemy Engine
# -----------------------------------------------------------------------------

# Create database engine using SUPABASE_DB_URL from environment
# Use psycopg (v3) driver - SQLAlchemy 2.0+ supports psycopg3
# Convert postgresql:// to postgresql+psycopg:// if not already specified
db_url = settings.SUPABASE_DB_URL
if db_url.startswith("postgresql://") and "+" not in db_url.split("://")[0]:
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    db_url,
    pool_pre_ping=True  # Ensures connections are valid before use
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# -----------------------------------------------------------------------------
# FastAPI Dependency
# -----------------------------------------------------------------------------

def get_db() -> Session:
    """
    FastAPI dependency: yields a database session for the duration of the request.

    Usage in API endpoint:
        def endpoint(db: Session = Depends(get_db)):
            db.query(...)

    Responsibility:
    - Open session → yield to request handler → close session on completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
