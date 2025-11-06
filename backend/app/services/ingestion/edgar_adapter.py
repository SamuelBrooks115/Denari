"""
edgar_adapter.py — SEC / EDGAR Filing Retrieval Layer

Purpose:
- Fetch raw 10-K and 10-Q filings for a company.
- Identify correct filing URLs based on CIK + period.
- Download the XBRL package (XML, JSON, or inline XBRL depending on availability).
- Return raw data to the normalization step. Do NOT normalize here.

Key Principle:
This module interacts with external data sources. It should be deterministic and testable.

Responsibilities:
- Convert ticker → CIK (if CIK missing)
- Query EDGAR index for available filings
- Download the latest filings covering required periods
- Return raw XBRL documents and file metadata to the orchestrator

This module does NOT:
- Parse or extract GAAP values (normalize_xbrl.py does that).
- Write to the database (ingest_orchestrator.py does that).
- Decide if data is “fresh enough” (orchestrator does that).
"""

import requests
from typing import List, Dict, Any

# TODO: If CIK is missing → implement lookup: ticker → CIK
# TODO: Use EDGAR full-text or SEC modern API when available
# TODO: Retry + rate-limit handling
# TODO: Implement basic request logging (use get_logger)

SEC_HEADERS = {
    "User-Agent": "Denari Research (contact: your_email_here)",
}


def fetch_filing_index(cik: str) -> List[Dict[str, Any]]:
    """
    Retrieve available filings for a company from EDGAR.

    Returns:
        A list of filings with metadata (form_type, filing_date, period_end, url).

    TODO:
    - Call SEC Company Filings endpoint.
    - Extract link to the filing's XBRL archive.
    - Return structured list.
    """
    raise NotImplementedError("fetch_filing_index() must be implemented.")


def download_xbrl_package(filing_url: str) -> Dict[str, Any]:
    """
    Download the raw XBRL package from SEC.

    Returns:
        {
            "raw_xbrl_xml": <str>,
            "metadata": { ... }
        }

    TODO:
    - Perform HTTP GET with SEC_HEADERS.
    - Handle gzipped / zipped inline XBRL.
    - Return raw text or bytes for normalization.
    """
    raise NotImplementedError("download_xbrl_package() must be implemented.")
