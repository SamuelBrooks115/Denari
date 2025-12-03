"""
calc_tags.py — Calculation tag vocabulary for financial line item classification.

This module defines the canonical set of calc tags that can be assigned to financial
line items for downstream calculation purposes. Tags are organized by statement type.
"""

from enum import Enum
from typing import Literal, Optional

# ============================================================================
# INCOME STATEMENT TAGS
# ============================================================================

# Total GAAP revenue / sales
REVENUE_TOTAL = "revenue_total"

# Cost of goods sold / cost of sales
COGS = "cogs"

# SG&A, R&D, and other operating expenses (excluding COGS)
OPERATING_EXPENSE = "operating_expense"

# Gross profit (if reported as a separate line item)
GROSS_PROFIT = "gross_profit"

# Operating income (EBIT)
OPERATING_INCOME = "operating_income"

# Depreciation and amortization expense (income statement)
DEPRECIATION_AMORTIZATION = "depreciation_amortization"

# Other adjustments needed to derive EBITDA (e.g., restructuring, impairments)
EBITDA_ADJUSTMENT_OTHER = "ebitda_adjustment_other"

# Income before income taxes
PRE_TAX_INCOME = "pre_tax_income"

# Income tax expense (benefit)
INCOME_TAX_EXPENSE = "income_tax_expense"

# Net income / net earnings (GAAP)
NET_INCOME = "net_income"

# ============================================================================
# BALANCE SHEET TAGS
# ============================================================================

# Net Property, Plant, and Equipment
PPE_NET = "ppe_net"

# Inventory
INVENTORY = "inventory"

# Accounts payable / trade payables
ACCOUNTS_PAYABLE = "accounts_payable"

# Accounts receivable / trade receivables
ACCOUNTS_RECEIVABLE = "accounts_receivable"

# Accrued expenses / accrued liabilities
ACCRUED_EXPENSES = "accrued_expenses"

# Any component of interest-bearing debt (current or long-term)
TOTAL_DEBT_COMPONENT = "total_debt_component"

# ============================================================================
# CASH FLOW STATEMENT TAGS
# ============================================================================

# Cash used to repurchase common stock
SHARE_REPURCHASES = "share_repurchases"

# Dividends paid to common shareholders
DIVIDENDS_PAID = "dividends_paid"

# ============================================================================
# ENUM DEFINITION
# ============================================================================

class CalcTag(Enum):
    """Enumeration of all valid calculation tags."""
    # Income Statement
    REVENUE_TOTAL = "revenue_total"
    COGS = "cogs"
    OPERATING_EXPENSE = "operating_expense"
    GROSS_PROFIT = "gross_profit"
    OPERATING_INCOME = "operating_income"
    DEPRECIATION_AMORTIZATION = "depreciation_amortization"
    PRE_TAX_INCOME = "pre_tax_income"
    INCOME_TAX_EXPENSE = "income_tax_expense"
    NET_INCOME = "net_income"
    
    # Balance Sheet
    PPE_NET = "ppe_net"
    INVENTORY = "inventory"
    ACCOUNTS_PAYABLE = "accounts_payable"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    ACCRUED_EXPENSES = "accrued_expenses"
    TOTAL_DEBT_COMPONENT = "total_debt_component"
    
    # Cash Flow
    SHARE_REPURCHASES = "share_repurchases"
    DIVIDENDS_PAID = "dividends_paid"


# ============================================================================
# VALIDATION
# ============================================================================

# All valid calc tags (for backward compatibility and validation)
VALID_CALC_TAGS = {
    # Income Statement
    REVENUE_TOTAL,
    COGS,
    OPERATING_EXPENSE,
    GROSS_PROFIT,
    OPERATING_INCOME,
    DEPRECIATION_AMORTIZATION,
    EBITDA_ADJUSTMENT_OTHER,
    PRE_TAX_INCOME,
    INCOME_TAX_EXPENSE,
    NET_INCOME,
    # Balance Sheet
    PPE_NET,
    INVENTORY,
    ACCOUNTS_PAYABLE,
    ACCOUNTS_RECEIVABLE,
    ACCRUED_EXPENSES,
    TOTAL_DEBT_COMPONENT,
    # Cash Flow
    SHARE_REPURCHASES,
    DIVIDENDS_PAID,
}

# Type hint for calc tags (string values)
CalcTagStr = Literal[
    "revenue_total",
    "cogs",
    "operating_expense",
    "gross_profit",
    "operating_income",
    "depreciation_amortization",
    "pre_tax_income",
    "income_tax_expense",
    "net_income",
    "ppe_net",
    "inventory",
    "accounts_payable",
    "accounts_receivable",
    "accrued_expenses",
    "total_debt_component",
    "share_repurchases",
    "dividends_paid",
]


def is_valid_calc_tag(tag: str) -> bool:
    """
    Check if a tag is in the valid vocabulary.
    
    Args:
        tag: Tag string to validate
        
    Returns:
        True if tag is valid, False otherwise
    """
    return tag in VALID_CALC_TAGS


def get_tag_enum_value(tag_str: str) -> Optional[CalcTag]:
    """
    Get CalcTag enum from string value.
    
    Args:
        tag_str: Tag string value
        
    Returns:
        CalcTag enum or None if not found
    """
    try:
        return CalcTag(tag_str)
    except ValueError:
        return None


def get_tag_definitions() -> dict[str, str]:
    """
    Get human-readable definitions for all calc tags.
    
    Returns:
        Dictionary mapping tag -> definition
    """
    return {
        # Income Statement
        REVENUE_TOTAL: "Total GAAP revenue / sales",
        COGS: "Cost of goods sold / cost of sales",
        OPERATING_EXPENSE: "SG&A, R&D, and other operating expenses (excluding COGS)",
        GROSS_PROFIT: "Gross profit (if reported as a separate line item)",
        OPERATING_INCOME: "Operating income (EBIT)",
        DEPRECIATION_AMORTIZATION: "Depreciation and amortization expense (income statement)",
        EBITDA_ADJUSTMENT_OTHER: "Other adjustments needed to derive EBITDA (e.g., restructuring, impairments)",
        PRE_TAX_INCOME: "Income before income taxes",
        INCOME_TAX_EXPENSE: "Income tax expense (benefit)",
        NET_INCOME: "Net income / net earnings (GAAP)",
        # Balance Sheet
        PPE_NET: "Net Property, Plant, and Equipment",
        INVENTORY: "Inventory",
        ACCOUNTS_PAYABLE: "Accounts payable / trade payables",
        ACCOUNTS_RECEIVABLE: "Accounts receivable / trade receivables",
        ACCRUED_EXPENSES: "Accrued expenses / accrued liabilities",
        TOTAL_DEBT_COMPONENT: "Any component of interest-bearing debt (current or long-term)",
        # Cash Flow
        SHARE_REPURCHASES: "Cash used to repurchase common stock",
        DIVIDENDS_PAID: "Dividends paid to common shareholders",
    }

