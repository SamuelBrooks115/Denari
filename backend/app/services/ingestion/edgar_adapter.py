"""
edgar_adapter.py — SEC / EDGAR data access facade.

The ingestion pipeline should talk to this module rather than importing the
HTTP client directly. This keeps the outward-facing API function-oriented and
easy to mock in tests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.ingestion.clients import EdgarClient
from app.services.ingestion.structured_formatter import format_with_llm_classification
from app.services.ingestion.structured_output import (
    determine_annual_bs_anchor,
    extract_statements_for_date,
    find_currency,
)

logger = get_logger(__name__)

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


def fetch_and_format_structured(
    cik: int,
    ticker: str,
    report_date: Optional[str] = None,
    edgar_client: Optional[EdgarClient] = None,
) -> Dict[str, Any]:
    """
    Fetch EDGAR facts and format into structured JSON with LLM classification.

    This function orchestrates the full workflow:
    1. Fetches raw EDGAR Company Facts data
    2. Extracts facts for the specified report date (or latest annual)
    3. Builds structured JSON without classifications
    4. Tags only required modeling items using LLM matching
    5. Updates JSON in-place with classifications

    Args:
        cik: Company CIK number
        ticker: Company ticker symbol
        report_date: Optional report date (ISO format). If None, uses latest annual filing
        edgar_client: Optional EdgarClient instance (creates new one if not provided)

    Returns:
        Complete structured JSON matching Denari schema with LLM classifications
    """
    client = edgar_client or EdgarClient()

    # 1) Fetch company facts
    facts = client.get_company_facts(cik)
    entity_name = facts.get("entityName") or f"Company {ticker}"
    facts_root = (facts or {}).get("facts", {})
    us_gaap = facts_root.get("us-gaap", {})
    if not us_gaap:
        raise RuntimeError(f"No 'us-gaap' section found in company facts for CIK {cik}.")

    # 2) Determine report date if not provided
    if not report_date:
        anchor = determine_annual_bs_anchor(us_gaap)
        report_date = anchor["report_date"]
        filing_type = anchor["filing_type"]
        accession = anchor["accession"]
        fiscal_year = anchor["fiscal_year"]
    else:
        # If report_date provided, try to get filing metadata from submissions
        submissions = client.get_submissions(cik)
        filing_type = "10-K"  # Default
        accession = ""
        fiscal_year = None
        # Try to extract fiscal year from report_date
        try:
            from datetime import datetime
            d = datetime.fromisoformat(report_date.split("T")[0])
            fiscal_year = d.year
        except Exception:
            pass

    fiscal_year_str = str(fiscal_year) if fiscal_year is not None else ""

    # 3) Extract raw facts for the report date
    raw_facts = extract_statements_for_date(us_gaap, report_date)

    # 4) Determine statement currency
    statement_currency = (
        find_currency(
            raw_facts.get("bs", []),
            raw_facts.get("is", []),
            raw_facts.get("cf", []),
        )
        or "USD"
    )

    # 5) Build metadata
    metadata = {
        "cik": f"{cik:010d}",
        "ticker": ticker,
        "company_name": entity_name,
        "filing_type": filing_type,
        "filing_accession": accession,
        "fiscal_year": fiscal_year_str,
        "fiscal_period": "FY",
        "us_gaap_taxonomy_year": "",
    }

    # 6) Format with LLM classification
    logger.info(f"Formatting structured output with LLM classification for {ticker} (CIK: {cik:010d})")
    structured_json = format_with_llm_classification(
        raw_facts=raw_facts,
        metadata=metadata,
        report_date=report_date,
        statement_currency=statement_currency,
    )

    return structured_json
