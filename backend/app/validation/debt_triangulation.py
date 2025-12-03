"""
debt_triangulation.py — Multi-method Total Debt triangulation for Ford.

This module implements multiple independent methods to estimate Total Debt,
providing transparency and cross-validation for debt calculations.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import statistics

from app.core.logging import get_logger
from app.core.model_role_map import (
    BS_ACCOUNTS_PAYABLE,
    BS_ACCRUED_LIABILITIES,
    BS_AP_AND_ACCRUED,
    BS_DEBT_CURRENT,
    BS_DEBT_NONCURRENT,
    BS_LIABILITIES_CURRENT,
    BS_LIABILITIES_TOTAL,
    CF_DEBT_ISSUANCE,
    CF_DEBT_REPAYMENT,
    IS_INTEREST_EXPENSE,
)

logger = get_logger(__name__)


@dataclass
class DebtEstimate:
    """Data structure for storing a debt estimation method's result."""
    method_name: str
    value: Optional[float]
    components: Dict[str, float]
    assumptions: Dict[str, Any]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def _get_line_item_value(
    line_items: List[Dict[str, Any]],
    model_role: str,
    period: str,
) -> Optional[float]:
    """
    Extract value from line items by model_role and period.
    
    Args:
        line_items: List of line item dictionaries
        model_role: Model role to search for (e.g., "BS_DEBT_CURRENT")
        period: Period date string (e.g., "2024-12-31")
        
    Returns:
        Float value if found, None otherwise
    """
    for item in line_items:
        if item.get("model_role") == model_role:
            periods = item.get("periods", {})
            val = periods.get(period)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
    return None


def _extract_balance_sheet_dict(
    balance_sheet: Dict[str, Any],
    period: str,
) -> Dict[str, float]:
    """
    Extract balance sheet values as a normalized dictionary.
    
    Args:
        balance_sheet: Balance sheet dictionary with line_items
        period: Period date string
        
    Returns:
        Dictionary mapping normalized field names to values
    """
    line_items = balance_sheet.get("line_items", [])
    bs_dict = {}
    
    # Map model roles to normalized field names
    field_mapping = {
        BS_DEBT_CURRENT: "short_term_debt",
        BS_DEBT_NONCURRENT: "long_term_debt",
        BS_LIABILITIES_TOTAL: "total_liabilities",
        BS_LIABILITIES_CURRENT: "current_liabilities",
        BS_ACCOUNTS_PAYABLE: "accounts_payable",
        BS_ACCRUED_LIABILITIES: "accrued_expenses",
        BS_AP_AND_ACCRUED: "accounts_payable_and_accrued",
    }
    
    for model_role, field_name in field_mapping.items():
        value = _get_line_item_value(line_items, model_role, period)
        if value is not None:
            bs_dict[field_name] = value
    
    # Also search for other debt-related items by tag/label patterns
    debt_keywords = [
        "current_portion_long_term_debt",
        "finance_lease_liabilities_current",
        "finance_lease_liabilities_noncurrent",
        "other_interest_bearing_liabilities",
        "deferred_revenue",
        "income_taxes_payable",
        "other_current_liabilities",
        "operating_lease_liabilities_current",
        "operating_lease_liabilities_noncurrent",
        "pension_liabilities",
    ]
    
    # Search line items for additional fields by tag/label
    for item in line_items:
        tag = (item.get("tag", "") or "").lower()
        label = (item.get("label", "") or "").lower()
        model_role = item.get("model_role", "")
        
        # Skip if already mapped
        if model_role in field_mapping:
            continue
        
        # Check for additional debt-related fields
        for keyword in debt_keywords:
            if keyword.replace("_", "") in tag.replace("-", "").replace("_", "") or \
               keyword.replace("_", " ") in label:
                periods = item.get("periods", {})
                val = periods.get(period)
                if val is not None:
                    try:
                        bs_dict[keyword] = float(val)
                    except (ValueError, TypeError):
                        pass
                break
    
    return bs_dict


