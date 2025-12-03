# Backend

Denari backend application for financial data ingestion and analysis.

## Setup

1. Install Python 3.12 or higher
2. Install Poetry: `pip install poetry` or follow [Poetry installation guide](https://python-poetry.org/docs/#installation)
3. Install dependencies: `poetry install`
4. Set up environment variables (see below)
5. Run the application: `poetry run uvicorn app.main:app --reload`

## Environment Variables

### FMP API Key (Required)

This project uses Financial Modeling Prep (FMP) API to fetch financial data.

**Set the `FMP_API_KEY` environment variable:**

**Option 1: Direct value**
```bash
export FMP_API_KEY=your-api-key-here  # Linux/Mac
# or
set FMP_API_KEY=your-api-key-here     # Windows CMD
```

**Option 2: Create a `.env` file** in the project root:
```
FMP_API_KEY=your-api-key-here
```

**Option 3: Use a file path** (set `FMP_API_KEY` to point to a file containing your key)

For detailed setup instructions, see [FMP_SETUP.md](./FMP_SETUP.md).

Get your API key from: https://financialmodelingprep.com/

### Other Environment Variables

See `app/core/config.py` for other optional environment variables.

### Required Environment Variables

- `FMP_API_KEY` - Financial Modeling Prep API key (required for branding and financial data endpoints)
  - Can be set directly: `FMP_API_KEY=your_api_key_here`
  - Or as a file path: `FMP_API_KEY=/path/to/api_key.txt` (the script will read the key from the file)

## API Endpoints

### Company Branding

**GET** `/api/v1/branding?ticker={TICKER}`

Retrieve company branding data including logo URL and company information.

**Query Parameters:**
- `ticker` (required) - Stock ticker symbol (e.g., "F", "AAPL", "MSFT")

**Response:**
```json
{
  "ticker": "F",
  "companyName": "Ford Motor Company",
  "website": "https://www.ford.com",
  "logoUrl": "https://financialmodelingprep.com/image-stock/F.png"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/branding?ticker=F"
```

**Error Responses:**
- `400` - Missing or invalid ticker parameter
- `404` - Company branding not found
- `500` - Internal server error

**Notes:**
- Branding data is cached in-memory for 1 hour
- Requires `FMP_API_KEY` environment variable to be set

### Industry Screener

**GET** `/api/v1/meta/sectors`

Retrieve list of available sectors from FMP.

**Response:**
```json
["Technology", "Healthcare", "Financial Services", "Consumer Cyclical", ...]
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/meta/sectors"
```

---

**GET** `/api/v1/meta/industries`

Retrieve list of available industries from FMP.

**Response:**
```json
["Consumer Electronics", "Banks—Regional", "Software—Infrastructure", ...]
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/meta/industries"
```

---

**GET** `/api/v1/industry-screener`

Search for companies matching specified filters.

**Query Parameters:**
- `sector` (optional) - Filter by sector (e.g., "Technology")
- `industry` (optional) - Filter by industry (e.g., "Consumer Electronics")
- `minCap` (optional) - Minimum market cap in dollars (e.g., 10000000000 for $10B)
- `maxCap` (optional) - Maximum market cap in dollars (e.g., 1000000000000000 for $1T)
- `page` (optional, default: 0) - Page number (0-indexed)
- `pageSize` (optional, default: 50, max: 200) - Number of results per page

**Response:**
```json
{
  "page": 0,
  "pageSize": 50,
  "results": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "marketCap": 4228844465070,
      "website": "https://www.apple.com",
      "logoUrl": "https://images.financialmodelingprep.com/symbol/AAPL.png",
      "description": "Apple Inc. designs, manufactures, and markets smartphones...",
      "ceo": "Timothy D. Cook",
      "employees": 164000
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/industry-screener?sector=Technology&industry=Consumer%20Electronics&minCap=10000000000&maxCap=1000000000000000"
```

**Error Responses:**
- `400` - Invalid request parameters
- `500` - Internal server error or FMP API failure

**Notes:**
- Market cap values should be provided in raw dollars (not billions)
- Results are paginated; use `page` and `pageSize` to navigate
- Requires `FMP_API_KEY` environment variable to be set

