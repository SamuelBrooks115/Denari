"""
model_role_map.py — Model role definitions and flag mappings.

Defines valid model roles for each statement type and maps them to boolean flags
indicating which models (3-statement, DCF, Comps) each role is relevant for.
"""

from typing import Dict, List

# Model role naming convention:
# - Income Statement: IS_*
# - Balance Sheet: BS_*
# - Cash Flow: CF_*

# Income Statement model roles
IS_REVENUE = "IS_REVENUE"
IS_COGS = "IS_COGS"
IS_GROSS_PROFIT = "IS_GROSS_PROFIT"
IS_OPERATING_EXPENSE = "IS_OPERATING_EXPENSE"
IS_RD_EXPENSE = "IS_RD_EXPENSE"
IS_SGA_EXPENSE = "IS_SGA_EXPENSE"
IS_OPERATING_INCOME = "IS_OPERATING_INCOME"
IS_EBITDA = "IS_EBITDA"
IS_NON_OPERATING_INCOME = "IS_NON_OPERATING_INCOME"
IS_INTEREST_EXPENSE = "IS_INTEREST_EXPENSE"
IS_TAX_EXPENSE = "IS_TAX_EXPENSE"
IS_NET_INCOME = "IS_NET_INCOME"

# Balance Sheet model roles
BS_CASH = "BS_CASH"
BS_MARKETABLE_SECURITIES = "BS_MARKETABLE_SECURITIES"
BS_ACCOUNTS_RECEIVABLE = "BS_ACCOUNTS_RECEIVABLE"
BS_INVENTORY = "BS_INVENTORY"
BS_ASSETS_CURRENT = "BS_ASSETS_CURRENT"
BS_PP_AND_E = "BS_PP_AND_E"
BS_GOODWILL = "BS_GOODWILL"
BS_INTANGIBLES = "BS_INTANGIBLES"
BS_ASSETS_NONCURRENT = "BS_ASSETS_NONCURRENT"
BS_ASSETS_TOTAL = "BS_ASSETS_TOTAL"
BS_ACCOUNTS_PAYABLE = "BS_ACCOUNTS_PAYABLE"
BS_ACCRUED_LIABILITIES = "BS_ACCRUED_LIABILITIES"
BS_DEBT_CURRENT = "BS_DEBT_CURRENT"
BS_LIABILITIES_CURRENT = "BS_LIABILITIES_CURRENT"
BS_DEBT_NONCURRENT = "BS_DEBT_NONCURRENT"
BS_LIABILITIES_NONCURRENT = "BS_LIABILITIES_NONCURRENT"
BS_LIABILITIES_TOTAL = "BS_LIABILITIES_TOTAL"
BS_COMMON_STOCK = "BS_COMMON_STOCK"
BS_RETAINED_EARNINGS = "BS_RETAINED_EARNINGS"
BS_EQUITY_TOTAL = "BS_EQUITY_TOTAL"

# Cash Flow Statement model roles
CF_CASH_FROM_OPERATIONS = "CF_CASH_FROM_OPERATIONS"
CF_DEPRECIATION = "CF_DEPRECIATION"
CF_CHANGE_IN_WORKING_CAPITAL = "CF_CHANGE_IN_WORKING_CAPITAL"
CF_CAPEX = "CF_CAPEX"
CF_CASH_FROM_INVESTING = "CF_CASH_FROM_INVESTING"
CF_DEBT_ISSUANCE = "CF_DEBT_ISSUANCE"
CF_DEBT_REPAYMENT = "CF_DEBT_REPAYMENT"
CF_DIVIDENDS_PAID = "CF_DIVIDENDS_PAID"
CF_SHARE_REPURCHASES = "CF_SHARE_REPURCHASES"
CF_CASH_FROM_FINANCING = "CF_CASH_FROM_FINANCING"
CF_NET_CHANGE_IN_CASH = "CF_NET_CHANGE_IN_CASH"

