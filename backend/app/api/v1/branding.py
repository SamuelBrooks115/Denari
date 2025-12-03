"""
branding.py — Company Branding API Endpoints

Purpose:
- Expose endpoints for retrieving company branding data (logo URL, company info)
- Uses FMP company profile data

Endpoints:
- GET /branding?ticker={TICKER} → Returns company branding data
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.branding.fmp_branding_service import (
    get_company_branding,
    BrandingNotFoundError,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/branding",
    tags=["branding"]
)

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

class CompanyBrandingResponse(BaseModel):
    """Response schema for company branding data."""
    ticker: str
    companyName: str
    website: str
    logoUrl: str

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "F",
                "companyName": "Ford Motor Company",
                "website": "https://www.ford.com",
                "logoUrl": "https://financialmodelingprep.com/image-stock/F.png"
            }
        }


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@router.get("", response_model=CompanyBrandingResponse)
async def get_branding(ticker: str = Query(..., description="Stock ticker symbol (e.g., F, AAPL, MSFT)")):
    """
    GET /branding?ticker={TICKER}
    
    Retrieve company branding data including:
    - Company name and website
    - Logo URL
    
    Args:
        ticker: Stock ticker symbol (required)
        
    Returns:
        CompanyBrandingResponse with branding data
        
    Raises:
        400: If ticker is missing or invalid
        404: If company branding cannot be found
        500: If there's an error retrieving branding data
    """
    # Validate ticker
    if not ticker or not ticker.strip():
        raise HTTPException(
            status_code=400,
            detail="Ticker parameter is required and cannot be empty"
        )
    
    # Normalize ticker
    normalized_ticker = ticker.upper().strip()
    
    try:
        logger.info(f"Fetching branding for ticker: {normalized_ticker}")
        branding = await get_company_branding(normalized_ticker)
        
        return CompanyBrandingResponse(**branding)
    
    except BrandingNotFoundError as e:
        logger.warning(f"Branding not found for {normalized_ticker}: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Company branding not found for ticker: {normalized_ticker}"
        )
    
    except Exception as e:
        logger.error(f"Error retrieving branding for {normalized_ticker}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error retrieving branding for ticker: {normalized_ticker}"
        )

