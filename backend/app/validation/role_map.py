"""
role_map.py — Mapping of required DCF variables to expected model roles.

Defines the mapping spec for required variables → expected model_roles,
using the Denari role taxonomy.
"""

from typing import Dict, List

from app.core.model_role_map import (
    BS_ACCOUNTS_PAYABLE,
    BS_ACCOUNTS_RECEIVABLE,
    BS_ACCRUED_LIABILITIES,
    BS_AP_AND_ACCRUED,
    BS_DEBT_CURRENT,
    BS_DEBT_NONCURRENT,
    BS_INVENTORY,
    BS_PP_AND_E,
    CF_DEPRECIATION,
    CF_DIVIDENDS_PAID,
    CF_SHARE_REPURCHASES,
    IS_COGS,
    IS_D_AND_A,
    IS_EBITDA,
    IS_NET_INCOME,
    IS_OPERATING_EXPENSE,
    IS_OPERATING_INCOME,
    IS_RD_EXPENSE,
    IS_REVENUE,
    IS_SGA_EXPENSE,
    IS_TAX_EXPENSE,
)

# Mapping of required variable name → list of acceptable model roles
# Multiple roles may be acceptable (e.g., operating costs could be IS_OPERATING_EXPENSE or derived from IS_COGS + IS_OPERATING_EXPENSE)
REQUIRED_VARIABLE_ROLES: Dict[str, List[str]] = {
    # Income Statement variables
    "Revenue": [IS_REVENUE],
    "Operating Costs / Margin": [
        IS_OPERATING_EXPENSE,  # Direct match preferred
        # Can be computed from: IS_COGS + IS_SGA_EXPENSE + IS_RD_EXPENSE + other operating expenses
    ],
    "Gross Margin / Costs": [IS_COGS],  # Gross margin = Revenue - COGS, so we need COGS
    "EBITDA Margins / Costs": [
        IS_EBITDA,  # Direct match preferred
        # Can be computed from: IS_OPERATING_INCOME + IS_D_AND_A (or CF_DEPRECIATION)
    ],
    "Tax Rate": [IS_TAX_EXPENSE],  # Tax rate = Tax Expense / Pretax Income (may need both)
    
    # Balance Sheet variables
    "PP&E": [BS_PP_AND_E],
    "Inventory": [BS_INVENTORY],
    "Accounts Payable": [
        BS_ACCOUNTS_PAYABLE,  # Direct match preferred
        BS_AP_AND_ACCRUED,  # Proxy: combined tag (acceptable if no separate AP exists)
    ],
    "Accounts Receivable": [BS_ACCOUNTS_RECEIVABLE],
    "Accrued Expenses": [
        BS_ACCRUED_LIABILITIES,  # Direct match preferred
        BS_AP_AND_ACCRUED,  # Proxy: combined tag (can compute if separate AP exists)
    ],
    
    # Cash Flow Statement variables
    "Share Repurchases": [CF_SHARE_REPURCHASES],
    "Debt Amount": [
        BS_DEBT_CURRENT,
        BS_DEBT_NONCURRENT,
        # Can be computed from: BS_DEBT_CURRENT + BS_DEBT_NONCURRENT
    ],
    "Dividend as a % of Net Income": [CF_DIVIDENDS_PAID],  # Need dividends and net income
}

# Statement type for each variable
VARIABLE_STATEMENT_TYPE: Dict[str, str] = {
    "Revenue": "income_statement",
    "Operating Costs / Margin": "income_statement",
    "Gross Margin / Costs": "income_statement",
    "EBITDA Margins / Costs": "income_statement",
    "Tax Rate": "income_statement",
    "PP&E": "balance_sheet",
    "Inventory": "balance_sheet",
    "Accounts Payable": "balance_sheet",
    "Accounts Receivable": "balance_sheet",
    "Accrued Expenses": "balance_sheet",
    "Share Repurchases": "cash_flow_statement",
    "Debt Amount": "balance_sheet",  # Debt is on balance sheet, not cash flow
    "Dividend as a % of Net Income": "cash_flow_statement",  # Need both CF_DIVIDENDS_PAID and IS_NET_INCOME
}

# Special handling notes for computed variables
COMPUTED_VARIABLES: Dict[str, str] = {
    "Operating Costs / Margin": "May need IS_COGS + IS_OPERATING_EXPENSE if not directly available",
    "Gross Margin / Costs": "Gross Margin = Revenue - COGS, need both IS_REVENUE and IS_COGS",
    "EBITDA Margins / Costs": "EBITDA may be computed from Operating Income + Depreciation",
    "Tax Rate": "Tax Rate = Tax Expense / Pretax Income, need both IS_TAX_EXPENSE and pretax income",
    "Debt Amount": "May need BS_DEBT_CURRENT + BS_DEBT_NONCURRENT if no combined tag",
    "Dividend as a % of Net Income": "Need CF_DIVIDENDS_PAID and IS_NET_INCOME",
}


def get_expected_roles(variable_name: str) -> List[str]:
    """
    Get expected model roles for a required variable.
    
    Args:
        variable_name: Name of required variable
        
    Returns:
        List of acceptable model role strings
    """
    return REQUIRED_VARIABLE_ROLES.get(variable_name, [])


def get_statement_type(variable_name: str) -> str:
    """
    Get statement type for a required variable.
    
    Args:
        variable_name: Name of required variable
        
    Returns:
        Statement type: "income_statement", "balance_sheet", or "cash_flow_statement"
    """
    return VARIABLE_STATEMENT_TYPE.get(variable_name, "")


def get_all_required_variables() -> List[str]:
    """
    Get list of all required variable names.
    
    Returns:
        List of variable names
    """
    return list(REQUIRED_VARIABLE_ROLES.keys())

