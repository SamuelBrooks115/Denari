"""
historical.py — API endpoints for fetching historical financial metrics.

These endpoints are used ONLY for the "Create New Project" page.
They fetch historical data from FMP API and calculate metrics for context.

NOT used for Excel export (which uses only user-entered values).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.modeling.historical_metrics import fetch_and_calculate_historical_metrics
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/historical",
    tags=["historical"]
)


class HistoricalMetricsRequest(BaseModel):
    ticker: str
    limit: int = 40


class HistoricalMetricsResponse(BaseModel):
    ticker: str
    historicals: Dict[str, List[float]]


@router.post("/metrics", response_model=HistoricalMetricsResponse)
async def get_historical_metrics(request: HistoricalMetricsRequest):
    """
    Fetch historical financial data and calculate metrics for a ticker.
    
    This endpoint:
    1. Fetches income statements, balance sheets, and cash flow statements from FMP API
    2. Calculates historical metrics (growth, margins, ratios, etc.)
    3. Returns structured data ready for storage in project JSON
    
    Used ONLY for the "Create New Project" page to provide historical context.
    NOT used for Excel export (which uses only user-entered values).
    
    Args:
        request: HistoricalMetricsRequest with ticker and optional limit
        
    Returns:
        HistoricalMetricsResponse with ticker and historical metrics
        
    Raises:
        HTTPException: If API calls fail or data is insufficient
    """
    try:
        logger.info(f"Fetching historical metrics for ticker: {request.ticker}")
        
        result = fetch_and_calculate_historical_metrics(
            ticker=request.ticker.upper(),
            limit=request.limit
        )
        
        return HistoricalMetricsResponse(
            ticker=result["ticker"],
            historicals=result["historicals"]
        )
        
    except RuntimeError as e:
        logger.error(f"Error fetching historical metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error fetching historical metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

