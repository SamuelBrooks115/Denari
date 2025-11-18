"""
structured.py — Structured Financial Data Extraction Endpoints (API Layer)

Purpose:
- Provide endpoints for on-demand extraction of structured 3-statement data from EDGAR.
- Returns data in single-year or multi-year filing JSON format.
- Used when users need immediate structured output without database persistence.

Key Interactions:
- app.services.ingestion.structured_output → core extraction logic
- app.services.ingestion.clients.EdgarClient → EDGAR API access
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.core.logging import get_logger
from app.services.ingestion.clients import EdgarClient
from app.services.ingestion.structured_output import (
    extract_single_year_structured,
    extract_multi_year_structured,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/structured",
    tags=["structured"]
)

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------


class StructuredRequest(BaseModel):
    """Request schema for structured extraction endpoints."""
    ticker: Optional[str] = Field(None, description="Company ticker symbol (e.g., 'F', 'AAPL')")
    cik: Optional[int] = Field(None, description="Company CIK number (e.g., 37996 for Ford)")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "F",
                "cik": None
            }
        }


class MultiYearRequest(StructuredRequest):
    """Request schema for multi-year extraction."""
    max_filings: int = Field(5, ge=1, le=10, description="Maximum number of annual filings to include (1-10)")


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------


@router.post("/single-year")
async def get_single_year_structured(request: StructuredRequest):
    """
    POST /api/v1/structured/single-year

    Extract structured 3-statement data (Balance Sheet, Income Statement, Cash Flow)
    for the latest annual filing period.

    Request Body:
    - ticker (optional): Company ticker symbol
    - cik (optional): Company CIK number
    - At least one of ticker or cik must be provided

    Returns:
    - Structured JSON matching single-year filing template with metadata and statements

    Example:
    ```json
    {
        "ticker": "F"
    }
    ```
    """
    if not request.ticker and not request.cik:
        raise HTTPException(
            status_code=400,
            detail="Either 'ticker' or 'cik' must be provided"
        )

    try:
        edgar_client = EdgarClient()
        
        # Resolve CIK if only ticker provided
        cik = request.cik
        ticker = request.ticker or ""

        if not cik and ticker:
            cik_map = edgar_client.get_cik_map()
            cik = cik_map.get(ticker.upper())
            if not cik:
                raise HTTPException(
                    status_code=404,
                    detail=f"CIK not found for ticker '{ticker}'"
                )
            ticker = ticker.upper()
        elif cik and not ticker:
            # If only CIK provided, try to get ticker from map (optional)
            cik_map = edgar_client.get_cik_map()
            ticker = next((t for t, c in cik_map.items() if c == cik), f"CIK{cik:010d}")
        else:
            ticker = ticker.upper()

        # Extract structured data
        result = extract_single_year_structured(cik=cik, ticker=ticker, edgar_client=edgar_client)

        return result

    except HTTPException:
        raise
    except RuntimeError as e:
        logger.exception("Error extracting single-year structured data")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract structured data: {str(e)}"
        )
    except Exception as e:
        logger.exception("Unexpected error in single-year extraction")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/multi-year")
async def get_multi_year_structured(request: MultiYearRequest):
    """
    POST /api/v1/structured/multi-year

    Extract structured 3-statement data (Balance Sheet, Income Statement, Cash Flow)
    for multiple annual filing periods (latest first).

    Request Body:
    - ticker (optional): Company ticker symbol
    - cik (optional): Company CIK number
    - max_filings (optional): Maximum number of annual filings to include (default: 5, max: 10)
    - At least one of ticker or cik must be provided

    Returns:
    - Structured JSON matching multi-year filing template with company metadata and filings array

    Example:
    ```json
    {
        "ticker": "F",
        "max_filings": 5
    }
    ```
    """
    if not request.ticker and not request.cik:
        raise HTTPException(
            status_code=400,
            detail="Either 'ticker' or 'cik' must be provided"
        )

    try:
        edgar_client = EdgarClient()
        
        # Resolve CIK if only ticker provided
        cik = request.cik
        ticker = request.ticker or ""

        if not cik and ticker:
            cik_map = edgar_client.get_cik_map()
            cik = cik_map.get(ticker.upper())
            if not cik:
                raise HTTPException(
                    status_code=404,
                    detail=f"CIK not found for ticker '{ticker}'"
                )
            ticker = ticker.upper()
        elif cik and not ticker:
            # If only CIK provided, try to get ticker from map (optional)
            cik_map = edgar_client.get_cik_map()
            ticker = next((t for t, c in cik_map.items() if c == cik), f"CIK{cik:010d}")
        else:
            ticker = ticker.upper()

        # Extract structured data
        result = extract_multi_year_structured(
            cik=cik,
            ticker=ticker,
            max_filings=request.max_filings,
            edgar_client=edgar_client
        )

        return result

    except HTTPException:
        raise
    except RuntimeError as e:
        logger.exception("Error extracting multi-year structured data")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract structured data: {str(e)}"
        )
    except Exception as e:
        logger.exception("Unexpected error in multi-year extraction")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

