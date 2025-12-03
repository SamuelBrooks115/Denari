"""
test_ford_income_statement_to_json.py — Reconstruct income statement from XBRL presentation tree.

This script:
1. Loads XBRL instance using Arelle
2. Identifies income statement role from presentation linkbase
3. Traverses presentation tree in order
4. Finds facts matching fiscal year and consolidated entity
5. Outputs structured JSON (not terminal)

Usage:
    python scripts/test_ford_income_statement_to_json.py \
        --instance-path data/xbrl/ford_2024_10k.ixbrl \
        --fiscal-year 2024 \
        --output-json outputs/ford_income_statement_2024.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try to import Arelle
try:
    from arelle import XbrlConst
    ARELLE_CONST_AVAILABLE = True
except ImportError:
    ARELLE_CONST_AVAILABLE = False
    XbrlConst = None

from app.xbrl.arelle_loader import find_role_by_keywords, get_role_uris, load_xbrl_instance


def extract_company_info(model_xbrl: Any) -> str:
    """
    Extract company name from XBRL instance.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        
    Returns:
        Company name string
    """
    # Search for dei:EntityRegistrantName
    for fact in model_xbrl.facts:
        if not fact.concept:
            continue
        
        concept_qname = None
        if hasattr(fact.concept, "qname") and fact.concept.qname:
            concept_qname = str(fact.concept.qname)
        elif hasattr(fact, "qname") and fact.qname:
            concept_qname = str(fact.qname)
        
        if concept_qname and "EntityRegistrantName" in concept_qname:
            # Get value
            value = None
            if hasattr(fact, "textValue") and fact.textValue:
                value = str(fact.textValue).strip()
            elif hasattr(fact, "xValue") and fact.xValue:
                value = str(fact.xValue).strip()
            
            if value:
                return value
    
    return "Unknown"


def find_income_statement_role(model_xbrl: Any, verbose: bool = False) -> Tuple[str, str]:
    """
    Find the income statement role URI and label.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        verbose: Whether to print debug information
        
    Returns:
        Tuple of (role_uri, role_label)
        
    Raises:
        RuntimeError: If income statement role not found
    """
    # First, try to get roles from relationshipSet (more reliable)
    roles_from_rels = {}
    relationship_set = None
    
    try:
        # Get presentation relationship set
        if hasattr(model_xbrl, "relationshipSet"):
            if ARELLE_CONST_AVAILABLE and XbrlConst:
                relationship_set = model_xbrl.relationshipSet(XbrlConst.presentationLink)
            else:
                if hasattr(model_xbrl.relationshipSet, "__call__"):
                    try:
                        relationship_set = model_xbrl.relationshipSet("presentation")
                    except:
                        pass
        
        if relationship_set:
            # Extract unique role URIs from relationships
            if hasattr(relationship_set, "modelRelationships"):
                for rel in relationship_set.modelRelationships:
                    role_uri = None
                    if hasattr(rel, "role"):
                        role_uri = str(rel.role) if rel.role else None
                    elif hasattr(rel, "linkrole"):
                        role_uri = str(rel.linkrole) if rel.linkrole else None
                    
                    if role_uri and role_uri not in roles_from_rels:
                        # Try to get definition/label
                        definition = ""
                        # Role URI itself often contains the info
                        roles_from_rels[role_uri] = definition
    except Exception as e:
        if verbose:
            print(f"Could not extract roles from relationshipSet: {e}")
    
    # Also try the original method
    roles = get_role_uris(model_xbrl)
    
    # Merge both sources
    all_roles = {**roles, **roles_from_rels}
    
    if verbose:
        print(f"Found {len(all_roles)} roles in XBRL instance (from roleTypes: {len(roles)}, from relationships: {len(roles_from_rels)})")
        # Print first 10 roles for debugging
        for i, (uri, defn) in enumerate(list(all_roles.items())[:10]):
            print(f"  Role {i+1}: {uri[:80]}... -> {defn[:100] if defn else 'No definition'}")
    
    if not all_roles:
        # Last resort: try to get roles directly from relationshipSet
        if relationship_set and hasattr(relationship_set, "linkRoleUris"):
            link_role_uris = relationship_set.linkRoleUris
            if link_role_uris:
                if verbose:
                    print(f"Found {len(link_role_uris)} link role URIs from relationshipSet")
                for role_uri in link_role_uris:
                    all_roles[str(role_uri)] = ""
        
        if not all_roles:
            raise RuntimeError("ERROR: No roles found in XBRL instance")
    
    # Try keyword search first
    keywords_combinations = [
        ["statement", "income", "operations"],
        ["statement", "income"],
        ["statement", "operations"],
        ["income", "statement"],
        ["comprehensive", "income"],
        ["earnings"],
    ]
    
    for keywords in keywords_combinations:
        # Search in all_roles
        keywords_lower = [kw.lower() for kw in keywords]
        for role_uri, definition in all_roles.items():
            definition_lower = (definition or "").lower()
            role_uri_lower = role_uri.lower()
            if all(kw in definition_lower or kw in role_uri_lower for kw in keywords_lower):
                role_label = definition or role_uri
                if verbose:
                    print(f"Found income statement role via keyword search: {role_label}")
                return role_uri, role_label
    
    # Fallback: search all roles manually with scoring
    best_role_uri = None
    best_role_label = None
    best_score = 0
    
    for role_uri, definition in all_roles.items():
        if not definition:
            definition = ""
        
        definition_lower = definition.lower()
        role_uri_lower = role_uri.lower()
        
        # Score based on keywords in definition OR role URI
        score = 0
        if "statement" in definition_lower or "statement" in role_uri_lower:
            score += 2
        if "income" in definition_lower or "income" in role_uri_lower:
            score += 2
        if "operations" in definition_lower or "operations" in role_uri_lower:
            score += 1
        if "consolidated" in definition_lower or "consolidated" in role_uri_lower:
            score += 1
        if "earnings" in definition_lower or "earnings" in role_uri_lower:
            score += 1
        if "comprehensive" in definition_lower or "comprehensive" in role_uri_lower:
            score += 1
        if "profit" in definition_lower or "profit" in role_uri_lower:
            score += 1
        
        # Prefer longer definitions (more specific)
        if score > 0:
            score += len(definition) / 100
        
        if score > best_score:
            best_score = score
            best_role_uri = role_uri
            best_role_label = definition or role_uri
    
    if best_role_uri and best_score > 0:
        if verbose:
            print(f"Found income statement role via scoring (score={best_score:.2f}): {best_role_label}")
        return best_role_uri, best_role_label
    
    # Last resort: try to find ANY role that might be income statement related
    income_statement_patterns = [
        "statementofincome",
        "statementofoperations",
        "statementofearnings",
        "incomestatement",
        "operations",
        "comprehensiveincome",
    ]
    
    for role_uri, definition in all_roles.items():
        role_uri_lower = role_uri.lower()
        definition_lower = (definition or "").lower()
        
        for pattern in income_statement_patterns:
            if pattern in role_uri_lower or pattern in definition_lower:
                if verbose:
                    print(f"Found income statement role via pattern matching ({pattern}): {definition or role_uri}")
                return role_uri, definition or role_uri
    
    # If still nothing, print all roles and raise error
    error_msg = "ERROR: Could not find income statement role in XBRL instance\n"
    error_msg += f"Found {len(all_roles)} roles total.\n"
    error_msg += "First 10 roles:\n"
    for i, (uri, defn) in enumerate(list(all_roles.items())[:10]):
        error_msg += f"  {i+1}. {uri}\n"
        if defn:
            error_msg += f"     -> {defn[:150]}\n"
    
    raise RuntimeError(error_msg)


def get_income_statement_rels(model_xbrl: Any, role_uri: str) -> Any:
    """
    Get presentation relationships for income statement role.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        role_uri: Role URI for income statement
        
    Returns:
        RelationshipSet object for the income statement role
    """
    try:
        if hasattr(model_xbrl, "relationshipSet"):
            if ARELLE_CONST_AVAILABLE and XbrlConst:
                # Try with XbrlConst
                rels = model_xbrl.relationshipSet(XbrlConst.presentationLink, role_uri)
                if rels:
                    return rels
            
            # Try callable pattern
            if hasattr(model_xbrl.relationshipSet, "__call__"):
                try:
                    rels = model_xbrl.relationshipSet("presentation", role_uri)
                    if rels:
                        return rels
                except:
                    pass
            
            # Try direct attribute access
            if hasattr(model_xbrl.relationshipSet, "presentation"):
                pres_set = getattr(model_xbrl.relationshipSet, "presentation", None)
                if pres_set and hasattr(pres_set, "__call__"):
                    try:
                        rels = pres_set(role_uri)
                        if rels:
                            return rels
                    except:
                        pass
    except Exception as e:
        raise RuntimeError(f"ERROR: Could not access presentation relationships: {e}")
    
    raise RuntimeError("ERROR: Could not find presentation relationships for income statement role")


def get_period_end(context: Any) -> Optional[str]:
    """
    Extract period end date from Arelle context.
    
    Args:
        context: Arelle context object
        
    Returns:
        Period end date as ISO string (YYYY-MM-DD) or None
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


