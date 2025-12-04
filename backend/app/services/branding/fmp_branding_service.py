"""
fmp_branding_service.py — Company branding service using FMP profile data.

This module provides functionality to:
1. Fetch company profile data from FMP (including logo URL)
2. Return structured branding data (logo URL, company info)
"""

from __future__ import annotations

from typing import Dict

from app.core.logging import get_logger
from app.data.fmp_client import fetch_company_profile

logger = get_logger(__name__)

# Simple in-memory cache with TTL simulation
# Key: normalized ticker, Value: (branding_data, timestamp)
_branding_cache: Dict[str, tuple] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


class BrandingNotFoundError(Exception):
    """Raised when company branding data cannot be found or retrieved."""
    pass


async def get_company_branding(ticker: str) -> Dict[str, any]:
    """
    Get company branding data including logo URL.
    
    This function:
    1. Fetches company profile from FMP
    2. Extracts logo URL and company info
    3. Returns structured branding data
    
    Args:
        ticker: Stock ticker symbol (e.g., "F", "AAPL")
        
    Returns:
        Dictionary with branding data:
        {
            "ticker": str,
            "companyName": str,
            "website": str,
            "logoUrl": str,
        }
        
    Raises:
        BrandingNotFoundError: If company profile cannot be retrieved
    """
    # Normalize ticker
    normalized_ticker = ticker.upper().strip()
    
    # Check cache (simple TTL check)
    if normalized_ticker in _branding_cache:
        cached_data, timestamp = _branding_cache[normalized_ticker]
        import time
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            logger.debug(f"Returning cached branding for {normalized_ticker}")
            return cached_data
        else:
            # Cache expired, remove it
            del _branding_cache[normalized_ticker]
    
    try:
        # Fetch company profile from FMP (synchronous call, but in async context)
        logger.info(f"Fetching company profile for {normalized_ticker}")
        # Note: fetch_company_profile is synchronous, but we're in an async function
        # This is fine as it's I/O bound and FastAPI will handle it appropriately
        profile = fetch_company_profile(normalized_ticker)
        
        # Extract required fields
        symbol = profile.get("symbol", normalized_ticker)
        company_name = profile.get("companyName") or profile.get("name") or ""
        website = profile.get("website") or ""
        logo_url = profile.get("image") or profile.get("logo") or ""
        
        # Build branding response
        branding = {
            "ticker": symbol,
            "companyName": company_name,
            "website": website,
            "logoUrl": logo_url,
        }
        
        # Cache the result
        import time
        _branding_cache[normalized_ticker] = (branding, time.time())
        
        logger.info(f"Successfully retrieved branding for {normalized_ticker}")
        return branding
    
    except RuntimeError as e:
        # FMP API errors
        logger.error(f"FMP API error for {normalized_ticker}: {e}")
        raise BrandingNotFoundError(f"Could not retrieve company profile for {normalized_ticker}: {e}")
    
    except Exception as e:
        # Other errors
        logger.error(f"Unexpected error retrieving branding for {normalized_ticker}: {e}")
        raise BrandingNotFoundError(f"Failed to retrieve branding for {normalized_ticker}: {e}")

