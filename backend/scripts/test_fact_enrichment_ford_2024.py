"""
test_fact_enrichment_ford_2024.py — Test script to verify fact enrichment and debt classification.

This script:
1. Loads Ford FY2024 XBRL via Arelle
2. Builds enriched JSON using fact extraction logic
3. Filters facts where calc_bucket == "interest_bearing_debt_total_component"
4. Prints contributing facts and total sum
5. Verifies the classification logic selects the right line items

Usage:
    python scripts/test_fact_enrichment_ford_2024.py \
        --xbrl-file data/xbrl/ford_2024_10k.ixbrl \
        --fiscal-year 2024
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from app.xbrl.arelle_loader import load_xbrl_instance
from app.xbrl.fact_enricher import enrich_fact_with_metadata


def get_period_end(context: Any) -> str | None:
    """Extract period end date from Arelle context."""
    if not context:
        return None
    
    if hasattr(context, "endDatetime") and context.endDatetime:
        end_date = context.endDatetime.date() - timedelta(days=1)
        return end_date.isoformat()
    elif hasattr(context, "instantDatetime") and context.instantDatetime:
        return context.instantDatetime.date().isoformat()
    
    return None


def extract_fact_value(fact: Any) -> float | None:
    """Extract numeric value from Arelle fact."""
    if not fact:
        return None
    
    try:
        # Try textValue first (for iXBRL)
        if hasattr(fact, "textValue") and fact.textValue:
            try:
                return float(str(fact.textValue).replace(",", "").strip())
            except (ValueError, TypeError):
                pass
        
        # Fallback to xValue
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


def matches_fiscal_year(period_end: str | None, fiscal_year: int) -> bool:
    """Check if period end matches fiscal year."""
    if not period_end:
        return False
    
    try:
        date_obj = datetime.fromisoformat(period_end).date()
        return date_obj.year == fiscal_year
    except (ValueError, TypeError):
        return False


def main():
    """Main entry point."""
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    parser = argparse.ArgumentParser(
        description="Test fact enrichment and debt classification for Ford 2024"
    )
    parser.add_argument(
        "--xbrl-file",
        type=str,
        default="data/xbrl/ford_2024_10k.ixbrl",
        help="Path to Ford 2024 10-K iXBRL file (default: data/xbrl/ford_2024_10k.ixbrl)",
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        default=2024,
        help="Target fiscal year (default: 2024)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional: Save enriched facts to JSON file",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Fact Enrichment Test - Ford 2024")
    print("=" * 80)
    
    # Load XBRL instance
    print(f"\nLoading XBRL instance from: {args.xbrl_file}")
    xbrl_path = Path(args.xbrl_file)
    if not xbrl_path.exists():
        print(f"[ERROR] XBRL file not found at {xbrl_path}")
        print("\nPlease run: python scripts/download_ford_2024_ixbrl.py")
        return 1
    
    try:
        model_xbrl = load_xbrl_instance(xbrl_path)
        print(f"[OK] Loaded XBRL instance")
        print(f"  Total facts: {len(model_xbrl.facts)}")
    except Exception as e:
        print(f"[ERROR] Error loading XBRL instance: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Extract and enrich facts
    print(f"\nExtracting and enriching facts for fiscal year {args.fiscal_year}...")
    enriched_facts: List[Dict[str, Any]] = []
    
    for fact in model_xbrl.facts:
        if not fact.concept:
            continue
        
        # Get period end
        period_end = get_period_end(fact.context)
        if not period_end or not matches_fiscal_year(period_end, args.fiscal_year):
            continue
        
        # Extract value
        value = extract_fact_value(fact)
        if value is None:
            continue
        
        # Get concept info
        concept = fact.concept
        concept_qname = str(concept.qname) if hasattr(concept, "qname") else "unknown"
        
        # Get unit
        unit = get_unit_string(model_xbrl, fact)
        
        # Create fact record
        fact_record = {
            "concept_qname": concept_qname,
            "value": value,
            "unit": unit,
            "end": period_end,
            "context_id": fact.contextID if hasattr(fact, "contextID") else None,
        }
        
        # Enrich with metadata
        enrich_fact_with_metadata(fact, model_xbrl, fact_record)
        
        enriched_facts.append(fact_record)
    
    print(f"[OK] Extracted and enriched {len(enriched_facts)} facts")
    
    # Filter facts for interest-bearing debt total components
    target_period_end = f"{args.fiscal_year}-12-31"
    debt_total_components = [
        f for f in enriched_facts
        if f.get("calc_bucket") == "interest_bearing_debt_total_component"
        and f.get("period_end") == target_period_end
    ]
    
    print(f"\n" + "=" * 80)
    print("Total Interest-Bearing Debt Components")
    print("=" * 80)
    print(f"Target period: {target_period_end}")
    print(f"Found {len(debt_total_components)} component(s):\n")
    
    total_debt = 0.0
    
    for i, fact in enumerate(debt_total_components, 1):
        concept_qname = fact.get("concept_qname", "unknown")
        display_role = fact.get("display_role", "unknown")
        dimensions = fact.get("dimensions", {})
        value = fact.get("value", 0.0)
        unit = fact.get("unit", "USD")
        
        total_debt += value
        
        print(f"{i}. {concept_qname}")
        print(f"   Display Role: {display_role}")
        print(f"   Dimensions: {json.dumps(dimensions, indent=2)}")
        print(f"   Value: {value:,.0f} {unit}")
        print(f"   Line Item ID: {fact.get('line_item_id', 'N/A')}")
        print(f"   Display Line ID: {fact.get('display_line_id', 'N/A')}")
        print()
    
    print("=" * 80)
    print(f"Total Interest-Bearing Debt per JSON enrichment: ${total_debt:,.0f}")
    print("=" * 80)
    
    # Summary statistics
    print(f"\nEnrichment Statistics:")
    print(f"  Total enriched facts: {len(enriched_facts)}")
    
    calc_bucket_counts = {}
    for fact in enriched_facts:
        bucket = fact.get("calc_bucket")
        if bucket:
            calc_bucket_counts[bucket] = calc_bucket_counts.get(bucket, 0) + 1
    
    if calc_bucket_counts:
        print(f"  Facts with calc_bucket:")
        for bucket, count in sorted(calc_bucket_counts.items()):
            print(f"    {bucket}: {count}")
    
    # Check for facts with display identifiers
    facts_with_display_role = sum(1 for f in enriched_facts if f.get("display_role"))
    facts_with_line_item_id = sum(1 for f in enriched_facts if f.get("line_item_id"))
    facts_with_dimensions = sum(1 for f in enriched_facts if f.get("dimensions"))
    
    print(f"  Facts with display_role: {facts_with_display_role}")
    print(f"  Facts with line_item_id: {facts_with_line_item_id}")
    print(f"  Facts with dimensions: {facts_with_dimensions}")
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "company": "Ford Motor Company",
            "fiscal_year": args.fiscal_year,
            "period_end": target_period_end,
            "total_enriched_facts": len(enriched_facts),
            "debt_total_components": debt_total_components,
            "total_interest_bearing_debt": total_debt,
            "all_enriched_facts": enriched_facts,
        }
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Saved enriched facts to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

