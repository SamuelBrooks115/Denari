"""
financials.py — Historical Financial Data Access Endpoints (API Layer)

Purpose:
- Expose endpoints for retrieving normalized historical financial statements and facts.
- Primarily used by the frontend when displaying:
    * Income Statement history
    * Balance Sheet history
    * Cash Flow history
    * Derived KPIs (margins, growth rates, leverage ratios, etc.)
- Also supports internal modeling logic by providing clean, ready-to-use GAAP-line data.

Key Interactions:
- app.models.xbrl_fact → stores normalized GAAP tag/value per period.
- app.models.filing → associates reported values with specific filings.
- app.services.kpis → may compute derived metrics (optional during MVP).
- app.core.database → SQL/ORM access.
- app.services.ingestion.ingest_orchestrator ensures the data exists before modeling.

This module does NOT:
- Trigger ingestion (handled by /companies/{id}/prepare).
- Perform modeling (handled in app/services/modeling/*).
- Perform normalization (handled in app/services/ingestion/xbrl/normalizer.py).
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.core.database import get_db
from app.models.xbrl_fact import XbrlFact  # ORM for normalized facts
from app.services.kpis import compute_kpis  # Optional derived metrics layer (future use)

router = APIRouter(
    prefix="/financials",
    tags=["financials"]
)

# -----------------------------------------------------------------------------
# Schemas (Simplified for MVP)
# -----------------------------------------------------------------------------

class FinancialFactOut:
    """
    Response schema representing a single normalized financial fact.

    Fields (final expected):
    - period_end: Date the fact applies to (e.g., 2022-12-31)
    - statement_type: 'IS', 'BS', or 'CF'
    - tag: GAAP tag (e.g., "Revenues", "NetIncomeLoss", "Assets")
    - value: Numeric reported value (as-reported, no scaling)
    - unit: e.g., USD, shares (optional)
    - breakdown: Optional dimension value if present (e.g., segment, product)

    TODO:
    - Convert to Pydantic BaseModel + enable orm_mode once schema final.
    """
    pass  # Treated as placeholder for now


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/{company_id}", response_model=List[FinancialFactOut])
async def get_financials(company_id: int,
                         statement: Optional[str] = None,
                         db=Depends(get_db)):
    """
    GET /financials/{company_id}?statement=IS|BS|CF

    Returns:
    - Normalized GAAP facts for the requested company.
    - Optionally filtered to a specific statement type.

    Parameters:
    - company_id: Internal ID for the company.
    - statement (optional): "IS", "BS", or "CF".

    Usage Examples:
    - GET /financials/12 → all normalized facts for company 12
    - GET /financials/12?statement=IS → only Income Statement facts

    TODO:
    - Validate company exists (else 404).
    - Query XbrlFact rows by company_id.
    - Filter by statement type if provided.
    - Convert ORM results to FinancialFactOut format.
    - Sort results in descending period order (latest → oldest).
    """
    # TODO: lookup + return real data
    return []


@router.get("/{company_id}/periods")
async def get_available_periods(company_id: int, db=Depends(get_db)):
    """
    GET /financials/{company_id}/periods

    Returns:
    - A list of unique financial reporting periods available for the company.
    - Useful to confirm minimum coverage (≥ 3 annual statements required for modeling).

    TODO:
    - Query distinct XbrlFact.period_end values.
    - Sort chronologically.
    """
    return {"periods": []}  # placeholder
