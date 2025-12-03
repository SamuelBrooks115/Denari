"""
fmp_client.py — Financial Modeling Prep (FMP) API client.

This module provides a clean interface to fetch financial statements
from the FMP REST API using the /stable endpoints.

All API calls require an FMP_API_KEY environment variable.
Designed to work with FMP Starter plan limits and includes retry/backoff logic.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from app.core.logging import get_logger

# Load .env file if it exists (from project root)
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

logger = get_logger(__name__)

# FMP API base URL - using /stable endpoints
FMP_BASE_URL = "https://financialmodelingprep.com/stable"

# Retry configuration for Starter plan friendliness
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # Base delay in seconds (exponential backoff)


def get_fmp_api_key() -> str:
    """
    Get FMP API key from environment variable or file path.
    
    If FMP_API_KEY is a file path (contains path separators), the function
    will read the API key from that file. Otherwise, it uses the value directly.
    
    Returns:
        API key string
        
    Raises:
        RuntimeError: If FMP_API_KEY environment variable is not set or file cannot be read
    """
    api_key_path_or_value = os.getenv("FMP_API_KEY")
    if not api_key_path_or_value:
        raise RuntimeError(
            "FMP_API_KEY environment variable is not set. "
            "Please set it before running FMP API calls.\n"
            "You can set it to:\n"
            "  - The API key directly: FMP_API_KEY=your-api-key-here\n"
            "  - A file path containing the key: FMP_API_KEY=C:\\path\\to\\key.txt"
        )
    
    # Check if it looks like a file path (contains path separators)
    is_file_path = (
        "\\" in api_key_path_or_value or 
        "/" in api_key_path_or_value or
        api_key_path_or_value.endswith(".txt") or
        api_key_path_or_value.endswith(".key")
    )
    
    if is_file_path:
        # Treat as file path and read the key from file
        key_file = Path(api_key_path_or_value).expanduser()
        if not key_file.exists():
            raise RuntimeError(
                f"FMP_API_KEY file not found: {key_file}\n"
                f"Please check that the file path is correct."
            )
        
        try:
            with key_file.open("r", encoding="utf-8") as f:
                api_key = f.read().strip()
            
            if not api_key:
                raise RuntimeError(
                    f"FMP_API_KEY file is empty: {key_file}\n"
                    f"Please ensure the file contains your API key."
                )
            
            return api_key
        
        except Exception as e:
            raise RuntimeError(
                f"Failed to read FMP_API_KEY from file {key_file}: {e}\n"
                f"Please check file permissions and format."
            ) from e
    else:
        # Treat as direct API key value
        return api_key_path_or_value.strip()


def _get_json(
    path: str,
    params: Dict[str, Any] | None = None,
) -> Any:
    """
    Call FMP /stable/{path} with params + apikey and return parsed JSON.
    
    Implements retry/backoff for HTTP 429 and 5xx errors to be
    friendly to Starter plan limits.
    
    Args:
        path: API path (e.g., "income-statement" or "/income-statement")
        params: Optional query parameters (apikey will be added automatically)
        
    Returns:
        Parsed JSON response (list or dict)
        
    Raises:
        RuntimeError: If API call fails or returns invalid data
    """
    api_key = get_fmp_api_key()
    
    # Build full URL - strip leading slash from path if present
    clean_path = path.lstrip("/")
    url = f"{FMP_BASE_URL}/{clean_path}"
    
    # Prepare parameters - merge with apikey
    request_params = params.copy() if params else {}
    request_params["apikey"] = api_key
    
    logger.debug(f"Making FMP API request: {url}")
    
    # Retry logic for 429 and 5xx errors
    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=request_params, timeout=30)
            
            # Handle rate limiting (429)
            if response.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Rate limited (429). Retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise RuntimeError(
                        f"FMP API rate limit exceeded after {MAX_RETRIES} attempts. "
                        f"Please wait and try again later."
                    )
            
            # Handle server errors (5xx)
            if response.status_code in {500, 502, 503, 504}:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    logger.warning(
                        f"Server error {response.status_code}. Retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    response.raise_for_status()
            
            # Handle other HTTP errors
            if response.status_code == 401:
                raise RuntimeError(
                    f"FMP API returned 401 Unauthorized. "
                    f"Your API key may be invalid or expired.\n"
                    f"Please verify your API key in the FMP dashboard."
                )
            elif response.status_code == 403:
                # Try to get error message from response
                try:
                    error_data = response.json()
                    error_msg = error_data.get("Error Message", "Forbidden")
                except:
                    error_msg = "Forbidden"
                
                raise RuntimeError(
                    f"FMP API returned 403 Forbidden.\n"
                    f"Error: {error_msg}\n"
                    f"Please check your FMP account status and plan access."
                )
            
            response.raise_for_status()
            
            # Parse JSON
            data = response.json()
            
            logger.debug(f"Successfully fetched data from {url}")
            return data
        
        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(
                    f"Request failed: {e}. Retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})"
                )
                time.sleep(delay)
            else:
                raise RuntimeError(
                    f"Failed to fetch data from FMP API after {MAX_RETRIES} attempts: {e}\n"
                    f"URL: {url}"
                ) from e
    
    # Should not reach here, but just in case
    if last_exception:
        raise RuntimeError(f"Failed after {MAX_RETRIES} attempts: {last_exception}")
    raise RuntimeError("Unexpected error in retry logic")


def fetch_income_statement(
    symbol: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetch income statement data from FMP /stable API.
    
    Calls /stable/income-statement?symbol={symbol}&limit={limit}
    
    Args:
        symbol: Stock ticker symbol (e.g., "F" for Ford)
        limit: Number of periods to fetch (default: 10)
        
    Returns:
        List of income statement dictionaries (most recent first)
        Each dict contains fields like: revenue, costOfRevenue, grossProfit, etc.
        
    Raises:
        RuntimeError: If API call fails or returns invalid data
    """
    path = "income-statement"
    params = {
        "symbol": symbol,
        "limit": limit,
    }
    
    logger.info(f"Fetching income statement for {symbol} (limit={limit})")
    
    data = _get_json(path, params)
    
    if not isinstance(data, list):
        raise RuntimeError(
            f"FMP API returned unexpected data type for income statement: {type(data)}. "
            f"Expected a list."
        )
    
    if not data:
        logger.warning(f"FMP API returned empty list for {symbol} income statement")
    
    logger.info(f"Successfully fetched {len(data)} income statement(s) for {symbol}")
    return data


