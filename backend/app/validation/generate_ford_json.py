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
from app.validation.debt_triangulation import triangulate_debt_for_period

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
            
            # Run debt triangulation
            print("  Running debt triangulation...")
            periods = result.get("periods", [])
            triangulated_debt = {}
            
            for period in periods:
                statements = result.get("statements", {})
                debt_result = triangulate_debt_for_period(
                    statements=statements,
                    period=period,
                    prev_statements=None,  # Single year, no previous period
                    prev_period=None,
                    assumed_interest_rate=0.06,  # 6% default
                )
                # Use fiscal year as key for consistency
                fiscal_year = result.get("metadata", {}).get("fiscal_year", period[:4])
                period_key = f"FY{fiscal_year}"
                triangulated_debt[period_key] = debt_result
            
            result["triangulated_debt"] = triangulated_debt
            
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
            filings = result.get("filings", [])
            triangulated_debt = {}
            
            for i, filing in enumerate(filings):
                # Build a temporary structure for classification
                temp_structure = {
                    "statements": filing.get("statements", {}),
                }
                classified = generate_structured_output(temp_structure)
                filing["statements"] = classified.get("statements", {})
                
                # Run debt triangulation for this filing
                fiscal_year = filing.get("fiscal_year", "")
                period_key = f"FY{fiscal_year}" if fiscal_year else f"period_{i}"
                
                # Extract period date from balance sheet line items
                current_period = None
                statements = filing.get("statements", {})
                bs = statements.get("balance_sheet", {})
                line_items = bs.get("line_items", [])
                if line_items:
                    # Get first available period from any line item
                    for item in line_items:
                        periods = item.get("periods", {})
                        if periods:
                            current_period = list(periods.keys())[0]
                            break
                
                # Fallback to fiscal year if no period found
                if not current_period and fiscal_year:
                    current_period = f"{fiscal_year}-12-31"
                
                # Get previous period statements for roll-forward
                prev_statements = None
                prev_period = None
                if i < len(filings) - 1:
                    # Previous period is the next filing (filings are latest first)
                    prev_filing = filings[i + 1]
                    prev_statements = prev_filing.get("statements", {})
                    # Extract previous period date
                    prev_bs = prev_statements.get("balance_sheet", {})
                    prev_line_items = prev_bs.get("line_items", [])
                    if prev_line_items:
                        for item in prev_line_items:
                            periods = item.get("periods", {})
                            if periods:
                                prev_period = list(periods.keys())[0]
                                break
                    # Fallback
                    if not prev_period:
                        prev_fiscal_year = prev_filing.get("fiscal_year", "")
                        if prev_fiscal_year:
                            prev_period = f"{prev_fiscal_year}-12-31"
                
                if current_period:
                    print(f"    Triangulating debt for {period_key} ({current_period})...")
                    debt_result = triangulate_debt_for_period(
                        statements=statements,
                        period=current_period,
                        prev_statements=prev_statements,
                        prev_period=prev_period,
                        assumed_interest_rate=0.06,  # 6% default
                    )
                    triangulated_debt[period_key] = debt_result
            
            result["triangulated_debt"] = triangulated_debt
            
            # Extract number of filings for filename
            num_filings = len(filings)
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

