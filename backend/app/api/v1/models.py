"""
models.py — Live Model Generation API Endpoints (MVP - No Database)

Purpose:
- Provide endpoints for on-the-fly model generation
- Fetch from EDGAR, parse, and generate models live
- No database persistence - all data processed in-memory

Endpoints:
- POST /api/v1/models/search - Search company by ticker
- POST /api/v1/models/fetch-financials - Fetch and parse financial data
- POST /api/v1/models/generate - Generate complete model (3-statement, DCF, comps)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from app.services.ingestion.live_fetcher import fetch_company_live, search_company_by_ticker
from app.services.modeling.three_statement import run_three_statement
from app.services.modeling.dcf import run_dcf
from app.services.modeling.comps import run_comps
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/models",
    tags=["models"]
)

# -----------------------------------------------------------------------------
# Request/Response Schemas
# -----------------------------------------------------------------------------


class SearchRequest(BaseModel):
    ticker: str


class SearchResponse(BaseModel):
    ticker: str
    cik: Optional[int] = None
    name: Optional[str] = None
    found: bool
    in_sp500: bool = False
    error: Optional[str] = None


class FetchFinancialsRequest(BaseModel):
    ticker: str
    years: int = 5


class FetchFinancialsResponse(BaseModel):
    ticker: str
    cik: int
    name: str
    taxonomy: str
    financials: Dict[str, Dict[str, Dict[str, float]]]
    periods: List[str]


class GenerateModelRequest(BaseModel):
    ticker: str
    frequency: str = "annual"  # "annual" or "quarterly"
    historical_periods: int = 5
    forecast_periods: int = 5
    assumptions: Dict[str, Any] = {}


class GenerateModelResponse(BaseModel):
    company_info: Dict[str, Any]
    historical_financials: Dict[str, Dict[str, Dict[str, float]]]
    projections: Dict[str, Any]
    dcf: Dict[str, Any]
    comps: Dict[str, Any]


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------


@router.post("/search", response_model=SearchResponse)
async def search_company(request: SearchRequest):
    """
    Search for a company by ticker symbol.
    
    Returns basic company information from EDGAR (ticker, CIK, name).
    """
    try:
        result = search_company_by_ticker(request.ticker)
        return SearchResponse(**result)
    except Exception as exc:
        logger.exception("Error searching for company: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error searching company: {str(exc)}")


@router.post("/fetch-financials", response_model=FetchFinancialsResponse)
async def fetch_financials(request: FetchFinancialsRequest):
    """
    Fetch and parse financial data from EDGAR for a company.
    
    This endpoint:
    1. Looks up CIK for the ticker
    2. Fetches submissions and company facts from EDGAR
    3. Parses XBRL data
    4. Normalizes to canonical financial statements
    
    Returns structured financial data organized by statement type and period.
    """
    try:
        result = fetch_company_live(request.ticker, years=request.years)
        
        if not result.get("periods"):
            raise HTTPException(
                status_code=404,
                detail=f"No financial data found for ticker: {request.ticker}"
            )
        
        return FetchFinancialsResponse(
            ticker=result["ticker"],
            cik=result["cik"],
            name=result["name"],
            taxonomy=result["taxonomy"],
            financials=result["financials"],
            periods=result["periods"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error fetching financials: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error fetching financials: {str(exc)}")


@router.post("/generate", response_model=GenerateModelResponse)
async def generate_model(request: GenerateModelRequest):
    """
    Generate a complete valuation model on-the-fly.
    
    This endpoint orchestrates:
    1. Fetch company data from EDGAR
    2. Parse and normalize financial statements
    3. Generate 3-statement projections
    4. Calculate DCF valuation
    5. Compute comps multiples
    
    All processing is done live without database persistence.
    """
    try:
        # Step 1: Fetch company financial data
        logger.info("Fetching financial data for %s", request.ticker)
        company_data = fetch_company_live(request.ticker, years=request.historical_periods)
        
        if not company_data.get("periods"):
            raise HTTPException(
                status_code=404,
                detail=f"No financial data found for ticker: {request.ticker}"
            )
        
        # Step 2: Extract historical financials for modeling
        # Convert from statement-type organization to period-based organization
        financials_by_period: Dict[str, Dict[str, float]] = {}
        
        for stmt_type, periods_dict in company_data["financials"].items():
            for period_end, metrics in periods_dict.items():
                if period_end not in financials_by_period:
                    financials_by_period[period_end] = {}
                financials_by_period[period_end].update(metrics)
        
        # Step 3: Generate 3-statement projections
        logger.info("Generating 3-statement projections")
        projections = run_three_statement(
            historical_financials=financials_by_period,
            assumptions=request.assumptions,
            forecast_periods=request.forecast_periods,
            frequency=request.frequency,
        )
        
        # Step 4: Calculate DCF
        logger.info("Calculating DCF valuation")
        dcf_assumptions = {
            "wacc": request.assumptions.get("wacc", 0.10),
            "terminal_growth_rate": request.assumptions.get("terminal_growth_rate", 0.025),
            "shares_outstanding": request.assumptions.get("shares_outstanding"),
            "debt": request.assumptions.get("debt", 0.0),
            "cash": request.assumptions.get("cash", 0.0),
        }
        dcf_result = run_dcf(projections, dcf_assumptions)
        
        # Step 5: Calculate comps (simplified - no peers in MVP)
        logger.info("Calculating comps multiples")
        latest_period = sorted(financials_by_period.keys())[-1]
        latest_financials = financials_by_period[latest_period]
        
        # Extract metrics for comps
        target_financials = {
            "revenue": latest_financials.get("revenue", 0.0),
            "ebitda": latest_financials.get("operating_income"),  # Approximate
            "operating_income": latest_financials.get("operating_income", 0.0),
            "net_income": latest_financials.get("net_income", 0.0),
        }
        
        # If we have DCF enterprise value, use it for comps
        market_data = None
        if dcf_result.get("enterprise_value"):
            market_data = {
                "enterprise_value": dcf_result["enterprise_value"],
                "market_cap": dcf_result.get("equity_value"),
                "shares_outstanding": request.assumptions.get("shares_outstanding"),
            }
        
        comps_result = run_comps(target_financials, market_data)
        
        return GenerateModelResponse(
            company_info={
                "ticker": company_data["ticker"],
                "cik": company_data["cik"],
                "name": company_data["name"],
                "taxonomy": company_data["taxonomy"],
            },
            historical_financials=company_data["financials"],
            projections=projections,
            dcf=dcf_result,
            comps=comps_result,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error generating model: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error generating model: {str(exc)}")

