"""
build_ford_fact_table.py — Build normalized fact table from Ford XBRL instance.

This script extracts all facts from a Ford XBRL/iXBRL instance and writes
a normalized fact table JSON with comprehensive metadata.

Usage (PowerShell):
    python scripts/build_ford_fact_table.py `
        --instance-path data/xbrl/ford_2024_10k.ixbrl `
        --output-json outputs/F_FY2024_fact_table.json `
        --fiscal-year 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.xbrl.fact_table_extractor import write_fact_table_json


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build normalized fact table from Ford XBRL instance"
    )
    parser.add_argument(
        "--instance-path",
        type=str,
        required=True,
        help="Path to XBRL/iXBRL instance file",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        required=True,
        help="Path to output JSON file",
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        default=None,
        help="Optional: Filter facts to specific fiscal year",
    )
    
    args = parser.parse_args()
    
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    try:
        write_fact_table_json(
            instance_path=args.instance_path,
            output_path=args.output_json,
            fiscal_year=args.fiscal_year,
        )
        
        print(f"Successfully built fact table and wrote to {args.output_json}")
    
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

