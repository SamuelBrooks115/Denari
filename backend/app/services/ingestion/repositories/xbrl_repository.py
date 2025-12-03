"""
Persistence layer wiring Supabase helpers into the ingestion workflow.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.ingestion.db_client import SupabaseDBClient, get_db_client


logger = get_logger(__name__)


class XbrlRepository:
    def __init__(self, db_client: Optional[SupabaseDBClient] = None) -> None:
        self._db = db_client or get_db_client()

    # ------------------------------------------------------------------ #
    def resolve_company_id(self, ticker: str, cik: Optional[int]) -> uuid.UUID:
        if cik is None:
            raise ValueError("CIK is required to resolve company.")
        return self._db.upsert_cik_safe(name=ticker, cik=f"{cik:010d}", ticker=ticker)

    def persist_period(
        self,
        company_id: uuid.UUID,
        filing_meta: Dict[str, Any],
        normalized_facts: List[Dict[str, Any]],
        filing_type: str,
        report_date: str,
        taxonomy: str,
        raw_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        fiscal_year = datetime.fromisoformat(report_date).year

        inserted_statements: Dict[str, uuid.UUID] = {}
        inserted_facts = 0

        for statement_type in {"IS", "BS", "CF"}:
            existing = self._db.get_statement_by_keys(company_id, fiscal_year, statement_type)
            if existing:
                logger.debug("Statement already exists for %s FY%d %s", filing_meta["ticker"], fiscal_year, statement_type)
                continue

            stmt_id = self._db.insert_financial_statement(
                company_id=company_id,
                stmt_type=statement_type,
                filing_type=filing_meta.get("filing_type", "10-K"),
                fiscal_period_end=datetime.fromisoformat(report_date),
                fiscal_year=fiscal_year,
            )
            statements_facts = [
                fact for fact in normalized_facts if fact["statement_type"] == statement_type and fact["period_end"] == report_date
            ]
            if statements_facts:
                # Determine period_type based on statement_type, not filing_type
                # Balance Sheets are "instant" (point in time), IS and CF are "duration" (period)
                period_type = "instant" if statement_type == "BS" else "duration"
                self._db.insert_financial_facts(stmt_id, statements_facts, period_type=period_type)
                inserted_facts += len(statements_facts)
            inserted_statements[statement_type] = stmt_id

        self._db.store_raw_companyfacts(company_id, report_date, raw_payload)

        return {
            "company_id": str(company_id),
            "report_date": report_date,
            "taxonomy": taxonomy,
            "statements_inserted": {k: str(v) for k, v in inserted_statements.items()},
            "facts_inserted": inserted_facts,
        }






