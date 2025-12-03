# Migration to Arelle-Based XBRL Extraction

## Summary

This document describes the migration from EDGAR Company Facts API-based extraction to Arelle-based XBRL parsing for financial statement extraction.

## What Changed

### New Modules (Arelle-Based)

1. **`app/xbrl/arelle_loader.py`**
   - Loads XBRL instance documents using Arelle
   - Provides helper functions for role discovery

2. **`app/xbrl/statement_extractor.py`**
   - Extracts Balance Sheet, Income Statement, Cash Flow from Arelle ModelXbrl
   - Maps XBRL concepts to normalized line items via `MASTER_MAP`
   - Handles consolidated context selection

3. **`app/xbrl/debt_note_extractor.py`**
   - Extracts Note 18 (Debt and Commitments) with segment and maturity breakdowns
   - Classifies debt facts by segment (consolidated, company_excl_ford_credit, ford_credit)
   - Classifies by maturity (within_one_year, after_one_year, etc.)

4. **`scripts/build_ford_2024_structured_output.py`**
   - End-to-end script that wires everything together
   - Produces structured JSON matching existing schema
   - Runs reconciliation checks

### Deprecated Modules (Still Present, But Not Used)

The following modules are still in the codebase but should not be used for new extractions:

- `app/services/ingestion/structured_output.py` (EDGAR Company Facts)
- `app/services/ingestion/xbrl/companyfacts_parser.py`
- `app/services/ingestion/clients/edgar_client.py` (for statement extraction)

**Note**: These may still be used for other purposes (e.g., fetching raw company facts for analysis), but the primary extraction pipeline now uses Arelle.

## Benefits of Arelle Approach

1. **More Accurate Debt Extraction**
   - Direct access to Note 18 disclosure tables
   - Segment breakdowns (Company excl. Ford Credit, Ford Credit)
   - Maturity breakdowns (within one year, after one year)

2. **Better Dimension Handling**
   - Direct access to XBRL dimensions and contexts
   - More precise consolidated vs. segment filtering

3. **No API Dependencies**
   - Works with local XBRL files
   - No rate limiting or network issues
   - Faster for repeated extractions

4. **Full Note Disclosure Access**
   - Can extract any note disclosure, not just face statements
   - Access to presentation linkbase relationships

## Migration Steps

### For New Extractions

1. **Install Arelle**:
   ```bash
   poetry add arelle-release
   ```

2. **Download XBRL File**:
   - Get company's 10-K iXBRL from SEC EDGAR
   - Place in `data/xbrl/` directory

3. **Run Extraction**:
   ```bash
   python scripts/build_ford_2024_structured_output.py \
       --xbrl-file data/xbrl/ford_2024_10k.ixbrl \
       --output outputs/F_FY2024_structured_output_arelle.json
   ```

### For Existing Code

If you have code that uses the old `extract_single_year_structured()` or `extract_multi_year_structured()` functions:

1. **Update imports**:
   ```python
   # Old
   from app.services.ingestion.structured_output import extract_single_year_structured
   
   # New
   from app.xbrl.arelle_loader import load_xbrl_instance
   from app.xbrl.statement_extractor import extract_balance_sheet, extract_income_statement, extract_cash_flow_statement
   ```

2. **Update extraction logic**:
   ```python
   # Old
   result = extract_single_year_structured(cik=37996, ticker="F", edgar_client=client)
   
   # New
   model_xbrl = load_xbrl_instance("data/xbrl/ford_2024_10k.ixbrl")
   bs = extract_balance_sheet(model_xbrl, fiscal_year=2024)
   is_stmt = extract_income_statement(model_xbrl, fiscal_year=2024)
   cf = extract_cash_flow_statement(model_xbrl, fiscal_year=2024)
   ```

## Output Schema Compatibility

The new Arelle-based extraction produces JSON that matches the existing schema:

- Same top-level structure: `company`, `ticker`, `cik`, `fiscal_year`, `periods`
- Same `statements` structure: `income_statement`, `balance_sheet`, `cash_flow_statement`
- Same `line_items` format with `tag`, `label`, `model_role`, `periods`, etc.
- **New**: `notes.debt_and_commitments_note18` section with detailed debt breakdowns

## Testing

Run the test suite:

```bash
# Unit tests
pytest tests/test_arelle_statement_extractor.py -v
pytest tests/test_arelle_debt_note_extractor.py -v

# Integration test (requires XBRL file)
python scripts/build_ford_2024_structured_output.py \
    --xbrl-file data/xbrl/ford_2024_10k.ixbrl \
    --output outputs/F_FY2024_structured_output_arelle.json
```

## Known Limitations

1. **Requires Local XBRL Files**: Must download XBRL files from SEC EDGAR manually (or automate download separately)

2. **Arelle Dependency**: Requires Arelle to be installed (adds ~50MB to dependencies)

3. **Company-Specific Logic**: Some segment classification logic is Ford-specific and may need adjustment for other companies

## Future Improvements

1. **Automated XBRL Download**: Add utility to automatically download XBRL files from SEC EDGAR
2. **Multi-Company Support**: Generalize segment classification for other companies
3. **Additional Notes**: Extract other notes (e.g., Note 17 - Leases, Note 19 - Fair Value)
4. **Performance**: Optimize for large XBRL files with many facts

## Questions?

See `app/xbrl/README_ARELLE.md` for detailed documentation on the Arelle-based pipeline.

