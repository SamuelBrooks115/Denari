"""
kpis.py — Financial Ratio and Performance Metrics

Purpose:
- Calculate derived financial indicators (KPIs):
    * Revenue growth %
    * Gross margin, operating margin, net margin
    * FCF margin
    * Leverage ratios (Debt / Equity, Debt / EBITDA)
- Used for:
    * Display in UI
    * Comps methodology
    * Sanity checking projection assumptions

Inputs:
- Normalized financial facts (XbrlFact)
- Optional projected values (post-three-statement)

Outputs:
- Dictionary of computed KPI time series.

This module does NOT:
- Query external APIs.
- Write to the database.
- Perform projection logic (handled in three_statement.py).
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.xbrl_fact import XbrlFact


def compute_kpis(company_id: int, db: Session) -> Dict[str, List[Any]]:
    """
    Compute financial KPIs based on historical normalized facts.

    Example Output:
    {
      "years": [...],
      "revenue": [...],
      "revenue_growth": [...],
      "operating_margin": [...],
      "net_margin": [...],
      "fcf_margin": [...]
    }

    TODO:
    - Extract Revenues, OperatingIncome, NetIncome from XbrlFact.
    - Compute year-over-year change and ratios.
    - Return KPI vectors sorted by period.
    """
    raise NotImplementedError("compute_kpis() requires basic XbrlFact extraction + ratio calculations.")
