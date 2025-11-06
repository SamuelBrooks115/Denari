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

from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.company import Company
from app.models.price_bar import PriceBar

logger = get_logger(__name__)

# TODO: choose vendor strategy — WHERE EVER THE FUCK WE GET IT FROM
# TODO: API KEYS FOR THE VENDOR


def get_latest_price_date(company_id: int, db: Session) -> Optional[date]:
    """
    Return the most recent date for which we have price data, or None if none exists.

    TODO:
    - Query PriceBar filtered by company_id ordered by date desc.
    """
    raise NotImplementedError("get_latest_price_date() must be implemented.")


def fetch_prices_from_vendor(ticker: str, start_date: Optional[date]) -> list[dict]:
    """
    Fetch price bars from the external data vendor.

    Returns list of dicts:
    [
        {"date": date, "close": float, "open": float|None, ...},
        ...
    ]

    TODO:
    - If start_date is None → fetch ~3-5 years history.
    - If start_date is provided → fetch from (start_date + 1 day) forward.
    - Use the vendor with settings.VENDOR_API_KEY or fallback.
    """
    raise NotImplementedError("fetch_prices_from_vendor() must be implemented.")


def upsert_price_bars(company_id: int, price_data: list[dict], db: Session) -> int:
    """
    Insert or update price_bar rows.

    Returns:
        Number of records inserted/updated.

    TODO:
    - Loop through returned price data.
    - Insert new rows only if (company_id, date) does not already exist.
    - Commit in chunks for performance if needed.
    """
    raise NotImplementedError("upsert_price_bars() must be implemented.")


def ensure_prices_fresh(company: Company, db: Session) -> bool:
    """
    High-level entrypoint used by ingest_orchestrator.

    Steps:
        1) Determine last stored price date.
        2) Fetch only *new* prices.
        3) Upsert into DB.
        4) Return whether new data was added.

    TODO:
    - Implement call flow once vendor + schema confirmed.
    """
    logger.info("Checking price freshness for %s", company.ticker)
    raise NotImplementedError("ensure_prices_fresh() must be implemented.")
