"""
sp500_price_fetcher.py — Fetch and Store Latest S&P 500 Close Prices

Purpose:
- Fetch today's (or most recent) close price for all S&P 500 companies using yfinance
- Store in a JSON file for easy access by ticker
- Automatically refresh if file is not from today

This module does NOT:
- Store historical data (only latest close price)
- Store OHLCV data (only close price)
- Store data in database (use prices_adapter.py for that)
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import json
import pandas as pd
import yfinance as yf

from app.services.ingestion.sp500_tickers import SP500_TICKERS
from app.core.logging import get_logger

logger = get_logger(__name__)

# Determine data file location
_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_PRICES_FILE = _DATA_DIR / "sp500_latest_prices.json"


def fetch_latest_sp500_prices(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Fetch the latest close price for all S&P 500 companies and save to file.
    
    Args:
        force_refresh: If True, force a fresh fetch even if file exists and is from today
    
    Returns:
        Dictionary mapping ticker to price data:
        {
            "AAPL": {
                "date": "11/28/2025",
                "close": 150.25
            },
            ...
        }
    """
    # Check if file exists and is from today
    if not force_refresh and _PRICES_FILE.exists():
        file_date = datetime.fromtimestamp(_PRICES_FILE.stat().st_mtime).date()
        today = date.today()
        
        if file_date == today:
            logger.info(f"Price file is from today ({today}), loading from file")
            return _load_prices_from_file()
        else:
            logger.info(f"Price file is from {file_date}, refreshing for today ({today})")
    
    # Fetch fresh data
    logger.info(f"Fetching latest prices for {len(SP500_TICKERS)} S&P 500 companies...")
    
    price_data = {}
    failed_tickers = []
    ticker_list = list(SP500_TICKERS)
    batch_size = 30  # Reduced from 100 to 30 for better reliability
    
    # Calculate date range (last 7 days to ensure we get a trading day)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    # Batch fetching
    for i in range(0, len(ticker_list), batch_size):
        batch = ticker_list[i:i + batch_size]
        logger.info(f"Fetching batch {i//batch_size + 1}/{(len(ticker_list) + batch_size - 1)//batch_size} ({len(batch)} tickers)")
        
        try:
            # Download data using date range (last 7 days)
            ticker_data = yf.download(
                batch,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=False,
                group_by='ticker'
            )
            
            # Handle MultiIndex columns (when multiple tickers)
            if isinstance(ticker_data.columns, pd.MultiIndex):
                for ticker in batch:
                    if ticker in ticker_data.columns.levels[0]:
                        ticker_df = ticker_data[ticker]
                        if not ticker_df.empty:
                            # Get the most recent row (last row) - only close price
                            latest = ticker_df.iloc[-1]
                            close_price = latest.get("Close")
                            if pd.notna(close_price):
                                # Format date as MM/DD/YYYY
                                if hasattr(latest.name, 'strftime'):
                                    date_str = latest.name.strftime("%m/%d/%Y")
                                else:
                                    date_obj = latest.name.date() if hasattr(latest.name, 'date') else latest.name
                                    date_str = date_obj.strftime("%m/%d/%Y") if hasattr(date_obj, 'strftime') else str(date_obj)
                                price_data[ticker] = {
                                    "date": date_str,
                                    "close": float(close_price),
                                }
                        else:
                            failed_tickers.append(ticker)
                    else:
                        failed_tickers.append(ticker)
            else:
                # Single ticker case
                if len(batch) == 1:
                    ticker = batch[0]
                    if not ticker_data.empty:
                        latest = ticker_data.iloc[-1]
                        close_price = latest.get("Close")
                        if pd.notna(close_price):
                            # Format date as MM/DD/YYYY
                            if hasattr(latest.name, 'strftime'):
                                date_str = latest.name.strftime("%m/%d/%Y")
                            else:
                                date_obj = latest.name.date() if hasattr(latest.name, 'date') else latest.name
                                date_str = date_obj.strftime("%m/%d/%Y") if hasattr(date_obj, 'strftime') else str(date_obj)
                            price_data[ticker] = {
                                "date": date_str,
                                "close": float(close_price),
                            }
                    else:
                        failed_tickers.append(ticker)
        
        except Exception as e:
            logger.error(f"Error fetching batch starting at index {i}: {e}")
            failed_tickers.extend(batch)
    
    # Retry failed tickers individually (backup mechanism)
    if failed_tickers:
        logger.info(f"Retrying {len(failed_tickers)} failed tickers individually...")
        retry_failed = []
        
        for ticker in failed_tickers:
            try:
                ticker_data = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=False
                )
                
                if not ticker_data.empty:
                    latest = ticker_data.iloc[-1]
                    close_price = latest.get("Close")
                    if pd.notna(close_price):
                        # Format date as MM/DD/YYYY
                        if hasattr(latest.name, 'strftime'):
                            date_str = latest.name.strftime("%m/%d/%Y")
                        else:
                            date_obj = latest.name.date() if hasattr(latest.name, 'date') else latest.name
                            date_str = date_obj.strftime("%m/%d/%Y") if hasattr(date_obj, 'strftime') else str(date_obj)
                        price_data[ticker] = {
                            "date": date_str,
                            "close": float(close_price),
                        }
                        logger.info(f"✓ Successfully fetched {ticker} on retry")
                    else:
                        retry_failed.append(ticker)
                else:
                    retry_failed.append(ticker)
            except Exception as e:
                logger.warning(f"Retry failed for {ticker}: {e}")
                retry_failed.append(ticker)
        
        if retry_failed:
            logger.warning(f"Still failed to fetch {len(retry_failed)} tickers after retry: {retry_failed[:10]}...")
        else:
            logger.info(f"✓ All tickers successfully fetched after retry!")
    
    # Save to file
    _save_prices_to_file(price_data)
    
    logger.info(f"Successfully fetched and saved latest prices for {len(price_data)} companies")
    return price_data


