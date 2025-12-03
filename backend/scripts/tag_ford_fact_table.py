"""
tag_ford_fact_table.py — Apply rule-based tagging to Ford fact table.

This script reads a normalized fact table JSON and applies Ford-specific
tagging rules to assign calculation tags to facts.

Usage (PowerShell):
    python scripts/tag_ford_fact_table.py `
        --input-json outputs/F_FY2024_fact_table.json `
        --output-json outputs/F_FY2024_tagged_facts.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.tagging.rule_based_tagger import tag_fact_table


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Apply rule-based tagging to Ford fact table"
    )
    parser.add_argument(
        "--input-json",
        type=str,
        required=True,
        help="Path to input fact table JSON",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        required=True,
        help="Path to output tagged facts JSON",
    )
    
    args = parser.parse_args()
    
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    try:
        tag_fact_table(
            input_json=args.input_json,
            output_json=args.output_json,
        )
        
        print(f"Successfully tagged fact table and wrote to {args.output_json}")
    
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

