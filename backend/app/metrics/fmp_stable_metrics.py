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
<<<<<<< Updated upstream
    Compute core financial metrics from normalized FMP /stable data.
=======
    Compute core financial metrics from normalized FMP /stable financials.
    
    Handles None values and division by zero safely.
>>>>>>> Stashed changes
    
    Args:
        fin: NormalizedFinancialsStable dataclass instance
        
    Returns:
<<<<<<< Updated upstream
        Dictionary of computed metrics including:
        - Revenue and growth metrics
        - Profitability margins (gross, operating, EBITDA, net)
        - Tax rate
        - Balance sheet items (assets, debt, equity)
        - Cash flow items (dividends, share repurchases)
        - Key ratios
    """
    metrics: Dict[str, Any] = {
        "symbol": fin.symbol,
        "fiscal_year": fin.fiscal_year,
        "period_end_date": fin.period_end_date,
    }
    
    # Revenue metrics
    metrics["revenue"] = fin.revenue
    
    # Profitability margins
    if fin.revenue and fin.revenue > 0:
        if fin.cost_of_revenue is not None:
            metrics["gross_margin"] = (fin.revenue - fin.cost_of_revenue) / fin.revenue
            metrics["gross_profit"] = fin.revenue - fin.cost_of_revenue
        
        if fin.operating_income is not None:
            metrics["operating_margin"] = fin.operating_income / fin.revenue
        
        if fin.ebitda is not None:
            metrics["ebitda_margin"] = fin.ebitda / fin.revenue
        
        if fin.net_income is not None:
            metrics["net_margin"] = fin.net_income / fin.revenue
    
    # EBITDA
    metrics["ebitda"] = fin.ebitda
    
    # Tax rate
    if fin.pretax_income and fin.pretax_income != 0:
        if fin.income_tax_expense is not None:
            metrics["tax_rate"] = fin.income_tax_expense / fin.pretax_income
    else:
        metrics["tax_rate"] = None
    
    # Income statement items
    metrics["net_income"] = fin.net_income
    metrics["operating_income"] = fin.operating_income
    metrics["income_before_tax"] = fin.pretax_income  # Alias for compatibility
    metrics["pretax_income"] = fin.pretax_income
    metrics["income_tax_expense"] = fin.income_tax_expense
    
    # Balance sheet items
    metrics["total_assets"] = fin.total_assets
    metrics["total_liabilities"] = fin.total_liabilities
    # Calculate total_equity if not directly available
    if fin.total_assets is not None and fin.total_liabilities is not None:
        metrics["total_equity"] = fin.total_assets - fin.total_liabilities
    else:
        metrics["total_equity"] = None
    metrics["debt_amount"] = fin.total_debt
    metrics["cash_and_equivalents"] = fin.cash_and_equivalents
    metrics["inventory"] = fin.inventory
    metrics["accounts_receivable"] = fin.accounts_receivable
    metrics["accounts_payable"] = fin.accounts_payable
    metrics["ppe_net"] = fin.ppe_net
    
    # Cash flow items
    metrics["dividends_paid"] = fin.dividends_paid
    metrics["share_repurchases"] = fin.share_repurchases
    # Note: operating_cash_flow and capital_expenditures may not be in NormalizedFinancialsStable
    # Add them if they exist in the dataclass
    
    # Key ratios
    if fin.net_income and fin.revenue and fin.revenue > 0:
        metrics["net_margin"] = fin.net_income / fin.revenue
    
    # Dividend payout ratio
    if fin.net_income and fin.net_income > 0:
        if fin.dividends_paid is not None:
            metrics["dividend_payout_ratio"] = abs(fin.dividends_paid) / fin.net_income
    else:
        metrics["dividend_payout_ratio"] = None
    
    # Debt to equity ratio
    if metrics["total_equity"] and metrics["total_equity"] != 0:
        if fin.total_debt is not None:
            metrics["debt_to_equity"] = fin.total_debt / metrics["total_equity"]
    else:
        metrics["debt_to_equity"] = None
    
    # Current ratio (if we have current assets/liabilities)
    # Note: FMP /stable may not provide current assets/liabilities breakdown
    # This would need to be added if those fields are available in NormalizedFinancialsStable
=======
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
>>>>>>> Stashed changes
    
    return metrics

