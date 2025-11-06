"""
excel_export.py — Excel Workbook Export Builder

Purpose:
- Convert model outputs (projections, DCF, comps) into a structured .xlsx file.
- This is the final client-facing artifact used by analysts and investors.
- Template-driven approach to ensure readability and familiarity.

Inputs:
- company_id
- model_version (optional)
- DB session (for historicals + assumptions)
- Must call:
    run_three_statement()
    run_dcf()
    run_comps()
  to gather values prior to export.

Outputs:
- In-memory .xlsx file (returned as bytes or BytesIO stream).

This module does NOT:
- Perform valuation logic.
- Fetch filings or prices.
"""

from io import BytesIO
from sqlalchemy.orm import Session
from typing import Optional

from app.services.modeling.three_statement import run_three_statement
from app.services.modeling.dcf import run_dcf
from app.services.modeling.comps import run_comps

# Recommended Excel writer: openpyxl or xlsxwriter
# We choose xlsxwriter for formatting flexibility
import xlsxwriter


def build_excel_workbook(company_id: int,
                         model_version: Optional[str],
                         db: Session) -> bytes:
    """
    Generate and return an Excel workbook for download.

    Workflow:
        1. Run three-statement model → get projections.
        2. Run DCF → get valuation outputs.
        3. Run comps → get peer comparison outputs.
        4. Create workbook (memory-only).
        5. Write:
            - Historical tables
            - Projection tables
            - DCF valuation summary
            - Comps valuation summary
            - Inputs / assumptions for transparency
        6. Return workbook as bytes.

    TODO:
    - Design tab structure (MVP: 'Inputs', 'Projections', 'DCF', 'Comps')
    - Implement clean table formatting (headers bold, numbers comma-formatted)
    - Add company & model_version labeling to header

    Returns:
        bytes: Excel file content suitable for StreamingResponse
    """
    # Create an in-memory workbook buffer
    output = BytesIO()

    # Workbook object
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})

    # TODO: Create sheets and write data
    # sheet = workbook.add_worksheet("Inputs")
    # sheet.write(0, 0, "TODO: Populate with assumptions")

    workbook.close()
    output.seek(0)
    return output.read()
