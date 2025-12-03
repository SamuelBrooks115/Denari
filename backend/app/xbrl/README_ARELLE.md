# Arelle-Based XBRL Extraction Pipeline

This directory contains the Arelle-based XBRL extraction pipeline that replaces the previous EDGAR Company Facts API approach.

## Overview

The pipeline uses **Arelle** (Python XBRL engine) to directly parse XBRL instance documents and extract:
- Balance Sheet
- Income Statement
- Cash Flow Statement
- Note 18 (Debt and Commitments) with segment and maturity breakdowns

## Architecture

### Core Modules

1. **`arelle_loader.py`**: Loads XBRL instance documents using Arelle
   - `load_xbrl_instance()`: Main loader function
   - `get_role_uris()`: Get all role URIs from instance
   - `find_role_by_keywords()`: Find specific roles by keywords

2. **`statement_extractor.py`**: Extracts financial statements
   - `extract_balance_sheet()`: Extract BS from ModelXbrl
   - `extract_income_statement()`: Extract IS from ModelXbrl
   - `extract_cash_flow_statement()`: Extract CF from ModelXbrl
   - Uses `MASTER_MAP` to map XBRL concepts to normalized line items

3. **`debt_note_extractor.py`**: Extracts Note 18 (Debt and Commitments)
   - `extract_note18_debt()`: Extract complete Note 18 table
   - `DebtCell`: Represents one debt fact with segment and maturity
   - `Note18DebtTable`: Complete table with aggregation methods

