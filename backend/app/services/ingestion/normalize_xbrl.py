"""
normalize_xbrl.py — Convert Raw XBRL Filings into Normalized Financial Facts

Purpose:
- Take raw XBRL (downloaded via edgar_adapter) and extract:
    * GAAP tags (e.g., Revenues, NetIncomeLoss, Assets, CashAndCashEquivalents)
    * Values for a specific reporting period
    * Statement classification (IS, BS, CF)
- Output clean rows that match the XbrlFact ORM model.

Key Responsibilities:
- Parse XBRL structure (which varies between issuers and filing years).
- Map multiple vendor tag variants → canonical GAAP tag names.
- Ensure period_end detection is accurate.
- Return normalized values in a machine-usable structure.

This module does **not**:
- Decide which filings to process (orchestrator does that).
- Write to the database (ingest_orchestrator.py does that).
- Perform modeling or scaling adjustments.

Core Output Format (list of dict):
[
  {
    "company_id": int,
    "filing_id": int,
    "period_end": date,
    "statement_type": "IS" | "BS" | "CF",
    "tag": "Revenues",
    "value": 125000000.0,
    "unit": "USD"
  },
  ...
]
"""

from typing import List, Dict, Any
from datetime import date

# Potential future imports:
#  - from lxml import etree
#  - tag_mapping_table for canonical GAAP mappings
#  - get_logger for debug tracing

# TODO: Create and maintain canonical tag map
TAG_MAP = {
    # Example basic normalizations (these expand over time):
    "Revenues": "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "Revenues",
    "NetIncomeLoss": "NetIncomeLoss",
    "Assets": "Assets",
    "CashAndCashEquivalentsAtCarryingValue": "CashAndCashEquivalents",
}


def normalize_xbrl(raw_xbrl: Any, filing_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert raw XBRL to canonical fact rows.

    Parameters:
        raw_xbrl: Raw XBRL XML/JSON blob (as returned from edgar_adapter).
        filing_meta: {
            "company_id": int,
            "filing_id": int,
            "period_end": date,
        }

    Returns:
        List[Dict[str, Any]] formatted for bulk upsert into xbrl_fact.

    TODO:
    - Parse XML tree and iterate over contextRef → value nodes.
    - Determine whether each tag belongs to IS/BS/CF.
    - Apply TAG_MAP canonicalization.
    - Extract numeric values and convert to float.
    - Filter out dimensioned facts for MVP (segments, breakdowns).
    """
    raise NotImplementedError("normalize_xbrl must be implemented based on selected XBRL parsing approach.")
