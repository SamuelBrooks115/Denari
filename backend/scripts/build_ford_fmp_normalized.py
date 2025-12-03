"""
build_ford_fmp_normalized.py — Build normalized financials from cached FMP data.

This script loads cached FMP raw JSON files and normalizes them into
a single unified view for a specific fiscal year.

Usage (PowerShell):
    python scripts/build_ford_fmp_normalized.py `
        --ticker F `
        --fiscal-year 2024 `
        --input-dir data/fmp_raw `
        --output-json outputs/F_FY2024_fmp_normalized.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.data.fmp_normalizer import normalize_for_year, NormalizedFinancials
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build normalized financials from cached FMP data"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default="F",
        help="Stock ticker symbol (default: F for Ford)",
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
        default="data/fmp_raw",
        help="Input directory with cached FMP JSON files (default: data/fmp_raw)",
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
        ticker = args.ticker.upper()
        
        # Load raw JSON files
        income_file = input_dir / f"{ticker}_income_statement_raw.json"
        balance_file = input_dir / f"{ticker}_balance_sheet_raw.json"
        cash_flow_file = input_dir / f"{ticker}_cash_flow_raw.json"
        
        if not income_file.exists():
            raise FileNotFoundError(f"Income statement file not found: {income_file}")
        if not balance_file.exists():
            raise FileNotFoundError(f"Balance sheet file not found: {balance_file}")
        if not cash_flow_file.exists():
            raise FileNotFoundError(f"Cash flow file not found: {cash_flow_file}")
        
        logger.info(f"Loading raw FMP data for {ticker} fiscal year {args.fiscal_year}")
        
        with income_file.open("r", encoding="utf-8") as f:
            income_data = json.load(f)
        
        with balance_file.open("r", encoding="utf-8") as f:
            balance_data = json.load(f)
        
        with cash_flow_file.open("r", encoding="utf-8") as f:
            cash_flow_data = json.load(f)
        
        # Normalize
        normalized = normalize_for_year(
            ticker=ticker,
            fiscal_year=args.fiscal_year,
            income_stmt_raw=income_data,
            balance_sheet_raw=balance_data,
            cash_flow_raw=cash_flow_data,
        )
        
        # Convert to dict and structure output
        normalized_dict = asdict(normalized)
        
        output_data = {
            "ticker": normalized.ticker,
            "fiscal_year": normalized.fiscal_year,
            "period_end_date": normalized.period_end_date,
            "income_statement": {
                "revenue": normalized.revenue,
                "cost_of_revenue": normalized.cost_of_revenue,
                "gross_profit": normalized.gross_profit,
                "operating_expenses": normalized.operating_expenses,
                "operating_income": normalized.operating_income,
                "ebitda": normalized.ebitda,
                "pretax_income": normalized.pretax_income,
                "income_tax_expense": normalized.income_tax_expense,
                "net_income": normalized.net_income,
            },
            "balance_sheet": {
                "total_assets": normalized.total_assets,
                "total_liabilities": normalized.total_liabilities,
                "cash_and_equivalents": normalized.cash_and_equivalents,
                "inventory": normalized.inventory,
                "accounts_receivable": normalized.accounts_receivable,
                "accounts_payable": normalized.accounts_payable,
                "accrued_expenses": normalized.accrued_expenses,
                "ppe_net": normalized.ppe_net,
                "total_debt": normalized.total_debt,
            },
            "cash_flow": {
                "dividends_paid": normalized.dividends_paid,
                "share_repurchases": normalized.share_repurchases,
            },
        }
        
        # Write JSON
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully built normalized financials and wrote to {args.output_json}")
        print(f"  Ticker: {normalized.ticker}")
        print(f"  Fiscal Year: {normalized.fiscal_year}")
        print(f"  Period End: {normalized.period_end_date}")
        if normalized.revenue:
            print(f"  Revenue: ${normalized.revenue:,.0f}")
        if normalized.net_income:
            print(f"  Net Income: ${normalized.net_income:,.0f}")
    
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

