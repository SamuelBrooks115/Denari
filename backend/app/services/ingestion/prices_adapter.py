"""
prices_adapter.py — Market Data Ingestion (Daily Closing Prices)

Purpose:
- Ensure daily price history (price_bar) is complete and up to date.
- Fetch missing days from WHERE EVER THE FUCK WE GET IT FROM.
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
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import requests

from app.core.config import settings
from app.core.logging import get_logger
from app.models.company import Company
from app.models.price_bar import PriceBar

logger = get_logger(__name__)

# FMP API key is available via settings.FMP_API_KEY
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"


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
    Fetch price bars from FMP (Financial Modeling Prep) API.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        start_date: If None, fetches ~5 years of history. If provided, fetches from
                   (start_date + 1 day) to today.

    Returns:
        List of dicts with price data:
        [
            {"date": date, "close": float, "open": float|None, "high": float|None,
             "low": float|None, "volume": float|None},
            ...
        ]
        Returns empty list on error.

    Raises:
        None - errors are logged and empty list is returned.
    """
    api_key = settings.FMP_API_KEY
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

    # Build API URL
    url = f"{FMP_BASE_URL}/historical-price-full/{ticker}"
    params = {
        "apikey": api_key,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": today.strftime("%Y-%m-%d")
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # Raises HTTPError for bad responses

        data = response.json()

        # Check for FMP error responses
        if isinstance(data, dict):
            if "Error Message" in data:
                logger.error("FMP API error for %s: %s", ticker, data["Error Message"])
                return []
            if "historical" in data:
                historical_data = data["historical"]
            else:
                logger.warning("Unexpected FMP API response format for %s: %s", ticker, data)
                return []
        elif isinstance(data, list):
            historical_data = data
        else:
            logger.warning("Unexpected FMP API response format for %s", ticker)
            return []

        # Convert FMP format to our format
        price_bars = []
        for item in historical_data:
            # Parse date string to date object
            price_date = date.fromisoformat(item["date"])

            price_bar = {
                "date": price_date,
                "close": float(item.get("close", 0)),
                "open": float(item["open"]) if item.get("open") is not None else None,
                "high": float(item["high"]) if item.get("high") is not None else None,
                "low": float(item["low"]) if item.get("low") is not None else None,
                "volume": float(item["volume"]) if item.get("volume") is not None else None,
            }
            price_bars.append(price_bar)

        # FMP returns data in reverse chronological order (newest first)
        # Reverse to get chronological order (oldest first)
        price_bars.reverse()

        logger.info("Fetched %d price bars for %s", len(price_bars), ticker)
        return price_bars

    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch prices from FMP for %s: %s", ticker, str(e))
        return []
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error parsing FMP response for %s: %s", ticker, str(e))
        return []


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

    except Exception as e:
        logger.error(
            "Error ensuring price freshness for %s (company_id: %d): %s",
            company.ticker, company.id, str(e)
        )
        # Re-raise to allow caller to handle the error
        raise
