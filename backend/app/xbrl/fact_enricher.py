"""
fact_enricher.py — Enrich XBRL facts with rich metadata for display line identification.

LEGACY: Replaced by FMP /stable-based pipeline (see app/data/fmp_client.py).

This module adds comprehensive metadata to XBRL facts including:
- Role/presentation tree information (which statement or note)
- Dimensions (axes and members)
- Stable display/line identifiers (display_role, line_item_id, display_line_id)
- calc_bucket field for debt classification

Usage:
    from app.xbrl.fact_enricher import enrich_fact_with_metadata
    
    fact_dict = {
        "concept_qname": "us-gaap:DebtCurrent",
        "value": 1000000,
        ...
    }
    enrich_fact_with_metadata(fact, model_xbrl, fact_dict)
    # fact_dict now includes: role_uri, dimensions, display_role, line_item_id, display_line_id, calc_bucket, etc.
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# Try to import Arelle constants
try:
    from arelle import XbrlConst
    ARELLE_CONST_AVAILABLE = True
except ImportError:
    ARELLE_CONST_AVAILABLE = False
    XbrlConst = None


def enrich_fact_with_metadata(
    fact: Any,
    model_xbrl: Any,
    fact_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Main entry point that enriches a fact dictionary with all metadata.
    
    Args:
        fact: Arelle fact object
        model_xbrl: Arelle ModelXbrl object
        fact_dict: Dictionary to enrich (mutated in place)
        
    Returns:
        Enriched fact_dict (same object, mutated)
    """
    try:
        # Extract concept metadata
        extract_concept_metadata(fact, fact_dict)
        
        # Extract presentation metadata (role, parent, order)
        extract_presentation_metadata(fact, model_xbrl, fact_dict)
        
        # Extract dimensions
        extract_dimensions(fact, fact_dict)
        
        # Extract period metadata (period_start, period_end)
        extract_period_metadata(fact, fact_dict)
        
        # Build display identifiers
        build_display_identifiers(fact_dict)
        
        # Assign calc_bucket for debt classification
        fact_dict["calc_bucket"] = assign_calc_bucket(fact_dict)
        
    except Exception as e:
        logger.warning(f"Error enriching fact {fact_dict.get('concept_qname', 'unknown')}: {e}")
        # Continue - don't break fact extraction if enrichment fails
    
    return fact_dict


def extract_concept_metadata(fact: Any, fact_dict: Dict[str, Any]) -> None:
    """
    Extract concept metadata: local_name, standard_label, doc_label.
    
    Args:
        fact: Arelle fact object
        fact_dict: Dictionary to enrich
    """
    # Extract local name from concept_qname (always available from fact extraction)
    concept_qname = fact_dict.get("concept_qname")
    if concept_qname:
        if ":" in concept_qname:
            fact_dict["concept_local_name"] = concept_qname.split(":")[-1]
        else:
            fact_dict["concept_local_name"] = concept_qname
    else:
        fact_dict["concept_local_name"] = None
    
    # Try to get labels from concept if available
    fact_dict["standard_label"] = None
    fact_dict["doc_label"] = None
    
    if fact and hasattr(fact, "concept") and fact.concept:
        concept = fact.concept
        # Extract standard label
        try:
            if hasattr(concept, "label"):
                standard_label = concept.label("standard")
                fact_dict["standard_label"] = standard_label if standard_label else None
        except Exception:
            pass
        
        # Extract documentation label
        try:
            if hasattr(concept, "label"):
                doc_label = concept.label("documentation")
                fact_dict["doc_label"] = doc_label if doc_label else None
        except Exception:
            pass


