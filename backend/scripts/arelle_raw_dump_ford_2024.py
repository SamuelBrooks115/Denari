"""
arelle_raw_dump_ford_2024.py — Dump raw Arelle facts from Ford 2024 10-K for debugging.

This script:
1. Loads Ford 2024 10-K iXBRL using the same loader as the structured-output script
2. Filters facts to 2024 fiscal year
3. Dumps all facts to JSON for inspection

Usage:
    python scripts/arelle_raw_dump_ford_2024.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.xbrl.arelle_loader import load_xbrl_instance

# Ford 2024 10-K iXBRL file path
FORD_2024_IXBRL_PATH = Path("data/xbrl/ford_2024_10k.ixbrl")
OUTPUT_PATH = Path("outputs/F_FY2024_arelle_raw_facts.json")

FORD_CIK = "0000037996"
FORD_COMPANY_NAME = "Ford Motor Company"
TARGET_FISCAL_YEAR = 2024


def serialize_context_segment(context: Any) -> str:
    """
    Serialize context segment/dimensions to a string for debugging.
    
    Args:
        context: Arelle context object
        
    Returns:
        String representation of segment/dimensions
    """
    if not context:
        return "consolidated"
    
    segments = []
    
    # Check for segment dimensions
    if hasattr(context, "segDimValues") and context.segDimValues:
        for dim in context.segDimValues:
            dim_str = str(dim)
            segments.append(dim_str)
    
    if segments:
        return " | ".join(segments)
    
    return "consolidated"


def get_role_uri_for_fact(model_xbrl: Any, fact: Any) -> str:
    """
    Try to determine which role/statement a fact belongs to.
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        fact: Arelle fact object
        
    Returns:
        Role URI or statement type (e.g., "balance_sheet", "income_statement", "note18")
    """
    if not fact or not fact.concept:
        return "unknown"
    
    # Try to get role from presentation relationships
    # For now, infer from concept name
    concept_qname = str(fact.concept.qname) if hasattr(fact.concept, "qname") else ""
    concept_lower = concept_qname.lower()
    
    # Balance sheet indicators
    if any(keyword in concept_lower for keyword in [
        "assets", "liabilities", "equity", "stockholders", "cash", "inventory",
        "receivable", "payable", "debtcurrent", "debtnoncurrent"
    ]):
        return "balance_sheet"
    
    # Income statement indicators
    if any(keyword in concept_lower for keyword in [
        "revenue", "income", "expense", "cost", "profit", "loss", "earnings"
    ]):
        return "income_statement"
    
    # Cash flow indicators
    if any(keyword in concept_lower for keyword in [
        "cashflow", "cashprovided", "cashused", "operatingactivities",
        "investingactivities", "financingactivities"
    ]):
        return "cash_flow"
    
    # Debt/Note 18 indicators
    if any(keyword in concept_lower for keyword in [
        "debt", "borrowing", "notespayable", "lease", "obligation"
    ]):
        return "note18_debt"
    
    return "other"


def get_period_end(context: Any) -> str | None:
    """Extract period end date from Arelle context."""
    if not context:
        return None
    
    # Check if it's an instant period (balance sheet)
    if hasattr(context, "isInstantPeriod") and context.isInstantPeriod():
        if hasattr(context, "instantDatetime") and context.instantDatetime:
            return context.instantDatetime.date().isoformat()
    
    # Check if it's a duration period (income statement, cash flow)
    if hasattr(context, "isStartEndPeriod") and context.isStartEndPeriod():
        if hasattr(context, "endDatetime") and context.endDatetime:
            # endDatetime is the day AFTER the period ends, so subtract 1 day
            from datetime import timedelta
            end_date = context.endDatetime.date() - timedelta(days=1)
            return end_date.isoformat()
    
    # Fallback: try direct attributes
    if hasattr(context, "instantDatetime") and context.instantDatetime:
        return context.instantDatetime.date().isoformat()
    
    if hasattr(context, "endDatetime") and context.endDatetime:
        from datetime import timedelta
        end_date = context.endDatetime.date() - timedelta(days=1)
        return end_date.isoformat()
    
    return None


def matches_fiscal_year(period_end: str | None, fiscal_year: int) -> bool:
    """Check if period end matches fiscal year."""
    if not period_end:
        return False
    
    try:
        date_obj = datetime.fromisoformat(period_end).date()
        return date_obj.year == fiscal_year
    except (ValueError, TypeError):
        return False


def extract_fact_value(fact: Any) -> float | None:
    """Extract numeric value from Arelle fact."""
    if not fact:
        return None
    
    try:
        value = fact.xValue
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        return float(str(value))
    
    except (ValueError, TypeError, AttributeError):
        return None


def get_unit_string(model_xbrl: Any, fact: Any) -> str:
    """Extract unit string from fact."""
    if not fact or not hasattr(fact, "unitID"):
        return "USD"
    
    unit = "USD"
    if fact.unitID and hasattr(model_xbrl, "units"):
        unit_obj = model_xbrl.units.get(fact.unitID)
        if unit_obj:
            if hasattr(unit_obj, "measures"):
                measures = unit_obj.measures
                if measures and len(measures) > 0:
                    unit = str(measures[0][0]) if isinstance(measures[0], tuple) else str(measures[0])
    
    return unit


def main():
    """Main entry point."""
    import sys
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    print("=" * 80)
    print("Ford 2024 Raw Arelle Facts Dump")
    print("=" * 80)
    
    # Load XBRL instance
    print(f"\nLoading XBRL instance from: {FORD_2024_IXBRL_PATH}")
    if not FORD_2024_IXBRL_PATH.exists():
        print(f"[ERROR] XBRL file not found at {FORD_2024_IXBRL_PATH}")
        print("\nPlease run: python scripts/download_ford_2024_ixbrl.py")
        return
    
    try:
        model_xbrl = load_xbrl_instance(FORD_2024_IXBRL_PATH)
        print(f"[OK] Loaded XBRL instance")
        print(f"  Total facts: {len(model_xbrl.facts)}")
        print(f"  Total contexts: {len(model_xbrl.contexts)}")
    except Exception as e:
        print(f"[ERROR] Error loading XBRL instance: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # First, collect all periods to see what's available
    print(f"\nAnalyzing all periods in XBRL instance...")
    all_periods: Dict[str, int] = {}
    sample_contexts: List[Dict[str, Any]] = []
    
    # Sample first 20 facts to inspect context structure
    for i, fact in enumerate(list(model_xbrl.facts)[:20]):
        if not fact.concept:
            continue
        
        context = fact.context
        context_info = {
            "fact_index": i,
            "concept": str(fact.concept.qname) if hasattr(fact.concept, "qname") else "unknown",
            "has_context": context is not None,
        }
        
        if context:
            # Try different ways to get period
            context_info["context_id"] = getattr(context, "id", None)
            context_info["has_instantDatetime"] = hasattr(context, "instantDatetime")
            context_info["has_endDatetime"] = hasattr(context, "endDatetime")
            context_info["has_startDatetime"] = hasattr(context, "startDatetime")
            
            if hasattr(context, "instantDatetime"):
                context_info["instantDatetime"] = str(context.instantDatetime) if context.instantDatetime else None
            if hasattr(context, "endDatetime"):
                context_info["endDatetime"] = str(context.endDatetime) if context.endDatetime else None
            if hasattr(context, "startDatetime"):
                context_info["startDatetime"] = str(context.startDatetime) if context.startDatetime else None
            
            # Try to get period end
            period_end = get_period_end(context)
            context_info["period_end_extracted"] = period_end
            
            if period_end:
                all_periods[period_end] = all_periods.get(period_end, 0) + 1
        
        sample_contexts.append(context_info)
    
    print(f"Sample context inspection (first 20 facts):")
    for ctx_info in sample_contexts[:5]:
        print(f"  Concept: {ctx_info['concept']}")
        print(f"    Context ID: {ctx_info.get('context_id', 'N/A')}")
        print(f"    Has instantDatetime: {ctx_info.get('has_instantDatetime', False)}")
        print(f"    Has endDatetime: {ctx_info.get('has_endDatetime', False)}")
        if ctx_info.get('instantDatetime'):
            print(f"    instantDatetime: {ctx_info['instantDatetime']}")
        if ctx_info.get('endDatetime'):
            print(f"    endDatetime: {ctx_info['endDatetime']}")
        print(f"    Period end extracted: {ctx_info.get('period_end_extracted', 'None')}")
        print()
    
    print(f"Periods found in sample:")
    for period, count in sorted(all_periods.items())[:20]:
        print(f"  {period}: {count} facts")
    
    # Collect ALL facts first, then filter
    print(f"\nCollecting all facts...")
    all_facts: List[Dict[str, Any]] = []
    period_counts: Dict[str, int] = {}
    
    for fact in model_xbrl.facts:
        if not fact.concept:
            continue
        
        # Get period end (try multiple methods)
        period_end = get_period_end(fact.context)
        
        # If period extraction failed, try direct access
        if not period_end and fact.context:
            if hasattr(fact.context, "endDatetime") and fact.context.endDatetime:
                from datetime import timedelta
                end_date = fact.context.endDatetime.date() - timedelta(days=1)
                period_end = end_date.isoformat()
            elif hasattr(fact.context, "instantDatetime") and fact.context.instantDatetime:
                period_end = fact.context.instantDatetime.date().isoformat()
        
        if period_end:
            period_counts[period_end] = period_counts.get(period_end, 0) + 1
        
        # Extract value (only include numeric facts)
        value = extract_fact_value(fact)
        if value is None:
            continue
        
        # Get concept info
        concept = fact.concept
        concept_qname = str(concept.qname) if hasattr(concept, "qname") else "unknown"
        label = concept.label() if hasattr(concept, "label") else None
        
        # Get unit
        unit = get_unit_string(model_xbrl, fact)
        
        # Get segment/dimensions
        segment = serialize_context_segment(fact.context)
        
        # Get role/statement type
        role_uri = get_role_uri_for_fact(model_xbrl, fact)
        
        # Get context ID
        context_id = fact.contextID if hasattr(fact, "contextID") else None
        
        # Create fact record
        fact_record = {
            "concept_qname": concept_qname,
            "value": value,
            "unit": unit,
            "end": period_end,
            "segment": segment,
            "role_uri": role_uri,
            "context_id": context_id,
            "label": label,
        }
        
        all_facts.append(fact_record)
    
    print(f"[OK] Collected {len(all_facts)} total facts")
    print(f"\nPeriod distribution:")
    for period, count in sorted(period_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {period}: {count} facts")
    
    # Filter facts for 2024 fiscal year
    print(f"\nFiltering facts for fiscal year {TARGET_FISCAL_YEAR}...")
    facts_2024 = [
        f for f in all_facts
        if f["end"] and ("2024" in f["end"] or matches_fiscal_year(f["end"], TARGET_FISCAL_YEAR))
    ]
    
    print(f"[OK] Found {len(facts_2024)} facts for fiscal year {TARGET_FISCAL_YEAR}")
    
    # Group by role for summary
    role_counts: Dict[str, int] = {}
    for fact in facts_2024:
        role = fact["role_uri"]
        role_counts[role] = role_counts.get(role, 0) + 1
    
    print(f"\nFacts by role/statement:")
    for role, count in sorted(role_counts.items(), key=lambda x: -x[1]):
        print(f"  {role}: {count}")
    
    # Build output structure
    output = {
        "company": FORD_COMPANY_NAME,
        "cik": FORD_CIK,
        "fiscal_year": TARGET_FISCAL_YEAR,
        "total_facts": len(facts_2024),
        "facts_by_role": role_counts,
        "facts": facts_2024,
    }
    
    # Write to file
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nWriting raw facts to: {OUTPUT_PATH}")
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Successfully wrote {len(facts_2024)} facts to {OUTPUT_PATH}")
    print(f"\nFile size: {OUTPUT_PATH.stat().st_size / 1024 / 1024:.2f} MB")
    print("\nYou can now inspect the raw facts to identify:")
    print("  - Actual concept QNames used by Ford")
    print("  - Segment/dimension patterns")
    print("  - Period end dates")
    print("  - Role/statement assignments")


if __name__ == "__main__":
    main()

