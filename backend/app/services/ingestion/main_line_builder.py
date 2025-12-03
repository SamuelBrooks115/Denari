"""
main_line_builder.py — Build consolidated main-line financial statements.

This module constructs Income Statement, Balance Sheet, and Cash Flow Statement
with consolidated totals only (no dimensional splits), using deterministic
tag selection and consolidation logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.core.model_role_map import (
    BS_ACCOUNTS_PAYABLE,
    BS_ACCOUNTS_RECEIVABLE,
    BS_ACCRUED_LIABILITIES,
    BS_AP_AND_ACCRUED,
    BS_ASSETS_CURRENT,
    BS_ASSETS_TOTAL,
    BS_CASH,
    BS_DEBT_CURRENT,
    BS_DEBT_NONCURRENT,
    BS_EQUITY_TOTAL,
    BS_INVENTORY,
    BS_LIABILITIES_CURRENT,
    BS_LIABILITIES_TOTAL,
    BS_PP_AND_E,
    CF_CAPEX,
    CF_CASH_FROM_FINANCING,
    CF_CASH_FROM_INVESTING,
    CF_CASH_FROM_OPERATIONS,
    CF_CHANGE_IN_WORKING_CAPITAL,
    CF_DEBT_ISSUANCE,
    CF_DEBT_REPAYMENT,
    CF_DEPRECIATION,
    CF_DIVIDENDS_PAID,
    CF_NET_CHANGE_IN_CASH,
    CF_SHARE_REPURCHASES,
    IS_COGS,
    IS_D_AND_A,
    IS_GROSS_PROFIT,
    IS_NET_INCOME,
    IS_OPERATING_EXPENSE,
    IS_OPERATING_INCOME,
    IS_REVENUE,
    IS_TAX_EXPENSE,
    get_model_role_flags,
)
from app.services.ingestion.consolidation import select_consolidated_fact
from app.services.ingestion.xbrl.utils import flatten_units, annual_duration_ok, parse_date

logger = get_logger(__name__)

# Core role to tag candidate mappings (Ford scope)
# These are the primary GAAP tags we look for
CORE_ROLE_TAG_MAP: Dict[str, List[str]] = {
    # Income Statement
    IS_REVENUE: [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
    ],
    IS_COGS: [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
        "CostOfSales",
    ],
    IS_GROSS_PROFIT: [
        "GrossProfit",
    ],
    IS_OPERATING_EXPENSE: [
        "OperatingExpenses",
        "OperatingCosts",
    ],
    IS_OPERATING_INCOME: [
        "OperatingIncomeLoss",
        "OperatingProfitLoss",
        "EarningsBeforeInterestAndTaxes",
    ],
    IS_TAX_EXPENSE: [
        "IncomeTaxExpenseBenefit",
        "IncomeTaxExpense",
    ],
    IS_NET_INCOME: [
        "NetIncomeLoss",
        "ProfitLoss",
    ],
    IS_D_AND_A: [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
    ],
    # Balance Sheet
    BS_CASH: [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",
    ],
    BS_ACCOUNTS_RECEIVABLE: [
        "AccountsReceivableNetCurrent",
        "ReceivablesNetCurrent",
    ],
    BS_INVENTORY: [
        "Inventories",
        "InventoryNet",
    ],
    BS_PP_AND_E: [
        "PropertyPlantAndEquipmentNet",
    ],
    BS_ASSETS_CURRENT: [
        "AssetsCurrent",
    ],
    BS_ASSETS_TOTAL: [
        "Assets",
    ],
    BS_ACCOUNTS_PAYABLE: [
        "AccountsPayableCurrent",
    ],
    BS_ACCRUED_LIABILITIES: [
        "AccruedLiabilitiesCurrent",
    ],
    BS_AP_AND_ACCRUED: [
        "AccountsPayableAndAccruedLiabilitiesCurrent",
    ],
    BS_DEBT_CURRENT: [
        "DebtCurrent",
        "ShortTermDebt",
        "ShortTermBorrowings",
    ],
    BS_DEBT_NONCURRENT: [
        "DebtNoncurrent",
        "LongTermDebtNoncurrent",
        "LongTermDebt",
    ],
    BS_LIABILITIES_CURRENT: [
        "LiabilitiesCurrent",
    ],
    BS_LIABILITIES_TOTAL: [
        "Liabilities",
    ],
    BS_EQUITY_TOTAL: [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "Equity",
    ],
    # Cash Flow
    CF_CASH_FROM_OPERATIONS: [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    CF_DEPRECIATION: [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
    ],
    CF_CHANGE_IN_WORKING_CAPITAL: [
        "IncreaseDecreaseInWorkingCapital",
    ],
    CF_CAPEX: [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquirePropertyAndEquipment",
        "PurchasesOfPropertyAndEquipment",
        "CapitalExpenditures",
    ],
    CF_CASH_FROM_INVESTING: [
        "NetCashProvidedByUsedInInvestingActivities",
    ],
    CF_DEBT_ISSUANCE: [
        "ProceedsFromIssuanceOfLongTermDebt",
        "ProceedsFromIssuanceOfShortTermDebt",
    ],
    CF_DEBT_REPAYMENT: [
        "RepaymentsOfLongTermDebt",
        "RepaymentsOfShortTermDebt",
    ],
    CF_DIVIDENDS_PAID: [
        "PaymentsOfDividends",
    ],
    CF_SHARE_REPURCHASES: [
        "PaymentsForRepurchaseOfCommonStock",
        "PaymentsForRepurchaseOfEquityInstruments",
    ],
    CF_CASH_FROM_FINANCING: [
        "NetCashProvidedByUsedInFinancingActivities",
    ],
    CF_NET_CHANGE_IN_CASH: [
        "CashAndCashEquivalentsPeriodIncreaseDecrease",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecrease",
    ],
}


def _find_candidate_tags_for_role(
    us_gaap: Dict[str, Any],
    role: str,
    statement_type: str,
) -> List[Tuple[str, str]]:
    """
    Find candidate tags for a given role.
    
    Returns list of (tag, label) tuples.
    """
    candidates = []
    tag_list = CORE_ROLE_TAG_MAP.get(role, [])
    
    for tag in tag_list:
        if tag in us_gaap:
            node = us_gaap[tag]
            label = node.get("label") or node.get("description") or tag
            candidates.append((tag, label))
    
    return candidates


def _get_facts_for_tag_period(
    us_gaap: Dict[str, Any],
    tag: str,
    period: str,
    statement_type: str,
) -> List[Dict[str, Any]]:
    """
    Get all fact records for a tag and period.
    
    Args:
        us_gaap: US-GAAP facts dictionary
        tag: XBRL tag name
        period: Period end date (ISO format)
        statement_type: "IS", "BS", or "CF"
        
    Returns:
        List of fact records
    """
    node = us_gaap.get(tag)
    if not node:
        return []
    
    units = node.get("units")
    if not isinstance(units, dict):
        return []
    
    all_records = flatten_units(units)
    
    # Filter by period and statement type
    filtered = []
    for rec in all_records:
        end = rec.get("end")
        if end != period:
            continue
        
        # Filter by statement type characteristics
        if statement_type == "BS":
            # Balance sheet items are instant (point-in-time)
            start = rec.get("start")
            if start and start != end:
                continue
        elif statement_type in ("IS", "CF"):
            # Income statement and cash flow are annual durations
            start = rec.get("start")
            if not annual_duration_ok(start, end):
                continue
        
        filtered.append(rec)
    
    return filtered


def build_main_line_statements(
    us_gaap: Dict[str, Any],
    periods: List[str],
) -> Dict[str, Any]:
    """
    Build consolidated main-line financial statements.
    
    For each statement type (IS, BS, CF) and each core role:
    1. Find candidate tags
    2. Use select_consolidated_fact to get consolidated value
    3. Build line items with "direct", "computed", or "proxy" status
    
    Args:
        us_gaap: US-GAAP facts dictionary from Company Facts API
        periods: List of period end dates (ISO format)
        
    Returns:
        Dictionary with structure:
        {
            "income_statement": {"line_items": [...]},
            "balance_sheet": {"line_items": [...]},
            "cash_flow_statement": {"line_items": [...]}
        }
    """
    statements = {
        "income_statement": {"line_items": []},
        "balance_sheet": {"line_items": []},
        "cash_flow_statement": {"line_items": []},
    }
    
    # Define core roles by statement
    role_mapping = {
        "income_statement": [
            IS_REVENUE,
            IS_COGS,
            IS_GROSS_PROFIT,
            IS_OPERATING_EXPENSE,
            IS_OPERATING_INCOME,
            IS_TAX_EXPENSE,
            IS_NET_INCOME,
            IS_D_AND_A,
        ],
        "balance_sheet": [
            BS_CASH,
            BS_ACCOUNTS_RECEIVABLE,
            BS_INVENTORY,
            BS_PP_AND_E,
            BS_ASSETS_CURRENT,
            BS_ASSETS_TOTAL,
            BS_ACCOUNTS_PAYABLE,
            BS_ACCRUED_LIABILITIES,
            BS_AP_AND_ACCRUED,
            BS_DEBT_CURRENT,
            BS_DEBT_NONCURRENT,
            BS_LIABILITIES_CURRENT,
            BS_LIABILITIES_TOTAL,
            BS_EQUITY_TOTAL,
        ],
        "cash_flow_statement": [
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
        ],
    }
    
    statement_type_map = {
        "income_statement": "IS",
        "balance_sheet": "BS",
        "cash_flow_statement": "CF",
    }
    
    # Process each statement type
    for stmt_name, roles in role_mapping.items():
        stmt_type = statement_type_map[stmt_name]
        line_items = []
        
        for role in roles:
            # Find candidate tags
            candidates = _find_candidate_tags_for_role(us_gaap, role, stmt_type)
            
            if not candidates:
                logger.debug(f"No candidate tags found for role {role}")
                continue
            
            # Try each candidate tag, pick best consolidated fact
            best_fact: Optional[Dict[str, Any]] = None
            best_tag: Optional[str] = None
            best_label: Optional[str] = None
            
            for tag, label in candidates:
                # Get facts for all periods
                all_facts = {}
                for period in periods:
                    facts = _get_facts_for_tag_period(us_gaap, tag, period, stmt_type)
                    if facts:
                        all_facts[period] = facts
                
                if not all_facts:
                    continue
                
                # Select consolidated fact for each period
                period_values = {}
                dimensions_used_any = False
                consolidated_unit = "USD"
                consolidated_context = {}
                
                for period, facts_list in all_facts.items():
                    consolidated = select_consolidated_fact(facts_list, tag, period)
                    if consolidated:
                        period_values[period] = consolidated["value"]
                        consolidated_unit = consolidated.get("unit", "USD")
                        consolidated_context = consolidated.get("context_metadata", {})
                        if consolidated.get("dimensions_used"):
                            dimensions_used_any = True
                
                if period_values:
                    # Use this tag if we have values
                    if best_fact is None:
                        best_fact = {
                            "periods": period_values,
                            "unit": consolidated_unit,
                            "dimensions_used": dimensions_used_any,
                            "context_metadata": consolidated_context,
                        }
                        best_tag = tag
                        best_label = label
                    # Prefer tags with more periods or no dimensions
                    elif (
                        len(period_values) > len(best_fact["periods"])
                        or (not dimensions_used_any and best_fact.get("dimensions_used"))
                    ):
                        best_fact = {
                            "periods": period_values,
                            "unit": consolidated_unit,
                            "dimensions_used": dimensions_used_any,
                            "context_metadata": consolidated_context,
                        }
                        best_tag = tag
                        best_label = label
            
            if best_fact and best_tag:
                # Build line item
                flags = get_model_role_flags(role)
                line_item = {
                    "tag": best_tag,
                    "label": best_label,
                    "model_role": role,
                    "is_core_3_statement": flags.get("is_core_3_statement", False),
                    "is_dcf_key": flags.get("is_dcf_key", False),
                    "is_comps_key": flags.get("is_comps_key", False),
                    "status": "direct" if not best_fact.get("dimensions_used") else "proxy",
                    "unit": best_fact["unit"],
                    "periods": best_fact["periods"],
                    "supporting_tags": [best_tag],
                    "llm_classification": {
                        "best_fit_role": role,
                        "confidence": 1.0 if not best_fact.get("dimensions_used") else 0.8,
                    },
                }
                line_items.append(line_item)
                logger.debug(
                    f"Added {role} from tag {best_tag} "
                    f"(status={line_item['status']}, periods={len(best_fact['periods'])})"
                )
            else:
                logger.debug(f"No consolidated fact found for role {role}")
        
        statements[stmt_name]["line_items"] = line_items
        logger.info(
            f"Built {stmt_name} with {len(line_items)} main-line items"
        )
    
    return statements

