"""
fetch_ford_fmp_raw.py — Fetch and cache raw FMP financial data for Ford.

This script fetches income statement, balance sheet, and cash flow data
from the FMP API and caches them to JSON files.

Usage (PowerShell):
    python scripts/fetch_ford_fmp_raw.py `
        --ticker F `
        --limit 10 `
        --output-dir data/fmp_raw
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
        description="Fetch and cache raw FMP financial data for a ticker"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default="F",
        help="Stock ticker symbol (default: F for Ford)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of annual periods to fetch (default: 10)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/fmp_raw",
        help="Output directory for cached JSON files (default: data/fmp_raw)",
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
        
        ticker = args.ticker.upper()
        
        # Fetch income statement
        logger.info(f"Fetching income statement for {ticker}...")
        income_data = fetch_income_statement(ticker, limit=args.limit)
        income_file = output_dir / f"{ticker}_income_statement_raw.json"
        with income_file.open("w", encoding="utf-8") as f:
            json.dump(income_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(income_data)} income statement(s) to {income_file}")
        
        # Fetch balance sheet
        logger.info(f"Fetching balance sheet for {ticker}...")
        balance_data = fetch_balance_sheet(ticker, limit=args.limit)
        balance_file = output_dir / f"{ticker}_balance_sheet_raw.json"
        with balance_file.open("w", encoding="utf-8") as f:
            json.dump(balance_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(balance_data)} balance sheet(s) to {balance_file}")
        
        # Fetch cash flow
        logger.info(f"Fetching cash flow for {ticker}...")
        cash_flow_data = fetch_cash_flow(ticker, limit=args.limit)
        cash_flow_file = output_dir / f"{ticker}_cash_flow_raw.json"
        with cash_flow_file.open("w", encoding="utf-8") as f:
            json.dump(cash_flow_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(cash_flow_data)} cash flow statement(s) to {cash_flow_file}")
        
        print(f"\nSuccessfully fetched and cached FMP data for {ticker}")
        print(f"  Income statement: {income_file}")
        print(f"  Balance sheet: {balance_file}")
        print(f"  Cash flow: {cash_flow_file}")
    
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

