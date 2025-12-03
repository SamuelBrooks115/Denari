"""
parser.py — JSON format normalization utilities.

Parses single-year and multi-year structured output JSON files into a unified
in-memory structure for validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json_file(file_path: str | Path) -> Dict[str, Any]:
    """
    Load JSON file from path.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON dictionary
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def normalize_single_year(
    json_data: Dict[str, Any],
    include_computed: bool = True,
) -> Dict[str, Any]:
    """
    Normalize single-year structured output format.
    
    Expected structure:
    {
        "metadata": {...},
        "statements": {
            "income_statement": {
                "line_items": [...]
            },
            "balance_sheet": {
                "line_items": [...]
            },
            "cash_flow_statement": {
                "line_items": [...]
            }
        }
    }
    
    Args:
        json_data: Single-year JSON structure
        
    Returns:
        Normalized structure: {
            "income_statement": [line_items...],
            "balance_sheet": [line_items...],
            "cash_flow_statement": [line_items...]
        }
    """
    normalized: Dict[str, List[Dict[str, Any]]] = {
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow_statement": [],
    }
    
    statements = json_data.get("statements", {})
    
    for statement_type in normalized.keys():
        statement_data = statements.get(statement_type, {})
        line_items = statement_data.get("line_items", [])
        
        # Normalize each line item to include all fields
        for item in line_items:
            normalized_item = {
                "tag": item.get("tag", ""),
                "label": item.get("label", ""),
                "model_role": item.get("model_role", ""),
                "llm_classification": item.get("llm_classification", {}),
                "periods": item.get("periods", {}),
                "variable_status": item.get("variable_status", "direct"),  # New field
                "computation_method": item.get("computation_method", ""),  # New field
                "supporting_tags": item.get("supporting_tags", []),  # New field
            }
            normalized[statement_type].append(normalized_item)
    
    result: Dict[str, Any] = {"statements": normalized}
    
    # Include computed_variables if present
    if include_computed and "computed_variables" in json_data:
        result["computed_variables"] = json_data["computed_variables"]
    
    return result


def normalize_multi_year(
    json_data: Dict[str, Any],
    include_computed: bool = True,
) -> Dict[str, Any]:
    """
    Normalize multi-year structured output format.
    
    Expected structure:
    {
        "company": {...},
        "filings": [
            {
                "fiscal_year": 2024,
                "statements": {
                    "income_statement": {
                        "line_items": [...]
                    },
                    ...
                }
            },
            ...
        ]
    }
    
    Args:
        json_data: Multi-year JSON structure
        
    Returns:
        Normalized structure aggregating all filings (most recent first)
    """
    normalized: Dict[str, List[Dict[str, Any]]] = {
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow_statement": [],
    }
    
    filings = json_data.get("filings", [])
    
    # Process filings in order (most recent first typically)
    for filing in filings:
        statements = filing.get("statements", {})
        
        for statement_type in normalized.keys():
            statement_data = statements.get(statement_type, {})
            line_items = statement_data.get("line_items", [])
            
            for item in line_items:
                # Check if we already have this tag (from a more recent filing)
                existing_item = next(
                    (existing for existing in normalized[statement_type]
                     if existing.get("tag") == item.get("tag")),
                    None
                )
                
                if existing_item is None:
                    # New tag, add it
                    normalized_item = {
                        "tag": item.get("tag", ""),
                        "label": item.get("label", ""),
                        "model_role": item.get("model_role", ""),
                        "llm_classification": item.get("llm_classification", {}),
                        "periods": item.get("periods", {}),
                        "variable_status": item.get("variable_status", "direct"),  # New field
                        "computation_method": item.get("computation_method", ""),  # New field
                        "supporting_tags": item.get("supporting_tags", []),  # New field
                        "fiscal_year": filing.get("fiscal_year"),
                    }
                    normalized[statement_type].append(normalized_item)
                else:
                    # Merge periods from this filing into existing item
                    existing_periods = existing_item.get("periods", {})
                    new_periods = item.get("periods", {})
                    existing_periods.update(new_periods)
    
    return normalized


def parse_structured_output(file_path: str | Path) -> Dict[str, Any]:
    """
    Auto-detect format and parse structured output JSON.
    
    Args:
        file_path: Path to JSON file (single-year or multi-year)
        
    Returns:
        Normalized structure with statements and computed_variables
    """
    json_data = load_json_file(file_path)
    
    # Detect format: multi-year has "filings" array, single-year has "statements"
    if "filings" in json_data:
        return normalize_multi_year(json_data)
    elif "statements" in json_data:
        return normalize_single_year(json_data)
    else:
        raise ValueError(
            "Unknown JSON format: expected 'filings' (multi-year) or 'statements' (single-year)"
        )

