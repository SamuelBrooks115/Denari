"""
prices_adapter.py — Market Data Ingestion (Daily Closing Prices)

Purpose:
- Ensure daily price history (price_bar) is complete and up to date.
- Fetch missing days from Yahoo Finance.
- Insert or update rows in price_bar.

Key Concept:
We do NOT fetch full history every time. We:
1) Check the most recent price date we have stored.
2) Fetch only data AFTER that date.
3) Insert missing rows.

This keeps the pipeline fast and cheap.

This module does NOT:
- Trigger workflows (ingest_orchestrator does that).
- Perform valuation math.
"""

from datetime import date, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
import yfinance as yf
import pandas as pd

from app.core.logging import get_logger
from app.models.company import Company
from app.models.price_bar import PriceBar

logger = get_logger(__name__)


# Custom exceptions for Yahoo Finance errors
class YahooFinanceError(Exception):
    """Base exception for Yahoo Finance errors."""
    pass


class YahooFinanceNetworkError(YahooFinanceError):
    """Raised when network/connection errors occur fetching Yahoo Finance data."""
    pass


class YahooFinanceTickerError(YahooFinanceError):
    """Raised when ticker is invalid or no data is available."""
    pass


def _validate_and_clamp_dates(from_date: date, to_date: date) -> Tuple[date, date]:
    """
    Validate and clamp dates to prevent future dates and ensure from_date <= to_date.

    Args:
        from_date: Start date (may be in future)
        to_date: End date (may be in future)

    Returns:
        Tuple of (validated_from_date, validated_to_date) where:
        - Both dates are clamped to today if in the future
        - from_date <= to_date (swapped if needed)
    """
    today = date.today()
    # Clamp to today if future
    from_date = min(from_date, today)
    to_date = min(to_date, today)
    # Ensure from <= to
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    return from_date, to_date


def get_latest_price_date(company_id: int, db: Session) -> Optional[date]:
    """
    Return the most recent date for which we have price data, or None if none exists.

    Args:
        company_id: The ID of the company to check
        db: Database session

    Returns:
        The most recent date with price data, or None if no price data exists
    """
    latest_date = (
        db.query(PriceBar.date)
        .filter(PriceBar.company_id == company_id)
        .order_by(desc(PriceBar.date))
        .limit(1)
        .scalar()
    )

    return latest_date


def fetch_prices_from_vendor(ticker: str, start_date: Optional[date]) -> list[dict]:
    """
    Fetch price bars from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        start_date: If None, fetches ~5 years of history. If provided, fetches from
                   (start_date + 1 day) to today.

    Returns:
        List of dicts with price data:
        [
            {"date": date, "close": float, "open": float|None, "high": float|None,
             "low": float|None, "volume": float|None, "adj_close": float|None},
            ...
        ]
        Returns empty list if no data available or on non-critical errors.

    Raises:
        YahooFinanceTickerError: If ticker is invalid or no data available
        YahooFinanceNetworkError: If network/connection errors occur
        YahooFinanceError: For other Yahoo Finance errors
    """
    today = date.today()

    # Determine date range
    if start_date is None:
        # Fetch ~5 years of history
        from_date = today - timedelta(days=5 * 365)
        logger.info("Fetching 5 years of price history for %s", ticker)
    else:
        # Fetch from day after start_date to today
        from_date = start_date + timedelta(days=1)
        logger.info("Fetching price data for %s from %s to %s", ticker, from_date, today)

    # Validate and clamp dates to prevent future dates
    from_date, to_date = _validate_and_clamp_dates(from_date, today)

    # Check if date range is valid
    if from_date > to_date:
        logger.warning("Invalid date range for %s: from_date %s > to_date %s", ticker, from_date, to_date)
        return []

    try:
        # Create yfinance Ticker object
        ticker_obj = yf.Ticker(ticker)

        # Fetch historical data
        # yfinance expects dates as strings or date objects
        hist = ticker_obj.history(start=from_date, end=to_date)

        # Check if DataFrame is empty (invalid ticker or no data)
        if hist.empty:
            error_msg = f"No price data available for ticker {ticker} in date range {from_date} to {to_date}"
            logger.warning(error_msg)
            raise YahooFinanceTickerError(error_msg)

        # Convert DataFrame to list of dicts
        price_bars = []
        for idx, row in hist.iterrows():
            # yfinance returns DatetimeIndex, convert to date
            if isinstance(idx, pd.Timestamp):
                price_date = idx.date()
            elif hasattr(idx, 'date'):
                price_date = idx.date()
            else:
                logger.warning("Unexpected date index type for %s: %s", ticker, type(idx))
                continue

            # Extract OHLCV data, handling NaN values
            # yfinance columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
            # Note: yfinance uses "Adj Close" but we'll get it from the Close column
            # and calculate adjusted close if needed
            open_val = row.get("Open")
            high_val = row.get("High")
            low_val = row.get("Low")
            close_val = row.get("Close")
            adj_close_val = row.get("Adj Close") if "Adj Close" in row else close_val
            volume_val = row.get("Volume")

            # Convert NaN to None for optional fields
            price_bar = {
                "date": price_date,
                "open": float(open_val) if pd.notna(open_val) else None,
                "high": float(high_val) if pd.notna(high_val) else None,
                "low": float(low_val) if pd.notna(low_val) else None,
                "close": float(close_val) if pd.notna(close_val) else 0.0,
                "adj_close": float(adj_close_val) if pd.notna(adj_close_val) else None,
                "volume": float(volume_val) if pd.notna(volume_val) else None,
            }
            price_bars.append(price_bar)

        logger.info("Fetched %d price bars for %s", len(price_bars), ticker)
        return price_bars

    except YahooFinanceTickerError:
        # Re-raise ticker errors
        raise
    except Exception as e:
        # Check if it's a network-related error
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ["network", "connection", "timeout", "dns", "resolve"]):
            error_msg = f"Network error fetching Yahoo Finance data for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise YahooFinanceNetworkError(error_msg) from e
        else:
            error_msg = f"Error fetching Yahoo Finance data for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise YahooFinanceError(error_msg) from e


