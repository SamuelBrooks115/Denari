# Denari

A comprehensive financial modeling platform for valuation analysis, featuring 3-statement modeling, DCF (Discounted Cash Flow) analysis, and relative valuation (comps) capabilities. Denari ingests financial data from EDGAR, processes it through structured classification, and generates Excel-based financial models.

## 🎯 Project Overview

Denari is a full-stack financial analysis platform that:

- **Ingests** financial data from SEC EDGAR filings
- **Classifies** financial line items using LLM-powered classification
- **Models** financial projections using 3-statement, DCF, and comps methodologies
- **Exports** results to Excel templates for further analysis

### Key Features

- 📊 **3-Statement Financial Modeling**: Income Statement, Balance Sheet, and Cash Flow projections
- 💰 **DCF Valuation**: Discounted Cash Flow analysis with WACC calculations
- 📈 **Relative Valuation**: Comparable company analysis (comps)
- 📥 **EDGAR Integration**: Automated fetching and parsing of SEC filings
- 🤖 **LLM Classification**: Intelligent classification of financial line items
- 📋 **Excel Export**: Populated Excel templates with historical data and forecasts

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.12+)
- **Frontend**: React + TypeScript + Vite
- **Database**: Supabase (PostgreSQL)
- **Dependency Management**: Poetry (backend), npm (frontend)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **Poetry** ([Installation Guide](https://python-poetry.org/docs/#installation))
- **Node.js 18+** and **npm** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/downloads))

### Optional but Recommended

- **PostgreSQL** (if running Supabase locally)
- **VS Code** or your preferred IDE

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Denari
```

### 2. Backend Setup

#### Install Dependencies

```bash
cd backend
poetry install
```

This will install all Python dependencies including:
- FastAPI and Uvicorn (web framework)
- pandas, numpy (data processing)
- openpyxl, xlsxwriter (Excel handling)
- supabase (database client)
- openai (LLM classification)
- And more...

#### Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cd backend
touch .env
```

Add the following environment variables to `.env`:

```env
# EDGAR API Configuration (Required)
EDGAR_USER_AGENT="Denari/1.0 (contact: ingestion@denari.ai)"
EDGAR_REQUEST_SLEEP_SECONDS=0.45
EDGAR_REQUEST_TIMEOUT_SECONDS=45
EDGAR_MAX_RETRIES=4
EDGAR_BACKOFF_BASE=0.6

# LLM Configuration (Required for classification)
LLM_ENABLED=true
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=3

# Database Configuration (Required for Supabase)
SUPABASE_DB_URL=postgresql://user:password@host:port/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# S&P 500 Ticker Source (Optional)
SP500_TICKER_SOURCE=path/to/sp500_tickers.json
```

**Important Notes:**
- Replace `your_openai_api_key_here` with your actual OpenAI API key
- Replace Supabase credentials with your actual Supabase project details
- The `EDGAR_USER_AGENT` should follow SEC guidelines (include contact info)

#### Activate Poetry Shell

```bash
poetry shell
```

#### Run the Backend Server

```bash
# From the backend directory
poetry run uvicorn app.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`

**Verify it's running:**
```bash
curl http://localhost:8000/
```

You should see:
```json
{"status": "ok", "message": "Denari backend running"}
```

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment Variables

Create a `.env` file in the `frontend/` directory (optional):

```bash
cd frontend
touch .env
```

Add the API URL:

```env
VITE_API_URL=http://localhost:8000
```

#### Run the Frontend Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port shown in terminal)

## 🧪 Testing the Setup

### Test Backend Excel Export

The backend includes a test script that demonstrates the full modeling pipeline:

```bash
cd backend
poetry run python test.py
```

This script:
1. Loads structured financial data from JSON
2. Loads the Excel template (`Denari.xlsx`)
3. Runs 3-statement and DCF modeling
4. Populates historical data into Excel sheets
5. Saves the output to `downloads/Denari_populated2.xlsx`

**Prerequisites for test.py:**
- Ensure you have a structured JSON file with financial data in `backend/downloads/`
- Ensure `backend/downloads/Denari.xlsx` exists

### Test API Endpoints

#### Search for a Company

```bash
curl -X POST "http://localhost:8000/api/v1/models/search" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

#### Fetch Financial Data

```bash
curl -X POST "http://localhost:8000/api/v1/models/fetch-financials" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "years": 5}'
```

#### Generate Full Model

```bash
curl -X POST "http://localhost:8000/api/v1/models/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "frequency": "annual",
    "historical_periods": 5,
    "forecast_periods": 5,
    "assumptions": {
      "revenue_growth": 0.05,
      "wacc": 0.10,
      "terminal_growth_rate": 0.025
    }
  }'
