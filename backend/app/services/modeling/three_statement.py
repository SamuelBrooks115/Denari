"""
three_statement.py — Forward Financial Projections (3-Statement Model)

Purpose:
- Generate forecasted:
    * Income Statement (Revenue → EBIT → Net Income)
    * Balance Sheet (minimal for MVP)
    * Cash Flow Statement (Free Cash Flow focus)

Inputs:
- company_id
- model_version (optional; if provided, pull assumptions from ModelSnapshot)
- DB session (for historical actuals + working valuation_model assumptions)

Outputs:
- Structured JSON tables usable by:
    * DCF valuation
    * Excel export layer
    * UI model visualization

This module does NOT:
- Calculate valuation directly (DCF does that).
- Query market data.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.xbrl_fact import XbrlFact
from app.models.valuation_model import ValuationModel
from app.models.model_snapshot import ModelSnapshot


def run_three_statement(company_id: int,
                        model_version: str | None,
                        db: Session) -> Dict[str, Any]:
    """
    Main entrypoint for generating forward projections.

    High-Level Steps:
    1. Load historical periods (Revenue, COGS, Opex, Taxes, CapEx, etc.) from XbrlFact.
    2. Load assumptions:
        - If model_version provided → load from ModelSnapshot
        - Else → load from ValuationModel (the editable working model).
    3. Determine projection horizon (MVP: 5 years).
    4. Compute forward revenue growth → revenue line.
    5. Apply margin assumptions → EBIT → Net Income.
    6. Convert Net Income → Free Cash Flow:
            FCF = Net Income + D&A - CapEx - ΔWorkingCapital
       (MVP may use simplified FCF approximation.)
    7. Return projections as dict of lists.

    Returned Structure (example):
    {
      "years": [2023, 2024, 2025, 2026, 2027],
      "revenue": [...],
      "ebit": [...],
      "net_income": [...],
      "free_cash_flow": [...]
    }

    TODO:
    - Identify which GAAP tags to use for historical extraction.
    - Implement simplified FCF formula initially.
    - Add balance sheet + working capital detail later.
    """
    raise NotImplementedError("run_three_statement() requires revenue/margin historical extraction + growth application.")
