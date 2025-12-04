"""
yfinance_market_data.py — Market data fetching using yfinance library.

This module provides functions to:
- Look up company tickers from the Denari database
- Fetch latest stock prices and shares outstanding from yfinance
- Expose clean, reusable functions for market data access
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import yfinance as yf

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.company import Company

logger = get_logger(__name__)


def get_ticker_for_company(session: Session, company_name: str) -> Optional[str]:
    """
    Look up the primary ticker symbol for a given company name in the Denari database.
    
    Searches for companies matching the name (case-insensitive partial match).
    Returns the ticker if found, None otherwise.
    
    Args:
        session: SQLAlchemy database session
        company_name: Company name to search for (e.g., "Ford Motor Company")
        
    Returns:
        Ticker symbol string if found, None otherwise
    """
    # Try exact match first
    company = (
        session.query(Company)
        .filter(Company.name.ilike(company_name))
        .first()
    )
    
    # If no exact match, try partial match
    if company is None:
        company = (
            session.query(Company)
            .filter(Company.name.ilike(f"%{company_name}%"))
            .first()
        )
    
    if company is None:
        logger.debug(f"Company '{company_name}' not found in database")
        return None
    
    ticker = company.ticker
    logger.debug(f"Found ticker '{ticker}' for company '{company_name}'")
    return ticker


def fetch_price_and_shares_from_yfinance(ticker: str) -> Dict[str, Optional[float]]:
    """
    Fetch the latest stock price and shares outstanding from yfinance for the given ticker.
    
    This function uses multiple fallback strategies to get reliable data:
    1. Tries to get price from recent market data (history)
    2. Falls back to info.currentPrice if history unavailable
    3. Gets shares outstanding from info.sharesOutstanding
    
    Args:
        ticker: Stock ticker symbol (e.g., "F" for Ford)
        
    Returns:
        Dictionary with keys:
        - 'ticker': The ticker symbol
        - 'last_price': Latest closing price (float or None)
        - 'shares_outstanding': Shares outstanding (float or None)
        - 'market_cap': Market capitalization (float or None, computed if both price and shares available)
    """
    result: Dict[str, Optional[float]] = {
        "ticker": ticker,
        "last_price": None,
        "shares_outstanding": None,
        "market_cap": None,
    }
    
    try:
        yf_ticker = yf.Ticker(ticker)
        
        # Try to get info dictionary
        info: Dict[str, Any] = {}
        try:
            info = yf_ticker.info or {}
        except Exception as e:
            logger.warning(f"Could not fetch yfinance info for {ticker}: {e}")
            info = {}
        
        # Method 1: Try to get last price from recent market data (most reliable)
        last_price = None
        try:
            hist = yf_ticker.history(period="5d")  # Get last 5 days for reliability
            if not hist.empty:
                last_price = float(hist["Close"].iloc[-1])
                logger.debug(f"Got price {last_price} from history for {ticker}")
        except Exception as e:
            logger.debug(f"Could not get price from history for {ticker}: {e}")
        
        # Method 2: Fallback to info.currentPrice
        if last_price is None:
            last_price = info.get("currentPrice")
            if last_price is not None:
                try:
                    last_price = float(last_price)
                    logger.debug(f"Got price {last_price} from info.currentPrice for {ticker}")
                except (ValueError, TypeError):
                    last_price = None
        
        # Method 3: Try regularMarketPrice as last resort
        if last_price is None:
            last_price = info.get("regularMarketPrice")
            if last_price is not None:
                try:
                    last_price = float(last_price)
                    logger.debug(f"Got price {last_price} from info.regularMarketPrice for {ticker}")
                except (ValueError, TypeError):
                    last_price = None
        
        result["last_price"] = last_price
        
        # Get shares outstanding
        shares_outstanding = info.get("sharesOutstanding")
        if shares_outstanding is not None:
            try:
                shares_outstanding = float(shares_outstanding)
                result["shares_outstanding"] = shares_outstanding
            except (ValueError, TypeError):
                pass
        
        # Calculate market cap if both available
        if last_price is not None and shares_outstanding is not None:
            result["market_cap"] = last_price * shares_outstanding
        
    except Exception as e:
        logger.error(f"Error fetching yfinance data for {ticker}: {e}")
        # Return dict with None values rather than raising
    
    return result


def get_ford_price_and_shares() -> Dict[str, Optional[float]]:
    """
    High-level helper that:
    1. Tries to look up Ford in the Denari database by name.
    2. Uses that ticker if found.
    3. Falls back to the hardcoded 'F' ticker if no DB record exists.
    
    This function manages its own database session and handles errors gracefully.
    
    Returns:
        Dictionary with 'ticker', 'last_price', 'shares_outstanding', and 'market_cap'
    """
    ticker = "F"  # Default fallback
    
    try:
        db = SessionLocal()
        try:
            # Try various Ford name variations
            for name_variant in [
                "Ford Motor Company",
                "Ford Motor Co",
                "Ford",
            ]:
                found_ticker = get_ticker_for_company(db, name_variant)
                if found_ticker:
                    ticker = found_ticker
                    logger.info(f"Found Ford ticker '{ticker}' in database for '{name_variant}'")
                    break
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Error looking up Ford in database, using default ticker 'F': {e}")
    
    return fetch_price_and_shares_from_yfinance(ticker)


def get_company_price_and_shares(
    company_name: Optional[str] = None,
    ticker: Optional[str] = None,
    session: Optional[Session] = None,
) -> Dict[str, Optional[float]]:
    """
    Generic helper to get price and shares for any company.
    
    This function can work with either a company name (looks up ticker from DB)
    or a direct ticker symbol. If a session is provided, uses it; otherwise
    creates its own.
    
    Args:
        company_name: Company name to look up (optional if ticker provided)
        ticker: Direct ticker symbol (optional if company_name provided)
        session: Database session (optional, creates own if not provided)
        
    Returns:
        Dictionary with 'ticker', 'last_price', 'shares_outstanding', and 'market_cap'
        
    Raises:
        ValueError: If neither company_name nor ticker is provided
    """
    if not ticker and not company_name:
        raise ValueError("Either company_name or ticker must be provided")
    
    # If ticker not provided, look it up from database
    if not ticker and company_name:
        if session:
            ticker = get_ticker_for_company(session, company_name)
        else:
            db = SessionLocal()
            try:
                ticker = get_ticker_for_company(db, company_name)
            finally:
                db.close()
        
        if not ticker:
            logger.warning(f"Could not find ticker for '{company_name}', cannot fetch market data")
            return {
                "ticker": None,
                "last_price": None,
                "shares_outstanding": None,
                "market_cap": None,
            }
    
    return fetch_price_and_shares_from_yfinance(ticker)

