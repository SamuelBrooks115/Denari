"""
validator.py — Core validation logic for tag classification.

Implements candidate finding, ranking, and selection for required variables.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.core.model_role_map import (
    BS_DEBT_CURRENT,
    BS_DEBT_NONCURRENT,
    get_model_role_flags,
)
from app.validation.role_map import (
    COMPUTED_VARIABLES,
    get_expected_roles,
    get_statement_type,
    get_all_required_variables,
)
from app.validation.fallback_computation import apply_fallback_computation


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


def find_candidates(
    variable_name: str,
    normalized_data: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Find all candidate line items for a required variable.
    
    Now supports:
    - Direct tags (model_role matches)
    - Computed variables (variable_status="computed" or "proxy")
    
    Args:
        variable_name: Name of required variable
        normalized_data: Normalized statement data
        
    Returns:
        List of candidate line items (with added metadata)
    """
    expected_roles = get_expected_roles(variable_name)
    statement_type = get_statement_type(variable_name)
    
    if not statement_type or not expected_roles:
        return []
    
    # Handle both old format (Dict[str, List]) and new format (Dict[str, Dict[str, List]])
    if "statements" in normalized_data:
        line_items = normalized_data["statements"].get(statement_type, [])
    else:
        line_items = normalized_data.get(statement_type, [])
    candidates = []
    
    for item in line_items:
        model_role = item.get("model_role", "")
        llm_classification = item.get("llm_classification", {})
        best_fit_role = llm_classification.get("best_fit_role", "")
        confidence = llm_classification.get("confidence", 0.0)
        variable_status = item.get("variable_status", "direct")  # "direct", "computed", or "proxy"
        
        # Check if model_role or llm_classification.best_fit_role matches expected
        matches = False
        matched_role = None
        
        if model_role in expected_roles:
            matches = True
            matched_role = model_role
        elif best_fit_role in expected_roles:
            matches = True
            matched_role = best_fit_role
        
        if matches:
            # Filter out broad liability rollups for Accounts Payable
            if variable_name == "Accounts Payable":
                tag = (item.get("tag") or "").lower()
                label = (item.get("label") or "").lower()
                
                # Block broad liability rollups
                rollup_indicators = [
                    "liabilitiescurrent",
                    "liabilitiesnoncurrent",
                    "liabilities",
                    "totalliabilities",
                    "liabilitiesandstockholdersequity",
                ]
                
                # If tag is a rollup, exclude it
                if any(ri in tag for ri in rollup_indicators):
                    # Only allow if label explicitly says "payable" (not just "liabilities")
                    if "payable" not in label:
                        continue  # Skip this candidate
            
            # Get flags for ranking
            flags = get_model_role_flags(matched_role or model_role)
            
            # Get latest period value
            periods = item.get("periods", {})
            latest_value = get_latest_period_value(periods)
            
            candidate = {
                **item,
                "matched_role": matched_role,
                "confidence": confidence,
                "variable_status": variable_status,
                "is_core_3_statement": flags.get("is_core_3_statement", False),
                "is_dcf_key": flags.get("is_dcf_key", False),
                "latest_value": latest_value,
                "latest_value_abs": abs(latest_value) if latest_value is not None else 0.0,
            }
            candidates.append(candidate)
    
    return candidates


