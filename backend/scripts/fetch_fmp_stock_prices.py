"""
fetch_fmp_stock_prices.py — Fetch and cache stock price data from FMP /stable API.

This script fetches current quote and historical price data from the FMP /stable API
and caches them to JSON files for any ticker.

Example (PowerShell):
    # Fetch current quote only
    python scripts/fetch_fmp_stock_prices.py `
        --symbol F `
        --output-dir data/fmp_stable_raw
    
    # Fetch quote + 1 year of historical prices
    python scripts/fetch_fmp_stock_prices.py `
        --symbol F `
        --historical-days 365 `
        --output-dir data/fmp_stable_raw
    
    # Fetch quote + historical prices for date range
    python scripts/fetch_fmp_stock_prices.py `
        --symbol F `
        --from-date 2023-01-01 `
        --to-date 2024-12-31 `
        --output-dir data/fmp_stable_raw
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.data.fmp_client import fetch_historical_prices, fetch_quote
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and cache stock price data from FMP /stable API"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Stock ticker symbol (e.g., F, AAPL, MSFT)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/fmp_stable_raw",
        help="Output directory for cached JSON files (default: data/fmp_stable_raw)",
    )
    parser.add_argument(
        "--historical-days",
        type=int,
        default=None,
        help="Number of days of historical prices to fetch (optional)",
    )
    parser.add_argument(
        "--from-date",
        type=str,
        default=None,
        help="Start date for historical prices in YYYY-MM-DD format (optional)",
    )
    parser.add_argument(
        "--to-date",
        type=str,
        default=None,
        help="End date for historical prices in YYYY-MM-DD format (optional)",
    )
    parser.add_argument(
        "--quote-only",
        action="store_true",
        help="Only fetch current quote, skip historical prices",
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
        
        # Fetch current quote
        logger.info(f"Fetching current quote for {symbol}...")
        quote_data = fetch_quote(symbol)
        quote_file = output_dir / f"{symbol}_quote_stable_raw.json"
        with quote_file.open("w", encoding="utf-8") as f:
            json.dump(quote_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote quote data to {quote_file}")
        
        if quote_data.get("price"):
            print(f"  Current Price: ${quote_data.get('price', 0):.2f}")
        if quote_data.get("marketCap"):
            print(f"  Market Cap: ${quote_data.get('marketCap', 0):,.0f}")
        
        # Fetch historical prices if requested
        if not args.quote_only:
            historical_data = None
            
            try:
                if args.historical_days:
                    logger.info(f"Fetching {args.historical_days} days of historical prices for {symbol}...")
                    historical_data = fetch_historical_prices(symbol, limit=args.historical_days)
                elif args.from_date or args.to_date:
                    logger.info(f"Fetching historical prices for {symbol} from {args.from_date or 'start'} to {args.to_date or 'end'}...")
                    historical_data = fetch_historical_prices(symbol, from_date=args.from_date, to_date=args.to_date)
                else:
                    # Default: fetch 1 year of historical data
                    logger.info(f"Fetching 1 year of historical prices for {symbol}...")
                    historical_data = fetch_historical_prices(symbol, limit=365)
                
                if historical_data:
                    historical_file = output_dir / f"{symbol}_historical_prices_stable_raw.json"
                    with historical_file.open("w", encoding="utf-8") as f:
                        json.dump(historical_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"Wrote {len(historical_data)} historical price records to {historical_file}")
                    
                    if historical_data:
                        latest = historical_data[0] if historical_data else {}
                        oldest = historical_data[-1] if historical_data else {}
                        print(f"  Historical Prices: {len(historical_data)} records")
                        if latest.get("date"):
                            print(f"    Latest: {latest.get('date')} - Close: ${latest.get('close', 0):.2f}")
                        if oldest.get("date"):
                            print(f"    Oldest: {oldest.get('date')} - Close: ${oldest.get('close', 0):.2f}")
            
            except RuntimeError as e:
                if "not available" in str(e).lower() or "404" in str(e):
                    print(f"\n⚠ Warning: Historical price data is not available via /stable API")
                    print(f"  Quote data has been saved successfully.")
                    print(f"  To get historical prices, you may need to use /api/v3 endpoints or check your subscription tier.")
                else:
                    raise
        
        print(f"\n✓ Successfully fetched and cached stock price data for {symbol}")
        print(f"  Quote: {quote_file}")
        if not args.quote_only:
            print(f"  Historical prices: {output_dir / f'{symbol}_historical_prices_stable_raw.json'}")
    
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

