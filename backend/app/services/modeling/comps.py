"""
comps.py — Comparable Companies Valuation Logic

Purpose:
- Compute valuation multiples for a company based on its financial metrics.
- For MVP: Simplified version without peer database (would require fetching multiple companies).

Inputs (MVP - no database):
- target_financials: Dict with latest period financial metrics
- market_data: Dict with market cap, enterprise value, etc. (if available)

Outputs (JSON-serializable):
{
  "target_metrics": {
    "revenue": float,
    "ebitda": float,
    "net_income": float,
  },
  "multiples": {
    "ev_rev": float | None,
    "ev_ebitda": float | None,
    "pe": float | None,
  },
  "note": str (explaining MVP limitations)
}

Note: Full comps analysis requires peer company data which is not available in MVP.
This simplified version computes multiples for the target company only.
"""

from typing import Dict, Any, Optional


def run_comps(
    target_financials: Dict[str, float],
    market_data: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Simplified comps valuation entrypoint (MVP - no peer database).

    Args:
        target_financials: Dict with keys:
            - revenue: float
            - ebitda: float (optional)
            - operating_income: float (optional, used if EBITDA not available)
            - net_income: float
        market_data: Optional Dict with:
            - market_cap: float
            - enterprise_value: float
            - shares_outstanding: float

    Returns:
        Dictionary with computed multiples for target company
    """
    revenue = target_financials.get("revenue", 0.0)
    ebitda = target_financials.get("ebitda")
    operating_income = target_financials.get("operating_income")
    net_income = target_financials.get("net_income", 0.0)

    # Use EBITDA if available, otherwise approximate with operating income
    if ebitda is None and operating_income is not None:
        # Rough approximation: EBITDA ≈ Operating Income + D&A
        # For MVP, use operating income as proxy
        ebitda = operating_income

    multiples: Dict[str, Optional[float]] = {}
    
    if market_data:
        ev = market_data.get("enterprise_value")
        market_cap = market_data.get("market_cap")
        
        # EV/Revenue
        if ev is not None and revenue > 0:
            multiples["ev_rev"] = ev / revenue
        
        # EV/EBITDA
        if ev is not None and ebitda is not None and ebitda > 0:
            multiples["ev_ebitda"] = ev / ebitda
        
        # P/E (Price to Earnings)
        if market_cap is not None and net_income > 0:
            multiples["pe"] = market_cap / net_income
    else:
        multiples = {
            "ev_rev": None,
            "ev_ebitda": None,
            "pe": None,
        }

    return {
        "target_metrics": {
            "revenue": revenue,
            "ebitda": ebitda,
            "net_income": net_income,
        },
        "multiples": multiples,
        "note": "MVP: Comps analysis limited to target company only. Full peer analysis requires database of comparable companies.",
    }
