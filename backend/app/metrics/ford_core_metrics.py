"""
ford_core_metrics.py — Compute core financial metrics from tagged Ford facts.

DEPRECATED — This module has been replaced by the FMP-based pipeline.
See app/metrics/fmp_core_metrics.py for the new implementation.

This module computes key financial metrics (margins, ratios, totals) from
tagged facts for a given fiscal year.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.tagging.calc_tags import CalcTag

logger = get_logger(__name__)


def _sum_values(facts: List[Dict[str, Any]], tag: CalcTag) -> float:
    """
    Sum value_typed for facts where calc_tags includes the given tag.
    
    Args:
        facts: List of tagged fact dictionaries
        tag: CalcTag enum value to filter by
        
    Returns:
        Sum of value_typed for matching facts
    """
    tag_value = tag.value
    total = 0.0
    
    for fact in facts:
        calc_tags = fact.get("calc_tags", [])
        if tag_value in calc_tags:
            value = fact.get("value_typed")
            if value is not None:
                try:
                    total += float(value)
                except (ValueError, TypeError):
                    pass
    
    return total


def compute_core_metrics(
    tagged_facts: List[Dict[str, Any]],
    fiscal_year: int,
) -> Dict[str, Any]:
    """
    Compute core financial metrics from tagged facts for a given fiscal year.
    
    Args:
        tagged_facts: List of tagged fact dictionaries
        fiscal_year: Target fiscal year
        
    Returns:
        Dictionary with computed metrics
    """
    # Filter facts to fiscal year
    fiscal_facts = []
    for fact in tagged_facts:
        period_end = fact.get("period_end")
        if period_end:
            try:
                period_year = int(period_end.split("-")[0])
                if period_year == fiscal_year:
                    fiscal_facts.append(fact)
            except (ValueError, TypeError):
                continue
    
    logger.info(f"Computing metrics for {len(fiscal_facts)} facts in fiscal year {fiscal_year}")
    
    # INCOME STATEMENT COMPONENTS
    revenue = _sum_values(fiscal_facts, CalcTag.REVENUE_TOTAL)
    cogs = _sum_values(fiscal_facts, CalcTag.COGS)
    operating_exp = _sum_values(fiscal_facts, CalcTag.OPERATING_EXPENSE)
    gross_profit = _sum_values(fiscal_facts, CalcTag.GROSS_PROFIT)
    operating_income = _sum_values(fiscal_facts, CalcTag.OPERATING_INCOME)
    da = _sum_values(fiscal_facts, CalcTag.DEPRECIATION_AMORTIZATION)
    pre_tax = _sum_values(fiscal_facts, CalcTag.PRE_TAX_INCOME)
    tax_expense = _sum_values(fiscal_facts, CalcTag.INCOME_TAX_EXPENSE)
    net_income = _sum_values(fiscal_facts, CalcTag.NET_INCOME)
    
    # BALANCE SHEET COMPONENTS
    ppe = _sum_values(fiscal_facts, CalcTag.PPE_NET)
    inventory = _sum_values(fiscal_facts, CalcTag.INVENTORY)
    ap = _sum_values(fiscal_facts, CalcTag.ACCOUNTS_PAYABLE)
    ar = _sum_values(fiscal_facts, CalcTag.ACCOUNTS_RECEIVABLE)
    accrued = _sum_values(fiscal_facts, CalcTag.ACCRUED_EXPENSES)
    debt = _sum_values(fiscal_facts, CalcTag.TOTAL_DEBT_COMPONENT)
    
    # CASH FLOW COMPONENTS
    repurchases = _sum_values(fiscal_facts, CalcTag.SHARE_REPURCHASES)
    dividends_paid = _sum_values(fiscal_facts, CalcTag.DIVIDENDS_PAID)
    
    # DERIVED METRICS
    # Gross profit fallback: revenue - cogs
    if gross_profit == 0.0 and revenue > 0 and cogs > 0:
        gross_profit = revenue - cogs
    
    # Gross margin
    gross_margin = None
    if revenue > 0:
        gross_margin = gross_profit / revenue
    
    # Operating costs
    operating_costs = cogs + operating_exp
    
    # Operating margin
    operating_margin = None
    if revenue > 0:
        operating_margin = operating_income / revenue
    
    # EBITDA
    ebitda = operating_income + da
    
    # EBITDA margin
    ebitda_margin = None
    if revenue > 0:
        ebitda_margin = ebitda / revenue
    
    # Tax rate
    tax_rate = None
    if pre_tax > 0:
        tax_rate = tax_expense / pre_tax
    
    # Dividend payout ratio
    dividend_payout_ratio = None
    if net_income > 0:
        dividend_payout_ratio = dividends_paid / net_income
    
    metrics = {
        "fiscal_year": fiscal_year,
        "revenue": revenue,
        "operating_costs": operating_costs,
        "gross_margin": gross_margin,
        "operating_margin": operating_margin,
        "ebitda": ebitda,
        "ebitda_margin": ebitda_margin,
        "tax_rate": tax_rate,
        "net_income": net_income,
        "ppe_net": ppe,
        "inventory": inventory,
        "accounts_payable": ap,
        "accounts_receivable": ar,
        "accrued_expenses": accrued,
        "debt_amount": debt,
        "share_repurchases": repurchases,
        "dividends_paid": dividends_paid,
        "dividend_payout_ratio": dividend_payout_ratio,
    }
    
    logger.info(f"Computed metrics for fiscal year {fiscal_year}")
    logger.info(f"  Revenue: {revenue:,.0f}")
    logger.info(f"  Net Income: {net_income:,.0f}")
    logger.info(f"  EBITDA: {ebitda:,.0f}")
    logger.info(f"  Debt: {debt:,.0f}")
    
    return metrics


def compute_metrics_from_json(
    tagged_json: str,
    fiscal_year: int,
) -> Dict[str, Any]:
    """
    Load tagged facts JSON and compute metrics.
    
    Args:
        tagged_json: Path to tagged facts JSON file
        fiscal_year: Target fiscal year
        
    Returns:
        Dictionary with computed metrics
    """
    tagged_path = Path(tagged_json)
    if not tagged_path.exists():
        raise FileNotFoundError(f"Tagged facts JSON not found: {tagged_json}")
    
    logger.info(f"Loading tagged facts from: {tagged_json}")
    
    with tagged_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    tagged_facts = data.get("facts_tagged", [])
    if not tagged_facts:
        raise ValueError("No tagged facts found in JSON")
    
    return compute_core_metrics(tagged_facts, fiscal_year)

