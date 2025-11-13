"""
edgar_adapter.py — SEC / EDGAR data access facade.

The ingestion pipeline should talk to this module rather than importing the
HTTP client directly. This keeps the outward-facing API function-oriented and
easy to mock in tests.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.services.ingestion.clients import EdgarClient

_client = EdgarClient()


def fetch_sp500_constituents() -> List[Dict[str, Any]]:
    """
    Return S&P 500 tickers with optional metadata (name, sector if present).
    """
    return _client.fetch_company_list(index="sp500")


def get_cik_map() -> Dict[str, int]:
    """Fetch the SEC-wide ticker→CIK map."""
    return _client.get_cik_map()


def fetch_submissions(cik: int) -> Dict[str, Any]:
    """Return the submissions feed for a CIK."""
    return _client.get_submissions(cik)


def fetch_company_facts(cik: int) -> Dict[str, Any]:
    """Return the company facts JSON for a CIK."""
    return _client.get_company_facts(cik)
