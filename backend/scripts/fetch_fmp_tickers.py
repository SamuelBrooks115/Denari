"""
fetch_fmp_tickers.py — Fetch and cache list of all available tickers from FMP /stable API.

This script fetches all available ticker symbols from the FMP /stable API
and caches them to a JSON file.

Example (PowerShell):
    python scripts/fetch_fmp_tickers.py `
        --output-json data/fmp_stable_raw/available_tickers.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.data.fmp_client import fetch_available_tickers
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and cache list of all available tickers from FMP /stable API"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="data/fmp_stable_raw/available_tickers.json",
        help="Output JSON file path (default: data/fmp_stable_raw/available_tickers.json)",
    )
    
    args = parser.parse_args()
    
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    try:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Fetch available tickers
        logger.info("Fetching available tickers from FMP...")
        tickers = fetch_available_tickers()
        
        # Write to JSON file
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(tickers, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Wrote {len(tickers)} tickers to {output_path}")
        
        print(f"\n✓ Successfully fetched and cached {len(tickers)} tickers")
        print(f"  Output file: {output_path}")
        
        # Show summary - first 10 tickers as examples
        if tickers:
            print(f"\nSample tickers (first 10):")
            for i, ticker in enumerate(tickers[:10], 1):
                symbol = ticker.get("symbol") or ticker.get("Symbol") or "N/A"
                name = ticker.get("companyName") or ticker.get("name") or ticker.get("Name") or "N/A"
                trading_currency = ticker.get("tradingCurrency") or ticker.get("trading_currency") or ""
                reporting_currency = ticker.get("reportingCurrency") or ticker.get("reporting_currency") or ""
                currency_info = f"{trading_currency}/{reporting_currency}" if trading_currency or reporting_currency else ""
                print(f"  {i}. {symbol:8s} - {name[:45]:45s} ({currency_info})")
            
            if len(tickers) > 10:
                print(f"  ... and {len(tickers) - 10} more")
        
        # Extract just symbols if user wants a simple list
        symbols_only = []
        for ticker in tickers:
            symbol = ticker.get("symbol") or ticker.get("Symbol")
            if symbol:
                symbols_only.append(symbol)
        
        if symbols_only:
            symbols_file = output_path.parent / "available_ticker_symbols_only.json"
            with symbols_file.open("w", encoding="utf-8") as f:
                json.dump(symbols_only, f, indent=2, ensure_ascii=False)
            print(f"\n  Also saved symbols-only list: {symbols_file} ({len(symbols_only)} symbols)")
    
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

