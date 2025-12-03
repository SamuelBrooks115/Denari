# XBRL Debt Extractor

Comprehensive XBRL debt fact extractor with segment classification for Ford and other issuers.

## Overview

This module extracts all interest-bearing debt facts from XBRL instances (EDGAR Company Facts format), properly classifying them by segment (consolidated, company excluding Ford Credit, Ford Credit, etc.) for use in debt calculations and reconciliation.

## Features

1. **Comprehensive Tag Detection**
   - Standard us-gaap debt tags (e.g., `ShortTermBorrowings`, `DebtCurrent`, `LongTermDebtNoncurrent`)
   - Company extension tags with debt keywords (e.g., `ford:FordCreditDebt`, `ford:AssetBackedDebt`)
   - Label-based detection for tags with debt-related labels

2. **Segment Classification**
   - **CONSOLIDATED**: Dimensionless facts (no segment dimensions)
   - **FORD_CREDIT**: Ford Credit financial services segment
   - **COMPANY_EXCL_FORD_CREDIT**: Company excluding Ford Credit (Automotive & Corporate)
   - **OTHER**: Other segments (geographic, etc.)

3. **Full Context Preservation**
   - XBRL tag, label, value, unit
   - Period information (instant vs duration)
   - Filing metadata (form, filing date, accession number)
   - Segment classification
   - Namespace (us-gaap vs company extensions)

## Usage

### Basic Usage

```python
from app.xbrl.debt_extractor import extract_debt_for_ticker

# Extract debt facts for Ford (ticker F) for 2024
result = extract_debt_for_ticker("F", report_date="2024-12-31")

print(f"Total debt facts: {len(result.facts)}")
print(f"Consolidated: {len(result.get_consolidated_facts())}")
print(f"Ford Credit: {len(result.get_ford_credit_facts())}")
print(f"Company excl. Ford Credit: {len(result.get_company_excl_ford_credit_facts())}")
```

### Extract from Cached File

```python
import json
from app.xbrl.debt_extractor import extract_debt_facts_from_instance

# Load cached company facts
with open("outputs/ford_all_tags_with_amounts.json", "r") as f:
    facts_payload = json.load(f)

# Convert to expected format if needed
if "tagsByTaxonomy" in facts_payload:
    facts_payload = {
        "cik": facts_payload.get("cik"),
        "entityName": facts_payload.get("entityName"),
        "facts": facts_payload["tagsByTaxonomy"],
    }

# Extract debt facts
result = extract_debt_facts_from_instance(facts_payload, report_date="2024-12-31")
```

### Extract by CIK

```python
from app.xbrl.debt_extractor import extract_debt_for_filing

# Ford CIK = 37996
result = extract_debt_for_filing(37996, report_date="2024-12-31")
```

## Data Structures

### DebtFact

A single debt-related XBRL fact with full context:

```python
@dataclass
class DebtFact:
    tag: str                    # XBRL tag name
    label: str                  # Human-readable label
    value: float                # Numeric value
    unit: str                   # Unit (typically "USD")
    period_end: str             # Period end date (YYYY-MM-DD)
    segment: DebtSegment        # Segment classification
    context_id: Optional[str]   # XBRL context ID
    period_start: Optional[str]  # For duration facts
    is_instant: bool            # True for balance sheet (instant)
    namespace: str              # Taxonomy namespace
    is_standard_gaap_tag: bool  # True if standard us-gaap tag
    filing_form: Optional[str]  # e.g., "10-K"
    filing_date: Optional[str]  # Filing date
    accession: Optional[str]     # SEC accession number
```

### DebtExtractionResult

Complete extraction result with all facts and metadata:

```python
@dataclass
class DebtExtractionResult:
    company: str
    cik: int
    fiscal_year: Optional[int]
    report_date: Optional[str]
    facts: List[DebtFact]
    
    # Helper methods:
    def get_facts_by_segment(segment: DebtSegment) -> List[DebtFact]
    def get_consolidated_facts() -> List[DebtFact]
    def get_ford_credit_facts() -> List[DebtFact]
    def get_company_excl_ford_credit_facts() -> List[DebtFact]
```

## Segment Classification Logic

The `classify_debt_segment()` function inspects XBRL dimensions/axes to determine segment:

1. **Dimensions Dict**: Checks `dimensions["us-gaap:ConsolidationItemsAxis"]["value"]` or similar axes
2. **Segment Field**: Checks `segment["member"]` or `segment["value"]`
3. **Tag/Label Fallback**: Checks tag and label names for segment indicators

**Ford Credit Indicators:**
- "Ford Credit", "FordCredit", "Credit Segment", "Financial Services", "Financing"

**Company Excl. Ford Credit Indicators:**
- "Company excluding Ford Credit", "Company excl Ford Credit", "Automotive", "Corporate"

**Important**: The classification checks for "Company excluding Ford Credit" patterns FIRST (more specific) before checking for "Ford Credit" patterns to avoid misclassification.

## Standard Debt Tags

The module recognizes these standard us-gaap debt tags:

- `ShortTermBorrowings`
- `DebtCurrent`
- `CommercialPaper`
- `LongTermDebt`
- `LongTermDebtNoncurrent`
- `LongTermDebtCurrent`
- `FinanceLeaseLiabilityCurrent`
- `FinanceLeaseLiabilityNoncurrent`
- `BorrowingsUnderRevolvingCreditFacility`
- `VariableInterestEntityDebt`
- And many more...

See `DEBT_TAGS_CORE` in `debt_extractor.py` for the complete list.

## Extension Tag Detection

Company extension tags are detected by keywords in tag names or labels:

- "debt", "borrowings", "notespayable", "loan", "creditfacility"
- "unsecured", "assetbacked", "secureddebt"
- "leaseobligation", "financeliability"

## Integration with Existing Infrastructure

This module uses existing Denari XBRL utilities:

- `app.services.ingestion.xbrl.utils.flatten_units()` - Flattens XBRL units structure
- `app.services.ingestion.clients.EdgarClient` - Fetches company facts from EDGAR
- EDGAR Company Facts API JSON structure

## Testing

Run tests with:

```bash
pytest tests/test_xbrl_debt_extractor.py -v
```

Tests verify:
- Standard us-gaap debt tags are detected
- Extension tags with debt keywords are detected
- Segment classification works correctly
- Period filtering works
- Non-monetary facts are excluded

## Example Output

```
Company: Ford Motor Co
CIK: 37996
Report Date: 2024-12-31

Total debt facts extracted: 26

By Segment:
  Consolidated: 26 facts
  Ford Credit: 0 facts
  Company excl. Ford Credit: 0 facts
  Other: 0 facts

Sample Consolidated Facts:
  LongTermDebtNoncurrent: $18,898,000,000
  DebtCurrent: $1,756,000,000
  FinanceLeaseLiabilityNoncurrent: $...
```

## Notes

- This module extracts and classifies facts; it does NOT compute totals or aggregate values
- Aggregation into "interest-bearing debt" should happen in a separate layer
- The extractor handles both instant (balance sheet) and duration facts
- Only monetary facts are included (excludes shares, percentages, etc.)

## Future Enhancements

- Support for TextBlock-based disclosures (if numeric facts are embedded)
- Enhanced segment detection for other issuers beyond Ford
- Integration with debt calculation/aggregation modules

