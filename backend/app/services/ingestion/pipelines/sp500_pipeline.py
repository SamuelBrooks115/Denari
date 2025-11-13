"""
Pipeline for ingesting S&P 500 historical financials.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.ingestion.clients import EdgarClient
from app.services.ingestion.repositories.xbrl_repository import XbrlRepository
from app.services.ingestion.xbrl.companyfacts_parser import (
    PeriodStatements,
    build_period_statements,
    detect_primary_taxonomy,
    extract_annual_report_dates,
)
from app.services.ingestion.xbrl.normalizer import CompanyFactsNormalizer


logger = get_logger(__name__)


class SP500IngestionPipeline:
    """
    Coordinates fetching and normalization for all S&P 500 constituents.
    """

    def __init__(
        self,
        edgar_client: Optional[EdgarClient] = None,
        normalizer: Optional[CompanyFactsNormalizer] = None,
        repository: Optional[XbrlRepository] = None,
        years: int = 5,
    ) -> None:
        self._edgar_client = edgar_client or EdgarClient()
        self._normalizer = normalizer or CompanyFactsNormalizer()
        self._repository = repository or XbrlRepository()
        self._years = years

    def ingest_all(self, years: Optional[int] = None) -> Dict[str, Any]:
        target_years = years or self._years
        constituents = self._edgar_client.fetch_company_list(index="sp500")
        cik_map = self._edgar_client.get_cik_map()

        summary = {
            "universe": len(constituents),
            "processed": 0,
            "succeeded": 0,
            "errors": [],
        }

        for record in constituents:
            ticker = record["ticker"]
            cik = cik_map.get(ticker.upper())
            summary["processed"] += 1
            if not cik:
                logger.warning("CIK not found for ticker %s; skipping.", ticker)
                summary["errors"].append({"ticker": ticker, "error": "cik_not_found"})
                continue

            try:
                result = self._process_ticker(ticker, cik, target_years)
                summary["succeeded"] += 1
                summary.setdefault("details", []).append(result)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Failed to ingest %s: %s", ticker, exc)
                summary["errors"].append({"ticker": ticker, "error": str(exc)})

        return summary

    # ------------------------------------------------------------------ #
    def ingest_single(
        self,
        ticker: str,
        cik: int,
        years: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        target_years = years or self._years
        return self._process_ticker(ticker, cik, target_years, company_id_override=company_id)

    # ------------------------------------------------------------------ #
    def _process_ticker(
        self,
        ticker: str,
        cik: int,
        years: int,
        company_id_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        submissions = self._edgar_client.get_submissions(cik)
        report_dates = extract_annual_report_dates(submissions, years=years)
        if not report_dates:
            logger.info("No annual filings found for %s (%s).", ticker, cik)
            return {"ticker": ticker, "cik": cik, "status": "no_data"}

        facts_payload = self._edgar_client.get_company_facts(cik)
        taxonomy = detect_primary_taxonomy(facts_payload)
        if not taxonomy:
            raise RuntimeError(f"No supported taxonomy found for CIK {cik}.")

        taxonomy_facts = facts_payload["facts"][taxonomy]
        statements_by_period: Dict[str, PeriodStatements] = {}
        for report_date in report_dates:
            statements_by_period[report_date] = build_period_statements(taxonomy_facts, report_date)

        company_id = company_id_override
        if company_id is None:
            company_id = self._repository.resolve_company_id(ticker, cik=cik)

        company_meta = {
            "company_id": company_id,
            "ticker": ticker,
            "cik": cik,
        }

        normalized = self._normalizer.normalize_companyfacts(company_meta, taxonomy, statements_by_period)
        persisted_periods: List[str] = []
        for period_end, facts in normalized.items():
            filing_meta = {
                "ticker": ticker,
                "cik": cik,
                "period_end": period_end,
                "taxonomy": taxonomy,
            }
            self._repository.upsert_company_period(company_id, filing_meta, facts)
            persisted_periods.append(period_end)

        return {
            "ticker": ticker,
            "cik": cik,
            "taxonomy": taxonomy,
            "periods": persisted_periods,
            "status": "ok",
        }


