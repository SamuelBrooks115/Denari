"""
generate_ford_json.py — Script to generate Ford structured output JSON files.

This script generates the JSON files that are then validated by ford_tag_validation.py.

Usage:
    python -m app.validation.generate_ford_json \
        --output-dir ./outputs \
        --single-year \
        --multi-year

This will generate:
    - outputs/F_FY2024_single_year_llm_classified.json
    - outputs/F_multi_year_3years_llm_classified.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.ingestion.clients import EdgarClient
from app.services.ingestion.edgar_adapter import fetch_and_format_structured
from app.services.ingestion.structured_output import (
    extract_multi_year_structured,
    extract_single_year_structured,
    generate_structured_output,
)

# Ford Motor Company constants
FORD_CIK = 37996
FORD_TICKER = "F"


def generate_ford_json(
    output_dir: str | Path = "outputs",
    single_year: bool = True,
    multi_year: bool = True,
    max_filings: int = 3,
) -> None:
    """
    Generate Ford structured output JSON files.
    
    Args:
        output_dir: Directory to save JSON files
        single_year: Whether to generate single-year JSON
        multi_year: Whether to generate multi-year JSON
        max_filings: Maximum number of filings for multi-year (default: 3)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    edgar_client = EdgarClient()
    
    if single_year:
        print(f"\n📊 Generating single-year structured output for {FORD_TICKER}...")
        try:
            # Extract structured data
            result = extract_single_year_structured(
                cik=FORD_CIK,
                ticker=FORD_TICKER,
                edgar_client=edgar_client,
            )
            
            # Apply LLM classification
            print("  Applying LLM classification...")
            result = generate_structured_output(result)
            
            # Extract fiscal year from metadata for filename
            fiscal_year = result.get("metadata", {}).get("fiscal_year", "2024")
            filename = output_dir / f"{FORD_TICKER}_FY{fiscal_year}_single_year_llm_classified.json"
            
            with filename.open('w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved single-year JSON to: {filename}")
            print(f"  Fiscal Year: {fiscal_year}")
            print(f"  Line Items: {sum(len(stmt.get('line_items', [])) for stmt in result.get('statements', {}).values())}")
            
        except Exception as e:
            print(f"❌ Error generating single-year JSON: {e}")
            raise
    
    if multi_year:
        print(f"\n📊 Generating multi-year structured output for {FORD_TICKER}...")
        try:
            # Extract structured data
            result = extract_multi_year_structured(
                cik=FORD_CIK,
                ticker=FORD_TICKER,
                max_filings=max_filings,
                edgar_client=edgar_client,
            )
            
            # Apply LLM classification to each filing
            print("  Applying LLM classification to each filing...")
            for filing in result.get("filings", []):
                # Build a temporary structure for classification
                temp_structure = {
                    "statements": filing.get("statements", {}),
                }
                classified = generate_structured_output(temp_structure)
                filing["statements"] = classified.get("statements", {})
            
            # Extract number of filings for filename
            num_filings = len(result.get("filings", []))
            filename = output_dir / f"{FORD_TICKER}_multi_year_{num_filings}years_llm_classified.json"
            
            with filename.open('w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved multi-year JSON to: {filename}")
            print(f"  Filings: {num_filings}")
            print(f"  Years: {[f.get('fiscal_year') for f in result.get('filings', [])]}")
            
        except Exception as e:
            print(f"❌ Error generating multi-year JSON: {e}")
            raise
    
    print("\n" + "=" * 80)
    print("Generation complete! You can now validate these files with:")
    print("  python -m app.validation.ford_tag_validation \\")
    if single_year:
        print(f"    --single-year {output_dir / f'{FORD_TICKER}_FY{fiscal_year}_single_year_llm_classified.json'}")
    if multi_year:
        print(f"    --multi-year {output_dir / f'{FORD_TICKER}_multi_year_{num_filings}years_llm_classified.json'}")
    print("=" * 80)


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Generate Ford structured output JSON files from EDGAR XBRL data"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Directory to save JSON files (default: outputs)",
    )
    parser.add_argument(
        "--single-year",
        action="store_true",
        help="Generate single-year JSON file",
    )
    parser.add_argument(
        "--multi-year",
        action="store_true",
        help="Generate multi-year JSON file",
    )
    parser.add_argument(
        "--max-filings",
        type=int,
        default=3,
        help="Maximum number of filings for multi-year (default: 3)",
    )
    
    args = parser.parse_args()
    
    if not args.single_year and not args.multi_year:
        # Default: generate both
        args.single_year = True
        args.multi_year = True
    
    generate_ford_json(
        output_dir=args.output_dir,
        single_year=args.single_year,
        multi_year=args.multi_year,
        max_filings=args.max_filings,
    )


if __name__ == "__main__":
    main()

