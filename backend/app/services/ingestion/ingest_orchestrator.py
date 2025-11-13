"""
ingest_orchestrator.py — Data Readiness Workflow Orchestrator.

Provides high-level orchestration for:
    * Full S&P 500 historical ingestion
    * Single-company refreshes (e.g., `/companies/{id}/prepare`)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.company import Company
from app.models.job import Job
from app.services.ingestion.pipelines import SP500IngestionPipeline
from app.services.ingestion.repositories import XbrlRepository


logger = get_logger(__name__)


class IngestOrchestrator:
    """
    Coordinates ingestion workflows using the configured pipeline components.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        repository = XbrlRepository(db_session=db)
        self._pipeline = SP500IngestionPipeline(repository=repository)

    # ------------------------------------------------------------------ #
    def run_sp500_backfill(self, years: int = 5) -> Dict[str, Any]:
        logger.info("Starting S&P 500 backfill for %s years.", years)
        result = self._pipeline.ingest_all(years=years)
        logger.info("S&P 500 backfill complete: %s successes, %s errors.", result.get("succeeded", 0), len(result.get("errors", [])))
        return result

    def prepare_company(self, company_id: int, years: int = 5) -> Dict[str, Any]:
        job = Job(company_id=company_id, job_type="prepare")
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)

        try:
            company = self._db.query(Company).filter(Company.id == company_id).first()
            if not company:
                job.mark_failed("Company not found.")
                self._db.commit()
                return {"error": "company_not_found"}

            if not company.cik:
                job.mark_failed("Company missing CIK; cannot fetch EDGAR filings.")
                self._db.commit()
                return {"error": "cik_missing"}

            try:
                cik_int = int(company.cik)
            except ValueError as exc:
                job.mark_failed("Invalid CIK stored for company.")
                self._db.commit()
                raise RuntimeError("Invalid company CIK") from exc

            logger.info("Preparing data for company %s (CIK %s)", company.ticker, company.cik)

            ingestion_result = self._pipeline.ingest_single(
                ticker=company.ticker,
                cik=cik_int,
                years=years,
                company_id=company.id,
            )

            job.mark_completed(
                message="Ingestion completed.",
                details=ingestion_result,
            )
            self._db.commit()

            return {
                "company": company.ticker,
                "status": "success",
                "ingestion": ingestion_result,
            }

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error in prepare_company: %s", exc)
            job.mark_failed(str(exc))
            self._db.commit()
            raise


# Backwards-compatible function -------------------------------------------------------------- #
def prepare_company_data(company_id: int, db: Session, years: int = 5) -> Dict[str, Any]:
    orchestrator = IngestOrchestrator(db)
    return orchestrator.prepare_company(company_id, years=years)
