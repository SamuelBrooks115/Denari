"""
comps.py — Comparable Companies Valuation Logic

Purpose:
- Identify a peer group for the target company.
- Pull the necessary financial metrics (Revenue, EBITDA, Net Income).
- Compute valuation multiples (EV/Revenue, EV/EBITDA, P/E).
- Return a distribution (median, quartiles) and implied valuation range.

Inputs:
- company_id (target)
- model_version (optional; if provided, use snapshot values)

Outputs (JSON-serializable):
{
  "peers": [
    {"ticker": "XYZ", "ev": 123e6, "revenue": 12e6, "ev_rev": 10.2, ...},
    ...
  ],
  "median_multiples": {
    "ev_rev": 9.8,
    "ev_ebitda": 14.3,
    "pe": 22.1
  },
  "implied_valuation_range": {
    "low": 110e6,
    "median": 135e6,
    "high": 160e6
  }
}

Core logic relies on:
- sector + industry stored in Company table
- normalized Revenue / EBITDA / NetIncome in xbrl_fact
"""

from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.company import Company
from app.models.xbrl_fact import XbrlFact


def run_comps(company_id: int, model_version: str | None, db: Session) -> Dict[str, Any]:
    """
    Main comps valuation entrypoint.

    High-Level Steps:
    1. Load target company → read sector + industry.
    2. Select peer set = other companies in same sector + industry.
    3. Pull latest Revenue, EBITDA, Net Income for all peers (from XbrlFact).
    4. Compute Enterprise Value (EV):
          EV = Market Cap + Total Debt - Cash
       (MVP may approximate EV = Market Cap if balance sheet data incomplete.)
    5. Compute valuation multiples for each peer.
    6. Compute medians / quartiles.
    7. Apply medians to target metrics → implied valuation.

    Returns structured valuation dictionary (see docstring).
    """
    raise NotImplementedError("run_comps() requires revenue/EBITDA extraction and EV approximation logic.")