def upsert_price_bars(company_id: int, price_data: list[dict], db: Session) -> int:
    """
    Insert or update price_bar rows.

    Args:
        company_id: The ID of the company
        price_data: List of dicts with price data (from fetch_prices_from_vendor)
        db: Database session

    Returns:
        Number of records inserted/updated.

    Behavior:
    - Checks if (company_id, date) already exists for each price bar
    - Inserts new records if they don't exist
    - Updates existing records if they do exist
    - Commits in chunks of 100 for performance
    """
    if not price_data:
        logger.info("No price data to upsert for company_id %d", company_id)
        return 0

    # Extract dates from price_data to query existing records
    dates = [item["date"] for item in price_data]

    # Query existing price bars for this company and these dates
    existing_bars = (
        db.query(PriceBar)
        .filter(
            PriceBar.company_id == company_id,
            PriceBar.date.in_(dates)
        )
        .all()
    )

    # Create a set of existing dates for fast lookup
    existing_dates = {bar.date for bar in existing_bars}
    existing_by_date = {bar.date: bar for bar in existing_bars}

    inserted_count = 0
    updated_count = 0
    chunk_size = 100

    try:
        for i, price_item in enumerate(price_data):
            price_date = price_item["date"]

            if price_date in existing_dates:
                # Update existing record
                existing_bar = existing_by_date[price_date]
                existing_bar.open = price_item.get("open")
                existing_bar.high = price_item.get("high")
                existing_bar.low = price_item.get("low")
                existing_bar.close = price_item["close"]  # Required field
                existing_bar.volume = price_item.get("volume")
                updated_count += 1
            else:
                # Insert new record
                new_bar = PriceBar(
                    company_id=company_id,
                    date=price_date,
                    open=price_item.get("open"),
                    high=price_item.get("high"),
                    low=price_item.get("low"),
                    close=price_item["close"],  # Required field
                    volume=price_item.get("volume")
                )
                db.add(new_bar)
                inserted_count += 1

            # Commit in chunks for performance
            if (i + 1) % chunk_size == 0:
                db.commit()
                logger.debug("Committed chunk of %d price bars for company_id %d", chunk_size, company_id)

        # Commit remaining records
        db.commit()

        total_count = inserted_count + updated_count
        logger.info(
            "Upserted %d price bars for company_id %d (%d inserted, %d updated)",
            total_count, company_id, inserted_count, updated_count
        )

        return total_count

    except Exception as e:
        db.rollback()
        logger.error("Error upserting price bars for company_id %d: %s", company_id, str(e))
        raise


def ensure_prices_fresh(company: Company, db: Session) -> bool:
    """
    High-level entrypoint used by ingest_orchestrator.

    Ensures price data for a company is up to date by:
        1) Determining the last stored price date (if any)
        2) Fetching only new prices from the vendor
        3) Upserting the new prices into the database
        4) Returning whether new data was added

    Args:
        company: Company object with ticker and id
        db: Database session

    Returns:
        True if new price data was added, False otherwise
    """
    logger.info("Checking price freshness for %s (company_id: %d)", company.ticker, company.id)

    try:
        # Step 1: Determine last stored price date
        latest_date = get_latest_price_date(company.id, db)

        if latest_date:
            logger.info("Latest price date for %s: %s", company.ticker, latest_date)
        else:
            logger.info("No existing price data found for %s, fetching initial history", company.ticker)

        # Step 2: Fetch new prices from vendor
        # Pass latest_date (or None if no data exists) to fetch only new data
        price_data = fetch_prices_from_vendor(company.ticker, latest_date)

        if not price_data:
            logger.info("No new price data available for %s", company.ticker)
            return False

        # Step 3: Upsert prices into database
        records_upserted = upsert_price_bars(company.id, price_data, db)

        # Step 4: Return whether new data was added
        if records_upserted > 0:
            logger.info(
                "Successfully updated prices for %s: %d records upserted",
                company.ticker, records_upserted
            )
            return True
        else:
            logger.info("No price records were upserted for %s", company.ticker)
            return False

    except YahooFinanceTickerError as e:
        # Log ticker errors but don't crash the pipeline
        logger.error(
            "Yahoo Finance ticker error for %s (company_id: %d): %s",
            company.ticker, company.id, str(e)
        )
        # Return False instead of raising to allow pipeline to continue
        return False
    except YahooFinanceNetworkError as e:
        logger.error(
            "Yahoo Finance network error for %s (company_id: %d): %s",
            company.ticker, company.id, str(e)
        )
        # Re-raise network errors as they may be transient
        raise
    except YahooFinanceError as e:
        logger.error(
            "Yahoo Finance error ensuring price freshness for %s (company_id: %d): %s",
            company.ticker, company.id, str(e)
        )
        # Re-raise to allow caller to handle the error
        raise
    except Exception as e:
        logger.error(
            "Error ensuring price freshness for %s (company_id: %d): %s",
            company.ticker, company.id, str(e)
        )
        # Re-raise to allow caller to handle the error
        raise