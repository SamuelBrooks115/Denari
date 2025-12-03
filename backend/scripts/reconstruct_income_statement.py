"""
reconstruct_income_statement.py — Reconstruct income statement in traditional order from FMP data.

This script takes FMP income statement data and reconstructs it in the traditional
format you'd see in a financial report, then exports it as JSON.

Traditional Income Statement Order:
1. Revenue
2. Cost of Revenue (COGS)
3. Gross Profit
4. Operating Expenses (R&D, SG&A, etc.)
5. Operating Income
6. Interest Income/Expense
7. Other Income/Expenses
8. Income Before Tax
9. Income Tax Expense
10. Net Income
11. EPS (Basic and Diluted)

Example (PowerShell):
    python scripts/reconstruct_income_statement.py `
        --symbol AAPL `
        --fiscal-year 2024 `
        --input-file data/fmp_stable_raw/AAPL_income_statement_stable_raw.json `
        --output-json outputs/AAPL_FY2024_income_statement_formatted.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def format_currency(value: Optional[float]) -> Optional[str]:
    """Format currency value as string with commas."""
    if value is None:
        return None
    return f"${value:,.0f}"


def reconstruct_income_statement(
    raw_data: Dict[str, Any],
    symbol: str,
    fiscal_year: int,
) -> Dict[str, Any]:
    """
    Reconstruct income statement in traditional order from FMP raw data.
    
    Args:
        raw_data: Single income statement record from FMP
        symbol: Stock ticker symbol
        fiscal_year: Fiscal year
        
    Returns:
        Dictionary with formatted income statement in traditional order
    """
    # Helper to safely get value
    def get_val(key: str, default: Optional[float] = None) -> Optional[float]:
        val = raw_data.get(key)
        if val is None or val == 0:
            return default
        return float(val)
    
    # Build line items in traditional order
    line_items: List[Dict[str, Any]] = []
    
    # 1. Revenue
    revenue = get_val("revenue")
    if revenue is not None:
        line_items.append({
            "line_number": 1,
            "label": "Revenue",
            "value": revenue,
            "formatted_value": format_currency(revenue),
            "category": "revenue",
            "is_subtotal": False,
        })
    
    # 2. Cost of Revenue (COGS)
    cost_of_revenue = get_val("costOfRevenue")
    if cost_of_revenue is not None:
        line_items.append({
            "line_number": 2,
            "label": "Cost of Revenue",
            "value": cost_of_revenue,
            "formatted_value": format_currency(cost_of_revenue),
            "category": "costs",
            "is_subtotal": False,
        })
    
    # 3. Gross Profit
    gross_profit = get_val("grossProfit")
    if gross_profit is None and revenue is not None and cost_of_revenue is not None:
        gross_profit = revenue - cost_of_revenue
    if gross_profit is not None:
        line_items.append({
            "line_number": 3,
            "label": "Gross Profit",
            "value": gross_profit,
            "formatted_value": format_currency(gross_profit),
            "category": "subtotal",
            "is_subtotal": True,
        })
    
    # 4. Operating Expenses
    # Add a section header
    line_items.append({
        "line_number": 4,
        "label": "Operating Expenses:",
        "value": None,
        "formatted_value": None,
        "category": "header",
        "is_subtotal": False,
    })
    
    # R&D Expenses
    rnd_expenses = get_val("researchAndDevelopmentExpenses")
    if rnd_expenses is not None:
        line_items.append({
            "line_number": 5,
            "label": "  Research and Development",
            "value": rnd_expenses,
            "formatted_value": format_currency(rnd_expenses),
            "category": "operating_expenses",
            "is_subtotal": False,
        })
    
    # SG&A Expenses
    sga_expenses = get_val("sellingGeneralAndAdministrativeExpenses")
    if sga_expenses is not None:
        line_items.append({
            "line_number": 6,
            "label": "  Selling, General and Administrative",
            "value": sga_expenses,
            "formatted_value": format_currency(sga_expenses),
            "category": "operating_expenses",
            "is_subtotal": False,
        })
    
    # Other operating expenses (if broken out separately)
    selling_expenses = get_val("sellingAndMarketingExpenses")
    if selling_expenses is not None:
        line_items.append({
            "line_number": 7,
            "label": "  Selling and Marketing",
            "value": selling_expenses,
            "formatted_value": format_currency(selling_expenses),
            "category": "operating_expenses",
            "is_subtotal": False,
        })
    
    general_expenses = get_val("generalAndAdministrativeExpenses")
    if general_expenses is not None:
        line_items.append({
            "line_number": 8,
            "label": "  General and Administrative",
            "value": general_expenses,
            "formatted_value": format_currency(general_expenses),
            "category": "operating_expenses",
            "is_subtotal": False,
        })
    
    other_expenses = get_val("otherExpenses")
    if other_expenses is not None:
        line_items.append({
            "line_number": 9,
            "label": "  Other Operating Expenses",
            "value": other_expenses,
            "formatted_value": format_currency(other_expenses),
            "category": "operating_expenses",
            "is_subtotal": False,
        })
    
    # Total Operating Expenses (if provided, otherwise calculate)
    total_operating_expenses = get_val("operatingExpenses")
    if total_operating_expenses is None:
        # Calculate from components
        total_operating_expenses = sum([
            rnd_expenses or 0,
            sga_expenses or 0,
            selling_expenses or 0,
            general_expenses or 0,
            other_expenses or 0,
        ])
        if total_operating_expenses == 0:
            total_operating_expenses = None
    
    if total_operating_expenses is not None:
        line_items.append({
            "line_number": 10,
            "label": "Total Operating Expenses",
            "value": total_operating_expenses,
            "formatted_value": format_currency(total_operating_expenses),
            "category": "subtotal",
            "is_subtotal": True,
        })
    
    # 5. Operating Income
    operating_income = get_val("operatingIncome")
    if operating_income is None and gross_profit is not None and total_operating_expenses is not None:
        operating_income = gross_profit - total_operating_expenses
    if operating_income is not None:
        line_items.append({
            "line_number": 11,
            "label": "Operating Income",
            "value": operating_income,
            "formatted_value": format_currency(operating_income),
            "category": "subtotal",
            "is_subtotal": True,
        })
    
    # 6. Interest Income
    interest_income = get_val("interestIncome")
    if interest_income is not None:
        line_items.append({
            "line_number": 12,
            "label": "Interest Income",
            "value": interest_income,
            "formatted_value": format_currency(interest_income),
            "category": "other_income",
            "is_subtotal": False,
        })
    
    # 7. Interest Expense
    interest_expense = get_val("interestExpense")
    if interest_expense is not None:
        line_items.append({
            "line_number": 13,
            "label": "Interest Expense",
            "value": -interest_expense,  # Negative for display
            "formatted_value": format_currency(-interest_expense),
            "category": "other_expenses",
            "is_subtotal": False,
        })
    
    # Net Interest Income (if provided)
    net_interest_income = get_val("netInterestIncome")
    if net_interest_income is not None:
        line_items.append({
            "line_number": 14,
            "label": "Net Interest Income",
            "value": net_interest_income,
            "formatted_value": format_currency(net_interest_income),
            "category": "subtotal",
            "is_subtotal": True,
        })
    
    # 8. Other Income/Expenses
    other_income_expenses = get_val("nonOperatingIncomeExcludingInterest")
    if other_income_expenses is not None:
        line_items.append({
            "line_number": 15,
            "label": "Other Income (Expenses)",
            "value": other_income_expenses,
            "formatted_value": format_currency(other_income_expenses),
            "category": "other_income",
            "is_subtotal": False,
        })
    
    total_other_income = get_val("totalOtherIncomeExpensesNet")
    if total_other_income is not None:
        line_items.append({
            "line_number": 16,
            "label": "Total Other Income (Expenses)",
            "value": total_other_income,
            "formatted_value": format_currency(total_other_income),
            "category": "subtotal",
            "is_subtotal": True,
        })
    
    # 9. Income Before Tax
    income_before_tax = get_val("incomeBeforeTax")
    if income_before_tax is None:
        # Calculate from components
        components = [
            operating_income,
            interest_income,
            -interest_expense if interest_expense else None,
            total_other_income,
        ]
        income_before_tax = sum([c for c in components if c is not None])
        if income_before_tax == 0:
            income_before_tax = None
    
    if income_before_tax is not None:
        line_items.append({
            "line_number": 17,
            "label": "Income Before Tax",
            "value": income_before_tax,
            "formatted_value": format_currency(income_before_tax),
            "category": "subtotal",
            "is_subtotal": True,
        })
    
    # 10. Income Tax Expense
    income_tax_expense = get_val("incomeTaxExpense")
    if income_tax_expense is not None:
        line_items.append({
            "line_number": 18,
            "label": "Income Tax Expense",
            "value": -income_tax_expense,  # Negative for display
            "formatted_value": format_currency(-income_tax_expense),
            "category": "taxes",
            "is_subtotal": False,
        })
    
    # 11. Net Income
    net_income = get_val("netIncome")
    if net_income is None:
        net_income = get_val("netIncomeFromContinuingOperations")
    if net_income is None and income_before_tax is not None and income_tax_expense is not None:
        net_income = income_before_tax - income_tax_expense
    
    if net_income is not None:
        line_items.append({
            "line_number": 19,
            "label": "Net Income",
            "value": net_income,
            "formatted_value": format_currency(net_income),
            "category": "subtotal",
            "is_subtotal": True,
        })
    
    # 12. Earnings Per Share
    eps_basic = get_val("eps")
    eps_diluted = get_val("epsDiluted")
    
    if eps_basic is not None or eps_diluted is not None:
        line_items.append({
            "line_number": 20,
            "label": "Earnings Per Share:",
            "value": None,
            "formatted_value": None,
            "category": "header",
            "is_subtotal": False,
        })
        
        if eps_basic is not None:
            line_items.append({
                "line_number": 21,
                "label": "  Basic",
                "value": eps_basic,
                "formatted_value": f"${eps_basic:.2f}",
                "category": "eps",
                "is_subtotal": False,
            })
        
        if eps_diluted is not None:
            line_items.append({
                "line_number": 22,
                "label": "  Diluted",
                "value": eps_diluted,
                "formatted_value": f"${eps_diluted:.2f}",
                "category": "eps",
                "is_subtotal": False,
            })
    
    # Build final structure
    result = {
        "symbol": symbol,
        "fiscal_year": fiscal_year,
        "period_end_date": raw_data.get("date"),
        "period": raw_data.get("period"),
        "currency": raw_data.get("reportedCurrency", "USD"),
        "filing_date": raw_data.get("filingDate"),
        "accepted_date": raw_data.get("acceptedDate"),
        "income_statement": {
            "line_items": line_items,
            "summary": {
                "revenue": revenue,
                "gross_profit": gross_profit,
                "operating_income": operating_income,
                "income_before_tax": income_before_tax,
                "net_income": net_income,
                "eps_basic": eps_basic,
                "eps_diluted": eps_diluted,
            },
        },
        "raw_data": raw_data,  # Include original for reference
    }
    
    return result


def find_fiscal_year_record(
    income_statements: List[Dict[str, Any]],
    fiscal_year: int,
) -> Optional[Dict[str, Any]]:
    """Find income statement record for specific fiscal year."""
    for stmt in income_statements:
        if str(stmt.get("fiscalYear")) == str(fiscal_year):
            return stmt
    return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reconstruct income statement in traditional order from FMP data"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Stock ticker symbol (e.g., F, AAPL, MSFT)",
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        required=True,
        help="Target fiscal year (e.g., 2024)",
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Path to cached FMP income statement JSON file (optional, will construct path if not provided)",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/fmp_stable_raw",
        help="Input directory with cached FMP JSON files (default: data/fmp_stable_raw)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        required=True,
        help="Path to output formatted income statement JSON file",
    )
    
    args = parser.parse_args()
    
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    try:
        symbol = args.symbol.upper()
        
        # Load income statement data
        if args.input_file:
            input_path = Path(args.input_file)
        else:
            input_dir = Path(args.input_dir)
            input_path = input_dir / f"{symbol}_income_statement_stable_raw.json"
        
        if not input_path.exists():
            raise FileNotFoundError(
                f"Income statement file not found: {input_path}\n"
                f"Run 'python scripts/fetch_fmp_stable_raw.py --symbol {symbol}' first."
            )
        
        logger.info(f"Loading income statement data from: {input_path}")
        
        with input_path.open("r", encoding="utf-8") as f:
            income_statements = json.load(f)
        
        if not isinstance(income_statements, list):
            raise ValueError(f"Expected list of income statements, got {type(income_statements)}")
        
        # Find the record for the specified fiscal year
        raw_data = find_fiscal_year_record(income_statements, args.fiscal_year)
        
        if not raw_data:
            available_years = [str(stmt.get("fiscalYear")) for stmt in income_statements]
            raise ValueError(
                f"No income statement found for {symbol} fiscal year {args.fiscal_year}.\n"
                f"Available years: {', '.join(available_years)}"
            )
        
        # Reconstruct income statement
        logger.info(f"Reconstructing income statement for {symbol} FY {args.fiscal_year}")
        formatted_statement = reconstruct_income_statement(
            raw_data=raw_data,
            symbol=symbol,
            fiscal_year=args.fiscal_year,
        )
        
        # Write output JSON
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(formatted_statement, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Successfully reconstructed income statement and wrote to {args.output_json}")
        print(f"\nSummary for {symbol} FY {args.fiscal_year}:")
        summary = formatted_statement["income_statement"]["summary"]
        if summary.get("revenue"):
            print(f"  Revenue: {format_currency(summary['revenue'])}")
        if summary.get("gross_profit"):
            print(f"  Gross Profit: {format_currency(summary['gross_profit'])}")
        if summary.get("operating_income"):
            print(f"  Operating Income: {format_currency(summary['operating_income'])}")
        if summary.get("net_income"):
            print(f"  Net Income: {format_currency(summary['net_income'])}")
        if summary.get("eps_basic"):
            print(f"  EPS (Basic): ${summary['eps_basic']:.2f}")
        
        print(f"\n  Total Line Items: {len(formatted_statement['income_statement']['line_items'])}")
    
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

