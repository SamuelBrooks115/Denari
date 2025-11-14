"""
live_fetcher.py — On-the-fly EDGAR data fetching and parsing (no database)

Purpose:
- Fetch company data from EDGAR in real-time
- Parse XBRL and normalize to financial statements
- Return in-memory data structures (no persistence)
- Used by MVP live workflow endpoints

This module orchestrates:
1. Ticker → CIK lookup
2. EDGAR submissions fetch
3. Company facts fetch
4. XBRL parsing
5. Normalization to canonical financial statements
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.ingestion.clients import EdgarClient
from app.services.ingestion.xbrl.companyfacts_parser import (
    PeriodStatements,
    build_period_statements,
    detect_primary_taxonomy,
    extract_annual_report_dates,
)
from app.services.ingestion.xbrl.normalizer import CompanyFactsNormalizer
from app.services.ingestion.sp500_tickers import SP500_TICKERS

logger = get_logger(__name__)


def fetch_company_live(
    ticker: str,
    years: int = 5,
    edgar_client: Optional[EdgarClient] = None,
) -> Dict[str, Any]:
    """
    Fetch and parse company financial data from EDGAR on-the-fly.

    Args:
        ticker: Company ticker symbol (e.g., "AAPL")
        years: Number of years of historical data to fetch
        edgar_client: Optional EdgarClient instance (creates new if not provided)

    Returns:
        Dictionary containing:
        - ticker: str
        - cik: int
        - name: str (from submissions)
        - taxonomy: str (e.g., "us-gaap")
        - financials: Dict[str, List[Dict]] - normalized facts by period_end
        - periods: List[str] - list of period_end dates
        - raw_submissions: Dict - raw submissions data
        - raw_facts: Dict - raw company facts data

    Raises:
        RuntimeError if ticker not found, CIK lookup fails, or parsing fails
    """
    client = edgar_client or EdgarClient()

    # Step 1: Get CIK from ticker
    logger.info("Looking up CIK for ticker: %s", ticker)
    cik_map = client.get_cik_map()
    cik = cik_map.get(ticker.upper())
    if not cik:
        raise RuntimeError(f"CIK not found for ticker: {ticker}")

    # Step 2: Fetch submissions (for company name and report dates)
    logger.info("Fetching submissions for CIK: %s", cik)
    submissions = client.get_submissions(cik)
    company_name = submissions.get("name", ticker)
    report_dates = extract_annual_report_dates(submissions, years=years)
    
    if not report_dates:
        logger.warning("No annual filings found for %s (CIK: %s)", ticker, cik)
        return {
            "ticker": ticker,
            "cik": cik,
            "name": company_name,
            "taxonomy": None,
            "financials": {},
            "periods": [],
            "raw_submissions": submissions,
            "raw_facts": {},
        }

    # Step 3: Fetch company facts (XBRL data)
    logger.info("Fetching company facts for CIK: %s", cik)
    facts_payload = client.get_company_facts(cik)
    
    # Step 4: Detect taxonomy
    taxonomy = detect_primary_taxonomy(facts_payload)
    if not taxonomy:
        raise RuntimeError(f"No supported taxonomy found for CIK {cik}")

    taxonomy_facts = facts_payload["facts"][taxonomy]

    # Step 5: Build period statements
    logger.info("Parsing XBRL for %d periods", len(report_dates))
    statements_by_period: Dict[str, PeriodStatements] = {}
    for report_date in report_dates:
        statements_by_period[report_date] = build_period_statements(taxonomy_facts, report_date)

    # Step 6: Normalize to canonical financial statements
    logger.info("Normalizing financial statements")
    normalizer = CompanyFactsNormalizer()
    company_meta = {
        "company_id": None,  # No DB in MVP
        "ticker": ticker,
        "cik": cik,
    }
    
    normalized = normalizer.normalize_companyfacts(company_meta, taxonomy, statements_by_period)

    # Convert to more usable format - organize by statement type and period
    financials_by_statement: Dict[str, Dict[str, Dict[str, float]]] = {
        "IS": {},  # Income Statement
        "BS": {},  # Balance Sheet
        "CF": {},  # Cash Flow
        "SHARES": {},  # Share data
    }

    for period_end, facts_list in normalized.items():
        for fact in facts_list:
            stmt_type = fact.get("statement_type", "IS")
            tag = fact.get("tag")
            value = fact.get("value")
            
            if stmt_type not in financials_by_statement:
                continue
            if period_end not in financials_by_statement[stmt_type]:
                financials_by_statement[stmt_type][period_end] = {}
            
            if tag and value is not None:
                financials_by_statement[stmt_type][period_end][tag] = value

    return {
        "ticker": ticker,
        "cik": cik,
        "name": company_name,
        "taxonomy": taxonomy,
        "financials": financials_by_statement,
        "periods": report_dates,
        "raw_submissions": submissions,
        "raw_facts": facts_payload,
    }


def _get_sp500_tickers() -> set:
    """Get set of S&P 500 tickers from hard-coded list."""
    return SP500_TICKERS


def search_company_by_ticker(ticker: str, edgar_client: Optional[EdgarClient] = None) -> Dict[str, Any]:
    """
    Quick search to get basic company info by ticker.
    MVP: Only searches S&P 500 companies.

    Args:
        ticker: Company ticker symbol
        edgar_client: Optional EdgarClient instance

    Returns:
        Dictionary with:
        - ticker: str
        - cik: int
        - name: str
        - found: bool
        - in_sp500: bool (whether ticker is in S&P 500)
    """
    client = edgar_client or EdgarClient()
    ticker_upper = ticker.upper()
    
    try:
        # Check if ticker is in S&P 500
        sp500_tickers = _get_sp500_tickers()
        if ticker_upper not in sp500_tickers:
            return {
                "ticker": ticker,
                "cik": None,
                "name": None,
                "found": False,
                "in_sp500": False,
                "error": f"Ticker {ticker} is not in S&P 500. Only S&P 500 companies are supported in MVP.",
            }
        
        cik_map = client.get_cik_map()
        cik = cik_map.get(ticker_upper)
        
        if not cik:
            return {
                "ticker": ticker,
                "cik": None,
                "name": None,
                "found": False,
                "in_sp500": ticker_upper in sp500_tickers,
            }
        
        # Get company name from submissions
        submissions = client.get_submissions(cik)
        company_name = submissions.get("name", ticker)
        
        return {
            "ticker": ticker,
            "cik": cik,
            "name": company_name,
            "found": True,
            "in_sp500": True,
        }
    except Exception as exc:
        logger.exception("Error searching for ticker %s: %s", ticker, exc)
        return {
            "ticker": ticker,
            "cik": None,
            "name": None,
            "found": False,
            "in_sp500": False,
            "error": str(exc),
        }

