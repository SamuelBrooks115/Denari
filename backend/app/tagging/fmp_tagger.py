"""
fmp_tagger.py — Tag normalized financials with calculation tags.

This module maps normalized financial fields to calculation tags.
Since the normalized schema is already aligned with our tag vocabulary,
this is mostly a 1:1 mapping.

TODO: This can be augmented or overridden by an LLM classifier later.
"""

from __future__ import annotations

from typing import Dict

from app.data.fmp_normalizer import NormalizedFinancials
from app.tagging.fmp_tags import CalcTag


def tag_from_normalized(fin: NormalizedFinancials) -> Dict[CalcTag, float]:
    """
    Map normalized financial fields to calculation tags.
    
    This function creates a dictionary mapping CalcTag enum values to
    numeric values from the normalized financials. Only fields with
    non-None values are included.
    
    Args:
        fin: NormalizedFinancials dataclass instance
        
    Returns:
        Dictionary mapping CalcTag -> float value (only non-None fields)
    """
    tags: Dict[CalcTag, float] = {}
    
    # Income Statement tags
    if fin.revenue is not None:
        tags[CalcTag.REVENUE_TOTAL] = fin.revenue
    
    if fin.cost_of_revenue is not None:
        tags[CalcTag.COGS] = fin.cost_of_revenue
    
    if fin.operating_expenses is not None:
        tags[CalcTag.OPERATING_EXPENSE] = fin.operating_expenses
    
    if fin.gross_profit is not None:
        tags[CalcTag.GROSS_PROFIT] = fin.gross_profit
    
    if fin.operating_income is not None:
        tags[CalcTag.OPERATING_INCOME] = fin.operating_income
    
    if fin.ebitda is not None:
        tags[CalcTag.EBITDA] = fin.ebitda
    
    if fin.pretax_income is not None:
        tags[CalcTag.PRE_TAX_INCOME] = fin.pretax_income
    
    if fin.income_tax_expense is not None:
        tags[CalcTag.INCOME_TAX_EXPENSE] = fin.income_tax_expense
    
    if fin.net_income is not None:
        tags[CalcTag.NET_INCOME] = fin.net_income
    
    # Balance Sheet tags
    if fin.ppe_net is not None:
        tags[CalcTag.PPE_NET] = fin.ppe_net
    
    if fin.inventory is not None:
        tags[CalcTag.INVENTORY] = fin.inventory
    
    if fin.accounts_payable is not None:
        tags[CalcTag.ACCOUNTS_PAYABLE] = fin.accounts_payable
    
    if fin.accounts_receivable is not None:
        tags[CalcTag.ACCOUNTS_RECEIVABLE] = fin.accounts_receivable
    
    if fin.accrued_expenses is not None:
        tags[CalcTag.ACCRUED_EXPENSES] = fin.accrued_expenses
    
    if fin.total_debt is not None:
        tags[CalcTag.TOTAL_DEBT] = fin.total_debt
    
    # Cash Flow tags
    if fin.share_repurchases is not None:
        tags[CalcTag.SHARE_REPURCHASES] = fin.share_repurchases
    
    if fin.dividends_paid is not None:
        tags[CalcTag.DIVIDENDS_PAID] = fin.dividends_paid
    
    return tags

