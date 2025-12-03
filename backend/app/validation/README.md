# Ford Tag Validation Harness

This validation harness validates tag classification for Ford Motor Company (ticker F) against required DCF calculation variables.

## Overview

The harness checks whether the Denari classification correctly identifies specific variables required for DCF model calculations by:

1. Loading and normalizing both single-year and multi-year structured output JSON formats
2. Mapping required variables to expected model roles using the Denari taxonomy
3. Finding and ranking candidate line items for each required variable
4. Generating validation reports (console + JSON)

## Required Variables

### Income Statement
- Revenue
- Operating Costs / Margin
- Gross Margin / Costs
- EBITDA Margins / Costs
- Tax Rate

### Balance Sheet
- PP&E
- Inventory
- Accounts Payable
- Accounts Receivable
- Accrued Expenses

### Cash Flow Statement
- Share Repurchases
- Debt Amount
- Dividend as a % of Net Income

## Usage

### Command Line

```bash
# Validate single-year file
python -m app.validation.ford_tag_validation \
    --single-year /path/to/F_FY2024_single_year.json \
    --output outputs/ford_tag_validation_report.json

# Validate multi-year file
python -m app.validation.ford_tag_validation \
    --multi-year /path/to/F_multi_year_3years.json \
    --output outputs/ford_tag_validation_report.json

# Validate both
python -m app.validation.ford_tag_validation \
    --single-year /path/to/F_FY2024_single_year.json \
    --multi-year /path/to/F_multi_year_3years.json \
    --output outputs/ford_tag_validation_report.json
```

### Python API

```python
from app.validation.ford_tag_validation import validate_ford_files

results = validate_ford_files(
    single_year_path="path/to/single_year.json",
    multi_year_path="path/to/multi_year.json",
    output_path="outputs/report.json"
)
```

## Extending to Other Companies

To extend this validation harness to other companies:

1. **Update file paths**: Change the file paths in `ford_tag_validation.py` or pass them as arguments
2. **Update metadata**: Modify the company name and ticker in the `validate_ford_files` function
3. **Add company-specific rules** (optional): If a company has unique requirements, add them to `role_map.py` or create a company-specific validator

### Example: Extending to Apple (AAPL)

```python
# In ford_tag_validation.py, create a new function:
def validate_apple_files(
    single_year_path: str,
    multi_year_path: str = None,
    output_path: str = "outputs/apple_tag_validation_report.json",
):
    # Same logic, just update metadata
    metadata = {
        "company": "Apple Inc.",
        "ticker": "AAPL",
        ...
    }
    # ... rest of validation logic
```

## Validation Logic

For each required variable:

1. **Find candidates**: All line items whose `model_role` OR `llm_classification.best_fit_role` matches expected role(s)
2. **Rank candidates** by:
   - `is_core_3_statement` (True first)
   - `is_dcf_key` (True first)
   - Highest `llm_classification.confidence`
   - Largest absolute value in most recent period
3. **Select chosen**: Top-ranked candidate becomes the "chosen" line item
4. **Report**: PASS if valid candidate found, FAIL with reason if not

## Output

### Console Output
- Clean table per statement showing variable, expected roles, chosen tag/label, confidence, periods, and PASS/FAIL status
- Summary statistics
- Detailed failure analysis

### JSON Report
Saved to `outputs/ford_tag_validation_report.json` with:
- Metadata (company, ticker, files processed)
- Summary (total, passed, failed)
- Detailed results for each variable

## File Structure

```
app/validation/
├── __init__.py              # Module initialization
├── parser.py                 # JSON format normalization
├── role_map.py              # Variable → model role mapping
├── validator.py             # Core validation logic
├── reporter.py              # Report generation
├── ford_tag_validation.py   # Main validation script
└── README.md                # This file
```

## Classification Gaps

If validation fails, the report will indicate:
- **Missing**: Variable not found in any statement
- **Mis-tagged**: Variable found but with wrong model_role
- **Ambiguous**: Multiple candidates with similar confidence
- **Low confidence**: LLM classification confidence too low

## Next Steps After Ford Validation

Once Ford validation passes:
1. Review any FAIL cases and implement fixes in `structured_output.py` or classification logic
2. Parameterize the harness to accept any ticker
3. Run validation on all S&P 500 companies
4. Aggregate results and identify systematic classification issues

