"""
fetch_fmp_industry_screener.py — Fetch and export company screener results from FMP /stable API.

This script allows you to filter companies by sector, industry, and market cap range,
then exports the results to a JSON file.

Example (PowerShell):
    # Search for Technology companies with market cap between $10B and $1T
    python scripts/fetch_fmp_industry_screener.py `
        --sector "Technology" `
        --min-cap 10000000000 `
        --max-cap 1000000000000 `
        --output-json data/fmp_stable_raw/tech_companies.json

    # Search for specific industry
    python scripts/fetch_fmp_industry_screener.py `
        --industry "Consumer Electronics" `
        --min-cap 100000000000 `
        --output-json data/fmp_stable_raw/consumer_electronics.json

    # Get all companies (no filters)
    python scripts/fetch_fmp_industry_screener.py `
        --output-json data/fmp_stable_raw/all_companies.json `
        --limit 200
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from app.data.fmp_client import fetch_company_screener
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and export company screener results from FMP /stable API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--sector",
        type=str,
        default=None,
        help="Filter by sector (e.g., 'Technology', 'Healthcare')",
    )
    parser.add_argument(
        "--industry",
        type=str,
        default=None,
        help="Filter by industry (e.g., 'Consumer Electronics', 'Banks—Regional')",
    )
    parser.add_argument(
        "--min-cap",
        type=int,
        default=None,
        help="Minimum market cap in dollars (e.g., 10000000000 for $10B)",
    )
    parser.add_argument(
        "--max-cap",
        type=int,
        default=None,
        help="Maximum market cap in dollars (e.g., 1000000000000 for $1T)",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=0,
        help="Page number (0-indexed, default: 0)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of results per page (default: 100, max: 200)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="data/fmp_stable_raw/screener_results.json",
        help="Output JSON file path (default: data/fmp_stable_raw/screener_results.json)",
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.limit < 1 or args.limit > 200:
        print("ERROR: --limit must be between 1 and 200", file=sys.stderr)
        sys.exit(1)
    
    if args.page < 0:
        print("ERROR: --page must be >= 0", file=sys.stderr)
        sys.exit(1)
    
    if args.min_cap is not None and args.max_cap is not None:
        if args.min_cap > args.max_cap:
            print("ERROR: --min-cap cannot be greater than --max-cap", file=sys.stderr)
            sys.exit(1)
    
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    try:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build filter summary
        filters = []
        if args.sector:
            filters.append(f"sector={args.sector}")
        if args.industry:
            filters.append(f"industry={args.industry}")
        if args.min_cap:
            filters.append(f"minCap=${args.min_cap:,}")
        if args.max_cap:
            filters.append(f"maxCap=${args.max_cap:,}")
        
        filter_str = ", ".join(filters) if filters else "none (all companies)"
        
        logger.info(f"Fetching screener results with filters: {filter_str}")
        logger.info(f"Page: {args.page}, Limit: {args.limit}")
        
        # Fetch screener results
        results = fetch_company_screener(
            sector=args.sector,
            industry=args.industry,
            market_cap_min=args.min_cap,
            market_cap_max=args.max_cap,
            limit=args.limit,
            page=args.page,
        )
        
        # Prepare output data
        output_data = {
            "filters": {
                "sector": args.sector,
                "industry": args.industry,
                "minCap": args.min_cap,
                "maxCap": args.max_cap,
                "page": args.page,
                "limit": args.limit,
            },
            "resultCount": len(results),
            "results": results,
        }
        
        # Write to JSON file
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Wrote {len(results)} companies to {output_path}")
        
        print(f"\n✓ Successfully fetched {len(results)} companies")
        print(f"  Filters: {filter_str}")
        print(f"  Page: {args.page}, Limit: {args.limit}")
        print(f"  Output file: {output_path}")
        
        # Show summary - first 10 companies as examples
        if results:
            print(f"\nSample companies (first 10):")
            for i, company in enumerate(results[:10], 1):
                symbol = company.get("symbol") or company.get("Symbol") or "N/A"
                name = company.get("companyName") or company.get("name") or company.get("company_name") or "N/A"
                sector = company.get("sector") or company.get("Sector") or "N/A"
                industry = company.get("industry") or company.get("Industry") or "N/A"
                market_cap = company.get("marketCap") or company.get("market_cap") or company.get("MarketCap") or 0
                
                # Format market cap
                if market_cap >= 1_000_000_000_000:
                    cap_str = f"${market_cap / 1_000_000_000_000:.2f}T"
                elif market_cap >= 1_000_000_000:
                    cap_str = f"${market_cap / 1_000_000_000:.2f}B"
                elif market_cap >= 1_000_000:
                    cap_str = f"${market_cap / 1_000_000:.2f}M"
                else:
                    cap_str = f"${market_cap:,}"
                
                print(f"  {i}. {symbol:8s} - {name[:40]:40s} | {sector[:20]:20s} | {cap_str:>12s}")
            
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more")
        
        # If we got the full limit, suggest pagination
        if len(results) == args.limit:
            print(f"\n  Note: Results may be paginated. Use --page {args.page + 1} to fetch next page.")
    
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