def extract_presentation_metadata(
    fact: Any,
    model_xbrl: Any,
    fact_dict: Dict[str, Any],
) -> None:
    """
    Extract presentation metadata: role_uri, role_name, parent_label, order.
    
    Uses Arelle's relationshipSet API to find presentation relationships.
    Prefers consolidated primary financial statement roles.
    
    Args:
        fact: Arelle fact object
        model_xbrl: Arelle ModelXbrl object
        fact_dict: Dictionary to enrich
    """
    role_uri, role_name, parent_label, order = _find_presentation_role_for_fact(fact, model_xbrl)
    
    fact_dict["role_uri"] = role_uri
    fact_dict["role_name"] = role_name
    fact_dict["parent_label"] = parent_label
    fact_dict["order"] = order


def _find_presentation_role_for_fact(
    fact: Any,
    model_xbrl: Any,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
    """
    Find presentation role, parent label, and order for a fact.
    
    Returns:
        Tuple of (role_uri, role_name, parent_label, order)
    """
    # Try to get concept - may not exist for all facts
    concept = None
    if fact and hasattr(fact, "concept") and fact.concept:
        concept = fact.concept
    elif not fact:
        return None, None, None, None
    
    # If no concept, try to infer from fact QName
    if not concept:
        return _infer_role_from_concept_qname(fact)
    
    # Try to access relationship set
    relationship_set = None
    try:
        if hasattr(model_xbrl, "relationshipSet"):
            if ARELLE_CONST_AVAILABLE and XbrlConst:
                relationship_set = model_xbrl.relationshipSet(XbrlConst.presentationLink)
            else:
                # Try alternative access patterns
                if hasattr(model_xbrl.relationshipSet, "__call__"):
                    # relationshipSet might be callable
                    try:
                        relationship_set = model_xbrl.relationshipSet("presentation")
                    except:
                        pass
    except Exception as e:
        logger.debug(f"Could not access relationshipSet: {e}")
    
    if not relationship_set:
        # Fallback: try to infer from fact/concept
        if concept:
            return _infer_role_from_concept(concept)
        else:
            return _infer_role_from_concept_qname(fact)
    
    if not concept:
        # Can't use relationship set without concept
        return _infer_role_from_concept_qname(fact)
    
    # Find relationships for this concept
    best_role_uri = None
    best_role_name = None
    best_parent_label = None
    best_order = None
    best_priority = 999
    
    try:
        # Get relationships where this concept is the "to" (child) concept
        relationships = relationship_set.fromModelObject(concept)
        
        if relationships:
            for rel in relationships:
                # Get role URI
                role_uri = None
                if hasattr(rel, "role"):
                    role_uri = str(rel.role) if rel.role else None
                elif hasattr(rel, "linkrole"):
                    role_uri = str(rel.linkrole) if rel.linkrole else None
                
                if not role_uri:
                    continue
                
                # Get parent concept (fromModelObject)
                parent_concept = None
                if hasattr(rel, "fromModelObject"):
                    parent_concept = rel.fromModelObject
                
                # Get order
                order = None
                if hasattr(rel, "order"):
                    order = rel.order
                elif hasattr(rel, "preferredLabel"):
                    # Sometimes order is in preferredLabel
                    pass
                
                # Get parent label
                parent_label = None
                if parent_concept:
                    try:
                        if hasattr(parent_concept, "label"):
                            parent_label = parent_concept.label("standard")
                    except:
                        pass
                
                # Calculate priority (prefer consolidated balance sheet)
                priority = _calculate_role_priority(role_uri, concept)
                
                if priority < best_priority:
                    best_priority = priority
                    best_role_uri = role_uri
                    best_role_name = _extract_role_name_from_uri(role_uri)
                    best_parent_label = parent_label
                    best_order = order
        
    except Exception as e:
        logger.debug(f"Error accessing presentation relationships: {e}")
        return _infer_role_from_concept(concept)
    
    if best_role_uri:
        return best_role_uri, best_role_name, best_parent_label, best_order
    
    # Fallback to inference
    return _infer_role_from_concept(concept)


def _calculate_role_priority(role_uri: str, concept: Any) -> int:
    """
    Calculate priority for role selection (lower = better).
    
    Prefers:
    1. Consolidated balance sheet roles
    2. Primary financial statement roles
    3. Note roles
    """
    role_lower = role_uri.lower()
    
    # Highest priority: consolidated balance sheet
    if "balancesheet" in role_lower or "statementoffinancialposition" in role_lower:
        if "consolidated" in role_lower or "consolidating" not in role_lower:
            return 1
    
    # High priority: other primary financial statements
    if "incomestatement" in role_lower or "statementofoperations" in role_lower:
        if "consolidated" in role_lower:
            return 2
    
    if "cashflow" in role_lower or "statementofcashflows" in role_lower:
        if "consolidated" in role_lower:
            return 2
    
    # Medium priority: balance sheet (non-consolidated)
    if "balancesheet" in role_lower:
        return 3
    
    # Lower priority: notes
    if "note" in role_lower or "disclosure" in role_lower:
        return 4
    
    # Default priority
    return 5


def _extract_role_name_from_uri(role_uri: str) -> Optional[str]:
    """Extract short role name from role URI."""
    if not role_uri:
        return None
    
    # Extract portion after /role/
    if "/role/" in role_uri:
        parts = role_uri.split("/role/")
        if len(parts) > 1:
            name = parts[-1]
            # Remove namespace prefixes and normalize
            name = name.split(":")[-1] if ":" in name else name
            return name
    
    # Fallback: use last part of URI
    parts = role_uri.split("/")
    if parts:
        name = parts[-1]
        name = name.split(":")[-1] if ":" in name else name
        return name
    
    return None


def _infer_role_from_concept_qname(fact: Any) -> Tuple[Optional[str], Optional[str], None, None]:
    """
    Infer role from fact QName when concept is not available.
    
    Returns:
        Tuple of (role_uri, role_name, None, None)
    """
    if not fact:
        return None, None, None, None
    
    # Try to get QName from fact
    concept_qname = None
    if hasattr(fact, "qname") and fact.qname:
        concept_qname = str(fact.qname).lower()
    elif hasattr(fact, "elementQname") and fact.elementQname:
        concept_qname = str(fact.elementQname).lower()
    else:
        return None, None, None, None
    
    # Use same inference logic as _infer_role_from_concept
    return _infer_role_from_qname_string(concept_qname)


def _infer_role_from_concept(concept: Any) -> Tuple[Optional[str], Optional[str], None, None]:
    """
    Infer role from concept name as fallback.
    
    Returns:
        Tuple of (role_uri, role_name, None, None)
    """
    if not concept:
        return None, None, None, None
    
    concept_qname = None
    if hasattr(concept, "qname") and concept.qname:
        concept_qname = str(concept.qname).lower()
    else:
        return None, None, None, None
    
    return _infer_role_from_qname_string(concept_qname)


def _infer_role_from_qname_string(concept_qname: str) -> Tuple[Optional[str], Optional[str], None, None]:
    """
    Infer role from QName string (shared logic).
    
    Returns:
        Tuple of (role_uri, role_name, None, None)
    """
    
    # Heuristic: infer from concept name
    if any(keyword in concept_qname for keyword in [
        "assets", "liabilities", "equity", "stockholders", "cash", "inventory",
        "receivable", "payable", "debtcurrent", "debtnoncurrent"
    ]):
        return "balance_sheet", "BalanceSheet", None, None
    
    if any(keyword in concept_qname for keyword in [
        "revenue", "income", "expense", "cost", "profit", "loss", "earnings"
    ]):
        return "income_statement", "IncomeStatement", None, None
    
    if any(keyword in concept_qname for keyword in [
        "cashflow", "cashprovided", "cashused", "operatingactivities",
        "investingactivities", "financingactivities"
    ]):
        return "cash_flow", "CashFlowStatement", None, None
    
    if any(keyword in concept_qname for keyword in [
        "debt", "borrowing", "notespayable", "lease", "obligation"
    ]):
        return "note18_debt", "DebtAndCommitmentsNote", None, None
    
    return None, None, None, None


def extract_dimensions(fact: Any, fact_dict: Dict[str, Any]) -> None:
    """
    Extract dimensions from fact context.
    
    Uses context.segDimValues to build a dictionary mapping dimension QName strings
    to member QName strings.
    
    Args:
        fact: Arelle fact object
        fact_dict: Dictionary to enrich
    """
    dimensions = _extract_dimensions_dict(fact.context if fact else None)
    fact_dict["dimensions"] = dimensions


def _extract_dimensions_dict(context: Any) -> Dict[str, str]:
    """
    Extract dimensions dictionary from context.
    
    Uses context.segDimValues to build a dictionary mapping dimension QName strings
    to member QName strings.
    
    Args:
        context: Arelle context object
        
    Returns:
        Dictionary mapping dimension QName strings to member QName strings
    """
    dimensions = {}
    
    if not context:
        return dimensions
    
    # First, try qnameDims if available (more structured)
    try:
        if hasattr(context, "qnameDims") and context.qnameDims:
            # qnameDims is typically a dict-like object mapping dimension QName to member QName
            if hasattr(context.qnameDims, "items"):
                for dim_qname, member_qname in context.qnameDims.items():
                    dim_qname_str = str(dim_qname) if dim_qname else None
                    member_qname_str = str(member_qname) if member_qname else None
                    if dim_qname_str and member_qname_str:
                        dimensions[dim_qname_str] = member_qname_str
            elif hasattr(context.qnameDims, "__iter__"):
                # Might be iterable of tuples or objects
                for item in context.qnameDims:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        dim_qname_str = str(item[0])
                        member_qname_str = str(item[1])
                        dimensions[dim_qname_str] = member_qname_str
    except Exception as e:
        logger.debug(f"Error extracting from qnameDims: {e}")
    
    # Fallback to segDimValues (as requested by user)
    if not dimensions and hasattr(context, "segDimValues") and context.segDimValues:
        try:
            for dim in context.segDimValues:
                # Try to extract QName attributes from dimension object
                dim_qname = None
                member_qname = None
                
                # Check for explicit QName attributes
                if hasattr(dim, "dimensionQname") and hasattr(dim, "memberQname"):
                    dim_qname = str(dim.dimensionQname) if dim.dimensionQname else None
                    member_qname = str(dim.memberQname) if dim.memberQname else None
                elif hasattr(dim, "qname"):
                    # Single QName - might be the dimension itself
                    dim_qname = str(dim.qname) if dim.qname else None
                    # Try to find member in the same object
                    if hasattr(dim, "member"):
                        member_qname = str(dim.member) if dim.member else None
                
                # If we got QNames, use them
                if dim_qname:
                    if member_qname:
                        dimensions[dim_qname] = member_qname
                    else:
                        # Store dimension with placeholder member
                        dimensions[dim_qname] = "unknown"
                else:
                    # Fallback: use string representation
                    dim_str = str(dim).strip()
                    if dim_str:
                        # Try to parse if it looks like "dimension:member"
                        if ":" in dim_str and "=" in dim_str:
                            # Format like "f:BusinessSectorAxis=f:ConsolidatedMember"
                            parts = dim_str.split("=", 1)
                            if len(parts) == 2:
                                dimensions[parts[0].strip()] = parts[1].strip()
                        else:
                            # Store as dimension with unknown member
                            dimensions[dim_str] = "unknown"
        
        except Exception as e:
            logger.debug(f"Error extracting from segDimValues: {e}")
    
    return dimensions


def extract_period_metadata(fact: Any, fact_dict: Dict[str, Any]) -> None:
    """
    Extract period metadata: period_start, period_end.
    
    Reuses period extraction logic from statement_extractor.py.
    
    Args:
        fact: Arelle fact object
        fact_dict: Dictionary to enrich
    """
    context = fact.context if fact else None
    
    # Extract period_end (reuse existing logic)
    period_end = _get_period_end(context)
    fact_dict["period_end"] = period_end
    
    # Extract period_start
    period_start = _get_period_start(context)
    fact_dict["period_start"] = period_start


def _get_period_end(context: Any) -> Optional[str]:
    """
    Extract period end date from Arelle context.
    
    Reuses logic from statement_extractor.py.
    """
    if context is None:
        return None
    
    # Check if it's an instant period (balance sheet)
    if hasattr(context, "isInstantPeriod"):
        is_instant = context.isInstantPeriod if not callable(context.isInstantPeriod) else context.isInstantPeriod()
        if is_instant:
            if hasattr(context, "instantDatetime") and context.instantDatetime:
                return context.instantDatetime.date().isoformat()
    
    # Check if it's a duration period (income statement, cash flow)
    if hasattr(context, "isStartEndPeriod"):
        is_start_end = context.isStartEndPeriod if not callable(context.isStartEndPeriod) else context.isStartEndPeriod()
        if is_start_end:
            if hasattr(context, "endDatetime") and context.endDatetime:
                # endDatetime is the day AFTER the period ends, so subtract 1 day
                end_date = context.endDatetime.date() - timedelta(days=1)
                return end_date.isoformat()
    
    # Fallback: try direct attributes
    if hasattr(context, "instantDatetime") and context.instantDatetime:
        return context.instantDatetime.date().isoformat()
    
    if hasattr(context, "endDatetime") and context.endDatetime:
        end_date = context.endDatetime.date() - timedelta(days=1)
        return end_date.isoformat()
    
    return None


def _get_period_start(context: Any) -> Optional[str]:
    """
    Extract period start date from Arelle context.
    """
    if context is None:
        return None
    
    # For duration periods, check startDatetime
    if hasattr(context, "isStartEndPeriod"):
        is_start_end = context.isStartEndPeriod if not callable(context.isStartEndPeriod) else context.isStartEndPeriod()
        if is_start_end:
            if hasattr(context, "startDatetime") and context.startDatetime:
                return context.startDatetime.date().isoformat()
    
    # Fallback: try direct attribute
    if hasattr(context, "startDatetime") and context.startDatetime:
        return context.startDatetime.date().isoformat()
    
    return None


def build_display_identifiers(fact_dict: Dict[str, Any]) -> None:
    """
    Build stable display identifiers: display_role, line_item_id, display_line_id.
    
    Args:
        fact_dict: Dictionary to enrich
    """
    # Extract role_uri and normalize to display_role
    role_uri = fact_dict.get("role_uri")
    display_role = _normalize_role_uri_to_display_role(role_uri)
    fact_dict["display_role"] = display_role
    
    # Build line_item_id
    concept_local_name = fact_dict.get("concept_local_name")
    dimensions = fact_dict.get("dimensions", {})
    line_item_id = _build_line_item_id(display_role, concept_local_name, dimensions)
    fact_dict["line_item_id"] = line_item_id
    
    # Build display_line_id
    parent_label = fact_dict.get("parent_label")
    period_end = fact_dict.get("period_end")
    display_line_id = _build_display_line_id(display_role, parent_label, concept_local_name, period_end)
    fact_dict["display_line_id"] = display_line_id


def _normalize_role_uri_to_display_role(role_uri: Optional[str]) -> Optional[str]:
    """
    Normalize role URI to a short, human-readable display role.
    
    Examples:
        "http://www.ford.com/role/ConsolidatedBalanceSheet" -> "ConsolidatedBalanceSheet"
        "http://fasb.org/us-gaap/role/StatementOfFinancialPosition" -> "StatementOfFinancialPosition"
    """
    if not role_uri:
        return None
    
    # Extract portion after /role/
    if "/role/" in role_uri:
        parts = role_uri.split("/role/")
        if len(parts) > 1:
            name = parts[-1]
            # Remove namespace prefixes
            name = name.split(":")[-1] if ":" in name else name
            # Normalize: remove common prefixes, capitalize appropriately
            name = re.sub(r"^StatementOf", "", name)
            name = re.sub(r"^Consolidated", "", name)
            if name:
                # Re-add Consolidated prefix if it was a consolidated role
                if "consolidated" in role_uri.lower():
                    name = "Consolidated" + name
                return name
    
    # Fallback: use role_name if available, or extract from URI
    if "/" in role_uri:
        parts = role_uri.split("/")
        name = parts[-1]
        name = name.split(":")[-1] if ":" in name else name
        return name
    
    return role_uri


def _build_line_item_id(
    display_role: Optional[str],
    concept_local_name: Optional[str],
    dimensions: Dict[str, str],
) -> Optional[str]:
    """
    Build stable line_item_id combining role + concept + dimensions.
    
    Format: <display_role>__<concept_local_name>__<dimensions_key>
    
    Examples:
        "ConsolidatedBalanceSheet__DebtCurrent__Consolidated"
        "DebtAndCommitmentsNote__DebtCurrent__BusinessSectorAxis=FordCreditMember"
    """
    if not display_role or not concept_local_name:
        return None
    
    # Build dimensions key
    dimensions_key = _build_dimensions_key(dimensions)
    
    parts = [display_role, concept_local_name, dimensions_key]
    return "__".join(parts)


def _build_dimensions_key(dimensions: Dict[str, str]) -> str:
    """
    Build a stable key from dimensions dictionary.
    
    Returns "Consolidated" if no dimensions or consolidated member,
    otherwise sorted "dim=member" pairs.
    """
    if not dimensions:
        return "Consolidated"
    
    # Check if consolidated
    for dim_qname, member_qname in dimensions.items():
        dim_lower = dim_qname.lower()
        member_lower = str(member_qname).lower() if member_qname else ""
        
        # Check for consolidated indicators
        if "consolidated" in member_lower or "consolidated" in dim_lower:
            return "Consolidated"
        
        # Check for business sector axis with consolidated member
        if "businesssector" in dim_lower or "businesssectoraxis" in dim_lower:
            if "consolidated" in member_lower:
                return "Consolidated"
    
    # Build sorted key-value pairs
    pairs = []
    for dim_qname, member_qname in sorted(dimensions.items()):
        dim_local = dim_qname.split(":")[-1] if ":" in dim_qname else dim_qname
        member_local = str(member_qname).split(":")[-1] if member_qname and ":" in str(member_qname) else str(member_qname)
        pairs.append(f"{dim_local}={member_local}")
    
    return "-".join(pairs) if pairs else "Consolidated"


def _build_display_line_id(
    display_role: Optional[str],
    parent_label: Optional[str],
    concept_local_name: Optional[str],
    period_end: Optional[str],
) -> Optional[str]:
    """
    Build display_line_id including parent label and period.
    
    Format: <display_role>__<parent_label_normalized>__<concept_local_name>__<period_end>
    
    Example: "ConsolidatedBalanceSheet__total_liabilities__DebtCurrent__2024-12-31"
    """
    if not display_role or not concept_local_name:
        return None
    
    parts = [display_role]
    
    # Normalize parent label
    if parent_label:
        parent_normalized = _normalize_label(parent_label)
        parts.append(parent_normalized)
    else:
        parts.append("unknown")
    
    parts.append(concept_local_name)
    
    if period_end:
        parts.append(period_end)
    else:
        parts.append("unknown")
    
    return "__".join(parts)


def _normalize_label(label: str) -> str:
    """
    Normalize a label for use in display_line_id.
    
    - Lowercase
    - Replace spaces and punctuation with underscores
    - Trim length if needed
    """
    if not label:
        return "unknown"
    
    # Lowercase
    normalized = label.lower()
    
    # Replace spaces and punctuation with underscores
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip("_")
    
    # Trim length (max 50 chars)
    if len(normalized) > 50:
        normalized = normalized[:50]
    
    return normalized if normalized else "unknown"


def assign_calc_bucket(fact_dict: Dict[str, Any]) -> Optional[str]:
    """
    Assign calc_bucket for debt classification.
    
    Returns:
        "interest_bearing_debt_total_component" - fact is a component of total interest-bearing debt
        "interest_bearing_debt_detail_only" - note/instrument-level detail for debt
        None - not related to interest-bearing debt
    """
    concept_qname = fact_dict.get("concept_qname", "").lower()
    concept_local_name = fact_dict.get("concept_local_name", "").lower()
    display_role = fact_dict.get("display_role", "").lower() if fact_dict.get("display_role") else ""
    dimensions = fact_dict.get("dimensions", {})
    
    # Check if concept is debt-related
    is_debt_concept = any(keyword in concept_qname or keyword in concept_local_name for keyword in [
        "debtcurrent", "debtnoncurrent", "longtermdebt", "shorttermdebt",
        "debtandcapitalleaseobligations", "notespayable", "borrowings"
    ])
    
    if not is_debt_concept:
        return None
    
    # Check for interest_bearing_debt_total_component
    # Must be: consolidated balance sheet + consolidated dimensions + current or long-term debt
    is_total_component = False
    
    # Check if it's a key debt concept for totals
    is_key_debt_concept = any(keyword in concept_qname or keyword in concept_local_name for keyword in [
        "debtcurrent", "longtermdebtandcapitalleaseobligations"
    ])
    
    if is_key_debt_concept:
        # Check if display_role indicates consolidated balance sheet
        is_balance_sheet = "balancesheet" in display_role or "financialposition" in display_role
        
        if is_balance_sheet:
            # Check if dimensions indicate consolidated
            is_consolidated = _is_consolidated_dimensions(dimensions)
            
            if is_consolidated:
                is_total_component = True
    
    if is_total_component:
        return "interest_bearing_debt_total_component"
    
    # Check for interest_bearing_debt_detail_only
    # Debt note OR has additional instrument/maturity dimensions
    is_detail_only = False
    
    # Check if display_role indicates debt note
    is_debt_note = any(keyword in display_role for keyword in [
        "debt", "commitments", "borrowings", "note"
    ])
    
    if is_debt_note:
        is_detail_only = True
    
    # Check for additional dimensions (instrument, maturity, etc.)
    if dimensions:
        for dim_qname in dimensions.keys():
            dim_lower = dim_qname.lower()
            if any(keyword in dim_lower for keyword in [
                "instrument", "maturity", "term", "type"
            ]):
                is_detail_only = True
                break
    
    if is_detail_only:
        return "interest_bearing_debt_detail_only"
    
    # Default: not classified
    return None


def _is_consolidated_dimensions(dimensions: Dict[str, str]) -> bool:
    """
    Check if dimensions indicate consolidated entity.
    
    Returns True if:
    - No dimensions (dimensionless = consolidated)
    - Has consolidated member
    - Business sector axis with consolidated member
    """
    if not dimensions:
        return True
    
    for dim_qname, member_qname in dimensions.items():
        dim_lower = dim_qname.lower()
        member_lower = str(member_qname).lower() if member_qname else ""
        
        # Check for consolidated indicators
        if "consolidated" in member_lower:
            return True
        
        # Check for business sector axis with consolidated member
        if "businesssector" in dim_lower or "businesssectoraxis" in dim_lower:
            if "consolidated" in member_lower:
                return True
            # If no explicit segment (like Ford Credit), assume consolidated
            if "ford" not in member_lower and "credit" not in member_lower:
                return True
    
    # If we have dimensions but they don't explicitly indicate a segment, assume consolidated
    # (conservative approach - may need refinement based on actual data)
    return True

