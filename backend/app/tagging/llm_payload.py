"""
llm_payload.py — Build compact JSON payloads for LLM classification.

This module creates optimized payloads to send to the LLM for classification,
including only the essential fields needed for accurate tagging.
"""

from typing import Any, Dict, List

from app.tagging.models import FactLine


def build_classification_payload(statement_type: str, lines: List[FactLine]) -> Dict[str, Any]:
    """
    Build a compact JSON-safe payload to send to the LLM for classification.
    
    The payload includes only essential fields to keep token usage low while
    providing enough context for accurate classification.
    
    Args:
        statement_type: "IS", "BS", or "CF"
        lines: List of FactLine objects to classify
        
    Returns:
        Dictionary with statement_type and lines array, ready for JSON serialization
    """
    payload_lines = []
    
    for line in lines:
        # Build compact line representation
        line_dict: Dict[str, Any] = {
            "line_id": line.line_id,
            "label": line.label,
            "parent_label": line.parent_label,
            "concept_qname": line.concept_qname,
            "is_abstract": line.is_abstract,
        }
        
        # Add value_hint for context (scale, sign) but don't rely on it for classification
        if line.value is not None:
            line_dict["value_hint"] = line.value
        else:
            line_dict["value_hint"] = None
        
        # Add dimensions if present (helps identify segments)
        if line.dimensions:
            line_dict["dimensions"] = line.dimensions
        else:
            line_dict["dimensions"] = {}
        
        payload_lines.append(line_dict)
    
    return {
        "statement_type": statement_type,
        "lines": payload_lines,
    }

