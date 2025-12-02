"""
comps.py — Comparable Companies Valuation Logic

Purpose:
- Compute valuation multiples for a company based on its financial metrics.
- Calculate implied values based on comparable company multiples.

This module is unit-testable without Excel and uses structured dataclass outputs.
"""

from typing import Dict, Any, Optional, List

from app.services.modeling.types import (
    CompanyModelInput,
    RelativeValuationOutput,
    ComparableCompany,
)


def run_comps(
    model_input: CompanyModelInput,
    comparables: Optional[List[Dict[str, Any]]] = None,
) -> RelativeValuationOutput:
    """
    Relative valuation entrypoint using comparable companies.

    Args:
        model_input: CompanyModelInput with historical financial data
        comparables: Optional list of comparable company dictionaries, each with:
            - name: str
            - ev_ebitda: Optional[float]
            - pe: Optional[float]
            - ev_sales: Optional[float]

    Returns:
        RelativeValuationOutput with subject metrics, comparables, and implied values
    """
    # Extract latest year metrics from historicals
    historicals = model_input.historicals.by_role
    
    # Find the latest year with data
    all_years = set()
    for role_values in historicals.values():
        all_years.update(role_values.keys())
    
    if not all_years:
        raise ValueError("No historical financial data provided")
    
    latest_year = max(all_years)
    
    # Extract subject company metrics
    revenue = historicals.get("IS_REVENUE", {}).get(latest_year, 0.0)
    net_income = historicals.get("IS_NET_INCOME", {}).get(latest_year, 0.0)
    
    # Calculate EBITDA if possible (EBIT + D&A)
    ebit = historicals.get("IS_EBIT", {}).get(latest_year)
    da = historicals.get("CF_DEPRECIATION", {}).get(latest_year, 0.0)
    if ebit is not None:
        ebitda = ebit + da
    else:
        # Fallback: use operating income if available
        operating_income = historicals.get("IS_OPERATING_INCOME", {}).get(latest_year)
        if operating_income is not None:
            ebitda = operating_income + da
        else:
            ebitda = None
    
    subject_metrics = {
        "revenue": revenue,
        "ebitda": ebitda if ebitda is not None else 0.0,
        "net_income": net_income,
    }
    
    # Convert comparables list to ComparableCompany objects
    comp_list: List[ComparableCompany] = []
    if comparables:
        for comp_dict in comparables:
            comp_list.append(ComparableCompany(
                name=comp_dict.get("name", ""),
                ev_ebitda=comp_dict.get("ev_ebitda"),
                pe=comp_dict.get("pe"),
                ev_sales=comp_dict.get("ev_sales"),
            ))
    
    # Calculate implied values based on comparables
    implied_values: Dict[str, Optional[float]] = {}
    
    if comp_list:
        # Calculate median multiples
        ev_ebitda_multiples = [c.ev_ebitda for c in comp_list if c.ev_ebitda is not None]
        pe_multiples = [c.pe for c in comp_list if c.pe is not None]
        ev_sales_multiples = [c.ev_sales for c in comp_list if c.ev_sales is not None]
        
        # Implied EV based on EV/EBITDA
        if ev_ebitda_multiples and ebitda is not None and ebitda > 0:
            median_ev_ebitda = sorted(ev_ebitda_multiples)[len(ev_ebitda_multiples) // 2]
            implied_values["ev_ebitda_implied"] = median_ev_ebitda * ebitda
        
        # Implied Market Cap based on P/E
        if pe_multiples and net_income > 0:
            median_pe = sorted(pe_multiples)[len(pe_multiples) // 2]
            implied_values["pe_implied_market_cap"] = median_pe * net_income
        
        # Implied EV based on EV/Sales
        if ev_sales_multiples and revenue > 0:
            median_ev_sales = sorted(ev_sales_multiples)[len(ev_sales_multiples) // 2]
            implied_values["ev_sales_implied"] = median_ev_sales * revenue
    
    return RelativeValuationOutput(
        subject_company=model_input.ticker,
        subject_metrics=subject_metrics,
        comparables=comp_list,
        implied_values=implied_values,
    )