def estimate_debt_direct_sum(
    balance_sheet: Dict[str, Any],
    period: str,
) -> DebtEstimate:
    """
    Method 1: Direct Sum of Known Debt Buckets (Bottom-up).
    
    Sums explicitly labeled interest-bearing liabilities from the balance sheet.
    
    Args:
        balance_sheet: Balance sheet dictionary with line_items
        period: Period date string
        
    Returns:
        DebtEstimate with direct sum calculation
    """
    bs_dict = _extract_balance_sheet_dict(balance_sheet, period)
    
    components = {}
    warnings = []
    
    # Core debt components
    debt_fields = [
        "short_term_debt",
        "current_portion_long_term_debt",
        "long_term_debt",
        "finance_lease_liabilities_current",
        "finance_lease_liabilities_noncurrent",
        "other_interest_bearing_liabilities",
    ]
    
    total_debt = 0.0
    for field in debt_fields:
        value = bs_dict.get(field, 0.0)
        components[field] = value
        total_debt += value
        if field not in bs_dict:
            warnings.append(f"Missing field: {field} (treated as 0)")
    
    assumptions = {
        "description": "Direct sum of explicitly labeled interest-bearing liabilities",
        "includes": debt_fields,
        "excludes": [
            "accounts_payable",
            "accrued_expenses",
            "deferred_revenue",
            "operating_lease_liabilities",
            "pension_liabilities",
        ],
    }
    
    if total_debt == 0.0 and not any(components.values()):
        warnings.append("No debt components found - all fields missing or zero")
        return DebtEstimate(
            method_name="direct_sum",
            value=None,
            components=components,
            assumptions=assumptions,
            warnings=warnings,
        )
    
    return DebtEstimate(
        method_name="direct_sum",
        value=total_debt,
        components=components,
        assumptions=assumptions,
        warnings=warnings,
    )


def estimate_debt_balance_sheet_recon(
    balance_sheet: Dict[str, Any],
    period: str,
) -> DebtEstimate:
    """
    Method 2: Balance Sheet Reconstruction (Top-down).
    
    Starts from total_liabilities and subtracts non-interest-bearing liabilities.
    
    Args:
        balance_sheet: Balance sheet dictionary with line_items
        period: Period date string
        
    Returns:
        DebtEstimate with balance sheet reconstruction calculation
    """
    bs_dict = _extract_balance_sheet_dict(balance_sheet, period)
    
    components = {}
    warnings = []
    
    total_liab = bs_dict.get("total_liabilities", 0.0)
    components["total_liabilities"] = total_liab
    
    if total_liab == 0.0:
        warnings.append("total_liabilities is missing or zero")
        return DebtEstimate(
            method_name="balance_sheet_recon",
            value=None,
            components=components,
            assumptions={"description": "Top-down: Total Liabilities - Non-debt liabilities"},
            warnings=warnings,
        )
    
    # Non-debt liabilities to subtract
    non_debt_fields = [
        "accounts_payable",
        "accrued_expenses",
        "accounts_payable_and_accrued",  # If separate AP not available
        "deferred_revenue",
        "income_taxes_payable",
        "other_current_liabilities",
        "operating_lease_liabilities_current",
        "operating_lease_liabilities_noncurrent",
        "pension_liabilities",
    ]
    
    non_debt_total = 0.0
    for field in non_debt_fields:
        value = bs_dict.get(field, 0.0)
        components[field] = value
        non_debt_total += value
        if field not in bs_dict:
            warnings.append(f"Missing non-debt field: {field} (treated as 0)")
    
    # Handle case where AP+Accrued is combined but we also have separate values
    if "accounts_payable_and_accrued" in components and \
       ("accounts_payable" in components or "accrued_expenses" in components):
        # Don't double-count - prefer separate if available
        if "accounts_payable" in components or "accrued_expenses" in components:
            combined = components.pop("accounts_payable_and_accrued", 0.0)
            non_debt_total -= combined
            warnings.append("Excluded combined AP+Accrued to avoid double-counting with separate fields")
    
    debt_estimate = total_liab - non_debt_total
    
    # Sanity checks
    if debt_estimate < 0:
        warnings.append(f"Negative debt estimate ({debt_estimate:,.0f}) - possible missing non-debt fields")
    elif debt_estimate > total_liab:
        warnings.append(f"Debt estimate ({debt_estimate:,.0f}) exceeds total liabilities ({total_liab:,.0f})")
    
    assumptions = {
        "description": "Top-down: Total Liabilities - Non-interest-bearing liabilities",
        "formula": "total_liabilities - sum(non_debt_liabilities)",
        "non_debt_fields": non_debt_fields,
    }
    
    return DebtEstimate(
        method_name="balance_sheet_recon",
        value=debt_estimate if debt_estimate >= 0 else None,
        components=components,
        assumptions=assumptions,
        warnings=warnings,
    )


