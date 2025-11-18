"""
structured_formatter.py — Format raw EDGAR facts into Denari structured JSON with LLM classification.

Takes raw EDGAR facts extracted from Company Facts API and formats them into the
Denari structured JSON schema, including LLM-based classification for each line item.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.core.normalized_order import get_normalized_order
from app.services.ingestion.structured_output import generate_structured_output

logger = get_logger(__name__)


def format_with_llm_classification(
    raw_facts: Dict[str, List[Dict[str, Any]]],
    metadata: Dict[str, Any],
    report_date: str,
    statement_currency: str = "USD",
) -> Dict[str, Any]:
    """
    Format raw EDGAR facts into structured JSON with LLM classification.

    Args:
        raw_facts: Dictionary with keys 'bs', 'is', 'cf', each containing list of fact dicts
            Each fact dict has: tag, label, amount, unit, end (and optionally start)
        metadata: Company/filing metadata (cik, ticker, company_name, filing_type, etc.)
        report_date: Report date string (ISO format)
        statement_currency: Currency code (default: "USD")

    Returns:
        Complete structured JSON matching Denari schema
    """
    statements = {}

    # Process each statement type
    for stmt_type, facts_list in [
        ("income_statement", raw_facts.get("is", [])),
        ("balance_sheet", raw_facts.get("bs", [])),
        ("cash_flow_statement", raw_facts.get("cf", [])),
    ]:
        statements[stmt_type] = _format_statement(
            stmt_type=stmt_type,
            facts=facts_list,
            report_date=report_date,
            currency=statement_currency,
        )

    # Build comps_config (can be extended later)
    comps_config = {
        "sector": metadata.get("sector", ""),
        "industry": metadata.get("industry", ""),
        "peer_selection_rule": {
            "by_sector_industry": False,
            "market_cap_tolerance_pct": None,
        },
        "key_metrics": [],
        "metric_sources": {},
    }

    # Build final payload
    payload: Dict[str, Any] = {
        "metadata": {
            "cik": metadata.get("cik", ""),
            "ticker": metadata.get("ticker", ""),
            "company_name": metadata.get("company_name", ""),
            "filing_type": metadata.get("filing_type", ""),
            "filing_accession": metadata.get("filing_accession", ""),
            "fiscal_year": metadata.get("fiscal_year", ""),
            "fiscal_period": metadata.get("fiscal_period", "FY"),
            "statement_currency": statement_currency,
            "us_gaap_taxonomy_year": metadata.get("us_gaap_taxonomy_year", ""),
        },
        "statements": statements,
        "comps_config": comps_config,
    }

    # Tag only required model items using LLM matching
    logger.info("Tagging required model items using LLM matching")
    payload = generate_structured_output(payload)

    return payload


def _format_statement(
    stmt_type: str,
    facts: List[Dict[str, Any]],
    report_date: str,
    currency: str,
) -> Dict[str, Any]:
    """
    Format a single statement (IS, BS, or CF) WITHOUT LLM classification.
    
    Classification is done later via generate_structured_output after all statements are built.

    Args:
        stmt_type: Statement type ("income_statement", "balance_sheet", "cash_flow_statement")
        facts: List of fact dictionaries
        report_date: Report date string
        currency: Currency code

    Returns:
        Dictionary with statement_type, normalized_order, and line_items (without classifications)
    """
    line_items: List[Dict[str, Any]] = []
    tag_to_item: Dict[str, Dict[str, Any]] = {}

    # Build line items WITHOUT classification (will be added later)
    for fact in facts:
        tag = fact.get("tag", "")
        label = fact.get("label", tag)
        amount = fact.get("amount", 0.0)
        unit = fact.get("unit") or currency

        # Build line item with empty/default classification fields
        line_item = {
            "tag": tag,
            "label": label,
            "model_role": "",  # Will be filled by generate_structured_output
            "is_core_3_statement": False,  # Will be filled by generate_structured_output
            "is_dcf_key": False,  # Will be filled by generate_structured_output
            "is_comps_key": False,  # Will be filled by generate_structured_output
            "llm_classification": {
                "best_fit_role": "",  # Will be filled by generate_structured_output
                "confidence": 0.0,  # Will be filled by generate_structured_output
            },
            "unit": unit,
            "periods": {
                report_date: amount,
            },
            "subitems": [],
        }

        tag_to_item[tag] = line_item
        line_items.append(line_item)

    # Build parent-child hierarchy (2-level max)
    # Group items by model_role to identify potential parent-child relationships
    # For now, we'll keep it simple - subitems can be populated later based on model_role patterns
    _build_hierarchy(line_items, tag_to_item)

    # Apply normalized ordering
    normalized_order = get_normalized_order(stmt_type)
    ordered_items = _apply_normalized_order(line_items, normalized_order)

    return {
        "statement_type": stmt_type,
        "normalized_order": [item["tag"] for item in ordered_items],
        "line_items": ordered_items,
    }


def _build_hierarchy(
    line_items: List[Dict[str, Any]],
    tag_to_item: Dict[str, Dict[str, Any]],
) -> None:
    """
    Build parent-child hierarchy (2-level max) based on model_role patterns.

    This is a simplified implementation. More sophisticated hierarchy building
    can be added later based on model_role relationships.
    """
    # Group by model_role prefix to identify potential parent-child relationships
    # For example, "assets_current" items might be children of "AssetsCurrent"
    role_groups: Dict[str, List[Dict[str, Any]]] = {}

    for item in line_items:
        model_role = item.get("model_role", "")
        if not model_role:
            continue

        # Extract base role (e.g., "assets" from "assets_current")
        base_role = model_role.split("_")[0] if "_" in model_role else model_role
        role_groups.setdefault(base_role, []).append(item)

    # For now, we keep subitems empty
    # Future enhancement: Use model_role patterns to build hierarchy
    # For example, if we have "Assets" and "AssetsCurrent", make "AssetsCurrent" a child


def _apply_normalized_order(
    line_items: List[Dict[str, Any]],
    normalized_order: List[str],
) -> List[Dict[str, Any]]:
    """
    Apply normalized ordering to line items.

    Items in normalized_order appear first in that order.
    Items not in normalized_order appear at the end, sorted by tag.
    """
    # Create lookup for quick access
    item_by_tag: Dict[str, Dict[str, Any]] = {item["tag"]: item for item in line_items}

    ordered: List[Dict[str, Any]] = []
    seen_tags: set[str] = set()

    # Add items in normalized order
    for tag in normalized_order:
        if tag in item_by_tag:
            ordered.append(item_by_tag[tag])
            seen_tags.add(tag)

    # Add remaining items not in normalized order, sorted by tag
    remaining = [item for item in line_items if item["tag"] not in seen_tags]
    remaining.sort(key=lambda x: x["tag"])

    ordered.extend(remaining)

    return ordered

