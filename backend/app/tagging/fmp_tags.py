"""
fmp_tags.py — Calculation tag vocabulary for FMP-based pipeline.

This module defines the canonical set of calc tags that map to normalized
financial fields. These tags are used for metric computation and can be
augmented by an LLM classifier later.
"""

from enum import Enum


class CalcTag(str, Enum):
    """
    Enumeration of calculation tags for financial metrics.
    
    These tags map directly to normalized financial fields from FMP data.
    """
    # Income Statement
    REVENUE_TOTAL = "revenue_total"
    COGS = "cogs"
    OPERATING_EXPENSE = "operating_expense"
    GROSS_PROFIT = "gross_profit"
    OPERATING_INCOME = "operating_income"
    EBITDA = "ebitda"
    PRE_TAX_INCOME = "pre_tax_income"
    INCOME_TAX_EXPENSE = "income_tax_expense"
    NET_INCOME = "net_income"
    
    # Balance Sheet
    PPE_NET = "ppe_net"
    INVENTORY = "inventory"
    ACCOUNTS_PAYABLE = "accounts_payable"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    ACCRUED_EXPENSES = "accrued_expenses"
    TOTAL_DEBT = "total_debt"
    
    # Cash Flow
    SHARE_REPURCHASES = "share_repurchases"
    DIVIDENDS_PAID = "dividends_paid"


# All valid calc tag values (for validation)
VALID_CALC_TAGS = {tag.value for tag in CalcTag}

