"""
fmp_stable_metrics.py — Compute core financial metrics from normalized FMP /stable data.

This module computes key financial metrics (margins, ratios, totals) from
normalized financial data for valuation purposes.
"""

from __future__ import annotations

from typing import Any, Dict

from app.data.fmp_stable_normalizer import NormalizedFinancialsStable
from app.core.logging import get_logger

logger = get_logger(__name__)


def compute_core_metrics_stable(fin: NormalizedFinancialsStable) -> Dict[str, Any]:
    """
    Compute core financial metrics from normalized FMP /stable financials.
    
    Handles None values and division by zero safely.
    
    Args:
        fin: NormalizedFinancialsStable dataclass instance
        
    Returns:
        Dictionary with computed metrics (all values in same units as input)
    """
    # Basic components
    revenue = fin.revenue or 0.0
    cost_of_revenue = fin.cost_of_revenue or 0.0
    operating_expenses = fin.operating_expenses or 0.0
    operating_income = fin.operating_income
    ebitda = fin.ebitda
    pretax_income = fin.pretax_income
    income_tax_expense = fin.income_tax_expense
    net_income = fin.net_income
    
    # Operating costs
    operating_costs = cost_of_revenue + operating_expenses
    
    # Gross profit (use reported or calculate)
    gross_profit = fin.gross_profit
    if gross_profit is None and revenue > 0:
        gross_profit = revenue - cost_of_revenue
    
    # Gross margin
    gross_margin = None
    if revenue > 0 and gross_profit is not None:
        gross_margin = gross_profit / revenue
    
    # Operating margin
    operating_margin = None
    if revenue > 0 and operating_income is not None:
        operating_margin = operating_income / revenue
    
    # EBITDA (use reported or approximate from operating income)
    if ebitda is None and operating_income is not None:
        # Note: This is an approximation. True EBITDA requires D&A which
        # may not be directly available in normalized data.
        # For now, we use operating_income as a proxy if EBITDA is missing.
        ebitda = operating_income
        logger.debug(
            "EBITDA not available, using operating_income as approximation"
        )
    
    # EBITDA margin
    ebitda_margin = None
    if revenue > 0 and ebitda is not None:
        ebitda_margin = ebitda / revenue
    
    # Tax rate
    tax_rate = None
    if pretax_income is not None and pretax_income > 0 and income_tax_expense is not None:
        tax_rate = income_tax_expense / pretax_income
    
    # Dividend payout ratio
    dividend_payout_ratio = None
    if net_income is not None and net_income > 0 and fin.dividends_paid is not None:
        # Note: dividends_paid is typically negative in cash flow statements
        # We use absolute value for the ratio calculation
        dividends_abs = abs(fin.dividends_paid) if fin.dividends_paid < 0 else fin.dividends_paid
        dividend_payout_ratio = dividends_abs / net_income
    
    metrics = {
        "symbol": fin.symbol,
        "fiscal_year": fin.fiscal_year,
        "period_end_date": fin.period_end_date,
        "revenue": revenue,
        "operating_costs": operating_costs,
        "gross_margin": gross_margin,
        "operating_margin": operating_margin,
        "ebitda": ebitda,
        "ebitda_margin": ebitda_margin,
        "tax_rate": tax_rate,
        "net_income": net_income,
        "ppe_net": fin.ppe_net,
        "inventory": fin.inventory,
        "accounts_receivable": fin.accounts_receivable,
        "accounts_payable": fin.accounts_payable,
        "accrued_expenses": fin.accrued_expenses,
        "debt_amount": fin.total_debt,
        "share_repurchases": fin.share_repurchases,
        "dividends_paid": fin.dividends_paid,
        "dividend_payout_ratio": dividend_payout_ratio,
    }
    
    logger.info(f"Computed metrics for {fin.symbol} FY {fin.fiscal_year}")
    logger.info(f"  Revenue: ${revenue:,.0f}")
    if net_income:
        logger.info(f"  Net Income: ${net_income:,.0f}")
    if ebitda:
        logger.info(f"  EBITDA: ${ebitda:,.0f}")
    if fin.total_debt:
        logger.info(f"  Total Debt: ${fin.total_debt:,.0f}")
    
    return metrics

