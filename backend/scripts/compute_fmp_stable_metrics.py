"""
compute_fmp_stable_metrics.py — Compute core metrics from normalized FMP /stable data.

This script loads normalized financials JSON and computes key financial metrics
for valuation purposes for any ticker.

Example (PowerShell):
    python scripts/compute_fmp_stable_metrics.py `
        --normalized-json outputs/F_FY2024_fmp_stable_normalized.json `
        --output-json outputs/F_FY2024_fmp_stable_metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.data.fmp_stable_normalizer import NormalizedFinancialsStable
from app.metrics.fmp_stable_metrics import compute_core_metrics_stable
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compute core financial metrics from normalized FMP /stable data"
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
        
        # Reconstruct NormalizedFinancialsStable from JSON
        # Handle structured format from build_fmp_stable_normalized.py
        if "normalized" in data:
            normalized_dict = data["normalized"]
        else:
            # Fallback: assume flat structure
            normalized_dict = data
        
        fin = NormalizedFinancialsStable(**normalized_dict)
        
        # Compute metrics
        metrics = compute_core_metrics_stable(fin)
        
        # Write metrics JSON
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully computed metrics and wrote to {args.output_json}")
        print(f"\nKey Metrics for {metrics['symbol']} FY {metrics['fiscal_year']}:")
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

