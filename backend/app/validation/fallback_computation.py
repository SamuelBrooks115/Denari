"""
fallback_computation.py — Post-processing fallback logic for computed DCF variables.

When LLM classification fails to find a direct tag match, this module computes
the required variable from available components.

Examples:
- Operating Costs = COGS + SG&A + R&D + other operating expenses
- EBITDA = Operating Income + Depreciation & Amortization
- Debt Amount = Debt Current + Debt Noncurrent
- Accrued Expenses = (Accounts Payable + Accrued Liabilities Combined) - Accounts Payable
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.core.model_role_map import (
    BS_ACCOUNTS_PAYABLE,
    BS_ACCRUED_LIABILITIES,
    BS_AP_AND_ACCRUED,
    BS_DEBT_CURRENT,
    BS_DEBT_NONCURRENT,
    CF_DEPRECIATION,
    IS_COGS,
    IS_D_AND_A,
    IS_EBITDA,
    IS_OPERATING_EXPENSE,
    IS_OPERATING_INCOME,
    IS_RD_EXPENSE,
    IS_SGA_EXPENSE,
)


def get_latest_period_value(periods: Dict[str, Any]) -> Optional[float]:
    """
    Extract the most recent period value from periods dictionary.
    
    Args:
        periods: Dictionary mapping date strings to values
        
    Returns:
        Most recent value as float, or None if no values found
    """
    if not periods:
        return None
    
    # Sort dates and get most recent
    sorted_dates = sorted(periods.keys(), reverse=True)
    if not sorted_dates:
        return None
    
    latest_date = sorted_dates[0]
    value = periods[latest_date]
    
    # Handle different value formats
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, dict):
        # Sometimes values are nested in a dict
        return float(value.get("value", 0))
    return None


def find_items_by_role(
    normalized_data: Dict[str, List[Dict[str, Any]]],
    role: str,
    statement_type: str,
) -> List[Dict[str, Any]]:
    """
    Find all line items with a specific model role.
    
    Args:
        normalized_data: Normalized statement data
        role: Model role to search for
        statement_type: Statement type to search in
        
    Returns:
        List of matching line items
    """
    line_items = normalized_data.get(statement_type, [])
    matches = []
    
    for item in line_items:
        model_role = item.get("model_role", "")
        llm_classification = item.get("llm_classification", {})
        best_fit_role = llm_classification.get("best_fit_role", "")
        
        if model_role == role or best_fit_role == role:
            matches.append(item)
    
    return matches


def compute_operating_costs(
    normalized_data: Dict[str, List[Dict[str, Any]]],
) -> Optional[Tuple[float, str, Dict[str, Any]]]:
    """
    Compute Operating Costs from components if direct tag not found.
    
    Formula: Operating Costs = COGS + SG&A + R&D + other operating expenses
    
    Args:
        normalized_data: Normalized statement data
        
    Returns:
        Tuple of (computed_value, computation_method, components_dict) or None
    """
    statement_type = "income_statement"
    
    # Try to find direct match first
    direct_matches = find_items_by_role(normalized_data, IS_OPERATING_EXPENSE, statement_type)
    if direct_matches:
        return None  # Direct match exists, no computation needed
    
    # Find components
    cogs_items = find_items_by_role(normalized_data, IS_COGS, statement_type)
    sga_items = find_items_by_role(normalized_data, IS_SGA_EXPENSE, statement_type)
    rd_items = find_items_by_role(normalized_data, IS_RD_EXPENSE, statement_type)
    
    # Get latest values for each component
    components = {}
    total = 0.0
    
    if cogs_items:
        cogs_value = get_latest_period_value(cogs_items[0].get("periods", {}))
        if cogs_value is not None:
            components["COGS"] = cogs_value
            total += cogs_value
    
    if sga_items:
        sga_value = get_latest_period_value(sga_items[0].get("periods", {}))
        if sga_value is not None:
            components["SG&A"] = sga_value
            total += sga_value
    
    if rd_items:
        rd_value = get_latest_period_value(rd_items[0].get("periods", {}))
        if rd_value is not None:
            components["R&D"] = rd_value
            total += rd_value
    
    if not components:
        return None  # No components found
    
    method = f"Computed from: {', '.join(components.keys())}"
    return (total, method, components)


def compute_ebitda(
    normalized_data: Dict[str, List[Dict[str, Any]]],
) -> Optional[Tuple[float, str, Dict[str, Any]]]:
    """
    Compute EBITDA from components if direct tag not found.
    
    Formula: EBITDA = Operating Income + Depreciation & Amortization
    
    Args:
        normalized_data: Normalized statement data
        
    Returns:
        Tuple of (computed_value, computation_method, components_dict) or None
    """
    statement_type = "income_statement"
    
    # Try to find direct match first
    direct_matches = find_items_by_role(normalized_data, IS_EBITDA, statement_type)
    if direct_matches:
        return None  # Direct match exists, no computation needed
    
    # Find components
    operating_income_items = find_items_by_role(normalized_data, IS_OPERATING_INCOME, statement_type)
    da_items = find_items_by_role(normalized_data, IS_D_AND_A, statement_type)
    
    # Also check cash flow statement for depreciation
    if not da_items:
        cf_dep_items = find_items_by_role(normalized_data, CF_DEPRECIATION, "cash_flow_statement")
        if cf_dep_items:
            da_items = cf_dep_items
    
    # Get latest values
    components = {}
    
    if not operating_income_items:
        return None  # Need operating income
    
    operating_income = get_latest_period_value(operating_income_items[0].get("periods", {}))
    if operating_income is None:
        return None
    
    components["Operating Income"] = operating_income
    
    if not da_items:
        return None  # Need D&A
    
    da_value = get_latest_period_value(da_items[0].get("periods", {}))
    if da_value is None:
        return None
    
    components["Depreciation & Amortization"] = da_value
    
    total = operating_income + da_value
    method = "Computed from: Operating Income + Depreciation & Amortization"
    
    return (total, method, components)


def _find_items_by_keywords(
    line_items: List[Dict[str, Any]],
    keywords: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    """Find line items matching any of the specified keywords in tag or label."""
    matches = []
    for item in line_items:
        label = (item.get("label") or "").lower()
        tag = (item.get("tag") or "").lower()
        if any(k.lower() in label for k in keywords) or any(k.lower() in tag for k in keywords):
            matches.append(item)
    return matches


def compute_debt_amount(
    normalized_data: Dict[str, List[Dict[str, Any]]],
) -> Optional[Tuple[float, str, Dict[str, Any]]]:
    """
    Compute total debt from current and noncurrent components (XBRL-first, deterministic).
    
    Formula: Debt Amount = Debt Current + Debt Noncurrent
    
    Priority:
      1) Combined debt tag (if exists): LongTermDebtAndCapitalLeaseObligations, Debt, TotalDebt
      2) Use role-classified candidates: BS_DEBT_CURRENT / BS_DEBT_NONCURRENT
      3) If missing, use keyword candidates (interest-bearing only, exclude operating leases)
      4) Sum by aligned periods
    
    Args:
        normalized_data: Normalized statement data
        
    Returns:
        Tuple of (computed_value, computation_method, components_dict) or None
    """
    statement_type = "balance_sheet"
    line_items = normalized_data.get(statement_type, [])
    
    # 1) Check for combined debt tags first
    combined_debt_tags = [
        "LongTermDebtAndCapitalLeaseObligations",
        "LongTermDebtAndFinanceLeaseObligations",
        "Debt",
        "TotalDebt",
        "LongTermDebt",  # Sometimes used as total
    ]
    
    for item in line_items:
        tag = (item.get("tag") or "").lower()
        label = (item.get("label") or "").lower()
        
        # Check if it's a combined debt tag
        if any(ct in tag for ct in [t.lower() for t in combined_debt_tags]):
            # Exclude if it's clearly operating lease
            if "operatinglease" in tag or "operating lease" in label:
                continue
            
            value = get_latest_period_value(item.get("periods", {}))
            if value is not None:
                return (
                    value,
                    f"Using combined debt tag: {item.get('tag')}",
                    {"Combined Debt": value},
                )
    
    # 2) Find components by role first
    current_debt_items = find_items_by_role(normalized_data, BS_DEBT_CURRENT, statement_type)
    noncurrent_debt_items = find_items_by_role(normalized_data, BS_DEBT_NONCURRENT, statement_type)
    
    # 3) Keyword fallback if roles missing - use curated allowlist
    if not current_debt_items:
        current_debt_items = _find_debt_items_by_allowlist(
            line_items,
            current_tags=[
                "LongTermDebtCurrent",
                "LongTermDebtAndCapitalLeaseObligationsCurrent",
                "LongTermDebtAndFinanceLeaseObligationsCurrent",
                "NotesPayableCurrent",
                "DebtCurrent",
                "ShortTermBorrowings",
                "CommercialPaper",
                "UnsecuredDebtCurrent",
                "SecuredDebtCurrent",
            ],
            current_keywords=[
                "short-term debt",
                "short term debt",
                "current debt",
                "long-term debt current",
                "current portion of long-term debt",
                "short-term borrowings",
                "notes payable current",
                "debt current",
            ],
        )
    
    if not noncurrent_debt_items:
        noncurrent_debt_items = _find_debt_items_by_allowlist(
            line_items,
            current_tags=[
                "LongTermDebtNoncurrent",
                "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
                "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
                "NotesPayableNoncurrent",
                "DebtNoncurrent",
                "LongTermDebt",
                "UnsecuredLongTermDebt",
                "SecuredLongTermDebt",
            ],
            current_keywords=[
                "long-term debt",
                "long term debt",
                "debt noncurrent",
                "notes payable noncurrent",
                "total long-term debt",
            ],
        )
    
    # Sum all current debt items
    current_total = 0.0
    current_components = {}
    for item in current_debt_items:
        value = get_latest_period_value(item.get("periods", {}))
        if value is not None:
            tag = item.get("tag", "Unknown")
            current_components[tag] = value
            current_total += value
    
    # Sum all noncurrent debt items
    noncurrent_total = 0.0
    noncurrent_components = {}
    for item in noncurrent_debt_items:
        value = get_latest_period_value(item.get("periods", {}))
        if value is not None:
            tag = item.get("tag", "Unknown")
            noncurrent_components[tag] = value
            noncurrent_total += value
    
    components = {**current_components, **noncurrent_components}
    total = current_total + noncurrent_total
    
    if not components:
        return None  # No debt components found
    
    # Build computation method string
    if len(current_components) > 0 and len(noncurrent_components) > 0:
        method = f"Computed from: {len(current_components)} current debt tag(s) + {len(noncurrent_components)} noncurrent debt tag(s)"
    elif len(current_components) > 0:
        method = f"Using current debt: {', '.join(list(current_components.keys())[:50])}"
    elif len(noncurrent_components) > 0:
        method = f"Using noncurrent debt: {', '.join(list(noncurrent_components.keys())[:50])}"
    else:
        method = "Computed from debt components"
    
    return (total, method, components)


def _find_debt_items_by_allowlist(
    line_items: List[Dict[str, Any]],
    current_tags: List[str],
    current_keywords: List[str],
) -> List[Dict[str, Any]]:
    """Find debt items using curated allowlist, excluding operating leases."""
    matches = []
    
    for item in line_items:
        tag = (item.get("tag") or "").lower()
        label = (item.get("label") or "").lower()
        
        # Exclude operating lease liabilities
        if "operatinglease" in tag or "operating lease" in label:
            continue
        
        # Check exact tag matches
        if any(ct.lower() in tag for ct in current_tags):
            matches.append(item)
            continue
        
        # Check keyword matches
        if any(kw.lower() in label or kw.lower() in tag for kw in current_keywords):
            # Additional exclusion: make sure it's not a cash flow activity
            if any(cf in tag or cf in label for cf in ["proceeds", "repayment", "issuancecosts"]):
                continue
            matches.append(item)
    
    return matches


def compute_accrued_expenses(
    normalized_data: Dict[str, List[Dict[str, Any]]],
) -> Optional[Tuple[float, str, Dict[str, Any]]]:
    """
    Compute Accrued Expenses from combined tag minus Accounts Payable.
    
    Formula: Accrued Expenses = (Accounts Payable + Accrued Liabilities Combined) - Accounts Payable
    
    Args:
        normalized_data: Normalized statement data
        
    Returns:
        Tuple of (computed_value, computation_method, components_dict) or None
    """
    statement_type = "balance_sheet"
    
    # Try to find direct match first
    direct_matches = find_items_by_role(normalized_data, BS_ACCRUED_LIABILITIES, statement_type)
    if direct_matches:
        return None  # Direct match exists, no computation needed
    
    # Find combined tag
    combined_items = find_items_by_role(normalized_data, BS_AP_AND_ACCRUED, statement_type)
    if not combined_items:
        return None  # No combined tag found
    
    # Find separate Accounts Payable
    ap_items = find_items_by_role(normalized_data, BS_ACCOUNTS_PAYABLE, statement_type)
    
    combined_value = get_latest_period_value(combined_items[0].get("periods", {}))
    if combined_value is None:
        return None
    
    components = {"Combined AP and Accrued": combined_value}
    
    if ap_items:
        # Can compute: Accrued = Combined - AP
        ap_value = get_latest_period_value(ap_items[0].get("periods", {}))
        if ap_value is not None:
            accrued_value = combined_value - ap_value
            components["Accounts Payable"] = ap_value
            method = "Computed from: (Accounts Payable + Accrued Combined) - Accounts Payable"
            return (accrued_value, method, components)
    
    # No separate AP found, use combined tag as proxy
    method = "Proxy: Using combined Accounts Payable and Accrued Liabilities tag"
    return (combined_value, method, components)


def apply_fallback_computation(
    variable_name: str,
    normalized_data: Dict[str, List[Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    """
    Apply fallback computation for a variable if direct classification failed.
    
    Args:
        variable_name: Name of required variable
        normalized_data: Normalized statement data
        
    Returns:
        Dictionary with computed value and metadata, or None if computation not possible
    """
    if variable_name == "Operating Costs / Margin":
        result = compute_operating_costs(normalized_data)
        if result:
            value, method, components = result
            return {
                "value": value,
                "computation_method": method,
                "components": components,
                "source": "computed",
            }
    
    elif variable_name == "EBITDA Margins / Costs":
        result = compute_ebitda(normalized_data)
        if result:
            value, method, components = result
            return {
                "value": value,
                "computation_method": method,
                "components": components,
                "source": "computed",
            }
    
    elif variable_name == "Debt Amount":
        result = compute_debt_amount(normalized_data)
        if result:
            value, method, components = result
            return {
                "value": value,
                "computation_method": method,
                "components": components,
                "source": "computed",
            }
    
    elif variable_name == "Accrued Expenses":
        result = compute_accrued_expenses(normalized_data)
        if result:
            value, method, components = result
            source = "proxy" if "Proxy" in method else "computed"
            return {
                "value": value,
                "computation_method": method,
                "components": components,
                "source": source,
            }
    
    return None