def estimate_debt_rollforward(
    prev_balance_sheet: Optional[Dict[str, Any]],
    curr_balance_sheet: Dict[str, Any],
    cash_flow: Optional[Dict[str, Any]],
    prev_period: Optional[str],
    curr_period: str,
) -> DebtEstimate:
    """
    Method 3: Debt Roll-Forward using Cash Flow Statement.
    
    Computes debt by rolling forward previous period debt using cash flow movements.
    
    Args:
        prev_balance_sheet: Previous period balance sheet (optional)
        curr_balance_sheet: Current period balance sheet
        cash_flow: Cash flow statement (optional)
        prev_period: Previous period date string (optional)
        curr_period: Current period date string
        
    Returns:
        DebtEstimate with roll-forward calculation
    """
    components = {}
    warnings = []
    
    if prev_balance_sheet is None or prev_period is None:
        warnings.append("Previous period balance sheet not available")
        return DebtEstimate(
            method_name="debt_rollforward",
            value=None,
            components=components,
            assumptions={"description": "Roll-forward: Previous Debt + Issuance - Repayment"},
            warnings=warnings,
        )
    
    if cash_flow is None:
        warnings.append("Cash flow statement not available")
        return DebtEstimate(
            method_name="debt_rollforward",
            value=None,
            components=components,
            assumptions={"description": "Roll-forward: Previous Debt + Issuance - Repayment"},
            warnings=warnings,
        )
    
    # Get previous period debt using Method 1
    prev_debt_est = estimate_debt_direct_sum(prev_balance_sheet, prev_period)
    prev_debt = prev_debt_est.value
    
    if prev_debt is None:
        warnings.append("Previous period debt could not be calculated")
        return DebtEstimate(
            method_name="debt_rollforward",
            value=None,
            components=components,
            assumptions={"description": "Roll-forward: Previous Debt + Issuance - Repayment"},
            warnings=warnings,
        )
    
    components["previous_period_debt"] = prev_debt
    
    # Extract cash flow line items
    cf_line_items = cash_flow.get("line_items", [])
    
    debt_issued = _get_line_item_value(cf_line_items, CF_DEBT_ISSUANCE, curr_period) or 0.0
    debt_repaid = _get_line_item_value(cf_line_items, CF_DEBT_REPAYMENT, curr_period) or 0.0
    
    components["debt_issued"] = debt_issued
    components["debt_repaid"] = debt_repaid
    
    # Look for finance lease principal payments and other debt movements
    finance_lease_payments = 0.0
    other_debt_movements = 0.0
    
    # Search for finance lease payments in cash flow
    for item in cf_line_items:
        tag = (item.get("tag", "") or "").lower()
        label = (item.get("label", "") or "").lower()
        if "finance" in tag or "finance" in label:
            if "lease" in tag or "lease" in label:
                if "payment" in tag or "payment" in label or "principal" in tag or "principal" in label:
                    periods = item.get("periods", {})
                    val = periods.get(curr_period)
                    if val is not None:
                        try:
                            finance_lease_payments = float(val)
                            components["finance_lease_principal_payments"] = finance_lease_payments
                        except (ValueError, TypeError):
                            pass
    
    components["other_debt_movements"] = other_debt_movements
    
    # Roll forward calculation
    rolled_forward = prev_debt + debt_issued - debt_repaid + other_debt_movements
    
    # Note: Finance lease principal payments are typically already reflected in debt balances,
    # so we don't add/subtract them separately unless they're explicitly separate
    
    components["rolled_forward_debt"] = rolled_forward
    
    assumptions = {
        "description": "Roll-forward: Previous Debt + Issuance - Repayment + Other Movements",
        "formula": "prev_debt + debt_issued - debt_repaid + other_movements",
        "assumes": "Cash flow line items fully capture all debt movements",
    }
    
    if debt_issued == 0.0 and debt_repaid == 0.0:
        warnings.append("No debt issuance or repayment found in cash flow statement")
    
    return DebtEstimate(
        method_name="debt_rollforward",
        value=rolled_forward,
        components=components,
        assumptions=assumptions,
        warnings=warnings,
    )


