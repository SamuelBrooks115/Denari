"""
Supabase database client helpers for the ingestion pipeline.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

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
        try:
            result = self._client.table("COMPANY").insert(payload).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to insert company: {e}") from e
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
        try:
            insert_response = self._client.table("IDENTIFIER").insert(ident_payload).execute()
        except Exception as e:
            logger.warning("Failed to insert identifier for %s: %s", ticker, e)

    # ------------------------------------------------------------------ #
    # Security & Listing helpers
    def ensure_security(self, company_id: uuid.UUID, security_type: str = "equity", share_class: Optional[str] = None) -> uuid.UUID:
        response = (
            self._client.table("SECURITY")
            .select("*")
            .eq("company_id", str(company_id))
            .limit(1)
            .execute()
        )
        if response.data:
            return uuid.UUID(response.data[0]["security_id"])

        security_id = uuid.uuid4()
        payload = {
            "security_id": str(security_id),
            "company_id": str(company_id),
            "security_type": security_type,
            "share_class": share_class,
            "created_at": datetime.utcnow().isoformat(),
        }
        try:
            insert_response = self._client.table("SECURITY").insert(payload).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to insert security: {e}") from e
        return security_id

    def ensure_listing(
        self,
        security_id: uuid.UUID,
        symbol: str,
        exchange: Optional[str] = None,
    ) -> uuid.UUID:
        response = (
            self._client.table("LISTING")
            .select("*")
            .eq("security_id", str(security_id))
            .eq("symbol", symbol.upper())
            .limit(1)
            .execute()
        )
        if response.data:
            return uuid.UUID(response.data[0]["listing_id"])

        listing_id = uuid.uuid4()
        now_iso = datetime.utcnow().isoformat()
        payload = {
            "listing_id": str(listing_id),
            "security_id": str(security_id),
            "symbol": symbol.upper(),
            "exchange": exchange,
            "effective_from": now_iso,
            "effective_to": None,
        }
        try:
            insert_response = self._client.table("LISTING").insert(payload).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to insert listing: {e}") from e
        return listing_id

    def upsert_price_eod(
        self,
        listing_id: uuid.UUID,
        price_rows: Sequence[Dict[str, Any]],
        currency: str = "USD",
    ) -> int:
        if not price_rows:
            return 0

        now_iso = datetime.utcnow().isoformat()
        
        # Extract dates to check for existing records
        price_dates = [item["date"].isoformat() for item in price_rows]
        
        # Query existing records for this listing and dates
        existing_response = (
            self._client.table("PRICE_EOD")
            .select("price_id, price_date")
            .eq("listing_id", str(listing_id))
            .in_("price_date", price_dates)
            .execute()
        )
        
        # Create a set of existing dates for fast lookup
        existing_dates = {record["price_date"] for record in existing_response.data or []}
        existing_by_date = {record["price_date"]: record["price_id"] for record in existing_response.data or []}
        
        rows_to_insert = []
        rows_to_update = []
        
        for item in price_rows:
            price_date = item["date"].isoformat()
            # Convert volume to int if present (database expects bigint, not float)
            volume = item.get("volume")
            volume_int = int(volume) if volume is not None else None
            
            row_data = {
                "listing_id": str(listing_id),
                "price_date": price_date,
                "open": item.get("open"),
                "high": item.get("high"),
                "low": item.get("low"),
                "close": item["close"],
                "adj_close": item.get("adj_close") or item.get("close"),
                "volume": volume_int,
                "currency": currency,
                "as_of_ts": now_iso,
                "source_id": str(self._config.data_source_id) if self._config.data_source_id else None,
            }
            
            if price_date in existing_dates:
                # Update existing record
                row_data["price_id"] = existing_by_date[price_date]
                rows_to_update.append(row_data)
            else:
                # Insert new record
                row_data["price_id"] = str(uuid.uuid4())
                rows_to_insert.append(row_data)
        
        try:
            # Insert new records
            if rows_to_insert:
                self._client.table("PRICE_EOD").insert(rows_to_insert).execute()
            
            # Update existing records
            if rows_to_update:
                for row in rows_to_update:
                    price_id = row.pop("price_id")
                    self._client.table("PRICE_EOD").update(row).eq("price_id", price_id).execute()
            
            return len(rows_to_insert) + len(rows_to_update)
        except Exception as e:
            raise RuntimeError(f"Failed to upsert PRICE_EOD rows: {e}") from e

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
        try:
            response = self._client.table("FINANCIAL_STATEMENT").insert(payload).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to insert financial statement: {e}") from e
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

        try:
            response = self._client.table("FINANCIAL_FACT").insert(rows).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to insert financial facts: {e}") from e

    # ------------------------------------------------------------------ #
    # Raw payload archival
    def store_raw_companyfacts(self, company_id: uuid.UUID, report_date: str, payload: Dict[str, Any]) -> Optional[uuid.UUID]:
        report_id = uuid.uuid4()
        checksum = str(abs(hash(json.dumps(payload, sort_keys=True))))
        # Note: company_id is embedded in storage_uri path since REPORT_ARTIFACT table doesn't have company_id column
        artifact_payload = {
            "report_id": str(report_id),
            "created_at": datetime.utcnow().isoformat(),
            "format": "json",
            "mime_type": "application/json",
            "storage_uri": f"companyfacts/{company_id}/{report_date}.json",
            "checksum": checksum,
            "org_id": str(self._config.org_id) if self._config.org_id else None,
        }
        try:
            response = self._client.table("REPORT_ARTIFACT").insert(artifact_payload).execute()
        except Exception as e:
            logger.warning("Failed to store raw company facts: %s", e)
            return None
        return report_id


def get_db_client() -> SupabaseDBClient:
    return SupabaseDBClient()


