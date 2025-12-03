"""
fetch_fmp_stable_raw.py — Fetch and cache raw FMP financial data using /stable endpoints.

This script fetches income statement, balance sheet, and cash flow data
from the FMP /stable API and caches them to JSON files for any ticker.

Example (PowerShell):
    python scripts/fetch_fmp_stable_raw.py `
        --symbol F `
        --limit 10 `
        --output-dir data/fmp_stable_raw
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.data.fmp_client import (
    fetch_balance_sheet,
    fetch_cash_flow,
    fetch_income_statement,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and cache raw FMP financial data using /stable endpoints"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Stock ticker symbol (e.g., F, AAPL, MSFT)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of periods to fetch (default: 10)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/fmp_stable_raw",
        help="Output directory for cached JSON files (default: data/fmp_stable_raw)",
    )
    
    args = parser.parse_args()
    
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    try:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        symbol = args.symbol.upper()
        
        # Fetch income statement
        logger.info(f"Fetching income statement for {symbol}...")
        income_data = fetch_income_statement(symbol, limit=args.limit)
        income_file = output_dir / f"{symbol}_income_statement_stable_raw.json"
        with income_file.open("w", encoding="utf-8") as f:
            json.dump(income_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(income_data)} income statement(s) to {income_file}")
        
        # Fetch balance sheet
        logger.info(f"Fetching balance sheet for {symbol}...")
        balance_data = fetch_balance_sheet(symbol, limit=args.limit)
        balance_file = output_dir / f"{symbol}_balance_sheet_stable_raw.json"
        with balance_file.open("w", encoding="utf-8") as f:
            json.dump(balance_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(balance_data)} balance sheet(s) to {balance_file}")
        
        # Fetch cash flow
        logger.info(f"Fetching cash flow for {symbol}...")
        cash_flow_data = fetch_cash_flow(symbol, limit=args.limit)
        cash_flow_file = output_dir / f"{symbol}_cash_flow_stable_raw.json"
        with cash_flow_file.open("w", encoding="utf-8") as f:
            json.dump(cash_flow_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(cash_flow_data)} cash flow statement(s) to {cash_flow_file}")
        
        print(f"\n✓ Successfully fetched and cached FMP /stable data for {symbol}")
        print(f"  Income Statement: {income_file}")
        print(f"  Balance Sheet: {balance_file}")
        print(f"  Cash Flow: {cash_flow_file}")
        
        # Show summary of most recent period
        if income_data:
            latest = income_data[0]
            print(f"\nMost Recent Period:")
            print(f"  Date: {latest.get('date', 'N/A')}")
            print(f"  Fiscal Year: {latest.get('fiscalYear', 'N/A')}")
            print(f"  Period: {latest.get('period', 'N/A')}")
            if latest.get('revenue'):
                print(f"  Revenue: ${latest.get('revenue', 0):,.0f}")
            if latest.get('netIncome'):
                print(f"  Net Income: ${latest.get('netIncome', 0):,.0f}")
    
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

