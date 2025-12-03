# Interest-Bearing Debt Extraction Module

## Overview

The `debt_extractor.py` module provides a comprehensive, auditable system for extracting interest-bearing debt from multiple data sources. It implements 5 fallback methods to ensure reliable debt calculation with full transparency.

## Key Features

- **Multiple Fallback Methods**: 5 independent methods for debt calculation
- **Full Auditability**: Every component and calculation step is documented
- **Human-Readable Reports**: Generate detailed reconciliation reports
- **Ford-Specific Support**: Handles Automotive + Credit segment splits
- **Type-Safe**: Uses dataclasses with full type hints

## Module Structure

### Dataclasses

- **`DebtComponent`**: Represents a single debt component with source information
- **`DebtMethodResult`**: Result from a single calculation method
- **`InterestBearingDebtResult`**: Final result with all methods attempted

### Core Functions

1. **`get_xbrl_debt_values()`** - Method 1: XBRL tag aggregation
2. **`get_statement_debt_values()`** - Method 2: Structured statement reconstruction
3. **`get_total_debt_summarized()`** - Method 3: Explicit "Total Debt" lines
4. **`get_segmented_debt_if_applicable()`** - Method 4: Ford-style segment split
5. **`compute_interest_bearing_debt()`** - Main orchestrator
6. **`get_interest_bearing_debt_for_ticker()`** - High-level entry point

## Usage

### Basic Usage

```python
from app.valuation.debt_extractor import get_interest_bearing_debt_for_ticker

# Extract debt for Ford
result = get_interest_bearing_debt_for_ticker(
    ticker="F",
    output_dir="outputs",
    period="2024-12-31",
    assumed_interest_rate=0.06,
)

# Get final value
print(f"Interest-Bearing Debt: ${result.final_value:,.0f}")

# Generate human-readable report
print(result.to_human_readable())
```

### Programmatic Usage

```python
from app.valuation.debt_extractor import compute_interest_bearing_debt

data_sources = {
    "structured_statements_json": structured_json,
    # "xbrl_json": raw_xbrl_json,  # Optional
}

result = compute_interest_bearing_debt(
    data_sources=data_sources,
    period="2024-12-31",
    assumed_interest_rate=0.06,
)
```

## Debt Definition

**Included:**
- Short-term borrowings
- Commercial paper
- Current portion of long-term debt
- Long-term debt (all maturities)
- Finance lease liabilities
- Secured/unsecured notes
- Interest-bearing borrowings from subsidiaries

**Excluded:**
- Accounts payable
- Accrued liabilities
- Operating lease liabilities
- Pension liabilities
- Deferred revenue
- Warranty obligations
- Taxes payable

## Method Priority

Methods are attempted in this order:

1. **XBRL Aggregation** - Sum of all debt XBRL tags
2. **Structured Statement** - Sum of debt line items from balance sheet
3. **Total Debt Summarized** - Use explicit "Total Debt" line if available
4. **Segmented Debt** - Ford-style Automotive + Credit split
5. **Interest Expense Backsolve** - Last resort: Interest Expense / Assumed Rate

The first reliable method becomes the primary result.

## Human-Readable Output

The `to_human_readable()` method generates a detailed report showing:

- Final interest-bearing debt value
- Primary method used
- All methods attempted with their results
- Component-level breakdown for each method
- Formulas applied
- Warnings and assumptions

Example output:

```
================================================================================
INTEREST-BEARING DEBT EXTRACTION REPORT
================================================================================

Period: 2024-12-31

Final Interest-Bearing Debt: $26,000,000,000

Primary Method: STRUCTURED_STATEMENT

--------------------------------------------------------------------------------
METHOD DETAILS
--------------------------------------------------------------------------------

Method 1: XBRL_AGGREGATION
  Description: Sum of all interest-bearing debt XBRL tags from company facts
  Result: $26,000,000,000
  Formula: sum(all_debt_xbrl_tags)
  Components (3):
    - Short-Term Borrowings (us-gaap:ShortTermBorrowings, context='Consolidated'): 5,000,000,000
    - Long-Term Debt, Noncurrent (us-gaap:LongTermDebtNoncurrent, context='Consolidated'): 20,000,000,000
    - Finance Lease Liability, Current (us-gaap:FinanceLeaseLiabilityCurrent, context='Consolidated'): 1,000,000,000

Method 2: STRUCTURED_STATEMENT
  Description: Sum of debt line items from structured balance sheet
  Result: $26,000,000,000
  Formula: Short-Term Debt + Current Portion of Long-Term Debt + Long-Term Debt + Finance Lease Liabilities
  Components (3):
    - Short-Term Borrowings (us-gaap:ShortTermBorrowings, context='Consolidated'): 5,000,000,000
    - Long-Term Debt, Noncurrent (us-gaap:LongTermDebtNoncurrent, context='Consolidated'): 20,000,000,000
    - Finance Lease Liability, Current (us-gaap:FinanceLeaseLiabilityCurrent, context='Consolidated'): 1,000,000,000
  [PRIMARY METHOD USED]
```

## Testing

Run unit tests:

```bash
pytest tests/test_debt_extractor.py -v
```

## Integration

This module integrates with:

- `app/services/ingestion/structured_output.py` - Structured JSON format
- `app/validation/generate_ford_json.py` - Ford JSON generation
- `app/core/model_role_map.py` - Model role definitions

## Example Script

See `app/valuation/example_usage.py` for complete usage examples.

