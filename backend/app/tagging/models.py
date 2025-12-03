"""
models.py — Data models for financial line item classification.

This module defines the FactLine dataclass and helper functions for normalizing
raw Arelle fact JSON into canonical FactLine objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.tagging.calc_tags import CalcTag


@dataclass
class FactLine:
    """
    Canonical representation of a financial line item for classification.
    
    Attributes:
        line_id: Unique identifier for this line item
        statement_type: "IS", "BS", or "CF"
        role_uri: XBRL role URI (full URI or normalized string)
        label: Human-readable line item label
        parent_label: Label of parent/header in presentation hierarchy
        concept_qname: Full XBRL concept QName (e.g., "us-gaap:Revenues")
        is_abstract: Whether this is an abstract header/concept
        period_start: Period start date (ISO format, YYYY-MM-DD) or None
        period_end: Period end date (ISO format, YYYY-MM-DD)
        value: Numeric value (float) or None
        unit: Unit identifier (e.g., "iso4217:USD") or None
        dimensions: Dictionary mapping dimension QName -> member QName
        calc_tags: List of assigned calc tags (empty list if not yet classified)
    """
    line_id: str
    statement_type: str  # "IS", "BS", or "CF"
    role_uri: Optional[str]
    label: Optional[str]
    parent_label: Optional[str]
    concept_qname: str
    is_abstract: bool
    period_start: Optional[str]
    period_end: str
    value: Optional[float]
    unit: Optional[str]
    dimensions: Dict[str, str] = field(default_factory=dict)
    calc_tags: List[str] = field(default_factory=list)


def derive_statement_type(
    role_uri: Optional[str],
    role_name: Optional[str],
    display_role: Optional[str],
) -> str:
    """
    Derive statement type from role information.
    
    Args:
        role_uri: Full role URI or normalized role string
        role_name: Short role name
        display_role: Normalized display role
        
    Returns:
        "IS" for Income Statement, "BS" for Balance Sheet, "CF" for Cash Flow,
        or "UNKNOWN" if cannot be determined
    """
    # Check all role fields (case-insensitive)
    role_text = " ".join([
        str(role_uri or ""),
        str(role_name or ""),
        str(display_role or ""),
    ]).lower()
    
    # Income Statement indicators
    if any(keyword in role_text for keyword in [
        "income",
        "operations",
        "earnings",
        "comprehensive income",
        "statement of income",
        "statement of operations",
    ]):
        return "IS"
    
    # Balance Sheet indicators
    if any(keyword in role_text for keyword in [
        "balance",
        "financial position",
        "assets",
        "liabilities",
        "equity",
        "balance sheet",
    ]):
        return "BS"
    
    # Cash Flow indicators
    if any(keyword in role_text for keyword in [
        "cash flow",
        "cashflow",
        "cash provided",
        "cash used",
        "operating activities",
        "investing activities",
        "financing activities",
    ]):
        return "CF"
    
    return "UNKNOWN"


def infer_is_abstract(raw_fact: Dict[str, Any]) -> bool:
    """
    Infer whether a fact represents an abstract concept.
    
    Args:
        raw_fact: Raw fact dictionary from Arelle JSON
        
    Returns:
        True if likely abstract, False otherwise
    """
    # Check explicit field if present
    if "is_abstract" in raw_fact:
        return bool(raw_fact["is_abstract"])
    
    # Abstract concepts typically:
    # 1. Have null/zero value
    # 2. Have concept names ending in "Abstract"
    # 3. Have no unit
    concept_qname = raw_fact.get("concept_qname", "")
    concept_local_name = raw_fact.get("concept_local_name", "")
    
    if "abstract" in concept_qname.lower() or "abstract" in concept_local_name.lower():
        return True
    
    # If value is None and no unit, might be abstract
    value = raw_fact.get("value")
    unit = raw_fact.get("unit")
    if value is None and not unit:
        return True
    
    return False


def normalize_fact_to_factline(raw_fact: Dict[str, Any]) -> FactLine:
    """
    Convert a raw Arelle fact dictionary to a FactLine object.
    
    Args:
        raw_fact: Raw fact dictionary from enriched Arelle JSON
        
    Returns:
        FactLine object with normalized fields
    """
    # Extract line_id (prefer line_item_id, fallback to display_line_id, or generate)
    line_id = (
        raw_fact.get("line_item_id") or
        raw_fact.get("display_line_id") or
        _generate_line_id(raw_fact)
    )
    
    # Derive statement type
    statement_type = derive_statement_type(
        role_uri=raw_fact.get("role_uri"),
        role_name=raw_fact.get("role_name"),
        display_role=raw_fact.get("display_role"),
    )
    
    # Extract label (prefer standard_label, fallback to label, then doc_label, then concept_local_name)
    label = (
        raw_fact.get("standard_label") or
        raw_fact.get("label") or
        raw_fact.get("doc_label") or
        raw_fact.get("concept_local_name")
    )
    
    # Extract other fields
    role_uri = raw_fact.get("role_uri")
    parent_label = raw_fact.get("parent_label")
    concept_qname = raw_fact.get("concept_qname", "")
    period_start = raw_fact.get("period_start") or raw_fact.get("start")
    period_end = raw_fact.get("period_end") or raw_fact.get("end", "")
    
    # Extract value (handle None, 0.0 is valid)
    value = raw_fact.get("value")
    if value is not None:
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = None
    
    # Extract unit
    unit = raw_fact.get("unit")
    
    # Extract dimensions (ensure it's a dict)
    dimensions = raw_fact.get("dimensions", {})
    if not isinstance(dimensions, dict):
        dimensions = {}
    
    # Infer is_abstract
    is_abstract = infer_is_abstract(raw_fact)
    
    return FactLine(
        line_id=line_id,
        statement_type=statement_type,
        role_uri=role_uri,
        label=label,
        parent_label=parent_label,
        concept_qname=concept_qname,
        is_abstract=is_abstract,
        period_start=period_start,
        period_end=period_end,
        value=value,
        unit=unit,
        dimensions=dimensions,
        calc_tags=[],  # Will be populated by classifier
    )


def _generate_line_id(raw_fact: Dict[str, Any]) -> str:
    """
    Generate a line_id if one doesn't exist.
    
    Args:
        raw_fact: Raw fact dictionary
        
    Returns:
        Generated line_id string
    """
    display_role = raw_fact.get("display_role") or "unknown"
    concept_local_name = raw_fact.get("concept_local_name") or raw_fact.get("concept_qname", "unknown")
    period_end = raw_fact.get("period_end") or raw_fact.get("end", "unknown")
    
    # Build dimensions key
    dimensions = raw_fact.get("dimensions", {})
    if dimensions:
        dim_key = "_".join(sorted(f"{k}_{v}" for k, v in dimensions.items()))
    else:
        dim_key = "Consolidated"
    
    return f"{display_role}__{concept_local_name}__{dim_key}__{period_end}"

