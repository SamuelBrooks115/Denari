"""
fetch_fmp_industry_screener.py — Fetch and export company screener results from FMP /stable API.

This script allows you to filter companies by sector, industry, and market cap range,
then exports the results to a JSON file.

You can either:
1. Use --interactive to select from available sectors/industries (recommended)
   - When you select a sector, only industries for that sector are shown
   - This prevents invalid sector/industry combinations
2. Use --sector and --industry with exact names (must match FMP exactly)

Example (PowerShell):
    # Interactive mode - select from available lists
    # If you select "Healthcare" sector, only healthcare industries will be shown
    poetry run python scripts/fetch_fmp_industry_screener.py `
        --interactive `
        --min-cap 10000000000 `
        --max-cap 1000000000000 `
        --output-json data/fmp_stable_raw/tech_companies.json

    # Direct mode - specify exact sector/industry names
    poetry run python scripts/fetch_fmp_industry_screener.py `
        --sector "Technology" `
        --min-cap 10000000000 `
        --max-cap 1000000000000 `
        --output-json data/fmp_stable_raw/tech_companies.json

    # Get all companies (no filters)
    poetry run python scripts/fetch_fmp_industry_screener.py `
        --output-json data/fmp_stable_raw/all_companies.json `
        --limit 200
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from app.data.fmp_client import (
    fetch_company_screener,
    fetch_available_sectors,
    fetch_available_industries,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def fetch_industries_for_sector(sector: str) -> list[str]:
    """
    Fetch unique industries for a specific sector by querying the screener.
    
    Args:
        sector: Sector name (e.g., "Healthcare", "Technology")
        
    Returns:
        Sorted list of unique industry names for that sector
    """
    print(f"  Fetching industries for sector '{sector}'...")
    
    try:
        # Fetch a sample of companies from this sector to extract industries
        # Use a larger limit to get a good sample of industries
        companies = fetch_company_screener(
            sector=sector,
            industry=None,
            market_cap_min=None,
            market_cap_max=None,
            limit=200,  # Max limit to get good coverage
            page=0,
        )
        
        # Extract unique industries from the results
        industries = set()
        for company in companies:
            industry = (
                company.get("industry") or 
                company.get("Industry") or 
                company.get("industryName")
            )
            if industry and str(industry).strip():
                industries.add(str(industry).strip())
        
        # Sort for consistent display
        sorted_industries = sorted(list(industries))
        
        logger.info(f"Found {len(sorted_industries)} unique industries for sector '{sector}'")
        return sorted_industries
        
    except Exception as e:
        logger.error(f"Error fetching industries for sector '{sector}': {e}")
        # Fallback: return empty list, will show all industries
        return []


def display_menu(items: list[str], title: str, allow_none: bool = True) -> Optional[str]:
    """
    Display a numbered menu and get user selection.
    
    Args:
        items: List of items to display
        title: Menu title
        allow_none: If True, allow user to skip selection (enter 0 or empty)
        
    Returns:
        Selected item string, or None if skipped
    """
    print(f"\n{title}")
    print("=" * 60)
    
    if allow_none:
        print("  0. (None - skip this filter)")
    
    for i, item in enumerate(items, start=1):
        print(f"  {i}. {item}")
    
    print("=" * 60)
    
    while True:
        try:
            choice = input(f"\nSelect {title.lower()} (0-{len(items)}): ").strip()
            
            if not choice and allow_none:
                return None
            
            choice_num = int(choice)
            
            if choice_num == 0 and allow_none:
                return None
            
            if 1 <= choice_num <= len(items):
                selected = items[choice_num - 1]
                print(f"  ✓ Selected: {selected}")
                return selected
            else:
                print(f"  ✗ Please enter a number between 0 and {len(items)}")
        except ValueError:
            print("  ✗ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            sys.exit(0)


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
        help="Filter by sector (e.g., 'Technology', 'Healthcare'). Use --interactive to select from available list.",
    )
    parser.add_argument(
        "--industry",
        type=str,
        default=None,
        help="Filter by industry (e.g., 'Consumer Electronics', 'Banks—Regional'). Use --interactive to select from available list.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactively select sector and industry from available lists (fetched from FMP)",
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
        # Interactive mode: fetch available options and let user select
        selected_sector = args.sector
        selected_industry = args.industry
        
        if args.interactive:
            print("\n" + "=" * 60)
            print("Interactive Sector & Industry Selection")
            print("=" * 60)
            
            # Fetch available sectors
            if not selected_sector:
                print("\nFetching available sectors from FMP...")
                try:
                    sectors = fetch_available_sectors()
                    if sectors:
                        selected_sector = display_menu(sectors, "Available Sectors")
                    else:
                        print("  ⚠ No sectors available")
                except Exception as e:
                    print(f"  ✗ Error fetching sectors: {e}")
                    print("  Continuing without sector filter...")
            
            # Fetch available industries
            if not selected_industry:
                print("\nFetching available industries from FMP...")
                try:
                    if selected_sector:
                        # If a sector was selected, only show industries for that sector
                        industries = fetch_industries_for_sector(selected_sector)
                        if industries:
                            print(f"  ✓ Found {len(industries)} industries in '{selected_sector}' sector")
                            selected_industry = display_menu(
                                industries, 
                                f"Available Industries (Sector: {selected_sector})"
                            )
                        else:
                            print(f"  ⚠ No industries found for sector '{selected_sector}'")
                            print("  Continuing without industry filter...")
                    else:
                        # No sector selected, show all industries
                        industries = fetch_available_industries()
                        if industries:
                            selected_industry = display_menu(industries, "Available Industries")
                        else:
                            print("  ⚠ No industries available")
                except Exception as e:
                    print(f"  ✗ Error fetching industries: {e}")
                    print("  Continuing without industry filter...")
        
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build filter summary
        filters = []
        if selected_sector:
            filters.append(f"sector={selected_sector}")
        if selected_industry:
            filters.append(f"industry={selected_industry}")
        if args.min_cap:
            filters.append(f"minCap=${args.min_cap:,}")
        if args.max_cap:
            filters.append(f"maxCap=${args.max_cap:,}")
        
        filter_str = ", ".join(filters) if filters else "none (all companies)"
        
        logger.info(f"Fetching screener results with filters: {filter_str}")
        logger.info(f"Page: {args.page}, Limit: {args.limit}")
        
        print(f"\n{'=' * 60}")
        print("Fetching screener results...")
        print(f"Filters: {filter_str}")
        print(f"{'=' * 60}")
        
        # Fetch screener results
        results = fetch_company_screener(
            sector=selected_sector,
            industry=selected_industry,
            market_cap_min=args.min_cap,
            market_cap_max=args.max_cap,
            limit=args.limit,
            page=args.page,
        )
        
        # Prepare output data
        output_data = {
            "filters": {
                "sector": selected_sector,
                "industry": selected_industry,
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

