"""
filings.py — Filing Retrieval & Normalization Status Endpoints (API Layer)

Purpose:
- Provide read-only visibility into a company's SEC filing data (10-K, 10-Q, etc.).
- Allow inspection of what filings exist in the database vs. what may be missing.
- Trigger (optionally) a re-fetch or refresh of filings via EDGAR/XBRL adapters.
- Display normalization status (raw filings pulled vs. XBRL facts extracted).

Key Interactions:
- app.services.ingestion.edgar_adapter → fetches raw filings from SEC/third-party APIs.
- app.services.ingestion.xbrl.normalizer → converts raw XBRL → standardized GAAP fact/value rows.
- app.services.ingestion.ingest_orchestrator → coordinates "if missing → fetch → normalize → upsert".
- app.models.filing → ORM model representing metadata about a filing.
- app.models.xbrl_fact → ORM model representing individual financial facts extracted per tag & period.

This file should remain *thin*. It does:
- Lookup records.
- Trigger ingestion operations.
- Return structured metadata.

It does not:
- Contain parsing logic.
- Define GAAP tag mapping.
- Perform any modeling math.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.core.database import get_db
from app.models.filing import Filing
from app.services.ingestion.ingest_orchestrator import refresh_filings_for_company

router = APIRouter(
    prefix="/filings",
    tags=["filings"]
)

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

class FilingOut:
    """
    Response schema for listing filings.

    Fields (Eventually):
    - id: Internal DB ID
    - company_id: Refers to company
    - form_type: e.g., '10-K', '10-Q'
    - filing_date: date filed with SEC
    - period_end: financial period being reported
    - source_url: URL to original filing (if stored)
    - normalized: Boolean indicating whether XBRL normalization has occurred

    TODO:
    - Convert to Pydantic BaseModel and enable orm_mode once ORM models are finalized.
    """
    pass  # Placeholder for later Pydantic model definition


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/{company_id}", response_model=List[FilingOut])
async def list_filings(company_id: int, db=Depends(get_db)):
    """
    GET /filings/{company_id}

    Returns:
    - A list of filings already stored for this company.

    TODO:
    - Implement DB query: db.query(Filing).filter(Filing.company_id == company_id).all()
    - Convert to FilingOut once schema is formal.
    """
    return []  # placeholder


@router.post("/{company_id}/refresh")
async def refresh_company_filings(company_id: int, db=Depends(get_db)):
    """
    POST /filings/{company_id}/refresh

    Purpose:
    - Force a re-check of filings for the company.
    - If filings are missing → fetch via EDGAR.
    - If filings exist but are not normalized → run normalization.

    Intended Use:
    - Useful in situations where filings were partially ingested or schema updated.

    High-Level Steps (handled in ingest_orchestrator):
    1. Determine latest expected filing periods (annual + quarterly).
    2. Check database to identify missing filings.
    3. Pull missing filings (edgar_adapter).
    4. Normalize all raw XBRL to consistent GAAP fact/value rows (% of revenue, actuals, etc.).
    5. Upsert normalized results into FINANCIAL_STATEMENT + FINANCIAL_FACT tables.

    TODO:
    - Look up company exists, else 404.
    - Call: refresh_filings_for_company(company_id, db)
    - Return structured summary (counts added, periods updated).
    """
    result = {"status": "placeholder"}
    return result