```

## 📁 Project Structure

```
Denari/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints
│   │   │   ├── companies.py   # Company management
│   │   │   ├── filings.py     # Filing endpoints
│   │   │   ├── financials.py  │   │   ├── financials.py  # Financial data
│   │   │   ├── models.py      # Model generation
│   │   │   └── structured.py  # Structured output
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py      # Settings & env vars
│   │   │   ├── database.py    # DB connection
│   │   │   └── logging.py     # Logging setup
│   │   ├── models/            # SQLAlchemy ORM models
│   │   └── services/
│   │       ├── ingestion/     # EDGAR data ingestion
│   │       │   ├── clients/   # External API clients
│   │       │   ├── pipelines/ # Ingestion workflows
│   │       │   ├── repositories/ # Data persistence
│   │       │   └── xbrl/      # XBRL parsing
│   │       └── modeling/      # Financial modeling
│   │           ├── dcf.py     # DCF calculations
│   │           ├── three_statement.py # 3-statement model
│   │           ├── comps.py   # Comps analysis
│   │           ├── excel_export.py # Excel generation
│   │           └── types.py   # Data structures
│   ├── downloads/             # Output directory
│   ├── test.py               # Test script
│   ├── pyproject.toml        # Poetry dependencies
│   └── .env                  # Environment variables (create this)
│
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   └── main.tsx         # Entry point
│   ├── package.json         # npm dependencies
│   └── vite.config.ts       # Vite configuration
│
└── README.md                 # This file
```

## 🔌 API Endpoints

### Company & Financial Data

- `POST /api/v1/models/search` - Search for a company by ticker
- `POST /api/v1/models/fetch-financials` - Fetch financial data from EDGAR
- `POST /api/v1/models/generate` - Generate complete valuation model

### Structured Output

- `POST /api/v1/structured/generate` - Generate structured JSON output

### Companies

- `GET /api/v1/companies` - List companies
- `POST /api/v1/companies` - Create company
- `GET /api/v1/companies/{id}` - Get company details
- `POST /api/v1/companies/{id}/prepare`/prepare` - Prepare company data

### Filings

- `GET /api/v1/filings` - List filings
- `GET /api/v1/filings/{id}` - Get filing details

### Financials

- `GET /api/v1/financials/{company_id}` - Get financial data

## 🛠️ Development

### Backend Development

```bash
cd backend
poetry shell  # Activate virtual environment
poetry run uvicorn app.main:app --reload  # Run with auto-reload
```

### Frontend Development

```bash
cd frontend
npm run dev  # Run development server with hot reload
```

### Running Tests

```bash
# Backend tests (when implemented)
cd backend
poetry run pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

## 📦 Building for Production

### Backend

```bash
cd backend
poetry build
```

### Frontend

```bash
cd frontend
npm run build
```

The production build will be in `frontend/dist/`

## 🐛 Troubleshooting

### Backend Issues

**Issue: Poetry command not found**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

**Issue: Module not found errors**
```bash
cd backend
poetry install  # Reinstall dependencies
```

**Issue: Environment variables not loading**
- Ensure `.env` file is in `backend/` directory
- Check that variable names match exactly (case-sensitive)
- Restart the server after changing `.env`

**Issue: Database connection errors**
- Verify `SUPABASE_DB_URL` is correct
- Check that Supabase project is active
- Ensure `SUPABASE_SERVICE_ROLE_KEY` has proper permissions

**Issue: OpenAI API errors**
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has sufficient credits
- Set `LLM_ENABLED=false` to disable LLM classification for testing

### Frontend Issues

**Issue: npm install fails**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue: API calls failing**
- Verify backend is running on `http://localhost:8000`
- Check `VITE_API_URL` in frontend `.env`
- Check browser console for CORS errors

**Issue: Port already in use**
```bash
# Kill process on port 5173 (or change port in vite.config.ts)
lsof -ti:5173 | xargs kill -9
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SEC EDGAR API](https://www.sec.gov/edgar/sec-api-documentation)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Vite Documentation](https://vitejs.dev/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

See LICENSE file for details.

## 👥 Authors

- Aiden Beeskow - CONTACT INFO
- Samuel Brooks - samuel111503@gmail.com
- Sophia Guiter - CONTACT INFO
- Ian Ortega - CONTACT INFO 

## 🙏 Acknowledgments

- SEC EDGAR for financial data
- OpenAI for LLM classification capabilities
- Supabase for database infrastructure

---

**Need Help?** Open an issue on GitHub or contact the development team.
