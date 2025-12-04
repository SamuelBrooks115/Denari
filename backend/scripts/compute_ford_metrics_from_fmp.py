"""
compute_ford_metrics_from_fmp.py — Compute core metrics from normalized FMP data.

This script loads normalized financials JSON and computes key financial metrics
for valuation purposes.

Usage (PowerShell):
    python scripts/compute_ford_metrics_from_fmp.py `
        --normalized-json outputs/F_FY2024_fmp_normalized.json `
        --output-json outputs/F_FY2024_fmp_metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.data.fmp_normalizer import NormalizedFinancials
from app.metrics.fmp_core_metrics import compute_core_metrics_from_normalized
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compute core financial metrics from normalized FMP data"
    )
    parser.add_argument(
        "--normalized-json",
        type=str,
        required=True,
        help="Path to normalized financials JSON file",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        required=True,
        help="Path to output metrics JSON file",
    )
    
    args = parser.parse_args()
    
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    try:
        normalized_path = Path(args.normalized_json)
        if not normalized_path.exists():
            raise FileNotFoundError(
                f"Normalized JSON file not found: {args.normalized_json}"
            )
        
        logger.info(f"Loading normalized financials from: {args.normalized_json}")
        
        with normalized_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Reconstruct NormalizedFinancials from JSON
        # Handle both structured format and flat format
        if "income_statement" in data:
            # Structured format from build_ford_fmp_normalized.py
            fin = NormalizedFinancials(
                ticker=data["ticker"],
                fiscal_year=data["fiscal_year"],
                period_end_date=data["period_end_date"],
                revenue=data["income_statement"].get("revenue"),
                cost_of_revenue=data["income_statement"].get("cost_of_revenue"),
                gross_profit=data["income_statement"].get("gross_profit"),
                operating_expenses=data["income_statement"].get("operating_expenses"),
                operating_income=data["income_statement"].get("operating_income"),
                ebitda=data["income_statement"].get("ebitda"),
                pretax_income=data["income_statement"].get("pretax_income"),
                income_tax_expense=data["income_statement"].get("income_tax_expense"),
                net_income=data["income_statement"].get("net_income"),
                total_assets=data["balance_sheet"].get("total_assets"),
                total_liabilities=data["balance_sheet"].get("total_liabilities"),
                cash_and_equivalents=data["balance_sheet"].get("cash_and_equivalents"),
                inventory=data["balance_sheet"].get("inventory"),
                accounts_receivable=data["balance_sheet"].get("accounts_receivable"),
                accounts_payable=data["balance_sheet"].get("accounts_payable"),
                accrued_expenses=data["balance_sheet"].get("accrued_expenses"),
                ppe_net=data["balance_sheet"].get("ppe_net"),
                total_debt=data["balance_sheet"].get("total_debt"),
                dividends_paid=data["cash_flow"].get("dividends_paid"),
                share_repurchases=data["cash_flow"].get("share_repurchases"),
            )
        else:
            # Flat format (direct NormalizedFinancials dict)
            fin = NormalizedFinancials(**data)
        
        # Compute metrics
        metrics = compute_core_metrics_from_normalized(fin)
        
        # Write metrics JSON
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully computed metrics and wrote to {args.output_json}")
        print(f"\nKey Metrics for {metrics['ticker']} FY {metrics['fiscal_year']}:")
        print(f"  Revenue: ${metrics.get('revenue', 0):,.0f}")
        if metrics.get('net_income'):
            print(f"  Net Income: ${metrics['net_income']:,.0f}")
        if metrics.get('gross_margin'):
            print(f"  Gross Margin: {metrics['gross_margin']:.1%}")
        if metrics.get('operating_margin'):
            print(f"  Operating Margin: {metrics['operating_margin']:.1%}")
        if metrics.get('ebitda_margin'):
            print(f"  EBITDA Margin: {metrics['ebitda_margin']:.1%}")
        if metrics.get('tax_rate'):
            print(f"  Tax Rate: {metrics['tax_rate']:.1%}")
        if metrics.get('debt_amount'):
            print(f"  Total Debt: ${metrics['debt_amount']:,.0f}")
        if metrics.get('dividend_payout_ratio'):
            print(f"  Dividend Payout Ratio: {metrics['dividend_payout_ratio']:.1%}")
    
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