def _save_prices_to_file(price_data: Dict[str, Dict[str, Any]]) -> None:
    """Save price data to JSON file."""
    try:
        with open(_PRICES_FILE, 'w') as f:
            json.dump(price_data, f, indent=2)
        logger.info(f"Saved latest prices to file: {_PRICES_FILE}")
    except Exception as e:
        logger.error(f"Error saving prices file: {e}")


def _load_prices_from_file() -> Dict[str, Dict[str, Any]]:
    """Load price data from JSON file."""
    try:
        with open(_PRICES_FILE, 'r') as f:
            price_data = json.load(f)
        logger.info(f"Loaded latest prices from file: {_PRICES_FILE} ({len(price_data)} tickers)")
        return price_data
    except Exception as e:
        logger.error(f"Error loading prices file: {e}")
        return {}


def get_ticker_price(ticker: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get the latest close price for a specific ticker.
    
    Args:
        ticker: Ticker symbol (e.g., "AAPL")
        force_refresh: If True, force a fresh fetch even if file exists
    
    Returns:
        Dictionary with price data for the ticker, or None if not found:
        {
            "date": "11/28/2025",
            "close": 150.25
        }
    
    Example:
        aapl_price = get_ticker_price("AAPL")
        print(aapl_price["close"])  # 150.25
    """
    # Load all prices (will use file if from today, or fetch if needed)
    all_prices = fetch_latest_sp500_prices(force_refresh=force_refresh)
    
    return all_prices.get(ticker.upper())


def get_all_prices(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Get latest prices for all S&P 500 companies.
    
    Args:
        force_refresh: If True, force a fresh fetch even if file exists and is from today
    
    Returns:
        Dictionary mapping ticker to price data
    
    Example:
        prices = get_all_prices()
        aapl = prices["AAPL"]
        msft = prices["MSFT"]
    """
    return fetch_latest_sp500_prices(force_refresh=force_refresh)
