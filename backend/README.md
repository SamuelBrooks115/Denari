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

