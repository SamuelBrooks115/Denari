"""
models.py — Valuation Model Execution Endpoints (API Layer)

Purpose:
- Expose endpoints that allow the client (UI or CLI) to:
    1. Select which valuation model version / assumptions to use.
    2. Trigger model computations (Three-Statement, DCF, Comps).
    3. Retrieve computed model outputs or summaries.

These endpoints do **not** perform calculations directly.
They call into the modeling service layer, which does the actual math.

Key Interactions:
- app.services.modeling.three_statement → builds forward projections.
- app.services.modeling.dcf → computes PV of future cash flows + terminal value.
- app.services.modeling.comps → computes peer multiples + implied valuation range.
- app.models.model_snapshot → stores specific saved sets of drivers + outputs (future feature).
- app.core.database → load historicals + assumption inputs.

Future Consideration:
- Snapshot model state so that analysts can “lock” assumptions and save versions.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any

from app.core.database import get_db
from app.services.modeling.three_statement import run_three_statement
from app.services.modeling.dcf import run_dcf
from app.services.modeling.comps import run_comps

router = APIRouter(
    prefix="/models",
    tags=["valuation-models"]
)

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/{company_id}/three-statement")
async def generate_three_statement(company_id: int,
                                   model_version: Optional[str] = None,
                                   db=Depends(get_db)):
    """
    GET /models/{company_id}/three-statement?model_version=x

    Returns:
    - A forward projected Income Statement / Balance Sheet / Cash Flow model.

    High-Level Workflow (delegated to services.modeling.three_statement):
    1. Ensure necessary historical coverage (≥ 3 periods).
    2. Load modeling assumptions (drivers: revenue growth, margins, capex, etc.).
    3. Produce forward projections for multiple years.
    4. Return structured tables (JSON serializable).

    TODO:
    - Lookup company exists or return 404.
    - Call run_three_statement(company_id, version, db).
    - Validate that assumptions exist; if not, return guidance to run `/companies/{id}/prepare`.
    """
    return {"status": "three-statement placeholder"}


@router.get("/{company_id}/dcf")
async def generate_dcf(company_id: int,
                       model_version: Optional[str] = None,
                       db=Depends(get_db)):
    """
    GET /models/{company_id}/dcf?model_version=x

    Returns:
    - DCF valuation summary:
        - Projected free cash flows
        - Discount factors
        - Present value
        - Terminal value (Gordon Growth or Exit Multiple)

    TODO:
    - Lookup company exists.
    - Call run_dcf(company_id, version, db).
    - Ensure three-statement projections exist (or compute inline).
    """
    return {"status": "dcf placeholder"}


@router.get("/{company_id}/comps")
async def generate_comps(company_id: int,
                         model_version: Optional[str] = None,
                         db=Depends(get_db)):
    """
    GET /models/{company_id}/comps?model_version=x

    Returns:
    - Peer-based valuation outputs:
        - EV/Revenue, EV/EBITDA, P/E multiples distribution
        - Median or interquartile implied valuations for the target company

    TODO:
    - Lookup company exists.
    - Call run_comps(company_id, version, db).
    - Ensure peer set can be identified. (May need a future peer-definition table.)
    """
    return {"status": "comps placeholder"}