def estimate_debt_interest_implied(
    income_statement: Dict[str, Any],
    period: str,
    assumed_rate: Optional[float] = None,
) -> DebtEstimate:
    """
    Method 4: Interest-Expense-Implied Debt (Sanity Check).
    
    Estimates debt by dividing interest expense by an assumed interest rate.
    This is a rough cross-check, not a precise accounting measure.
    
    Args:
        income_statement: Income statement dictionary with line_items
        period: Period date string
        assumed_rate: Assumed interest rate (default: 0.06 = 6%)
        
    Returns:
        DebtEstimate with interest-implied calculation
    """
    components = {}
    warnings = []
    
    line_items = income_statement.get("line_items", [])
    interest_expense = _get_line_item_value(line_items, IS_INTEREST_EXPENSE, period)
    
    if interest_expense is None:
        warnings.append("interest_expense not found in income statement")
        return DebtEstimate(
            method_name="interest_implied",
            value=None,
            components=components,
            assumptions={"description": "Implied: Interest Expense / Assumed Interest Rate"},
            warnings=warnings,
        )
    
    if interest_expense == 0.0:
        warnings.append("interest_expense is zero")
        return DebtEstimate(
            method_name="interest_implied",
            value=0.0,
            components={"interest_expense": 0.0, "assumed_rate": assumed_rate or 0.06},
            assumptions={"description": "Implied: Interest Expense / Assumed Interest Rate"},
            warnings=warnings,
        )
    
    rate = assumed_rate or 0.06
    implied_debt = interest_expense / rate if rate > 0 else None
    
    components["interest_expense"] = interest_expense
    components["assumed_rate"] = rate
    components["implied_debt"] = implied_debt
    
    assumptions = {
        "description": "Rough cross-check: Interest Expense / Assumed Interest Rate",
        "formula": "interest_expense / assumed_rate",
        "note": "This is a high-level sanity check, not a precise accounting measure",
        "assumed_rate_source": "Default 6% (can be overridden)",
    }
    
    if interest_expense < 0:
        warnings.append("Negative interest expense - may indicate interest income netting")
    
    return DebtEstimate(
        method_name="interest_implied",
        value=implied_debt,
        components=components,
        assumptions=assumptions,
        warnings=warnings,
    )


def aggregate_debt_estimates(
    estimates: List[DebtEstimate],
) -> Dict[str, Any]:
    """
    Method 5: Aggregate and summarize all debt estimates.
    
    Computes summary statistics and recommends a value based on multiple methods.
    
    Args:
        estimates: List of DebtEstimate objects
        
    Returns:
        Dictionary with methods and summary statistics
    """
    # Filter out None values
    valid_estimates = [e for e in estimates if e.value is not None]
    
    if not valid_estimates:
        return {
            "methods": [e.to_dict() for e in estimates],
            "summary": {
                "min": None,
                "max": None,
                "median": None,
                "average": None,
                "recommended_value": None,
                "recommended_basis": "no_valid_estimates",
            },
        }
    
    values = [e.value for e in valid_estimates]
    
    summary = {
        "min": min(values),
        "max": max(values),
        "median": statistics.median(values),
        "average": statistics.mean(values),
        "recommended_value": statistics.median(values),
        "recommended_basis": "median_of_non_null_methods",
        "method_count": len(valid_estimates),
        "total_methods": len(estimates),
    }
    
    return {
        "methods": [e.to_dict() for e in estimates],
        "summary": summary,
    }


def triangulate_debt_for_period(
    statements: Dict[str, Any],
    period: str,
    prev_statements: Optional[Dict[str, Any]] = None,
    prev_period: Optional[str] = None,
    assumed_interest_rate: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Run all debt triangulation methods for a single period.
    
    Args:
        statements: Dictionary with balance_sheet, income_statement, cash_flow_statement
        period: Current period date string
        prev_statements: Previous period statements (optional, for roll-forward)
        prev_period: Previous period date string (optional)
        assumed_interest_rate: Assumed interest rate for Method 4 (optional)
        
    Returns:
        Dictionary with aggregated debt estimates
    """
    balance_sheet = statements.get("balance_sheet", {})
    income_statement = statements.get("income_statement", {})
    cash_flow = statements.get("cash_flow_statement", {})
    
    estimates = []
    
    # Method 1: Direct Sum
    est1 = estimate_debt_direct_sum(balance_sheet, period)
    estimates.append(est1)
    
    # Method 2: Balance Sheet Reconstruction
    est2 = estimate_debt_balance_sheet_recon(balance_sheet, period)
    estimates.append(est2)
    
    # Method 3: Roll-Forward (if previous period available)
    if prev_statements and prev_period:
        prev_bs = prev_statements.get("balance_sheet", {})
        est3 = estimate_debt_rollforward(prev_bs, balance_sheet, cash_flow, prev_period, period)
        estimates.append(est3)
    
    # Method 4: Interest-Implied
    est4 = estimate_debt_interest_implied(income_statement, period, assumed_interest_rate)
    estimates.append(est4)
    
    # Aggregate all estimates
    result = aggregate_debt_estimates(estimates)
    
    return result


