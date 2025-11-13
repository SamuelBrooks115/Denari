"""
Placeholder persistence layer for normalized XBRL facts.

In a full implementation this module would:
    - Map tickers/CIKs to internal company IDs
    - Upsert normalized facts into `xbrl_fact` (or equivalent) tables
    - Track ingestion history / freshness

For now the class is intentionally thin so that the ingestion pipeline can be
implemented and tested without a backing database.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger


logger = get_logger(__name__)


class XbrlRepository:
    """
    Stub repository that can be swapped for a database-backed implementation.
    """

    def __init__(self, db_session: Optional[Any] = None) -> None:
        self._db = db_session

    # ------------------------------------------------------------------ #
    def resolve_company_id(self, ticker: str, cik: Optional[int] = None) -> Optional[int]:
        """
        Return the internal company ID for a ticker/CIK pair.

        Default implementation returns None; override when integrating with DB.
        """
        logger.debug("resolve_company_id called for %s (CIK %s)", ticker, cik)
        return None

    def upsert_company_period(self, company_id: Optional[int], filing_meta: Dict[str, Any], facts: List[Dict[str, Any]]) -> None:
        """
        Persist normalized facts for a single reporting period.

        Default implementation only logs the intent. Replace with real persistence.
        """
        logger.info(
            "Upsert requested for ticker=%s period=%s facts=%d",
            filing_meta.get("ticker"),
            filing_meta.get("period_end"),
            len(facts),
        )
        # TODO: Implement database upsert logic
        _ = company_id, filing_meta, facts  # keep signature obligations





