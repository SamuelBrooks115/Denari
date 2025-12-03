"""
build_fmp_stable_normalized.py — Build normalized financials from cached FMP /stable data.

This script loads cached FMP /stable raw JSON files and normalizes them into
a single unified view for a specific fiscal year for any ticker.

Example (PowerShell):
    python scripts/build_fmp_stable_normalized.py `
        --symbol F `
        --fiscal-year 2024 `
        --input-dir data/fmp_stable_raw `
        --output-json outputs/F_FY2024_fmp_stable_normalized.json
"""

from __future__ import annotations

import argparse
import json
import sys
<<<<<<< Updated upstream
from dataclasses import asdict
=======
>>>>>>> Stashed changes
from pathlib import Path

from app.data.fmp_stable_normalizer import (
    normalize_for_year_stable,
    NormalizedFinancialsStable,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build normalized financials from cached FMP /stable data"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Stock ticker symbol (e.g., F, AAPL, MSFT)",
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        required=True,
        help="Target fiscal year (e.g., 2024)",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/fmp_stable_raw",
        help="Input directory with cached FMP /stable JSON files (default: data/fmp_stable_raw)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        required=True,
        help="Path to output normalized JSON file",
    )
    
    args = parser.parse_args()
    
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    try:
        input_dir = Path(args.input_dir)
        symbol = args.symbol.upper()
        
        # Load raw JSON files
        income_file = input_dir / f"{symbol}_income_statement_stable_raw.json"
        balance_file = input_dir / f"{symbol}_balance_sheet_stable_raw.json"
        cash_flow_file = input_dir / f"{symbol}_cash_flow_stable_raw.json"
        
        if not income_file.exists():
            raise FileNotFoundError(f"Income statement file not found: {income_file}")
        if not balance_file.exists():
            raise FileNotFoundError(f"Balance sheet file not found: {balance_file}")
        if not cash_flow_file.exists():
            raise FileNotFoundError(f"Cash flow file not found: {cash_flow_file}")
        
        logger.info(f"Loading raw FMP /stable data for {symbol} fiscal year {args.fiscal_year}")
        
        with income_file.open("r", encoding="utf-8") as f:
            income_data = json.load(f)
        
        with balance_file.open("r", encoding="utf-8") as f:
            balance_data = json.load(f)
        
        with cash_flow_file.open("r", encoding="utf-8") as f:
            cash_flow_data = json.load(f)
        
        # Normalize
        normalized = normalize_for_year_stable(
            symbol=symbol,
            fiscal_year=args.fiscal_year,
            income_stmt_raw=income_data,
            balance_sheet_raw=balance_data,
            cash_flow_raw=cash_flow_data,
        )
        
        # Convert to dict and structure output
        normalized_dict = asdict(normalized)
        
        output_data = {
            "symbol": normalized.symbol,
            "fiscal_year": normalized.fiscal_year,
            "period_end_date": normalized.period_end_date,
            "normalized": normalized_dict,
        }
        
        # Write JSON
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
<<<<<<< Updated upstream
        print(f"✓ Successfully built normalized financials and wrote to {args.output_json}")
=======
        print(f"Successfully built normalized financials and wrote to {args.output_json}")
>>>>>>> Stashed changes
        print(f"  Symbol: {normalized.symbol}")
        print(f"  Fiscal Year: {normalized.fiscal_year}")
        print(f"  Period End: {normalized.period_end_date}")
        if normalized.revenue:
            print(f"  Revenue: ${normalized.revenue:,.0f}")
        if normalized.net_income:
            print(f"  Net Income: ${normalized.net_income:,.0f}")
<<<<<<< Updated upstream
        if normalized.total_assets:
            print(f"  Total Assets: ${normalized.total_assets:,.0f}")
        if normalized.total_debt:
            print(f"  Total Debt: ${normalized.total_debt:,.0f}")
=======
>>>>>>> Stashed changes
    
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

