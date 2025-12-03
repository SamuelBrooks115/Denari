"""
consolidation.py — Consolidated (dimensionless) fact selection for main-line statements.

This module provides deterministic selection of consolidated financial facts by filtering
out dimensioned/segmented observations (e.g., Ford Credit vs. Company splits, geographic
segments, etc.) to produce stable "core line" values for financial statements.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


def has_dimensions(record: Dict[str, Any]) -> bool:
    """
    Check if a fact record has any dimensions (segments, members, etc.).
    
    Args:
        record: XBRL fact record from Company Facts API
        
    Returns:
        True if record has dimensions, False otherwise
    """
    # Check for segment dimension
    if record.get("segment") or record.get("segments"):
        return True
    
    # Check for other common dimension fields
    # XBRL dimensions can appear in various formats
    if "dimensions" in record and record["dimensions"]:
        return True
    
    # Check for member fields (common in XBRL)
    if "member" in record and record["member"]:
        return True
    
    return False


def select_consolidated_fact(
    facts_for_tag_period: List[Dict[str, Any]],
    tag: str,
    period: str,
) -> Optional[Dict[str, Any]]:
    """
    Select the best consolidated (dimensionless) fact for a given tag and period.
    
    For each tag + period:
    1. Group observations by (end, unit)
    2. Prefer an observation with no dimensions / no segment members
    3. If none are dimensionless, choose the largest-magnitude observation after
       excluding obvious segment/member contexts (e.g., "Ford Credit", geographic segments)
    
    Args:
        facts_for_tag_period: List of fact records for the same tag and period
        tag: XBRL tag name (for logging)
        period: Period end date (for logging)
        
    Returns:
        Dictionary with:
            - value: float value
            - unit: unit string
            - context_metadata: dict with filing info
            - dimensions_used: bool (False if dimensionless, True if dimensions were dropped)
        Or None if no suitable fact found
    """
    if not facts_for_tag_period:
        return None
    
    # Group by (end, unit) - we want same period and same unit
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for fact in facts_for_tag_period:
        end = fact.get("end", "")
        unit = fact.get("_unit") or fact.get("unit") or "USD"
        key = (end, unit)
        if key not in groups:
            groups[key] = []
        groups[key].append(fact)
    
    # For each group, try to find dimensionless facts first
    best_candidate: Optional[Dict[str, Any]] = None
    best_score = -1
    used_dimensions = False
    
    for (end, unit), group in groups.items():
        # Step 1: Prefer dimensionless facts
        dimensionless = [f for f in group if not has_dimensions(f)]
        
        if dimensionless:
            # Among dimensionless, prefer 10-K forms, then by filed date
            candidates = sorted(
                dimensionless,
                key=lambda r: (
                    r.get("form") in {"10-K", "10-K/A"},
                    r.get("filed", ""),
                ),
                reverse=True,
            )
            candidate = candidates[0]
            score = 1000  # High score for dimensionless
            
            if best_candidate is None or score > best_score:
                best_candidate = candidate
                best_score = score
                used_dimensions = False
        
        # Step 2: If no dimensionless, fall back to largest magnitude
        # but exclude obvious segment contexts
        if not dimensionless:
            # Filter out obvious segment contexts
            # Common patterns: "Ford Credit", geographic segments, etc.
            filtered = []
            for f in group:
                segment = f.get("segment") or f.get("segments") or {}
                if isinstance(segment, dict):
                    # Check for common segment member patterns
                    member = segment.get("member") or ""
                    if isinstance(member, str):
                        member_lower = member.lower()
                        # Exclude obvious segments
                        if any(exclude in member_lower for exclude in [
                            "credit", "financial", "segment", "geographic",
                            "region", "division", "subsidiary"
                        ]):
                            continue
                
                filtered.append(f)
            
            # If we filtered everything, use original group
            if not filtered:
                filtered = group
            
            # Choose largest magnitude
            def get_magnitude(fact: Dict[str, Any]) -> float:
                val = fact.get("val")
                try:
                    return abs(float(val)) if val is not None else 0.0
                except (ValueError, TypeError):
                    return 0.0
            
            if filtered:
                candidate = max(filtered, key=get_magnitude)
                score = get_magnitude(candidate)
                
                if best_candidate is None or score > best_score:
                    best_candidate = candidate
                    best_score = score
                    used_dimensions = True
    
    if best_candidate is None:
        logger.warning(f"No consolidated fact found for tag {tag} period {period}")
        return None
    
    # Extract value
    val = best_candidate.get("val")
    try:
        value = float(val) if val is not None else None
    except (ValueError, TypeError):
        logger.warning(f"Invalid value for tag {tag} period {period}: {val}")
        return None
    
    if value is None:
        return None
    
    # Build context metadata
    context_metadata = {
        "filing_type": best_candidate.get("form", ""),
        "filed_date": best_candidate.get("filed", ""),
        "accession": best_candidate.get("accn", ""),
        "fiscal_year": best_candidate.get("fy"),
        "fiscal_period": best_candidate.get("fp", ""),
        "end": best_candidate.get("end", ""),
        "start": best_candidate.get("start"),
    }
    
    # Add dimension info if dimensions were used
    if used_dimensions:
        segment = best_candidate.get("segment") or best_candidate.get("segments")
        if segment:
            context_metadata["segment_info"] = segment
    
    result = {
        "value": value,
        "unit": best_candidate.get("_unit") or best_candidate.get("unit") or "USD",
        "context_metadata": context_metadata,
        "dimensions_used": used_dimensions,
    }
    
    if used_dimensions:
        logger.debug(
            f"Selected fact with dimensions for tag {tag} period {period}: "
            f"value={value}, segment={segment}"
        )
    
    return result

