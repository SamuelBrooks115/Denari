"""
fetch_fmp_company_profile.py — Fetch and cache company profile/bio information from FMP /stable API.

This script fetches comprehensive company profile data including:
- Company name, description, industry, sector
- Website, logo, address
- Market cap, employees, CEO
- Exchange, currency, ISIN, CUSIP
- And more company bio information

Example (PowerShell):
    python scripts/fetch_fmp_company_profile.py `
        --symbol F `
        --output-dir data/fmp_stable_raw
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.data.fmp_client import fetch_company_profile
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and cache company profile/bio information from FMP /stable API"
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
        "--output-file",
        type=str,
        default=None,
        help="Specific output file path (optional, defaults to {symbol}_company_profile_stable_raw.json)",
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
        
        # Fetch company profile
        logger.info(f"Fetching company profile for {symbol}...")
        profile_data = fetch_company_profile(symbol)
        
        # Determine output file
        if args.output_file:
            output_file = Path(args.output_file)
        else:
            output_file = output_dir / f"{symbol}_company_profile_stable_raw.json"
        
        # Write JSON
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Wrote company profile data to {output_file}")
        
        # Display key information
        print(f"\n✓ Successfully fetched and cached company profile for {symbol}")
        print(f"  Output: {output_file}")
        
        print(f"\nCompany Information:")
        if profile_data.get("companyName"):
            print(f"  Name: {profile_data.get('companyName')}")
        if profile_data.get("symbol"):
            print(f"  Symbol: {profile_data.get('symbol')}")
        if profile_data.get("exchangeShortName"):
            print(f"  Exchange: {profile_data.get('exchangeShortName')}")
        if profile_data.get("industry"):
            print(f"  Industry: {profile_data.get('industry')}")
        if profile_data.get("sector"):
            print(f"  Sector: {profile_data.get('sector')}")
        if profile_data.get("website"):
            print(f"  Website: {profile_data.get('website')}")
        if profile_data.get("description"):
            desc = profile_data.get('description', '')
            if desc:
                # Truncate long descriptions
                desc_preview = desc[:200] + "..." if len(desc) > 200 else desc
                print(f"  Description: {desc_preview}")
        if profile_data.get("ceo"):
            print(f"  CEO: {profile_data.get('ceo')}")
        if profile_data.get("fullTimeEmployees"):
            employees = profile_data.get('fullTimeEmployees')
            try:
                employees_int = int(employees) if employees else 0
                print(f"  Employees: {employees_int:,}")
            except (ValueError, TypeError):
                print(f"  Employees: {employees}")
        if profile_data.get("marketCap"):
            market_cap = profile_data.get('marketCap', 0)
            try:
                market_cap_float = float(market_cap) if market_cap else 0
                print(f"  Market Cap: ${market_cap_float:,.0f}")
            except (ValueError, TypeError):
                print(f"  Market Cap: {market_cap}")
        if profile_data.get("image"):
            print(f"  Logo URL: {profile_data.get('image')}")
        
        # Show all available fields
        print(f"\n  Total fields in profile: {len(profile_data)}")
        print(f"  All fields: {', '.join(sorted(profile_data.keys()))}")
    
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

