"""
compute_ford_metrics.py — Compute core financial metrics from tagged Ford facts.

This script reads tagged facts JSON and computes key financial metrics
(margins, ratios, totals) for a given fiscal year.

Usage (PowerShell):
    python scripts/compute_ford_metrics.py `
        --tagged-json outputs/F_FY2024_tagged_facts.json `
        --fiscal-year 2024 `
        --output-json outputs/F_FY2024_metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.metrics.ford_core_metrics import compute_metrics_from_json


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compute core financial metrics from tagged Ford facts"
    )
    parser.add_argument(
        "--tagged-json",
        type=str,
        required=True,
        help="Path to tagged facts JSON file",
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        required=True,
        help="Target fiscal year",
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
        metrics = compute_metrics_from_json(
            tagged_json=args.tagged_json,
            fiscal_year=args.fiscal_year,
        )
        
        # Write metrics JSON
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully computed metrics and wrote to {args.output_json}")
        print(f"\nKey Metrics for FY {args.fiscal_year}:")
        print(f"  Revenue: ${metrics.get('revenue', 0):,.0f}")
        print(f"  Net Income: ${metrics.get('net_income', 0):,.0f}")
        if metrics.get('gross_margin'):
            print(f"  Gross Margin: {metrics['gross_margin']:.1%}")
        if metrics.get('operating_margin'):
            print(f"  Operating Margin: {metrics['operating_margin']:.1%}")
        if metrics.get('ebitda_margin'):
            print(f"  EBITDA Margin: {metrics['ebitda_margin']:.1%}")
        print(f"  Total Debt: ${metrics.get('debt_amount', 0):,.0f}")
    
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

