"""
Example usage of debt_extractor.py

This script demonstrates how to use the interest-bearing debt extraction module
for Ford Motor Company and other companies.
"""

from pathlib import Path
from app.valuation.debt_extractor import (
    get_interest_bearing_debt_for_ticker,
    compute_interest_bearing_debt,
)


def example_ford_extraction():
    """Example: Extract debt for Ford from JSON files."""
    print("=" * 80)
    print("Example: Ford Motor Company Debt Extraction")
    print("=" * 80)
    
    try:
        result = get_interest_bearing_debt_for_ticker(
            ticker="F",
            output_dir="outputs",
            period="2024-12-31",
            assumed_interest_rate=0.06,
        )
        
        # Print human-readable report
        print(result.to_human_readable())
        
        # Access structured data
        print("\n" + "=" * 80)
        print("Structured Data Access")
        print("=" * 80)
        print(f"Final Value: ${result.final_value:,.0f}" if result.final_value else "Final Value: None")
        print(f"Primary Method: {result.primary_method}")
        print(f"Number of Methods Attempted: {len(result.all_methods)}")
        
        # Show all method results
        print("\nAll Method Results:")
        for i, method in enumerate(result.all_methods, 1):
            status = "✓ RELIABLE" if method.is_reliable() else "✗ UNRELIABLE"
            value_str = f"${method.value:,.0f}" if method.value else "None"
            print(f"  {i}. {method.method_name}: {value_str} [{status}]")
            if method.warnings:
                for warning in method.warnings:
                    print(f"      ⚠ {warning}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nTo use this example:")
        print("1. Run: python -m app.validation.generate_ford_json --single-year")
        print("2. This will generate JSON files in the outputs/ directory")
        print("3. Then run this example again")


def example_programmatic_usage():
    """Example: Programmatic usage with data sources."""
    print("\n" + "=" * 80)
    print("Example: Programmatic Usage")
    print("=" * 80)
    
    # Example structured JSON (simplified)
    structured_json = {
        "statements": {
            "balance_sheet": {
                "line_items": [
                    {
                        "tag": "us-gaap:ShortTermBorrowings",
                        "label": "Short-Term Borrowings",
                        "model_role": "BS_DEBT_CURRENT",
                        "periods": {
                            "2024-12-31": 5000000000.0
                        }
                    },
                    {
                        "tag": "us-gaap:LongTermDebtNoncurrent",
                        "label": "Long-Term Debt, Noncurrent",
                        "model_role": "BS_DEBT_NONCURRENT",
                        "periods": {
                            "2024-12-31": 20000000000.0
                        }
                    },
                ]
            },
            "income_statement": {
                "line_items": [
                    {
                        "tag": "us-gaap:InterestExpense",
                        "label": "Interest Expense",
                        "model_role": "IS_INTEREST_EXPENSE",
                        "periods": {
                            "2024-12-31": 1500000000.0
                        }
                    }
                ]
            }
        },
        "periods": ["2024-12-31"]
    }
    
    data_sources = {
        "structured_statements_json": structured_json,
    }
    
    result = compute_interest_bearing_debt(
        data_sources=data_sources,
        period="2024-12-31",
        assumed_interest_rate=0.06,
    )
    
    print(result.to_human_readable())


if __name__ == "__main__":
    # Run examples
    example_ford_extraction()
    example_programmatic_usage()

