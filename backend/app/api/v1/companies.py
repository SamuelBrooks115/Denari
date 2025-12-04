"""
Purpose:
- Expose API endpoints related to company lookup, readiness checks, and initiating data preparation.
- This includes endpoints such as:
    • GET /companies/{ticker} → Validate the ticker exists, return metadata.
    • GET /companies/{ticker}/status → Check whether prices + financials are already ingested.
    • POST /companies/{ticker}/prepare → Trigger ingestion workflow if data missing.

Key Interactions:
- app.services.ingestion.ingest_orchestrator → runs the full data readiness pipeline.
- app.services.ingestion.prices_adapter → fetches EOD prices from Yahoo Finance.
- app.services.ingestion.edgar_adapter → fetches filings when historicals are missing.
- app.models.company → ORM model representing company records.
- app.core.database → DB session.

Role in System:
- The API layer should NOT contain business logic.
- It calls into services/orchestrators in services/ingestion/.
- It should transform request parameters → service calls → JSON responses.

Data Flow:
Client → FastAPI Router → (this file) → ingest_orchestrator / data access services → Supabase DB → response
"""

#Imports 
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.models.company import Company  # ORM model
from app.services.ingestion.ingest_orchestrator import prepare_company_data  # Orchestration entrypoint
from app.services.market_data.yfinance_market_data import (
    get_company_price_and_shares,
    get_ford_price_and_shares,
)

router = APIRouter(
    prefix="/companies",
    tags=["companies"]
)

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

class CompanyOut(BaseModel):
    """
    Response schema for basic company information.
    Keep minimal for now. Expand later as needed.
    """
    id: int
    ticker: str
    name: str
    exchange: Optional[str] = None

    class Config:
        orm_mode = True


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@router.get("/", response_model=List[CompanyOut])
async def list_companies(db=Depends(get_db)):
    """
    GET /companies

    Returns a list of companies stored in the system.

    TODO:
    - Implement actual DB query: db.query(Company).all()
    """
    # TODO: implement real query
    return []


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: int, db=Depends(get_db)):
    """
    GET /companies/{company_id}

    Returns company details.

    TODO:
    - Implement DB lookup + 404 if not found.
    """
    # TODO: implement real lookup
    company = None
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/{company_id}/prepare")
async def prepare_company(company_id: int, db=Depends(get_db)):
    """
    POST /companies/{company_id}/prepare

    This is the core workflow trigger for valuation readiness.

    High-Level Sequence (handled inside ingest_orchestrator):
    1. Check whether company exists.
    2. Check if EOD prices exist & are fresh; fetch if missing.
    3. Check whether historical IS/BS/CF coverage is sufficient; fetch/normalize if missing.
    4. Upsert PRICE_EOD, FINANCIAL_STATEMENT, and FINANCIAL_FACT records.
    5. Return a status summary (what was fetched, normalized, updated).

    API Response Expectations:
    - Return structured info: e.g., {"prices_updated": True, "financials_updated": False}

    TODO:
    - Implement company lookup.
    - Implement call to prepare_company_data(company_id, db).
    """
    # TODO: lookup company or 404
    # TODO: call orchestrator
    result = {"status": "placeholder"}
    return result


@router.get("/market-data/ford")
async def read_ford_market_data():
    """
    GET /companies/market-data/ford
    
    Return latest price and shares outstanding for Ford (F),
    using the Denari DB if possible to determine the ticker.
    
    Returns:
        Dictionary with:
        - ticker: Ticker symbol used
        - last_price: Latest closing price
        - shares_outstanding: Shares outstanding
        - market_cap: Market capitalization (if both price and shares available)
    """
    data = get_ford_price_and_shares()
    return data


@router.get("/market-data/{ticker}")
async def read_market_data_by_ticker(ticker: str):
    """
    GET /companies/market-data/{ticker}
    
    Return latest price and shares outstanding for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., "F", "AAPL")
        
    Returns:
        Dictionary with:
        - ticker: Ticker symbol used
        - last_price: Latest closing price
        - shares_outstanding: Shares outstanding
        - market_cap: Market capitalization (if both price and shares available)
    """
    from app.services.market_data.yfinance_market_data import fetch_price_and_shares_from_yfinance
    data = fetch_price_and_shares_from_yfinance(ticker)
    return data


@router.get("/market-data/by-name/{company_name}")
async def read_market_data_by_name(company_name: str, db=Depends(get_db)):
    """
    GET /companies/market-data/by-name/{company_name}
    
    Return latest price and shares outstanding for a company by name.
    Looks up the ticker from the Denari database first.
    
    Args:
        company_name: Company name (e.g., "Ford Motor Company")
        
    Returns:
        Dictionary with:
        - ticker: Ticker symbol used (or None if not found)
        - last_price: Latest closing price
        - shares_outstanding: Shares outstanding
        - market_cap: Market capitalization (if both price and shares available)
    """
    data = get_company_price_and_shares(company_name=company_name, session=db)
    return data