def get_period_start(context: Any) -> Optional[str]:
    """
    Extract period start date from Arelle context.
    
    Args:
        context: Arelle context object
        
    Returns:
        Period start date as ISO string (YYYY-MM-DD) or None
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


def extract_dimensions_from_context(context: Any) -> Dict[str, str]:
    """
    Extract dimensions dictionary from context.
    
    Args:
        context: Arelle context object
        
    Returns:
        Dictionary mapping dimension QName strings to member QName strings
    """
    dimensions = {}
    
    if not context:
        return dimensions
    
    # Try qnameDims first (more structured)
    try:
        if hasattr(context, "qnameDims") and context.qnameDims:
            if hasattr(context.qnameDims, "items"):
                for dim_qname, member_qname in context.qnameDims.items():
                    dim_qname_str = str(dim_qname) if dim_qname else None
                    member_qname_str = str(member_qname) if member_qname else None
                    if dim_qname_str and member_qname_str:
                        dimensions[dim_qname_str] = member_qname_str
    except Exception:
        pass
    
    # Fallback to segDimValues
    if not dimensions and hasattr(context, "segDimValues") and context.segDimValues:
        try:
            for dim in context.segDimValues:
                if hasattr(dim, "dimensionQname") and hasattr(dim, "memberQname"):
                    dim_qname = str(dim.dimensionQname) if dim.dimensionQname else None
                    member_qname = str(dim.memberQname) if dim.memberQname else None
                    if dim_qname and member_qname:
                        dimensions[dim_qname] = member_qname
        except Exception:
            pass
    
    return dimensions


def is_consolidated_context(context: Any) -> bool:
    """
    Check if context represents consolidated entity.
    
    Args:
        context: Arelle context object
        
    Returns:
        True if consolidated (no segment dimensions or explicit consolidated member)
    """
    if not context:
        return True
    
    dimensions = extract_dimensions_from_context(context)
    
    if not dimensions:
        return True
    
    # Check for consolidated indicators
    for dim_qname, member_qname in dimensions.items():
        dim_lower = dim_qname.lower()
        member_lower = str(member_qname).lower() if member_qname else ""
        
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
    return True


def find_best_fact_for_concept(
    model_xbrl: Any,
    concept: Any,
    fiscal_year: Optional[int] = None,
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Find the best fact for a concept matching fiscal year and consolidated entity.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        concept: Arelle concept object
        fiscal_year: Target fiscal year (optional)
        
    Returns:
        Tuple of (fact, error_message) where error_message is None if fact found
    """
    if not concept:
        return None, "No concept provided"
    
    # Skip abstract concepts
    if hasattr(concept, "isAbstract") and concept.isAbstract:
        return None, None  # Abstract concepts don't have facts
    
    # Only process numeric concepts
    if hasattr(concept, "isNumeric") and not concept.isNumeric:
        return None, "Concept is not numeric"
    
    # Get concept QName
    concept_qname = None
    if hasattr(concept, "qname") and concept.qname:
        concept_qname = concept.qname
    else:
        return None, "Concept has no QName"
    
    # Find facts for this concept
    candidates = []
    
    # Try factsByQname if available
    if hasattr(model_xbrl, "factsByQname"):
        try:
            facts_by_qname = model_xbrl.factsByQname.get(concept_qname, [])
            candidates.extend(facts_by_qname)
        except:
            pass
    
    # Fallback: iterate all facts
    if not candidates:
        for fact in model_xbrl.facts:
            fact_qname = None
            if hasattr(fact, "qname") and fact.qname:
                fact_qname = fact.qname
            elif hasattr(fact, "elementQname") and fact.elementQname:
                fact_qname = fact.elementQname
            elif hasattr(fact, "concept") and fact.concept and hasattr(fact.concept, "qname"):
                fact_qname = fact.concept.qname
            
            if fact_qname == concept_qname:
                candidates.append(fact)
    
    if not candidates:
        return None, f"No facts found for concept {concept_qname}"
    
    # Filter and score candidates
    scored_candidates = []
    
    for fact in candidates:
        if not fact.context:
            continue
        
        score = 0
        
        # Check period
        period_end = get_period_end(fact.context)
        if fiscal_year and period_end:
            try:
                period_year = int(period_end.split("-")[0])
                if period_year == fiscal_year:
                    score += 10  # High priority for matching fiscal year
                else:
                    continue  # Skip facts from wrong year
            except:
                pass
        
        # Check consolidated
        if is_consolidated_context(fact.context):
            score += 5  # Prefer consolidated
        
        # Check if fact has a value
        value = None
        if hasattr(fact, "textValue") and fact.textValue is not None:
            try:
                text_val = str(fact.textValue).strip()
                if text_val:
                    cleaned = text_val.replace(",", "").replace("$", "").strip()
                    if cleaned:
                        value = float(cleaned)
            except:
                pass
        
        if value is None and hasattr(fact, "xValue") and fact.xValue is not None:
            try:
                value = float(fact.xValue)
            except:
                pass
        
        if value is None:
            continue  # Skip facts without values
        
        scored_candidates.append((fact, score, value))
    
    if not scored_candidates:
        return None, f"No matching facts found for concept {concept_qname} (fiscal_year={fiscal_year})"
    
    # Sort by score (descending), then by absolute value (descending for totals)
    scored_candidates.sort(key=lambda x: (-x[1], -abs(x[2])))
    
    best_fact = scored_candidates[0][0]
    return best_fact, None


