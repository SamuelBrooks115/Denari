"""
json_normalizer.py — Utility for Normalizing Valuation JSON Data

Purpose:
- Normalize CAPEX and Share Repurchases values to always be negative
- Ensure all other fields remain exactly as provided
- Can be applied before saving or processing project JSON data

Usage:
    from app.utils.json_normalizer import normalize_project_json
    
    normalized_data = normalize_project_json(project_data)
"""

from typing import Dict, Any, Union


def ensure_negative_value(value: Union[str, int, float, None]) -> Union[str, int, float, None]:
    """
    Ensure a value is always negative (for CAPEX and Share Repurchases).
    
    Rules:
    - If value is None or empty string, return as-is
    - If value is already negative, keep it as-is
    - If value is positive, make it negative
    
    Args:
        value: The value to normalize (can be string, int, float, or None)
        
    Returns:
        Normalized value (always negative if numeric, or original if None/empty)
    """
    if value is None:
        return None
    
    # Handle string values
    if isinstance(value, str):
        if value == "" or value.strip() == "":
            return value
        try:
            num_value = float(value)
            if num_value < 0:
                return value  # Already negative, return as-is
            # Positive value, make it negative
            return str(-abs(num_value))
        except (ValueError, TypeError):
            return value  # Not a number, return as-is
    
    # Handle numeric values
    if isinstance(value, (int, float)):
        if value < 0:
            return value  # Already negative, return as-is
        # Positive value, make it negative
        return -abs(value)
    
    # Unknown type, return as-is
    return value


def normalize_project_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize project JSON data to ensure CAPEX and Share Repurchases are always negative.
    
    This function:
    1. Normalizes cashFlow.capex.value to be negative
    2. Normalizes cashFlow.shareRepurchases to be negative
    3. Normalizes bearScenario.capex.value to be negative
    4. Normalizes bullScenario.capex.value to be negative
    5. Leaves all other fields exactly as provided
    
    Args:
        data: The project JSON data dictionary
        
    Returns:
        Normalized project JSON data dictionary
    """
    # Create a deep copy to avoid modifying the original
    normalized = data.copy()
    
    # Normalize cashFlow.capex.value
    if "cashFlow" in normalized and isinstance(normalized["cashFlow"], dict):
        if "capex" in normalized["cashFlow"] and isinstance(normalized["cashFlow"]["capex"], dict):
            if "value" in normalized["cashFlow"]["capex"]:
                normalized["cashFlow"]["capex"]["value"] = ensure_negative_value(
                    normalized["cashFlow"]["capex"]["value"]
                )
        
        # Normalize cashFlow.shareRepurchases
        if "shareRepurchases" in normalized["cashFlow"]:
            normalized["cashFlow"]["shareRepurchases"] = ensure_negative_value(
                normalized["cashFlow"]["shareRepurchases"]
            )
    
    # Normalize bearScenario.capex.value
    if "bearScenario" in normalized and isinstance(normalized["bearScenario"], dict):
        if "capex" in normalized["bearScenario"] and isinstance(normalized["bearScenario"]["capex"], dict):
            if "value" in normalized["bearScenario"]["capex"]:
                normalized["bearScenario"]["capex"]["value"] = ensure_negative_value(
                    normalized["bearScenario"]["capex"]["value"]
                )
    
    # Normalize bullScenario.capex.value
    if "bullScenario" in normalized and isinstance(normalized["bullScenario"], dict):
        if "capex" in normalized["bullScenario"] and isinstance(normalized["bullScenario"]["capex"], dict):
            if "value" in normalized["bullScenario"]["capex"]:
                normalized["bullScenario"]["capex"]["value"] = ensure_negative_value(
                    normalized["bullScenario"]["capex"]["value"]
                )
    
    return normalized

