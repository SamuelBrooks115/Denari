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
from app.xbrl.fact_enricher import enrich_fact_with_metadata

# Ford 2024 10-K iXBRL file path
FORD_2024_IXBRL_PATH = Path("data/xbrl/ford_2024_10k.ixbrl")
OUTPUT_PATH = Path("outputs/F_FY2024_arelle_raw_facts.json")

FORD_CIK = "0000037996"
FORD_COMPANY_NAME = "Ford Motor Company"
# TARGET_FISCAL_YEAR is now optional (set via command-line argument)


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
    # isInstantPeriod is a property, not a method
    if hasattr(context, "isInstantPeriod"):
        is_instant = context.isInstantPeriod if not callable(context.isInstantPeriod) else context.isInstantPeriod()
        if is_instant:
            if hasattr(context, "instantDatetime") and context.instantDatetime:
                return context.instantDatetime.date().isoformat()
    
    # Check if it's a duration period (income statement, cash flow)
    # isStartEndPeriod is a property, not a method
    if hasattr(context, "isStartEndPeriod"):
        is_start_end = context.isStartEndPeriod if not callable(context.isStartEndPeriod) else context.isStartEndPeriod()
        if is_start_end:
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
    """
    Extract numeric value from Arelle fact.
    
    Returns:
        float value (including 0.0) if value is available, None if no value
    """
    if not fact:
        return None
    
    try:
        # Try textValue first (for iXBRL facts) - match debug script exactly
        if hasattr(fact, "textValue") and fact.textValue:
            try:
                # Simple approach like debug script - just replace commas and parse
                value = float(str(fact.textValue).replace(",", "").strip())
                return value
            except (ValueError, TypeError):
                pass
        
        # Fallback to xValue (standard XBRL) - only if textValue didn't work
        if hasattr(fact, "xValue") and fact.xValue is not None:
            value = fact.xValue
            if isinstance(value, (int, float)):
                return float(value)  # Returns 0.0 for zero, which is correct
            try:
                return float(str(value))
            except (ValueError, TypeError):
                pass
        
        return None
    
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
    import argparse
    import sys
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    parser = argparse.ArgumentParser(
        description="Dump raw Arelle facts from Ford 2024 10-K with enrichment"
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        default=None,
        help="Optional: Filter facts to specific fiscal year (default: extract all facts)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional: Output file path (default: outputs/F_FY2024_arelle_raw_facts.json)",
    )
    
    args = parser.parse_args()
    
    target_fiscal_year = args.fiscal_year
    output_path = Path(args.output) if args.output else OUTPUT_PATH
    
    print("=" * 80)
    print("Ford 2024 Raw Arelle Facts Dump")
    if target_fiscal_year:
        print(f"Filtering to fiscal year: {target_fiscal_year}")
    else:
        print("Extracting ALL facts (no fiscal year filter)")
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
    
    fact_count = 0
    no_concept_count = 0
    no_value_count = 0
    has_value_count = 0
    
    for fact in model_xbrl.facts:
        fact_count += 1
        
        # Try multiple ways to get QName (don't require fact.concept)
        concept_qname = None
        if hasattr(fact, "qname") and fact.qname:
            concept_qname = str(fact.qname)
        elif hasattr(fact, "elementQname") and fact.elementQname:
            concept_qname = str(fact.elementQname)
        elif hasattr(fact, "concept") and fact.concept and hasattr(fact.concept, "qname"):
            concept_qname = str(fact.concept.qname)
        
        # Skip if we can't get a QName at all
        if not concept_qname:
            no_concept_count += 1
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
        
        # Extract value (include ALL facts, even if value is None for abstract concepts)
        value = extract_fact_value(fact)
        if value is not None:
            has_value_count += 1
        else:
            no_value_count += 1
            # Don't skip - include fact with value=None for abstract concepts, headers, etc.
        
        # Get concept info (try to get label if concept exists)
        label = None
        if hasattr(fact, "concept") and fact.concept:
            if hasattr(fact.concept, "label"):
                try:
                    label = fact.concept.label()
                except:
                    pass
        
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
        
        # Enrich with additional metadata (role, dimensions, display identifiers, calc_bucket)
        enrich_fact_with_metadata(fact, model_xbrl, fact_record)
        
        all_facts.append(fact_record)
    
    print(f"[OK] Collected {len(all_facts)} total facts")
    print(f"  Processed {fact_count} facts from model_xbrl")
    print(f"  Facts without concept: {no_concept_count}")
    print(f"  Facts without value: {no_value_count}")
    print(f"  Facts with value: {has_value_count}")
    print(f"\nPeriod distribution:")
    for period, count in sorted(period_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {period}: {count} facts")
    
    # Filter facts by fiscal year if specified (otherwise include all)
    if target_fiscal_year:
        print(f"\nFiltering facts for fiscal year {target_fiscal_year}...")
        filtered_facts = []
        for f in all_facts:
            # Try both field names (enrichment adds period_end)
            period_end = f.get("period_end") or f.get("end")
            if period_end:
                # Check if period matches target fiscal year
                if str(target_fiscal_year) in str(period_end) or matches_fiscal_year(period_end, target_fiscal_year):
                    filtered_facts.append(f)
        
        print(f"[OK] Found {len(filtered_facts)} facts for fiscal year {target_fiscal_year}")
        if len(filtered_facts) == 0 and len(all_facts) > 0:
            print(f"[WARNING] No facts matched {target_fiscal_year} filter, but {len(all_facts)} facts were collected.")
            print(f"  Sample periods found: {list(period_counts.keys())[:10]}")
            # For debugging: show a sample of what periods we have
            sample_facts = all_facts[:5]
            print(f"  Sample fact periods: {[f.get('period_end') or f.get('end') for f in sample_facts]}")
        
        facts_to_output = filtered_facts
    else:
        print(f"\nNo fiscal year filter specified - including all {len(all_facts)} facts")
        facts_to_output = all_facts
    
    # Group by role for summary
    role_counts: Dict[str, int] = {}
    for fact in facts_to_output:
        role = fact.get("role_uri") or fact.get("role_name") or "unknown"
        role_counts[role] = role_counts.get(role, 0) + 1
    
    print(f"\nFacts by role/statement:")
    for role, count in sorted(role_counts.items(), key=lambda x: -x[1]):
        print(f"  {role}: {count}")
    
    # Build output structure
    output = {
        "company": FORD_COMPANY_NAME,
        "cik": FORD_CIK,
        "fiscal_year": target_fiscal_year,
        "total_facts_collected": len(all_facts),
        "total_facts_output": len(facts_to_output),
        "fiscal_year_filter_applied": target_fiscal_year is not None,
        "facts_by_role": role_counts,
        "facts": facts_to_output,
    }
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nWriting raw facts to: {output_path}")
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Successfully wrote {len(facts_to_output)} facts to {output_path}")
    print(f"\nFile size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    print("\nYou can now inspect the raw facts to identify:")
    print("  - Actual concept QNames used by Ford")
    print("  - Segment/dimension patterns")
    print("  - Period end dates")
    print("  - Role/statement assignments")


if __name__ == "__main__":
    main()

