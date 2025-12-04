"""
fetch_fmp_enterprise_value.py — Fetch and cache enterprise value data from FMP /stable API.

This script fetches enterprise value data from the FMP /stable API and caches it
to a JSON file for any ticker.

Enterprise Value (EV) = Market Cap + Total Debt - Cash and Cash Equivalents

Example (PowerShell):
    python scripts/fetch_fmp_enterprise_value.py `
        --symbol F `
        --limit 10 `
        --output-dir data/fmp_stable_raw
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.data.fmp_client import fetch_enterprise_value
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and cache enterprise value data from FMP /stable API"
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
        
        # Fetch enterprise value
        logger.info(f"Fetching enterprise value for {symbol}...")
        ev_data = fetch_enterprise_value(symbol, limit=args.limit)
        
        ev_file = output_dir / f"{symbol}_enterprise_value_stable_raw.json"
        with ev_file.open("w", encoding="utf-8") as f:
            json.dump(ev_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(ev_data)} enterprise value record(s) to {ev_file}")
        
        print(f"\n✓ Successfully fetched and cached enterprise value data for {symbol}")
        print(f"  Enterprise Value: {ev_file}")
        
        # Show summary of most recent period
        if ev_data:
            latest = ev_data[0]
            print(f"\nMost Recent Period:")
            if latest.get("date"):
                print(f"  Date: {latest.get('date')}")
            if latest.get("symbol"):
                print(f"  Symbol: {latest.get('symbol')}")
            
            # Enterprise Value
            if latest.get("enterpriseValue") is not None:
                ev = latest.get("enterpriseValue", 0)
                print(f"  Enterprise Value: ${ev:,.0f}")
            
            # Components of EV (FMP uses different field names)
            market_cap = latest.get("marketCapitalization") or latest.get("marketCap")
            total_debt = latest.get("addTotalDebt") or latest.get("totalDebt")
            cash = latest.get("minusCashAndCashEquivalents") or latest.get("cashAndCashEquivalents")
            
            if market_cap is not None:
                print(f"  Market Cap: ${market_cap:,.0f}")
            if total_debt is not None:
                print(f"  Total Debt: ${total_debt:,.0f}")
            if cash is not None:
                # Note: minusCashAndCashEquivalents is already negative in the API response
                cash_abs = abs(cash)
                print(f"  Cash & Equivalents: ${cash_abs:,.0f}")
            
            # Show EV calculation if all components are available
            if market_cap is not None and total_debt is not None and cash is not None:
                # FMP's minusCashAndCashEquivalents is the cash amount (positive), 
                # but the name suggests it's already subtracted. Let's check both interpretations.
                cash_abs = abs(cash)
                calculated_ev_subtract = market_cap + total_debt - cash_abs
                calculated_ev_add = market_cap + total_debt + cash  # if cash is already negative
                
                print(f"\n  EV Calculation: Market Cap + Total Debt - Cash")
                print(f"    ${market_cap:,.0f} + ${total_debt:,.0f} - ${cash_abs:,.0f} = ${calculated_ev_subtract:,.0f}")
                
                if latest.get("enterpriseValue") is not None:
                    actual_ev = latest.get("enterpriseValue", 0)
                    # Check which calculation matches
                    diff_subtract = abs(calculated_ev_subtract - actual_ev)
                    diff_add = abs(calculated_ev_add - actual_ev) if cash < 0 else float('inf')
                    
                    if diff_subtract > 1000 and diff_add > 1000:
                        print(f"    (Note: API reports ${actual_ev:,.0f}, difference may be due to preferred stock, minority interest, or other adjustments)")
                    elif diff_subtract <= 1000:
                        print(f"    ✓ Matches API value: ${actual_ev:,.0f}")
            
            # Additional metrics if available
            if latest.get("stockPrice") is not None:
                print(f"  Stock Price: ${latest.get('stockPrice', 0):.2f}")
            if latest.get("numberOfShares") is not None:
                shares = latest.get("numberOfShares", 0)
                print(f"  Number of Shares: {shares:,.0f}")
    
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

