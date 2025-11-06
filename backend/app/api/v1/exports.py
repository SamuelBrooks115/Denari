"""
exports.py — Valuation Output Export Endpoints (API Layer)

Purpose:
- Expose endpoints to generate and return valuation outputs (primarily Excel workbooks).
- These exports represent the final deliverable of the valuation workflow.
- Endpoints should be callable once data ingestion + modeling are complete.
- All heavy lifting (three-statement, DCF, comps, workbook assembly) happens in services/modeling/.

Key Interactions:
- app.services.modeling.three_statement → generates projected financials.
- app.services.modeling.dcf → calculates valuation via discounted cash flow.
- app.services.modeling.comps → computes comparable multiples + implied valuation.
- app.services.modeling.excel_export → constructs the final downloadable Excel file.
- app.core.database → used for retrieving historical financials + assumptions.

This module should:
- Validate the target company + model snapshot exists.
- Call model computation layer functions.
- Return the file via StreamingResponse.

This module should NOT:
- Contain modeling math.
- Perform DB schema logic or ingestion steps.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional

from app.core.database import get_db
from app.services.modeling.excel_export import build_excel_workbook  # Excel generation entrypoint

router = APIRouter(
    prefix="/exports",
    tags=["exports"]
)


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/{company_id}/excel")
async def export_excel(company_id: int, model_version: Optional[str] = None, db=Depends(get_db)):
    """
    GET /exports/{company_id}/excel?model_version=x

    Returns:
    - A downloadable Excel workbook (.xlsx) containing:
        - Historical data used in modeling
        - Three-statement projections
        - DCF valuation outputs (PV of FCF + terminal value)
        - Comps valuation outputs
        - Input assumptions and configurable drivers

    High-Level Flow (delegated to services/modeling/excel_export):
    1. Validate that the company exists.
    2. Load historicals + assumptions from DB.
    3. Generate projected statements (Revenue → Net Income → Free Cash Flow).
    4. Compute DCF and Comps valuation ranges.
    5. Write tables + charts into an XLSX workbook.
    6. Return as StreamingResponse (as file download).

    Query Params:
    - `model_version` allows selecting a stored snapshot if implemented.
      If None → default to "latest" computed state.

    TODO:
    - Implement company + version lookup.
    - Implement error handling if insufficient data to model.
    - Connect to build_excel_workbook(company_id, version, db).
    """

    # TODO: lookup company or return 404
    # TODO: call build_excel_workbook and receive workbook bytes/stream

    workbook_bytes = b""  # placeholder
    # Example StreamingResponse usage once bytes are real:
    # return StreamingResponse(io.BytesIO(workbook_bytes), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    return {"status": "Excel export placeholder (implement build + return StreamingResponse)"}
