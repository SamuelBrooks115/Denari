"""
screener.py — Industry Screener API Endpoints

Purpose:
- Expose endpoints for industry analysis and company screening
- Uses FMP stable API endpoints for sectors, industries, and company screener
- Provides metadata endpoints and filtered company search

Endpoints:
- GET /meta/sectors → Returns list of available sectors
- GET /meta/industries → Returns list of available industries
- GET /industry-screener → Returns filtered list of companies
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

from app.core.logging import get_logger
from app.data.fmp_client import (
    fetch_available_sectors,
    fetch_available_industries,
    fetch_company_screener,
    fetch_available_tickers,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/meta",
    tags=["screener"]
)

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

class CompanyResult(BaseModel):
    """Response schema for a single company in screener results."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )
    
    symbol: str
    name: str
    sector: str
    industry: str
    marketCap: int
    website: Optional[str] = None
    logoUrl: Optional[str] = None
    description: Optional[str] = None
    ceo: Optional[str] = None
    employees: Optional[int] = None


class ScreenerResponse(BaseModel):
    """Response schema for industry screener endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                        "description": "Apple Inc. designs, manufactures...",
                        "ceo": "Timothy D. Cook",
                        "employees": 164000
                    }
                ]
            }
        }
    )
    
    page: int
    pageSize: int
    results: List[CompanyResult]


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@router.get("/sectors", response_model=List[str])
async def get_sectors():
    """
    GET /meta/sectors
    
    Retrieve list of available sectors from FMP.
    
    Returns:
        JSON array of sector name strings
        
    Raises:
        500: If FMP API call fails
    """
    try:
        logger.info("Fetching available sectors")
        sectors = fetch_available_sectors()
        return sectors
    except Exception as e:
        logger.error(f"Error fetching sectors: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch sectors: {str(e)}"
        )


@router.get("/industries", response_model=List[str])
async def get_industries():
    """
    GET /meta/industries
    
    Retrieve list of available industries from FMP.
    
    Returns:
        JSON array of industry name strings
        
    Raises:
        500: If FMP API call fails
    """
    try:
        logger.info("Fetching available industries")
        industries = fetch_available_industries()
        return industries
    except Exception as e:
        logger.error(f"Error fetching industries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch industries: {str(e)}"
        )


@router.get("/tickers", response_model=List[Dict[str, Any]])
async def get_tickers():
    """
    GET /meta/tickers
    
    Retrieve list of all available ticker symbols from FMP.
    
    Returns:
        JSON array of ticker objects. Each object contains:
        - symbol: str (ticker symbol, e.g., "AAPL")
        - name: str (company name)
        - exchange: str (exchange code, e.g., "NASDAQ", "NYSE")
        - Other metadata fields may be present
        
    Raises:
        500: If FMP API call fails
    """
    try:
        logger.info("Fetching available tickers")
        tickers = fetch_available_tickers()
        return tickers
    except Exception as e:
        logger.error(f"Error fetching tickers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tickers: {str(e)}"
        )


# Create a separate router for the screener endpoint (different prefix)
screener_router = APIRouter(
    prefix="/industry-screener",
    tags=["screener"]
)


@screener_router.get("", response_model=ScreenerResponse)
async def get_industry_screener(
    sector: Optional[str] = Query(None, description="Filter by sector (e.g., 'Technology')"),
    industry: Optional[str] = Query(None, description="Filter by industry (e.g., 'Consumer Electronics')"),
    minCap: Optional[int] = Query(None, description="Minimum market cap in dollars"),
    maxCap: Optional[int] = Query(None, description="Maximum market cap in dollars"),
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    pageSize: int = Query(50, gt=0, le=200, description="Number of results per page (max 200)")
):
    """
    GET /industry-screener
    
    Search for companies matching the specified filters.
    
    Query Parameters:
        sector: Optional sector filter
        industry: Optional industry filter
        minCap: Optional minimum market cap in dollars
        maxCap: Optional maximum market cap in dollars
        page: Page number (default: 0)
        pageSize: Results per page (default: 50, max: 200)
        
    Returns:
        ScreenerResponse with paginated company results
        
    Raises:
        400: If validation fails
        500: If FMP API call fails
    """
    try:
        # Normalize string parameters (trim, empty -> None)
        normalized_sector = sector.strip() if sector and sector.strip() else None
        normalized_industry = industry.strip() if industry and industry.strip() else None
        
        logger.info(
            f"Fetching screener results: sector={normalized_sector}, "
            f"industry={normalized_industry}, minCap={minCap}, maxCap={maxCap}, "
            f"page={page}, pageSize={pageSize}"
        )
        
        # Call FMP screener
        raw_results = fetch_company_screener(
            sector=normalized_sector,
            industry=normalized_industry,
            market_cap_min=minCap,
            market_cap_max=maxCap,
            limit=pageSize,
            page=page,
        )
        
        # Transform FMP response to normalized format
        results = []
        for company in raw_results:
            # Map FMP fields to our schema
            # Handle various possible field names from FMP
            symbol = company.get("symbol") or company.get("Symbol") or ""
            name = company.get("companyName") or company.get("name") or company.get("company_name") or ""
            sector_val = company.get("sector") or company.get("Sector") or ""
            industry_val = company.get("industry") or company.get("Industry") or ""
            market_cap = company.get("marketCap") or company.get("market_cap") or company.get("MarketCap") or 0
            website = company.get("website") or company.get("Website") or None
            logo_url = company.get("image") or company.get("logo") or company.get("logoUrl") or company.get("Image") or None
            description = company.get("description") or company.get("Description") or company.get("about") or None
            ceo = company.get("ceo") or company.get("CEO") or company.get("ceoName") or None
            employees = company.get("fullTimeEmployees") or company.get("employees") or company.get("Employees") or company.get("full_time_employees") or None
            
            # Convert market cap to int if it's a float or string
            if isinstance(market_cap, float):
                market_cap = int(market_cap)
            elif isinstance(market_cap, str):
                try:
                    market_cap = int(float(market_cap))
                except (ValueError, TypeError):
                    market_cap = 0
            
            # Convert employees to int if it's a float or string
            if employees is not None:
                if isinstance(employees, float):
                    employees = int(employees)
                elif isinstance(employees, str):
                    try:
                        employees = int(float(employees))
                    except (ValueError, TypeError):
                        employees = None
            
            results.append(CompanyResult(
                symbol=symbol,
                name=name,
                sector=sector_val,
                industry=industry_val,
                marketCap=market_cap,
                website=website,
                logoUrl=logo_url,
                description=description,
                ceo=ceo,
                employees=employees,
            ))
        
        return ScreenerResponse(
            page=page,
            pageSize=pageSize,
            results=results
        )
        
    except ValueError as e:
        logger.error(f"Validation error in screener: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching screener results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch screener results: {str(e)}"
        )