def extract_fact_data(fact: Any) -> Dict[str, Any]:
    """
    Extract data from a fact for JSON output.
    
    Args:
        fact: Arelle fact object
        
    Returns:
        Dictionary with value, unit, context_id, period_start, period_end, dimensions
    """
    result = {
        "value": None,
        "unit": None,
        "context_id": None,
        "period_start": None,
        "period_end": None,
        "dimensions": {},
    }
    
    if not fact:
        return result
    
    # Extract value
    value = None
    if hasattr(fact, "textValue") and fact.textValue is not None:
        try:
            text_val = str(fact.textValue).strip()
            if text_val:
                cleaned = text_val.replace(",", "").replace("$", "").strip()
                if cleaned:
                    value = float(cleaned)
        except:
            pass
    
    if value is None and hasattr(fact, "xValue") and fact.xValue is not None:
        try:
            value = float(fact.xValue)
        except:
            pass
    
    result["value"] = value
    
    # Extract unit
    if hasattr(fact, "unitID") and fact.unitID and hasattr(fact.modelXbrl, "units"):
        unit_obj = fact.modelXbrl.units.get(fact.unitID)
        if unit_obj:
            if hasattr(unit_obj, "measures"):
                measures = unit_obj.measures
                if measures and len(measures) > 0:
                    unit_str = str(measures[0][0]) if isinstance(measures[0], tuple) else str(measures[0])
                    result["unit"] = unit_str
    
    if not result["unit"]:
        result["unit"] = "USD"  # Default
    
    # Extract context info
    if fact.context:
        result["context_id"] = fact.contextID if hasattr(fact, "contextID") else None
        result["period_start"] = get_period_start(fact.context)
        result["period_end"] = get_period_end(fact.context)
        result["dimensions"] = extract_dimensions_from_context(fact.context)
    
    return result


