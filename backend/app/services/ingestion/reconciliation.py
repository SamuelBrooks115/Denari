"""
reconciliation.py — Financial statement reconciliation and validation.

This module verifies that financial statements reconcile correctly:
- Balance Sheet: Total Assets ≈ Total Liabilities + Total Equity
- Cash Flow: Net Change in Cash ≈ CFO + CFI + CFF
- Cash Flow: Ending Cash − Beginning Cash ≈ Net Change in Cash
- IS to CF: Net Income on IS matches CF NetIncomeLoss
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.core.model_role_map import (
    BS_ASSETS_TOTAL,
    BS_CASH,
    BS_EQUITY_TOTAL,
    BS_LIABILITIES_TOTAL,
    CF_CASH_FROM_FINANCING,
    CF_CASH_FROM_INVESTING,
    CF_CASH_FROM_OPERATIONS,
    CF_NET_CHANGE_IN_CASH,
    IS_NET_INCOME,
)

logger = get_logger(__name__)

# Tolerance for reconciliation (0.5% of assets for BS, absolute for CF)
BS_TOLERANCE_PCT = 0.005
CF_TOLERANCE_ABSOLUTE = 1000.0  # $1000 absolute tolerance for cash flow


def _get_line_item_value(
    line_items: List[Dict[str, Any]],
    model_role: str,
    period: str,
) -> Optional[float]:
    """Get value for a line item by model role and period."""
    for item in line_items:
        if item.get("model_role") == model_role:
            periods = item.get("periods", {})
            return periods.get(period)
    return None


def reconcile_balance_sheet(
    balance_sheet: Dict[str, Any],
    periods: List[str],
) -> Dict[str, Any]:
    """
    Reconcile balance sheet: Total Assets ≈ Total Liabilities + Total Equity.
    
    Args:
        balance_sheet: Balance sheet dictionary with line_items
        periods: List of period end dates
        
    Returns:
        Dictionary with reconciliation results:
        {
            "status": "pass" | "fail" | "partial",
            "periods": {
                period: {
                    "assets": float,
                    "liabilities": float,
                    "equity": float,
                    "sum": float,
                    "difference": float,
                    "difference_pct": float,
                    "passes": bool,
                }
            },
            "resolution": str,
        }
    """
    line_items = balance_sheet.get("line_items", [])
    results = {
        "status": "pass",
        "periods": {},
        "resolution": "",
    }
    
    all_pass = True
    any_pass = False
    
    for period in periods:
        assets = _get_line_item_value(line_items, BS_ASSETS_TOTAL, period)
        liabilities = _get_line_item_value(line_items, BS_LIABILITIES_TOTAL, period)
        equity = _get_line_item_value(line_items, BS_EQUITY_TOTAL, period)
        
        if assets is None or liabilities is None or equity is None:
            results["periods"][period] = {
                "assets": assets,
                "liabilities": liabilities,
                "equity": equity,
                "sum": None,
                "difference": None,
                "difference_pct": None,
                "passes": False,
                "reason": "Missing required line items",
            }
            all_pass = False
            continue
        
        sum_val = liabilities + equity
        difference = abs(assets - sum_val)
        difference_pct = difference / abs(assets) if assets != 0 else float("inf")
        
        # Check tolerance (0.5% of assets)
        passes = difference_pct <= BS_TOLERANCE_PCT
        
        results["periods"][period] = {
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "sum": sum_val,
            "difference": difference,
            "difference_pct": difference_pct,
            "passes": passes,
        }
        
        if passes:
            any_pass = True
        else:
            all_pass = False
            logger.warning(
                f"Balance sheet reconciliation failed for {period}: "
                f"Assets={assets}, Liabilities+Equity={sum_val}, "
                f"Difference={difference} ({difference_pct*100:.2f}%)"
            )
    
    if all_pass:
        results["status"] = "pass"
        results["resolution"] = "All periods reconcile within tolerance"
    elif any_pass:
        results["status"] = "partial"
        results["resolution"] = "Some periods reconcile, others require review"
    else:
        results["status"] = "fail"
        results["resolution"] = "Re-check consolidated selector for offending lines; prefer direct totals"
    
    return results


def reconcile_cash_flow(
    cash_flow: Dict[str, Any],
    balance_sheet: Dict[str, Any],
    periods: List[str],
) -> Dict[str, Any]:
    """
    Reconcile cash flow statements.
    
    Checks:
    1. Net Change in Cash ≈ CFO + CFI + CFF
    2. Ending Cash − Beginning Cash ≈ Net Change in Cash
    
    Args:
        cash_flow: Cash flow statement dictionary with line_items
        balance_sheet: Balance sheet dictionary with line_items (for cash values)
        periods: List of period end dates (sorted chronologically)
        
    Returns:
        Dictionary with reconciliation results
    """
    cf_line_items = cash_flow.get("line_items", [])
    bs_line_items = balance_sheet.get("line_items", [])
    
    results = {
        "status": "pass",
        "periods": {},
        "resolution": "",
    }
    
    all_pass = True
    any_pass = False
    
    # Sort periods chronologically
    sorted_periods = sorted(periods)
    
    for i, period in enumerate(sorted_periods):
        cfo = _get_line_item_value(cf_line_items, CF_CASH_FROM_OPERATIONS, period)
        cfi = _get_line_item_value(cf_line_items, CF_CASH_FROM_INVESTING, period)
        cff = _get_line_item_value(cf_line_items, CF_CASH_FROM_FINANCING, period)
        net_change = _get_line_item_value(cf_line_items, CF_NET_CHANGE_IN_CASH, period)
        
        ending_cash = _get_line_item_value(bs_line_items, BS_CASH, period)
        beginning_cash = None
        if i > 0:
            beginning_cash = _get_line_item_value(bs_line_items, BS_CASH, sorted_periods[i - 1])
        
        period_result = {
            "cfo": cfo,
            "cfi": cfi,
            "cff": cff,
            "net_change": net_change,
            "ending_cash": ending_cash,
            "beginning_cash": beginning_cash,
        }
        
        # Check 1: Net Change ≈ CFO + CFI + CFF
        if cfo is not None and cfi is not None and cff is not None and net_change is not None:
            sum_cf = cfo + cfi + cff
            difference = abs(net_change - sum_cf)
            passes_cf = difference <= CF_TOLERANCE_ABSOLUTE
            
            period_result["cf_sum"] = sum_cf
            period_result["cf_difference"] = difference
            period_result["cf_passes"] = passes_cf
            
            if not passes_cf:
                all_pass = False
                logger.warning(
                    f"Cash flow reconciliation failed for {period}: "
                    f"Net Change={net_change}, CFO+CFI+CFF={sum_cf}, "
                    f"Difference={difference}"
                )
            else:
                any_pass = True
        else:
            period_result["cf_sum"] = None
            period_result["cf_difference"] = None
            period_result["cf_passes"] = None
            period_result["cf_reason"] = "Missing required line items"
        
        # Check 2: Ending Cash − Beginning Cash ≈ Net Change
        if ending_cash is not None and beginning_cash is not None and net_change is not None:
            cash_change = ending_cash - beginning_cash
            difference = abs(net_change - cash_change)
            passes_cash = difference <= CF_TOLERANCE_ABSOLUTE
            
            period_result["cash_change"] = cash_change
            period_result["cash_difference"] = difference
            period_result["cash_passes"] = passes_cash
            
            if not passes_cash:
                all_pass = False
                logger.warning(
                    f"Cash reconciliation failed for {period}: "
                    f"Net Change={net_change}, Cash Change={cash_change}, "
                    f"Difference={difference}"
                )
            else:
                any_pass = True
        else:
            period_result["cash_change"] = None
            period_result["cash_difference"] = None
            period_result["cash_passes"] = None
            period_result["cash_reason"] = "Missing required line items"
        
        # Overall pass for this period
        period_result["passes"] = (
            period_result.get("cf_passes") is True
            and period_result.get("cash_passes") is True
        )
        
        results["periods"][period] = period_result
    
    if all_pass:
        results["status"] = "pass"
        results["resolution"] = "All periods reconcile within tolerance"
    elif any_pass:
        results["status"] = "partial"
        results["resolution"] = "Some periods reconcile, others require review"
    else:
        results["status"] = "fail"
        results["resolution"] = "Prefer direct net cash totals if present; re-check consolidated selector"
    
    return results


def reconcile_is_to_cf(
    income_statement: Dict[str, Any],
    cash_flow: Dict[str, Any],
    periods: List[str],
) -> Dict[str, Any]:
    """
    Reconcile Income Statement Net Income to Cash Flow Net Income.
    
    Args:
        income_statement: Income statement dictionary with line_items
        cash_flow: Cash flow statement dictionary with line_items
        periods: List of period end dates
        
    Returns:
        Dictionary with reconciliation results
    """
    is_line_items = income_statement.get("line_items", [])
    cf_line_items = cash_flow.get("line_items", [])
    
    results = {
        "status": "pass",
        "periods": {},
        "resolution": "",
    }
    
    all_pass = True
    any_pass = False
    
    for period in periods:
        is_net_income = _get_line_item_value(is_line_items, IS_NET_INCOME, period)
        # Note: CF Net Income might be in a different role, but typically it's the same
        # For now, we'll check if there's a NetIncomeLoss tag in CF
        # This is a simplified check - in practice, CF might have NetIncomeLoss separately
        cf_net_income = None
        for item in cf_line_items:
            tag = item.get("tag", "").lower()
            if "netincomeloss" in tag or "netincome" in tag:
                periods_dict = item.get("periods", {})
                cf_net_income = periods_dict.get(period)
                break
        
        if is_net_income is None or cf_net_income is None:
            results["periods"][period] = {
                "is_net_income": is_net_income,
                "cf_net_income": cf_net_income,
                "difference": None,
                "passes": False,
                "reason": "Missing required line items",
            }
            all_pass = False
            continue
        
        difference = abs(is_net_income - cf_net_income)
        # Use relative tolerance (0.1% of net income)
        tolerance = abs(is_net_income) * 0.001 if is_net_income != 0 else CF_TOLERANCE_ABSOLUTE
        passes = difference <= tolerance
        
        results["periods"][period] = {
            "is_net_income": is_net_income,
            "cf_net_income": cf_net_income,
            "difference": difference,
            "passes": passes,
        }
        
        if passes:
            any_pass = True
        else:
            all_pass = False
            logger.warning(
                f"IS to CF reconciliation failed for {period}: "
                f"IS Net Income={is_net_income}, CF Net Income={cf_net_income}, "
                f"Difference={difference}"
            )
    
    if all_pass:
        results["status"] = "pass"
        results["resolution"] = "All periods reconcile within tolerance"
    elif any_pass:
        results["status"] = "partial"
        results["resolution"] = "Some periods reconcile, others require review"
    else:
        results["status"] = "fail"
        results["resolution"] = "Re-check consolidated selector for Net Income tags"
    
    return results


def reconcile_all_statements(
    statements: Dict[str, Any],
    periods: List[str],
) -> Dict[str, Any]:
    """
    Run all reconciliation checks.
    
    Args:
        statements: Dictionary with income_statement, balance_sheet, cash_flow_statement
        periods: List of period end dates
        
    Returns:
        Dictionary with all reconciliation results
    """
    income_statement = statements.get("income_statement", {})
    balance_sheet = statements.get("balance_sheet", {})
    cash_flow = statements.get("cash_flow_statement", {})
    
    reconciliation = {
        "balance_sheet": reconcile_balance_sheet(balance_sheet, periods),
        "cash_flow": reconcile_cash_flow(cash_flow, balance_sheet, periods),
        "is_to_cf": reconcile_is_to_cf(income_statement, cash_flow, periods),
    }
    
    # Overall status
    all_statuses = [
        reconciliation["balance_sheet"]["status"],
        reconciliation["cash_flow"]["status"],
        reconciliation["is_to_cf"]["status"],
    ]
    
    if all(s == "pass" for s in all_statuses):
        reconciliation["overall_status"] = "pass"
    elif any(s == "fail" for s in all_statuses):
        reconciliation["overall_status"] = "fail"
    else:
        reconciliation["overall_status"] = "partial"
    
    return reconciliation