def rank_candidates(candidates: List[Dict[str, Any]], variable_name: str = "") -> List[Dict[str, Any]]:
    """
    Rank candidates by priority:
    1. is_core_3_statement (True first)
    2. is_dcf_key (True first)
    3. For Accounts Payable: direct AP tags outrank combined AP+accrued tags
    4. Highest llm_classification.confidence
    5. Largest absolute value in most recent period
    
    Args:
        candidates: List of candidate line items
        variable_name: Optional variable name for special ranking rules
        
    Returns:
        Ranked list (best first)
    """
    def sort_key(candidate: Dict[str, Any]) -> Tuple[bool, bool, bool, float, float]:
        tag = (candidate.get("tag") or "").lower()
        model_role = candidate.get("model_role", "")
        
        # Special ranking for Accounts Payable
        is_direct_ap = False
        is_combined_ap = False
        if variable_name == "Accounts Payable":
            # Direct AP tags (preferred)
            direct_ap_tags = ["accountspayablecurrent", "accountspayable", "accountspayabletrade", "tradeaccountspayablecurrent"]
            is_direct_ap = any(dt in tag for dt in direct_ap_tags) or model_role == "BS_ACCOUNTS_PAYABLE"
            
            # Combined AP+Accrued tags (acceptable but lower priority)
            combined_tags = ["accountspayableandaccruedliabilitiescurrent", "accountspayableandaccruedliabilities"]
            is_combined_ap = any(ct in tag for ct in combined_tags) or model_role == "BS_AP_AND_ACCRUED"
        
        return (
            not candidate.get("is_core_3_statement", False),  # False first (True is better)
            not candidate.get("is_dcf_key", False),  # False first (True is better)
            not is_direct_ap if variable_name == "Accounts Payable" else False,  # Direct AP first
            is_combined_ap if variable_name == "Accounts Payable" else False,  # Combined AP after direct
            -candidate.get("confidence", 0.0),  # Negative for descending
            -candidate.get("latest_value_abs", 0.0),  # Negative for descending
        )
    
    return sorted(candidates, key=sort_key)