def traverse_presentation_tree(
    model_xbrl: Any,
    rels: Any,
    concept: Any,
    depth: int = 0,
    parent_label: Optional[str] = None,
    fiscal_year: Optional[int] = None,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Recursively traverse presentation tree starting from a concept.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        rels: Presentation relationship set
        concept: Starting concept
        depth: Current depth in tree (0 for root)
        parent_label: Label of parent concept
        fiscal_year: Target fiscal year (optional)
        verbose: Whether to print warnings
        
    Returns:
        List of line item dictionaries
    """
    lines = []
    
    if not concept:
        return lines
    
    # Get concept QName
    concept_qname = None
    concept_local_name = None
    if hasattr(concept, "qname") and concept.qname:
        concept_qname = str(concept.qname)
        concept_local_name = concept_qname.split(":")[-1] if ":" in concept_qname else concept_qname
    
    # Get label
    label = None
    preferred_label_role = None
    
    # Try to get preferred label from relationship (if we have parent relationship)
    # For now, use standard label
    try:
        if hasattr(concept, "label"):
            label = concept.label("standard")
            if not label and hasattr(concept, "qname"):
                label = concept.qname.localName if hasattr(concept.qname, "localName") else concept_local_name
    except:
        label = concept_local_name
    
    if not label:
        label = concept_local_name or "Unknown"
    
    # Check if abstract
    is_abstract = False
    if hasattr(concept, "isAbstract"):
        is_abstract = concept.isAbstract
    
    # Get order (default to depth * 1000 for ordering)
    order = depth * 1000
    
    # Find fact if not abstract
    fact = None
    fact_data = {
        "value": None,
        "unit": None,
        "context_id": None,
        "period_start": None,
        "period_end": None,
        "dimensions": {},
    }
    
    if not is_abstract:
        fact, error = find_best_fact_for_concept(model_xbrl, concept, fiscal_year)
        if fact:
            fact_data = extract_fact_data(fact)
        elif verbose and error:
            print(f"WARNING: {error}")
    
    # Build line dict
    line = {
        "label": label,
        "concept_qname": concept_qname,
        "concept_local_name": concept_local_name,
        "depth": depth,
        "is_abstract": is_abstract,
        "order": order,
        "parent_label": parent_label,
        "value": fact_data["value"],
        "unit": fact_data["unit"],
        "context_id": fact_data["context_id"],
        "period_start": fact_data["period_start"],
        "period_end": fact_data["period_end"],
        "dimensions": fact_data["dimensions"],
    }
    
    lines.append(line)
    
    # Get children relationships
    try:
        child_rels = rels.fromModelObject(concept)
        if child_rels:
            # Sort by order
            child_rels_list = list(child_rels)
            child_rels_list.sort(key=lambda rel: rel.order if hasattr(rel, "order") and rel.order is not None else 999999)
            
            # Process children
            for rel in child_rels_list:
                child_concept = None
                if hasattr(rel, "toModelObject"):
                    child_concept = rel.toModelObject
                
                if child_concept:
                    # Get order from relationship
                    child_order = rel.order if hasattr(rel, "order") and rel.order is not None else order + len(lines)
                    
                    # Recursively process child
                    child_lines = traverse_presentation_tree(
                        model_xbrl,
                        rels,
                        child_concept,
                        depth=depth + 1,
                        parent_label=label,
                        fiscal_year=fiscal_year,
                        verbose=verbose,
                    )
                    
                    # Update order in child lines
                    for child_line in child_lines:
                        if child_line.get("order") == (depth + 1) * 1000:  # Default order
                            child_line["order"] = child_order
                    
                    lines.extend(child_lines)
    except Exception as e:
        if verbose:
            print(f"WARNING: Error processing children for concept {concept_qname}: {e}")
    
    return lines


def extract_income_statement_lines(
    model_xbrl: Any,
    role_uri: str,
    fiscal_year: Optional[int] = None,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Extract income statement lines by traversing presentation tree.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        role_uri: Income statement role URI
        fiscal_year: Target fiscal year (optional)
        verbose: Whether to print warnings
        
    Returns:
        List of line item dictionaries
    """
    # Get presentation relationships
    rels = get_income_statement_rels(model_xbrl, role_uri)
    
    all_lines = []
    
    # Get root concepts
    root_concepts = []
    try:
        if hasattr(rels, "rootConcepts"):
            root_concepts = list(rels.rootConcepts) if rels.rootConcepts else []
    except:
        pass
    
    # If no rootConcepts, try to find roots by looking for concepts with no incoming relationships
    if not root_concepts:
        # This is a fallback - we'd need to iterate all concepts
        # For now, try to get first concept from relationships
        try:
            # Get all concepts that appear in relationships
            seen_concepts = set()
            for rel in rels.modelRelationships:
                if hasattr(rel, "fromModelObject") and rel.fromModelObject:
                    seen_concepts.add(rel.fromModelObject)
                if hasattr(rel, "toModelObject") and rel.toModelObject:
                    seen_concepts.add(rel.toModelObject)
            
            # Find concepts that are "from" but never "to" (roots)
            from_concepts = set()
            to_concepts = set()
            for rel in rels.modelRelationships:
                if hasattr(rel, "fromModelObject") and rel.fromModelObject:
                    from_concepts.add(rel.fromModelObject)
                if hasattr(rel, "toModelObject") and rel.toModelObject:
                    to_concepts.add(rel.toModelObject)
            
            root_concepts = list(from_concepts - to_concepts)
        except Exception as e:
            if verbose:
                print(f"WARNING: Could not determine root concepts: {e}")
            return all_lines
    
    if not root_concepts:
        if verbose:
            print("WARNING: No root concepts found in income statement presentation tree")
        return all_lines
    
    # Traverse from each root
    for root_concept in root_concepts:
        root_lines = traverse_presentation_tree(
            model_xbrl,
            rels,
            root_concept,
            depth=0,
            parent_label=None,
            fiscal_year=fiscal_year,
            verbose=verbose,
        )
        all_lines.extend(root_lines)
    
    # Sort all lines by order
    all_lines.sort(key=lambda line: line.get("order", 999999))
    
    return all_lines


def write_income_statement_json(
    output_path: Path,
    company_info: str,
    fiscal_year: Optional[int],
    role_uri: str,
    role_label: str,
    lines: List[Dict[str, Any]],
) -> None:
    """
    Write income statement to JSON file.
    
    Args:
        output_path: Path to output JSON file
        company_info: Company name
        fiscal_year: Fiscal year (optional)
        role_uri: Income statement role URI
        role_label: Human-readable role label
        lines: List of line item dictionaries
    """
    data = {
        "company": company_info,
        "fiscal_year": fiscal_year,
        "role_uri": role_uri,
        "role_label": role_label,
        "lines": lines,
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reconstruct income statement from XBRL presentation tree"
    )
    parser.add_argument(
        "--instance-path",
        type=str,
        required=True,
        help="Path to XBRL instance file (e.g., data/xbrl/ford_2024_10k.ixbrl)",
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        default=None,
        help="Target fiscal year (optional, defaults to latest available)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        required=True,
        help="Output JSON file path (e.g., outputs/ford_income_statement_2024.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output (warnings, counts, etc.)",
    )
    
    args = parser.parse_args()
    
    try:
        # Load XBRL instance
        if args.verbose:
            print(f"Loading XBRL instance from: {args.instance_path}")
        
        model_xbrl = load_xbrl_instance(args.instance_path)
        
        if args.verbose:
            print(f"Loaded {len(model_xbrl.facts)} facts, {len(model_xbrl.contexts)} contexts")
        
        # Extract company info
        company_info = extract_company_info(model_xbrl)
        
        # Find income statement role
        if args.verbose:
            print("Finding income statement role...")
        
        role_uri, role_label = find_income_statement_role(model_xbrl, verbose=args.verbose)
        
        if args.verbose:
            print(f"Found income statement role: {role_label}")
            print(f"  Role URI: {role_uri}")
            if args.fiscal_year:
                print(f"Target fiscal year: {args.fiscal_year}")
        
        # Extract income statement lines
        if args.verbose:
            print("Traversing presentation tree...")
        
        lines = extract_income_statement_lines(
            model_xbrl,
            role_uri,
            fiscal_year=args.fiscal_year,
            verbose=args.verbose,
        )
        
        if args.verbose:
            lines_with_values = sum(1 for line in lines if line.get("value") is not None)
            print(f"Extracted {len(lines)} line items ({lines_with_values} with values)")
        
        # Write JSON
        output_path = Path(args.output_json)
        write_income_statement_json(
            output_path,
            company_info,
            args.fiscal_year,
            role_uri,
            role_label,
            lines,
        )
        
        print(f"Successfully wrote income statement JSON to {output_path}")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

