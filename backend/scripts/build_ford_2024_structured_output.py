"""
build_ford_2024_structured_output.py — End-to-end script to build Ford 2024 structured output using Arelle.

This script:
1. Loads Ford 2024 10-K iXBRL using Arelle
2. Extracts Balance Sheet, Income Statement, Cash Flow using statement_extractor
3. Extracts Note 18 (Debt and Commitments) using debt_note_extractor
4. Assembles structured JSON matching our existing schema
5. Runs reconciliation checks
6. Writes output to JSON file

Usage:
    python scripts/build_ford_2024_structured_output.py \
        --xbrl-file data/xbrl/ford_2024_10k.ixbrl \
        --output outputs/F_FY2024_structured_output_arelle.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from app.core.logging import get_logger
from app.services.ingestion.reconciliation import reconcile_all_statements
from app.xbrl.arelle_loader import load_xbrl_instance
from app.xbrl.debt_note_extractor import Note18DebtTable, extract_note18_debt
from app.xbrl.statement_extractor import (
    extract_balance_sheet,
    extract_cash_flow_statement,
    extract_income_statement,
)

logger = get_logger(__name__)

# Ford Motor Company constants
FORD_CIK = "0000037996"
FORD_TICKER = "F"
FORD_COMPANY_NAME = "Ford Motor Company"
FORD_FISCAL_YEAR = 2024


def build_ford_2024_structured_output(
    xbrl_file: str | Path,
    output_file: str | Path,
) -> Dict[str, Any]:
    """
    Build complete structured output for Ford 2024 from Arelle XBRL instance.
    
    Args:
        xbrl_file: Path to Ford 2024 10-K iXBRL file
        output_file: Path to output JSON file
        
    Returns:
        Complete structured output dictionary
    """
    logger.info(f"Building Ford 2024 structured output from: {xbrl_file}")
    
    # Step 1: Load XBRL instance
    logger.info("Loading XBRL instance with Arelle...")
    model_xbrl = load_xbrl_instance(xbrl_file)
    
    # Step 2: Extract financial statements
    logger.info("Extracting financial statements...")
    balance_sheet = extract_balance_sheet(model_xbrl, FORD_FISCAL_YEAR)
    income_statement = extract_income_statement(model_xbrl, FORD_FISCAL_YEAR)
    cash_flow_statement = extract_cash_flow_statement(model_xbrl, FORD_FISCAL_YEAR)
    
    # Step 3: Extract Note 18 (Debt and Commitments)
    logger.info("Extracting Note 18 - Debt and Commitments...")
    note18_table = extract_note18_debt(
        model_xbrl,
        FORD_FISCAL_YEAR,
        company_name=FORD_COMPANY_NAME,
        cik=FORD_CIK,
    )
    
    # Step 4: Assemble structured output
    logger.info("Assembling structured output...")
    
    # Get period end date (from balance sheet or Note 18)
    period_end = f"{FORD_FISCAL_YEAR}-12-31"
    if balance_sheet.get("line_items"):
        for item in balance_sheet["line_items"]:
            periods = item.get("periods", {})
            if periods:
                period_end = list(periods.keys())[0]
                break
    
    # Build statements dictionary
    statements = {
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
        "cash_flow_statement": cash_flow_statement,
    }
    
    # Build Note 18 structure
    note18_cells = []
    for cell in note18_table.cells:
        note18_cells.append({
            "line_item": cell.line_item,
            "raw_concept": cell.raw_concept,
            "label": cell.label,
            "segment": cell.segment,
            "maturity_bucket": cell.maturity_bucket,
            "value": cell.value,
            "unit": cell.unit,
            "period_end": cell.period_end,
            "context_id": cell.context_id,
        })
    
    # Aggregate Note 18 totals
    note18_aggregations = note18_table.aggregate_by_segment_and_maturity()
    
    # Calculate totals by segment
    company_excl_total = note18_table.get_total_by_segment("company_excl_ford_credit")
    ford_credit_total = note18_table.get_total_by_segment("ford_credit")
    consolidated_total = note18_table.get_consolidated_total()
    
    # If consolidated total is 0 but we have segment totals, compute it
    if consolidated_total == 0 and (company_excl_total > 0 or ford_credit_total > 0):
        consolidated_total = company_excl_total + ford_credit_total
        logger.info(
            f"Computed consolidated total from segments: "
            f"{company_excl_total:,.0f} + {ford_credit_total:,.0f} = {consolidated_total:,.0f}"
        )
    
    notes = {
        "debt_and_commitments_note18": {
            "cells": note18_cells,
            "aggregations": note18_aggregations,
            "totals": {
                "company_excl_ford_credit_total_debt": company_excl_total,
                "ford_credit_total_debt": ford_credit_total,
                "consolidated_total_debt": consolidated_total,
            },
            "metadata": {
                "fiscal_year": FORD_FISCAL_YEAR,
                "period_end": note18_table.period_end,
                "total_cells": len(note18_cells),
            },
        },
    }
    
    # Step 5: Run reconciliation
    logger.info("Running reconciliation checks...")
    reconciliation = reconcile_all_statements(statements, [period_end])
    
    # Step 6: Build complete output structure
    result = {
        "company": FORD_COMPANY_NAME,
        "ticker": FORD_TICKER,
        "cik": FORD_CIK,
        "fiscal_year": FORD_FISCAL_YEAR,
        "periods": [period_end],
        "statements": statements,
        "notes": notes,
        "reconciliation": reconciliation,
        "metadata": {
            "extraction_method": "arelle",
            "xbrl_file": str(xbrl_file),
            "extraction_timestamp": None,  # Will be set below
        },
    }
    
    # Add extraction timestamp
    from datetime import datetime, timezone
    result["metadata"]["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
    
    # Step 7: Write to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing structured output to: {output_path}")
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Successfully wrote structured output to: {output_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("Ford 2024 Structured Output Summary")
    print("=" * 80)
    print(f"Company: {FORD_COMPANY_NAME}")
    print(f"Fiscal Year: {FORD_FISCAL_YEAR}")
    print(f"Period End: {period_end}")
    print(f"\nFinancial Statements:")
    print(f"  Income Statement: {len(income_statement.get('line_items', []))} line items")
    print(f"  Balance Sheet: {len(balance_sheet.get('line_items', []))} line items")
    print(f"  Cash Flow: {len(cash_flow_statement.get('line_items', []))} line items")
    print(f"\nNote 18 - Debt and Commitments:")
    print(f"  Total cells: {len(note18_cells)}")
    print(f"  Company excl. Ford Credit: ${company_excl_total:,.0f}")
    print(f"  Ford Credit: ${ford_credit_total:,.0f}")
    print(f"  Consolidated: ${consolidated_total:,.0f}")
    print(f"\nReconciliation:")
    print(f"  Balance Sheet: {reconciliation.get('balance_sheet', {}).get('status', 'unknown')}")
    print(f"  Cash Flow: {reconciliation.get('cash_flow', {}).get('status', 'unknown')}")
    print(f"  IS to CF: {reconciliation.get('is_to_cf', {}).get('status', 'unknown')}")
    print(f"  Overall: {reconciliation.get('overall_status', 'unknown')}")
    print("=" * 80)
    
    return result


def main():
    """Main entry point."""
    import sys
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    parser = argparse.ArgumentParser(
        description="Build Ford 2024 structured output from Arelle XBRL instance"
    )
    parser.add_argument(
        "--xbrl-file",
        type=str,
        default="data/xbrl/ford_2024_10k.ixbrl",
        help="Path to Ford 2024 10-K iXBRL file (default: data/xbrl/ford_2024_10k.ixbrl)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/F_FY2024_structured_output_arelle.json",
        help="Output JSON file path (default: outputs/F_FY2024_structured_output_arelle.json)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="arelle.log",
        help="Arelle log file path (default: arelle.log)",
    )
    
    args = parser.parse_args()
    
    try:
        result = build_ford_2024_structured_output(
            xbrl_file=args.xbrl_file,
            output_file=args.output,
        )
        
        print(f"\n[OK] Successfully built structured output with {len(result.get('statements', {}))} statements")
        print(f"  Output file: {args.output}")
    
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease provide a valid XBRL file path.")
        print("You can download Ford's 2024 10-K iXBRL from SEC EDGAR.")
        print("\nExample:")
        print("  python scripts/build_ford_2024_structured_output.py \\")
        print("    --xbrl-file /path/to/ford_2024_10k.ixbrl")
    
    except ImportError as e:
        print(f"\n✗ Error: {e}")
        print("\nArelle is not installed. Install with:")
        print("  pip install arelle-release")
        print("  or")
        print("  poetry add arelle-release")
    
    except Exception as e:
        import sys
        if sys.platform == "win32":
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

