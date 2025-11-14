"""
Supabase database client helpers for the ingestion pipeline.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


def _create_supabase_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


@dataclass
class SupabaseConfig:
    data_source_id: Optional[uuid.UUID] = None
    org_id: Optional[uuid.UUID] = None


class SupabaseDBClient:
    """
    Thin wrapper providing typed helpers around Supabase tables.
    """

    def __init__(self, client: Optional[Client] = None, config: Optional[SupabaseConfig] = None):
        self._client = client or _create_supabase_client()
        self._config = config or SupabaseConfig()

    # ------------------------------------------------------------------ #
    # Company helpers
    def get_company_by_cik(self, cik: str) -> Optional[Dict[str, Any]]:
        response = (
            self._client.table("COMPANY")
            .select("*")
            .eq("cik", cik)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    def insert_company(self, name: str, cik: str, ticker: Optional[str] = None) -> uuid.UUID:
        company_id = uuid.uuid4()
        payload = {
            "company_id": str(company_id),
            "name": name,
            "cik": cik,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self._client.table("COMPANY").insert(payload).execute()
        if result.error:
            raise RuntimeError(f"Failed to insert company: {result.error}")
        if ticker:
            self._ensure_identifier(company_id, ticker)
        return company_id

    def upsert_cik_safe(self, name: str, cik: str, ticker: Optional[str] = None) -> uuid.UUID:
        existing = self.get_company_by_cik(cik)
        if existing:
            company_id = uuid.UUID(existing["company_id"])
            if ticker:
                self._ensure_identifier(company_id, ticker)
            return company_id
        return self.insert_company(name=name, cik=cik, ticker=ticker)

    def _ensure_identifier(self, company_id: uuid.UUID, ticker: str) -> None:
        response = (
            self._client.table("IDENTIFIER")
            .select("*")
            .eq("company_id", str(company_id))
            .eq("id_type", "ticker")
            .eq("id_value", ticker.upper())
            .limit(1)
            .execute()
        )
        if response.data:
            return
        ident_payload = {
            "ident_id": str(uuid.uuid4()),
            "company_id": str(company_id),
            "id_type": "ticker",
            "id_value": ticker.upper(),
            "effective_from": datetime.utcnow().isoformat(),
            "source": "edgar_ingestion",
        }
        insert_response = self._client.table("IDENTIFIER").insert(ident_payload).execute()
        if insert_response.error:
            logger.warning("Failed to insert identifier for %s: %s", ticker, insert_response.error)

    # ------------------------------------------------------------------ #
    # Financial statements & facts
    def get_statement_by_keys(self, company_id: uuid.UUID, fiscal_year: int, stmt_type: str) -> Optional[Dict[str, Any]]:
        response = (
            self._client.table("FINANCIAL_STATEMENT")
            .select("*")
            .eq("company_id", str(company_id))
            .eq("fiscal_year", fiscal_year)
            .eq("stmt_type", stmt_type)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    def insert_financial_statement(
        self,
        company_id: uuid.UUID,
        stmt_type: str,
        filing_type: str,
        fiscal_period_end: datetime,
        fiscal_year: int,
    ) -> uuid.UUID:
        stmt_id = uuid.uuid4()
        payload = {
            "stmt_id": str(stmt_id),
            "company_id": str(company_id),
            "stmt_type": stmt_type,
            "filing_type": filing_type,
            "fiscal_period_end": fiscal_period_end.date().isoformat(),
            "fiscal_year": fiscal_year,
            "source_id": str(self._config.data_source_id) if self._config.data_source_id else None,
            "fiscal_period": "FY",
        }
        response = self._client.table("FINANCIAL_STATEMENT").insert(payload).execute()
        if response.error:
            raise RuntimeError(f"Failed to insert financial statement: {response.error}")
        return stmt_id

    def insert_financial_facts(
        self,
        stmt_id: uuid.UUID,
        facts: List[Dict[str, Any]],
        period_type: str,
    ) -> None:
        rows = []
        for fact in facts:
            rows.append(
                {
                    "fact_id": str(uuid.uuid4()),
                    "stmt_id": str(stmt_id),
                    "period_type": period_type,
                    "us_gaap_tag": fact.get("source_tag") or fact["tag"],
                    "value": fact["value"],
                    "unit": fact.get("unit"),
                    "context_ref": f"{fact['statement_type']}_{fact['tag']}_{fact['period_end']}",
                    "effective_from": None,
                    "effective_to": None,
                    "source_id": str(self._config.data_source_id) if self._config.data_source_id else None,
                }
            )

        if not rows:
            return

        response = self._client.table("FINANCIAL_FACT").insert(rows).execute()
        if response.error:
            raise RuntimeError(f"Failed to insert financial facts: {response.error}")

    # ------------------------------------------------------------------ #
    # Raw payload archival
    def store_raw_companyfacts(self, company_id: uuid.UUID, report_date: str, payload: Dict[str, Any]) -> Optional[uuid.UUID]:
        report_id = uuid.uuid4()
        checksum = str(abs(hash(json.dumps(payload, sort_keys=True))))
        artifact_payload = {
            "report_id": str(report_id),
            "company_id": str(company_id),
            "created_at": datetime.utcnow().isoformat(),
            "format": "json",
            "mime_type": "application/json",
            "storage_uri": f"companyfacts/{company_id}/{report_date}.json",
            "checksum": checksum,
            "org_id": str(self._config.org_id) if self._config.org_id else None,
        }
        response = self._client.table("REPORT_ARTIFACT").insert(artifact_payload).execute()
        if response.error:
            logger.warning("Failed to store raw company facts: %s", response.error)
            return None
        return report_id


def get_db_client() -> SupabaseDBClient:
    return SupabaseDBClient()


