"""
Example usage of the XBRL debt extractor.

This script demonstrates how to use the debt extractor to extract and analyze
debt facts from XBRL instances.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.xbrl.debt_extractor import (
    DebtSegment,
    extract_debt_facts_from_instance,
    extract_debt_for_filing,
    extract_debt_for_ticker,
)


def example_extract_from_cached_file():
    """Example: Extract debt facts from a cached company facts JSON file."""
    print("=" * 80)
    print("Example 1: Extract from cached file")
    print("=" * 80)
    
    # Load cached Ford company facts
    cached_file = Path("outputs/ford_all_tags_with_amounts.json")
    if not cached_file.exists():
        print(f"File not found: {cached_file}")
        print("Skipping this example.")
        return
    
    with cached_file.open('r', encoding='utf-8') as f:
        cached_data = json.load(f)
    
    # Handle different cached file structures
    if "facts" in cached_data:
        facts_payload = cached_data
    elif "tagsByTaxonomy" in cached_data:
        # Convert tagsByTaxonomy structure to facts structure
        facts_payload = {
            "cik": cached_data.get("cik", "0000037996"),
            "entityName": cached_data.get("entityName", "Ford Motor Co"),
            "facts": cached_data["tagsByTaxonomy"],
        }
    elif "us-gaap" in cached_data:
        # Direct us-gaap structure
        facts_payload = {
            "cik": cached_data.get("cik", "0000037996"),
            "entityName": cached_data.get("entityName", "Ford Motor Co"),
            "facts": {"us-gaap": cached_data["us-gaap"]},
        }
    else:
        print("Unknown file structure, cannot extract debt facts")
        return
    
    # Extract debt facts for 2024
    result = extract_debt_facts_from_instance(facts_payload, report_date="2024-12-31")
    
    print(f"\nCompany: {result.company}")
    print(f"CIK: {result.cik}")
    print(f"Report Date: {result.report_date}")
    print(f"\nTotal debt facts extracted: {len(result.facts)}")
    
    # Group by segment
    consolidated = result.get_consolidated_facts()
    ford_credit = result.get_ford_credit_facts()
    company_excl = result.get_company_excl_ford_credit_facts()
    other = result.get_facts_by_segment(DebtSegment.OTHER)
    
    print(f"\nBy Segment:")
    print(f"  Consolidated: {len(consolidated)} facts")
    print(f"  Ford Credit: {len(ford_credit)} facts")
    print(f"  Company excl. Ford Credit: {len(company_excl)} facts")
    print(f"  Other: {len(other)} facts")
    
    # Show some examples
    print(f"\nSample Consolidated Facts (first 5):")
    for fact in consolidated[:5]:
        print(f"  {fact.tag}: ${fact.value:,.0f} ({fact.label})")
    
    if ford_credit:
        print(f"\nSample Ford Credit Facts (first 3):")
        for fact in ford_credit[:3]:
            print(f"  {fact.tag}: ${fact.value:,.0f} ({fact.label})")


def example_extract_from_edgar():
    """Example: Extract debt facts directly from EDGAR."""
    print("\n" + "=" * 80)
    print("Example 2: Extract from EDGAR (requires internet)")
    print("=" * 80)
    
    try:
        # Extract for Ford by ticker
        result = extract_debt_for_ticker("F", report_date="2024-12-31")
        
        print(f"\nCompany: {result.company}")
        print(f"CIK: {result.cik}")
        print(f"Total debt facts: {len(result.facts)}")
        
        # Show summary by segment
        print(f"\nSummary by Segment:")
        for segment in DebtSegment:
            facts = result.get_facts_by_segment(segment)
            if facts:
                total_value = sum(f.value for f in facts)
                print(f"  {segment.value}: {len(facts)} facts, Total: ${total_value:,.0f}")
    
    except Exception as e:
        print(f"Error: {e}")
        print("(This requires internet connection and EDGAR API access)")


def example_extract_by_cik():
    """Example: Extract debt facts by CIK."""
    print("\n" + "=" * 80)
    print("Example 3: Extract by CIK")
    print("=" * 80)
    
    try:
        # Ford CIK = 37996
        result = extract_debt_for_filing(37996, report_date="2024-12-31")
        
        print(f"\nCompany: {result.company}")
        print(f"CIK: {result.cik}")
        print(f"Total debt facts: {len(result.facts)}")
        
        # Show unique tags
        tags = sorted(set(f.tag for f in result.facts))
        print(f"\nUnique debt tags found: {len(tags)}")
        print(f"Sample tags: {', '.join(tags[:10])}")
    
    except Exception as e:
        print(f"Error: {e}")
        print("(This requires internet connection and EDGAR API access)")


if __name__ == "__main__":
    # Run examples
    example_extract_from_cached_file()
    # Uncomment to test EDGAR extraction (requires internet):
    # example_extract_from_edgar()
    # example_extract_by_cik()

