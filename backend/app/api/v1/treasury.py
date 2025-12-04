"""
treasury.py — Treasury Rates API Endpoints

Purpose:
- Expose endpoints for retrieving treasury rates (e.g., 10-year treasury rate)
- Uses FMP API to fetch current treasury rates

Endpoints:
- GET /treasury/rates → Returns current treasury rates including 10-year rate
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.logging import get_logger
from app.data.fmp_client import fetch_treasury_rates

logger = get_logger(__name__)

router = APIRouter(
    prefix="/treasury",
    tags=["treasury"]
)

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

class TreasuryRatesResponse(BaseModel):
    """Response schema for treasury rates data."""
    date: str
    year1: Optional[float] = None
    year2: Optional[float] = None
    year3: Optional[float] = None
    year5: Optional[float] = None
    year10: Optional[float] = None
    year20: Optional[float] = None
    year30: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-15",
                "year1": 4.50,
                "year2": 4.45,
                "year3": 4.40,
                "year5": 4.35,
                "year10": 4.33,
                "year20": 4.30,
                "year30": 4.28
            }
        }


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@router.get("/rates", response_model=TreasuryRatesResponse)
async def get_treasury_rates():
    """
    GET /treasury/rates
    
    Retrieve current treasury rates from FMP API.
    Returns the most recent treasury rate data including:
    - 1-year, 2-year, 3-year, 5-year, 10-year, 20-year, 30-year rates
    
    Returns:
        TreasuryRatesResponse with current treasury rates
        
    Raises:
        500: If there's an error retrieving treasury rates
    """
    try:
        logger.info("Fetching treasury rates from FMP API")
        rates_data = fetch_treasury_rates()
        
        # Extract the 10-year rate (primary use case)
        # FMP API may return different field names, so we'll try common variations
        year10 = (
            rates_data.get("year10") or 
            rates_data.get("year_10") or 
            rates_data.get("10year") or
            rates_data.get("10_year") or
            rates_data.get("10Y")
        )
        
        # Build response with all available rates
        response_data = {
            "date": rates_data.get("date", ""),
            "year1": rates_data.get("year1") or rates_data.get("year_1") or rates_data.get("1year") or rates_data.get("1Y"),
            "year2": rates_data.get("year2") or rates_data.get("year_2") or rates_data.get("2year") or rates_data.get("2Y"),
            "year3": rates_data.get("year3") or rates_data.get("year_3") or rates_data.get("3year") or rates_data.get("3Y"),
            "year5": rates_data.get("year5") or rates_data.get("year_5") or rates_data.get("5year") or rates_data.get("5Y"),
            "year10": year10,
            "year20": rates_data.get("year20") or rates_data.get("year_20") or rates_data.get("20year") or rates_data.get("20Y"),
            "year30": rates_data.get("year30") or rates_data.get("year_30") or rates_data.get("30year") or rates_data.get("30Y"),
        }
        
        logger.info(f"Successfully fetched treasury rates. 10-year rate: {year10}")
        return TreasuryRatesResponse(**response_data)
    
    except RuntimeError as e:
        logger.error(f"Error fetching treasury rates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve treasury rates: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving treasury rates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error retrieving treasury rates: {str(e)}"
        )