4. **`fact_enricher.py`**: Enriches XBRL facts with rich metadata for display line identification
   - `enrich_fact_with_metadata()`: Main entry point for fact enrichment
   - Adds role/presentation tree information, dimensions, stable display identifiers
   - Provides `calc_bucket` classification for debt facts
   - See [Fact Enrichment](#fact-enrichment) section below for details

## Installation

### Install Arelle

```bash
# Using pip
pip install arelle-release

# Using poetry
poetry add arelle-release
```

### Verify Installation

```bash
python scripts/debug_arelle_ford_2024.py --xbrl-file data/xbrl/ford_2024_10k.ixbrl
```

## Usage

### Basic Usage

```python
from app.xbrl.arelle_loader import load_xbrl_instance
from app.xbrl.statement_extractor import (
    extract_balance_sheet,
    extract_income_statement,
    extract_cash_flow_statement,
)
from app.xbrl.debt_note_extractor import extract_note18_debt

# Load XBRL instance
model_xbrl = load_xbrl_instance("data/xbrl/ford_2024_10k.ixbrl")

# Extract statements
bs = extract_balance_sheet(model_xbrl, fiscal_year=2024)
is_stmt = extract_income_statement(model_xbrl, fiscal_year=2024)
cf = extract_cash_flow_statement(model_xbrl, fiscal_year=2024)

# Extract Note 18
note18 = extract_note18_debt(
    model_xbrl,
    fiscal_year=2024,
    company_name="Ford Motor Company",
    cik="0000037996",
)
```

### End-to-End Script

```bash
python scripts/build_ford_2024_structured_output.py \
    --xbrl-file data/xbrl/ford_2024_10k.ixbrl \
    --output outputs/F_FY2024_structured_output_arelle.json
```

## Master Chart of Accounts

The `MASTER_MAP` in `statement_extractor.py` maps XBRL concepts to normalized line items:

- **Balance Sheet**: Assets, Liabilities, Equity components
- **Income Statement**: Revenue, COGS, Operating Income, Net Income, etc.
- **Cash Flow**: Operating, Investing, Financing activities

Each normalized line item has multiple candidate XBRL concepts (in precedence order).

## Fact Enrichment

The `fact_enricher.py` module adds comprehensive metadata to XBRL facts to uniquely identify which line item in the 10-K each fact corresponds to. This is essential when multiple facts share the same XBRL concept (e.g., `us-gaap:DebtCurrent`).

### Enriched Fields

Each enriched fact dictionary includes:

#### Concept Metadata
- `concept_local_name`: Local name of the concept (e.g., `"DebtCurrent"`)
- `standard_label`: Standard label from taxonomy (e.g., `"Debt, Current"`)
- `doc_label`: Documentation label if available

#### Presentation Metadata
- `role_uri`: Full role URI where fact appears (e.g., `"http://www.ford.com/role/ConsolidatedBalanceSheet"`)
- `role_name`: Short role name (e.g., `"ConsolidatedBalanceSheet"`)
- `parent_label`: Label of parent presentation node
- `order`: Presentation order within parent

#### Dimensions
- `dimensions`: Dictionary mapping dimension QName to member QName
  ```json
  {
    "f:BusinessSectorAxis": "f:ConsolidatedMember",
    "us-gaap:StatementClassOfStockAxis": "us-gaap:CommonStockMember"
  }
  ```

#### Period Metadata
- `period_start`: ISO date of period start (for duration periods)
- `period_end`: ISO date of period end

#### Display Identifiers
- `display_role`: Normalized role identifier (e.g., `"ConsolidatedBalanceSheet"`)
- `line_item_id`: Stable ID combining role + concept + dimensions
  - Format: `<display_role>__<concept_local_name>__<dimensions_key>`
  - Example: `"ConsolidatedBalanceSheet__DebtCurrent__Consolidated"`
- `display_line_id`: Visual line ID including parent and period
  - Format: `<display_role>__<parent_label_normalized>__<concept_local_name>__<period_end>`
  - Example: `"ConsolidatedBalanceSheet__total_liabilities__DebtCurrent__2024-12-31"`

#### Debt Classification
- `calc_bucket`: Classification for debt calculation
  - `"interest_bearing_debt_total_component"`: Component of total interest-bearing debt (consolidated balance sheet totals)
  - `"interest_bearing_debt_detail_only"`: Note/instrument-level detail, not used for totals
  - `null`: Not related to interest-bearing debt

### Usage

```python
from app.xbrl.fact_enricher import enrich_fact_with_metadata

# Create base fact record
fact_record = {
    "concept_qname": "us-gaap:DebtCurrent",
    "value": 1000000,
    "unit": "USD",
    "end": "2024-12-31",
}

# Enrich with metadata
enrich_fact_with_metadata(fact, model_xbrl, fact_record)

# fact_record now includes all enriched fields
print(fact_record["display_role"])  # "ConsolidatedBalanceSheet"
print(fact_record["line_item_id"])  # "ConsolidatedBalanceSheet__DebtCurrent__Consolidated"
print(fact_record["calc_bucket"])   # "interest_bearing_debt_total_component"
```

### Testing Debt Classification

Use the test script to verify debt classification:

```bash
python scripts/test_fact_enrichment_ford_2024.py \
    --xbrl-file data/xbrl/ford_2024_10k.ixbrl \
    --fiscal-year 2024
```

This will:
1. Load and enrich all facts
2. Filter facts with `calc_bucket == "interest_bearing_debt_total_component"`
3. Print contributing facts and total sum
4. Verify the classification selects the right line items

### Integration

The enrichment is automatically applied in:
- `scripts/arelle_raw_dump_ford_2024.py`: All facts are enriched when dumped to JSON

To integrate into your own extraction:

```python
from app.xbrl.fact_enricher import enrich_fact_with_metadata

for fact in model_xbrl.facts:
    fact_record = {...}  # Your base fact dict
    enrich_fact_with_metadata(fact, model_xbrl, fact_record)
    # fact_record now has all enriched fields
```

## Note 18 Extraction

Note 18 extraction:
1. Finds the Note 18 role using keyword search
2. Extracts all debt-related facts from that role
3. Classifies each fact by:
   - **Segment**: consolidated, company_excl_ford_credit, ford_credit, other
   - **Maturity**: within_one_year, after_one_year, 1-3_years, etc.
4. Creates `DebtCell` objects
5. Aggregates into `Note18DebtTable` with totals by segment and maturity

### Expected Totals (Ford 2024)

- Company excluding Ford Credit: ~$20,654M
- Ford Credit: ~$137,868M
- Consolidated: ~$158,522M

## Adding New Companies

To add support for a new company:

1. **Download XBRL file**: Get the company's 10-K iXBRL from SEC EDGAR
2. **Place in data directory**: `data/xbrl/company_ticker_2024_10k.ixbrl`
3. **Run extraction**:
   ```python
   model_xbrl = load_xbrl_instance("data/xbrl/company_ticker_2024_10k.ixbrl")
   bs = extract_balance_sheet(model_xbrl, fiscal_year=2024)
   # etc.
   ```

The extractors are designed to be company-agnostic, but you may need to:
- Adjust segment classification logic for company-specific dimensions
- Add company-specific XBRL concepts to `MASTER_MAP` if needed
- Customize Note 18 role finding if the company uses different role names

## Output Schema

The structured output matches the existing Denari JSON schema:

```json
{
  "company": "Ford Motor Company",
  "ticker": "F",
  "cik": "0000037996",
  "fiscal_year": 2024,
  "periods": ["2024-12-31"],
  "statements": {
    "income_statement": {
      "line_items": [...]
    },
    "balance_sheet": {
      "line_items": [...]
    },
    "cash_flow_statement": {
      "line_items": [...]
    }
  },
  "notes": {
    "debt_and_commitments_note18": {
      "cells": [...],
      "aggregations": {...},
      "totals": {
        "company_excl_ford_credit_total_debt": ...,
        "ford_credit_total_debt": ...,
        "consolidated_total_debt": ...
      }
    }
  },
  "reconciliation": {...}
}
```

## Reconciliation

The pipeline automatically runs reconciliation checks:
- **Balance Sheet**: Assets ≈ Liabilities + Equity (0.5% tolerance)
- **Cash Flow**: Net Change ≈ CFO + CFI + CFF
- **IS to CF**: Net Income matches between statements

## Migration from Company Facts API

This Arelle-based pipeline **replaces** the previous EDGAR Company Facts API approach:

**Old (Deprecated)**:
- `app/services/ingestion/structured_output.py` (EDGAR Company Facts)
- `app/services/ingestion/xbrl/companyfacts_parser.py`

**New (Current)**:
- `app/xbrl/arelle_loader.py`
- `app/xbrl/statement_extractor.py`
- `app/xbrl/debt_note_extractor.py`

The old code is still present but should not be used for new extractions. The new pipeline provides:
- More accurate debt extraction (Note 18 with segments)
- Better handling of dimensions and contexts
- Direct XBRL parsing (no API dependencies)
- Full note disclosure extraction

## Troubleshooting

### Arelle Not Found

```
ImportError: Arelle is not installed
```

**Solution**: Install Arelle:
```bash
pip install arelle-release
```

### XBRL File Not Found

```
FileNotFoundError: XBRL file not found
```

**Solution**: Download the XBRL file from SEC EDGAR and place it in the expected location.

### No Facts Extracted

If extraction returns empty results:
1. Check that the fiscal year matches the XBRL file
2. Verify the XBRL file is valid (use `debug_arelle_ford_2024.py`)
3. Check Arelle log file for errors

### Note 18 Not Found

If Note 18 extraction fails:
1. Check role URIs: `python scripts/debug_arelle_ford_2024.py`
2. Adjust keywords in `find_note18_role()` if needed
3. The extractor will fall back to searching all debt facts

## Testing

Run tests with:

```bash
pytest tests/test_arelle_statement_extractor.py -v
pytest tests/test_arelle_debt_note_extractor.py -v
```

Note: Some tests require Arelle to be installed and will be skipped if not available.

## References

- [Arelle Documentation](https://arelle.org/)
- [XBRL Specification](https://www.xbrl.org/)
- [SEC EDGAR](https://www.sec.gov/edgar.shtml)

