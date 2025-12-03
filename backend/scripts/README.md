# Scripts Directory

## fetch_fmp_industry_screener.py

Standalone script to fetch and export company screener results from FMP /stable API.

### Features

- **Filter by sector, industry, and market cap range**
- **Pagination support** (page and limit parameters)
- **Exports results to JSON** with filter metadata
- **Command-line interface** for easy automation

### Usage

```powershell
# Search for Technology companies with market cap between $10B and $1T
python scripts/fetch_fmp_industry_screener.py `
    --sector "Technology" `
    --min-cap 10000000000 `
    --max-cap 1000000000000 `
    --output-json data/fmp_stable_raw/tech_companies.json

# Search for specific industry
python scripts/fetch_fmp_industry_screener.py `
    --industry "Consumer Electronics" `
    --min-cap 100000000000 `
    --output-json data/fmp_stable_raw/consumer_electronics.json

# Get all companies (no filters) with pagination
python scripts/fetch_fmp_industry_screener.py `
    --output-json data/fmp_stable_raw/all_companies_page1.json `
    --limit 200 `
    --page 0

# Get next page
python scripts/fetch_fmp_industry_screener.py `
    --output-json data/fmp_stable_raw/all_companies_page2.json `
    --limit 200 `
    --page 1
```

### Arguments

- `--sector` (optional) - Filter by sector (e.g., "Technology", "Healthcare")
- `--industry` (optional) - Filter by industry (e.g., "Consumer Electronics", "Banks—Regional")
- `--min-cap` (optional) - Minimum market cap in dollars (e.g., 10000000000 for $10B)
- `--max-cap` (optional) - Maximum market cap in dollars (e.g., 1000000000000 for $1T)
- `--page` (optional, default: 0) - Page number (0-indexed)
- `--limit` (optional, default: 100, max: 200) - Number of results per page
- `--output-json` (optional, default: `data/fmp_stable_raw/screener_results.json`) - Output JSON file path

### Output Structure

The JSON output includes:

```json
{
  "filters": {
    "sector": "Technology",
    "industry": null,
    "minCap": 10000000000,
    "maxCap": 1000000000000,
    "page": 0,
    "limit": 100
  },
  "resultCount": 50,
  "results": [
    {
      "symbol": "AAPL",
      "companyName": "Apple Inc.",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "marketCap": 4228844465070,
      "website": "https://www.apple.com",
      "image": "https://images.financialmodelingprep.com/symbol/AAPL.png",
      "description": "Apple Inc. designs, manufactures...",
      "ceo": "Timothy D. Cook",
      "fullTimeEmployees": 164000
    }
  ]
}
```

### Requirements

- `FMP_API_KEY` environment variable set (required by FMP API)
- Internet connection

### Notes

- Market cap values should be in dollars (e.g., 10000000000 for $10B)
- The script validates that min-cap <= max-cap if both are provided
- Results are paginated; use `--page` to fetch additional pages
- Maximum limit is 200 results per page

## download_ford_2024_ixbrl.py

Automated script to download Ford Motor Company's 2024 10-K iXBRL file from SEC EDGAR.

### Features

- **Automatically finds the 2024 10-K filing** using EdgarClient
- **Downloads iXBRL file or ZIP archive** from SEC EDGAR
- **Extracts iXBRL from ZIP** if needed
- **Saves to `data/xbrl/ford_2024_10k.ixbrl`** for use with Arelle pipeline

### Usage

```bash
# Make sure EDGAR_USER_AGENT is set in .env file
python scripts/download_ford_2024_ixbrl.py
```

### Requirements

- `EDGAR_USER_AGENT` environment variable set (required by SEC EDGAR)
- Internet connection
- `requests` library (already in dependencies)

### Output

The script will:
1. Look up Ford's 2024 10-K filing from SEC EDGAR
2. Download the iXBRL file (or ZIP archive)
3. Save to `data/xbrl/ford_2024_10k.ixbrl`

If automatic download fails, the script provides manual download instructions with direct URLs.

## reconstruct_ford_balance_sheet.py

Standalone script to reconstruct Ford Motor Company's 2024 Balance Sheet from XBRL data.

### Features

- **Fetches XBRL data** from EDGAR or uses cached data
- **Extracts all balance sheet items** for FY 2024 (2024-12-31)
- **Categorizes items** into Assets, Liabilities, and Equity
- **Excludes subtotals** to avoid double-counting
- **Uses reported totals** when available (e.g., "Assets", "Liabilities", "Equity" tags)
- **Reconciles balance sheet** (Assets = Liabilities + Equity)
- **Exports to structured JSON** with full auditability

### Usage

```bash
# Using cached XBRL data (faster)
python scripts/reconstruct_ford_balance_sheet.py --use-cached --output outputs/ford_2024_balance_sheet.json

# Fetching from EDGAR (requires internet connection)
python scripts/reconstruct_ford_balance_sheet.py --output outputs/ford_2024_balance_sheet.json
```

### Output Structure

The JSON output includes:

```json
{
  "company": "Ford Motor Company",
  "ticker": "F",
  "cik": 37996,
  "report_date": "2024-12-31",
  "fiscal_year": 2024,
  "currency": "USD",
  "balance_sheet": {
    "assets": {
      "items": [...],  // Line items (excludes subtotals)
      "total": 285196000000.0,  // Reported total from XBRL
      "sum_of_items": 375433000000.0,  // Sum of line items
      "item_count": 35
    },
    "liabilities": {...},
    "equity": {...}
  },
  "totals": {
    "assets_total": 285196000000.0,
    "liabilities_total": 240338000000.0,
    "equity_total": 44835000000.0,
    "reconciliation_difference": -23000000.0,
    "balances": true
  },
  "metadata": {
    "total_items_extracted": 91,
    "reconciliation_passes": true,
    "uses_reported_totals": true
  }
}
```

### Key Features

1. **Subtotal Detection**: Automatically excludes subtotals like "AssetsCurrent", "LiabilitiesCurrent" to prevent double-counting
2. **Consolidated Values**: Prefers dimensionless (consolidated) facts over segment-specific ones
3. **Reconciliation**: Verifies Assets = Liabilities + Equity (within 1% tolerance)
4. **Full Auditability**: Every item includes tag, label, value, unit, and context

### Example Output

```
================================================================================
Ford Motor Company - Balance Sheet (FY 2024)
================================================================================
Report Date: 2024-12-31

Assets: $285,196,000,000 (35 items)
Liabilities: $240,338,000,000 (41 items)
Equity: $44,835,000,000 (4 items)

Reconciliation: Assets = Liabilities + Equity
  $285,196,000,000 = $240,338,000,000 + $44,835,000,000
  Difference: $-23,000,000
  [OK] Balance sheet reconciles (within 1% tolerance)
```