def validate_variable(
    variable_name: str,
    normalized_data: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Validate a single required variable.
    
    Supports direct classification, computed fallback, and proxy values.
    
    Args:
        variable_name: Name of required variable
        normalized_data: Normalized statement data
        
    Returns:
        Validation result dictionary with status: PASS (direct/computed/proxy) or FAIL
    """
    expected_roles = get_expected_roles(variable_name)
    statement_type = get_statement_type(variable_name)
    
    # Find all candidates
    candidates = find_candidates(variable_name, normalized_data)
    
    # Rank candidates
    ranked_candidates = rank_candidates(candidates, variable_name)
    
    # Special handling for Debt Amount: check computed_variables
    if variable_name == "Debt Amount" and not ranked_candidates:
        # Check if we have direct debt roles in normalized_data
        has_debt_roles = any(
            li.get("model_role") in (BS_DEBT_CURRENT, BS_DEBT_NONCURRENT)
            for stmt_items in normalized_data.get("statements", {}).values()
            for li in stmt_items
        )
        
        if has_debt_roles:
            # Direct roles exist, should have been found by find_candidates
            # Continue to normal flow
            pass
        else:
            # Check computed_variables
            computed_vars = normalized_data.get("computed_variables", {})
            debt_computed = computed_vars.get("DebtAmount", {})
            
            if debt_computed.get("status") == "computed":
                periods = debt_computed.get("periods", {})
                latest_value = get_latest_period_value(periods) if periods else None
                
                return {
                    "variable": variable_name,
                    "statement_type": statement_type,
                    "expected_roles": expected_roles,
                    "status": "PASS (computed)",
                    "reason": debt_computed.get("reason", "Computed from debt roles"),
                    "chosen": {
                        "tag": "COMPUTED_BS_DEBT_AMOUNT",
                        "label": "Computed: Debt Amount",
                        "model_role": BS_DEBT_NONCURRENT,
                        "matched_role": BS_DEBT_NONCURRENT,
                        "confidence": 1.0,
                        "periods_found": list(periods.keys()),
                        "latest_value": latest_value,
                        "computation_method": debt_computed.get("reason", ""),
                        "supporting_tags": debt_computed.get("supporting", []),
                        "source": "computed",
                    },
                    "alternates": [],
                }
    
    # If no direct candidates found, try fallback computation
    if not ranked_candidates:
        fallback_result = apply_fallback_computation(variable_name, normalized_data)
        
        if fallback_result:
            # Fallback computation succeeded
            source = fallback_result.get("source", "computed")
            status_prefix = "PASS"
            if source == "computed":
                status_prefix = "PASS (computed)"
            elif source == "proxy":
                status_prefix = "PASS (proxy)"
            
            return {
                "variable": variable_name,
                "statement_type": statement_type,
                "expected_roles": expected_roles,
                "status": status_prefix,
                "reason": f"Valid {source} value found",
                "chosen": {
                    "tag": None,
                    "label": f"Computed/Proxy: {fallback_result.get('computation_method', '')}",
                    "model_role": None,
                    "matched_role": None,
                    "confidence": 1.0,
                    "periods_found": [],
                    "latest_value": fallback_result.get("value"),
                    "computation_method": fallback_result.get("computation_method"),
                    "components": fallback_result.get("components", {}),
                    "source": source,
                },
                "alternates": [],
            }
        
        # No fallback available
        computed_note = COMPUTED_VARIABLES.get(variable_name, "")
        reason = "No candidates found - variable missing or mis-tagged"
        if computed_note:
            reason += f". Note: {computed_note}"
        
        return {
            "variable": variable_name,
            "statement_type": statement_type,
            "expected_roles": expected_roles,
            "status": "FAIL",
            "reason": reason,
            "chosen": None,
            "alternates": [],
        }
    
    chosen = ranked_candidates[0]
    alternates = ranked_candidates[1:5]  # Top 5 alternates
    
    # Check if chosen has sufficient confidence/quality
    confidence = chosen.get("confidence", 0.0)
    model_role = chosen.get("model_role", "")
    matched_role = chosen.get("matched_role", "")
    
    # Determine status based on variable_status
    variable_status = chosen.get("variable_status", "direct")
    
    if variable_status == "computed":
        status = "PASS (computed)"
        reason = "Valid computed value found"
    elif variable_status == "proxy":
        status = "PASS (proxy)"
        reason = "Valid proxy value found"
    else:
        status = "PASS (direct)"
        reason = "Valid candidate found"
    
    # Override to FAIL if quality checks fail
    if not matched_role:
        status = "FAIL"
        reason = "No matching role found in model_role or llm_classification"
    elif confidence < 0.5 and not model_role and variable_status == "direct":
        status = "FAIL"
        reason = f"Low LLM confidence ({confidence:.2f}) and no model_role"
    elif not chosen.get("latest_value"):
        status = "FAIL"
        reason = "No period values found"
    
    # Extract period info
    periods = chosen.get("periods", {})
    period_dates = sorted(periods.keys(), reverse=True)[:3]  # Most recent 3
    
    # Build chosen dict with computed/proxy metadata if applicable
    chosen_dict = {
        "tag": chosen.get("tag", ""),
        "label": chosen.get("label", ""),
        "model_role": model_role,
        "matched_role": matched_role,
        "confidence": confidence,
        "periods_found": period_dates,
        "latest_value": chosen.get("latest_value"),
    }
    
    # Add computed/proxy metadata if present
    if variable_status in ["computed", "proxy"]:
        chosen_dict["computation_method"] = chosen.get("computation_method", "")
        chosen_dict["supporting_tags"] = chosen.get("supporting_tags", [])
        chosen_dict["source"] = variable_status
    
    return {
        "variable": variable_name,
        "statement_type": statement_type,
        "expected_roles": expected_roles,
        "status": status,
        "reason": reason if status == "FAIL" else reason,
        "chosen": chosen_dict,
        "alternates": [
            {
                "tag": alt.get("tag", ""),
                "label": alt.get("label", ""),
                "model_role": alt.get("model_role", ""),
                "confidence": alt.get("confidence", 0.0),
            }
            for alt in alternates
        ],
    }


def validate_all_variables(
    normalized_data: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Validate all required variables.
    
    Args:
        normalized_data: Normalized statement data
        
    Returns:
        List of validation results
    """
    required_variables = get_all_required_variables()
    results = []
    
    for variable in required_variables:
        result = validate_variable(variable, normalized_data)
        results.append(result)
    
    return results