# Model role to flags mapping
MODEL_ROLE_MAP: Dict[str, Dict[str, bool]] = {
    # Income Statement roles
    IS_REVENUE: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": True,
    },
    IS_COGS: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    IS_GROSS_PROFIT: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": True,
    },
    IS_OPERATING_EXPENSE: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    IS_RD_EXPENSE: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    IS_SGA_EXPENSE: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    IS_OPERATING_INCOME: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": True,
    },
    IS_EBITDA: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": True,
    },
    IS_NON_OPERATING_INCOME: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    IS_INTEREST_EXPENSE: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    IS_TAX_EXPENSE: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    IS_NET_INCOME: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": True,
    },
    # Balance Sheet roles
    BS_CASH: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    BS_MARKETABLE_SECURITIES: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_ACCOUNTS_RECEIVABLE: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    BS_INVENTORY: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    BS_ASSETS_CURRENT: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_PP_AND_E: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    BS_GOODWILL: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_INTANGIBLES: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_ASSETS_NONCURRENT: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_ASSETS_TOTAL: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": True,
    },
    BS_ACCOUNTS_PAYABLE: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    BS_ACCRUED_LIABILITIES: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_DEBT_CURRENT: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    BS_LIABILITIES_CURRENT: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_DEBT_NONCURRENT: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    BS_LIABILITIES_NONCURRENT: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_LIABILITIES_TOTAL: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_COMMON_STOCK: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_RETAINED_EARNINGS: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    BS_EQUITY_TOTAL: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": True,
    },
    # Cash Flow Statement roles
    CF_CASH_FROM_OPERATIONS: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": True,
    },
    CF_DEPRECIATION: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    CF_CHANGE_IN_WORKING_CAPITAL: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    CF_CAPEX: {
        "is_core_3_statement": True,
        "is_dcf_key": True,
        "is_comps_key": False,
    },
    CF_CASH_FROM_INVESTING: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    CF_DEBT_ISSUANCE: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    CF_DEBT_REPAYMENT: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    CF_DIVIDENDS_PAID: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    CF_SHARE_REPURCHASES: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    CF_CASH_FROM_FINANCING: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
    CF_NET_CHANGE_IN_CASH: {
        "is_core_3_statement": True,
        "is_dcf_key": False,
        "is_comps_key": False,
    },
}

# Default flags for unknown roles
DEFAULT_FLAGS = {
    "is_core_3_statement": False,
    "is_dcf_key": False,
    "is_comps_key": False,
}


def get_model_role_flags(model_role: str) -> Dict[str, bool]:
    """
    Get boolean flags for a model role.
    
    Args:
        model_role: Model role string (e.g., "IS_REVENUE")
    
    Returns:
        Dictionary with is_core_3_statement, is_dcf_key, is_comps_key flags
    """
    return MODEL_ROLE_MAP.get(model_role, DEFAULT_FLAGS).copy()


def get_valid_roles_for_statement(statement_type: str) -> List[str]:
    """
    Get list of valid model roles for a statement type.
    
    Args:
        statement_type: One of "income_statement", "balance_sheet", "cash_flow_statement"
    
    Returns:
        List of valid model role strings
    """
    if statement_type == "income_statement":
        return [
            IS_REVENUE,
            IS_COGS,
            IS_GROSS_PROFIT,
            IS_OPERATING_EXPENSE,
            IS_RD_EXPENSE,
            IS_SGA_EXPENSE,
            IS_OPERATING_INCOME,
            IS_EBITDA,
            IS_NON_OPERATING_INCOME,
            IS_INTEREST_EXPENSE,
            IS_TAX_EXPENSE,
            IS_NET_INCOME,
        ]
    elif statement_type == "balance_sheet":
        return [
            BS_CASH,
            BS_MARKETABLE_SECURITIES,
            BS_ACCOUNTS_RECEIVABLE,
            BS_INVENTORY,
            BS_ASSETS_CURRENT,
            BS_PP_AND_E,
            BS_GOODWILL,
            BS_INTANGIBLES,
            BS_ASSETS_NONCURRENT,
            BS_ASSETS_TOTAL,
            BS_ACCOUNTS_PAYABLE,
            BS_ACCRUED_LIABILITIES,
            BS_DEBT_CURRENT,
            BS_LIABILITIES_CURRENT,
            BS_DEBT_NONCURRENT,
            BS_LIABILITIES_NONCURRENT,
            BS_LIABILITIES_TOTAL,
            BS_COMMON_STOCK,
            BS_RETAINED_EARNINGS,
            BS_EQUITY_TOTAL,
        ]
    elif statement_type == "cash_flow_statement":
        return [
            CF_CASH_FROM_OPERATIONS,
            CF_DEPRECIATION,
            CF_CHANGE_IN_WORKING_CAPITAL,
            CF_CAPEX,
            CF_CASH_FROM_INVESTING,
            CF_DEBT_ISSUANCE,
            CF_DEBT_REPAYMENT,
            CF_DIVIDENDS_PAID,
            CF_SHARE_REPURCHASES,
            CF_CASH_FROM_FINANCING,
            CF_NET_CHANGE_IN_CASH,
        ]
    else:
        return []