def fetch_balance_sheet(
    symbol: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetch balance sheet data from FMP /stable API.
    
    Calls /stable/balance-sheet-statement?symbol={symbol}&limit={limit}
    
    Args:
        symbol: Stock ticker symbol (e.g., "F" for Ford)
        limit: Number of periods to fetch (default: 10)
        
    Returns:
        List of balance sheet dictionaries (most recent first)
        Each dict contains fields like: totalAssets, totalLiabilities, inventory, etc.
        
    Raises:
        RuntimeError: If API call fails or returns invalid data
    """
    path = "balance-sheet-statement"
    params = {
        "symbol": symbol,
        "limit": limit,
    }
    
    logger.info(f"Fetching balance sheet for {symbol} (limit={limit})")
    
    data = _get_json(path, params)
    
    if not isinstance(data, list):
        raise RuntimeError(
            f"FMP API returned unexpected data type for balance sheet: {type(data)}. "
            f"Expected a list."
        )
    
    if not data:
        logger.warning(f"FMP API returned empty list for {symbol} balance sheet")
    
    logger.info(f"Successfully fetched {len(data)} balance sheet(s) for {symbol}")
    return data


def fetch_cash_flow(
    symbol: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetch cash flow statement data from FMP /stable API.
    
    Calls /stable/cash-flow-statement?symbol={symbol}&limit={limit}
    
    Args:
        symbol: Stock ticker symbol (e.g., "F" for Ford)
        limit: Number of periods to fetch (default: 10)
        
    Returns:
        List of cash flow statement dictionaries (most recent first)
        Each dict contains fields like: dividendsPaid, stockRepurchases, etc.
        
    Raises:
        RuntimeError: If API call fails or returns invalid data
    """
    path = "cash-flow-statement"
    params = {
        "symbol": symbol,
        "limit": limit,
    }
    
    logger.info(f"Fetching cash flow for {symbol} (limit={limit})")
    
    data = _get_json(path, params)
    
    if not isinstance(data, list):
        raise RuntimeError(
            f"FMP API returned unexpected data type for cash flow: {type(data)}. "
            f"Expected a list."
        )
    
    if not data:
        logger.warning(f"FMP API returned empty list for {symbol} cash flow")
    
    logger.info(f"Successfully fetched {len(data)} cash flow statement(s) for {symbol}")
    return data


def fetch_financial_report_json(
    symbol: str,
    year: int,
    period: str = "FY",
) -> Any:
    """
    Fetch as-reported 10-K JSON from FMP /stable API.
    
    Calls /stable/financial-reports-json?symbol={symbol}&year={year}&period={period}
    
    This endpoint provides as-reported financial data from 10-K filings.
    For now, this is optional/forward-compatible functionality.
    
    Args:
        symbol: Stock ticker symbol (e.g., "F" for Ford)
        year: Fiscal year (e.g., 2024)
        period: Period type - "FY" for full year, "Q1", "Q2", "Q3", "Q4" for quarters (default: "FY")
        
    Returns:
        Parsed JSON response (structure depends on FMP's response format)
        
    Raises:
        RuntimeError: If API call fails
    """
    path = "financial-reports-json"
    params = {
        "symbol": symbol,
        "year": year,
        "period": period,
    }
    
    logger.info(f"Fetching financial report JSON for {symbol} year {year} period {period}")
    
    data = _get_json(path, params)
    
    logger.info(f"Successfully fetched financial report JSON for {symbol}")
    return data


def fetch_quote(symbol: str) -> Dict[str, Any]:
    """
    Fetch current/latest stock quote from FMP /stable API.
    
    Calls /stable/quote?symbol={symbol}
    
    Args:
        symbol: Stock ticker symbol (e.g., "F" for Ford)
        
    Returns:
        Dictionary with quote data (price, volume, market cap, etc.)
        
    Raises:
        RuntimeError: If API call fails or returns invalid data
    """
    path = "quote"
    params = {
        "symbol": symbol,
    }
    
    logger.info(f"Fetching quote for {symbol}")
    
    data = _get_json(path, params)
    
    if isinstance(data, list):
        if len(data) > 0:
            logger.info(f"Successfully fetched quote for {symbol}")
            return data[0]
        else:
            raise RuntimeError(f"FMP API returned empty list for {symbol} quote")
    elif isinstance(data, dict):
        logger.info(f"Successfully fetched quote for {symbol}")
        return data
    else:
        raise RuntimeError(
            f"FMP API returned unexpected data type for quote: {type(data)}. "
            f"Expected list or dict."
        )


def fetch_historical_prices(
    symbol: str,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Fetch historical stock prices from FMP /stable API.
    
    Calls /stable/historical-price-full?symbol={symbol}&from={from_date}&to={to_date}
    
    Args:
        symbol: Stock ticker symbol (e.g., "F" for Ford)
        from_date: Start date in YYYY-MM-DD format (optional)
        to_date: End date in YYYY-MM-DD format (optional)
        limit: Number of days to fetch (optional, if not using date range)
        
    Returns:
        List of historical price dictionaries with date, open, high, low, close, volume
        
    Raises:
        RuntimeError: If API call fails or returns invalid data
    """
    # Note: Historical price endpoints may not be available in /stable API
    # Try common endpoint names
    endpoints_to_try = [
        "historical-price-full",
        "historical-price",
        "stock-price",
    ]
    
    params = {
        "symbol": symbol,
    }
    
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    if limit:
        params["limit"] = limit
    
    logger.info(f"Fetching historical prices for {symbol}")
    if from_date or to_date:
        logger.info(f"  Date range: {from_date or 'start'} to {to_date or 'end'}")
    if limit:
        logger.info(f"  Limit: {limit} days")
    
    last_error = None
    for endpoint_path in endpoints_to_try:
        try:
            data = _get_json(endpoint_path, params)
            
            # FMP returns historical data in a nested structure: {"historical": [...]}
            if isinstance(data, dict):
                if "historical" in data:
                    historical = data["historical"]
                    if isinstance(historical, list):
                        logger.info(f"Successfully fetched {len(historical)} historical price records for {symbol}")
                        return historical
                elif "prices" in data:
                    prices = data["prices"]
                    if isinstance(prices, list):
                        logger.info(f"Successfully fetched {len(prices)} historical price records for {symbol}")
                        return prices
                else:
                    # Try to extract any list-like data that looks like price data
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            first_item = value[0]
                            if isinstance(first_item, dict) and "date" in first_item:
                                logger.info(f"Successfully fetched {len(value)} historical price records for {symbol}")
                                return value
            elif isinstance(data, list):
                logger.info(f"Successfully fetched {len(data)} historical price records for {symbol}")
                return data
            
            raise RuntimeError(
                f"FMP API returned unexpected data structure for historical prices. "
                f"Expected dict with 'historical' key or list."
            )
        
        except RuntimeError as e:
            last_error = e
            # If it's a 404, try next endpoint
            if "404" in str(e) or "Not Found" in str(e):
                logger.debug(f"Endpoint {endpoint_path} returned 404, trying next...")
                continue
            else:
                # Other errors, re-raise
                raise
    
    # If all endpoints failed with 404, provide helpful error
    if last_error and ("404" in str(last_error) or "Not Found" in str(last_error)):
        raise RuntimeError(
            f"Historical price endpoints are not available in FMP /stable API for {symbol}.\n"
            f"Tried endpoints: {', '.join(endpoints_to_try)}\n"
            f"\nPossible reasons:\n"
            f"  - Historical prices may require /api/v3 endpoints instead of /stable\n"
            f"  - Historical prices may require a higher subscription tier\n"
            f"  - The endpoint name may be different in your plan\n"
            f"\nCurrent quote data is available via fetch_quote()."
        )
    elif last_error:
        raise last_error
    else:
        raise RuntimeError(f"Failed to fetch historical prices for {symbol}")
