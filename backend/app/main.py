"""
main.py — FastAPI Application Entrypoint

Purpose:
- Initialize application services (logging, config, DB session dependency).
- Register API routers.
- Define root-level health/status endpoints.
- Provide `app` object used by ASGI server (uvicorn / hypercorn).

This file should stay clean — no business logic here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import configure_logging
from app.api.v1 import companies, filings, financials, models, branding, screener, treasury

# -----------------------------------------------------------------------------
# App Initialization
# -----------------------------------------------------------------------------

configure_logging()  # Set logging defaults at startup

app = FastAPI(
    title="Denari Valuation Backend",
    description="Financial modeling + ingestion backend for Denari",
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# CORS (Optional — useful for local frontend development)
# -----------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Router Registration
# -----------------------------------------------------------------------------

# Mount all v1 API routers under /api/v1 prefix
app.include_router(companies.router, prefix="/api/v1")
app.include_router(filings.router, prefix="/api/v1")
app.include_router(financials.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
app.include_router(branding.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(screener.screener_router, prefix="/api/v1")
app.include_router(treasury.router, prefix="/api/v1")

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "Denari backend running"}
