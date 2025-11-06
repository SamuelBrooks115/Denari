"""
ingest_orchestrator.py — Data Readiness Workflow Orchestrator

Purpose:
- Ensure a company's data is ready for valuation.
- Coordinates:
    1. Price freshness checks + ingestion
    2. Filing completeness checks + EDGAR fetch
    3. XBRL normalization → XbrlFact records
    4. Upserts into Postgres
    5. Job logging for transparency

This is the *command layer* — the workflow brain.

Inputs:
- company_id
- DB session

Outputs:
- Status summary dict (what was updated / unchanged)

This module does NOT:
- Perform API calls directly (delegates to prices_adapter & edgar_adapter).
- Parse XBRL itself (delegates to normalize_xbrl).
- Perform valuation modeling (that is services/modeling/*).
"""

from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.logging import get_logger
from app.models.company import Company
from app.models.job import Job

# Adapters / Steps
from app.services.ingestion.prices_adapter import ensure_prices_fresh
from app.services.ingestion.edgar_adapter import fetch_filing_index, download_xbrl_package
from app.services.ingestion.normalize_xbrl import normalize_xbrl

logger = get_logger(__name__)


def prepare_company_data(company_id: int, db: Session) -> Dict[str, Any]:
    """
    Main entrypoint for /companies/{id}/prepare

    High-Level Workflow:
        1. Verify company exists.
        2. Start a Job record.
        3. Ensure prices are fresh (add or update price_bar records).
        4. Check if filings exist for required historical coverage.
        5. If missing: fetch, download XBRL, normalize → upsert.
        6. Mark job complete or failed.
        7. Return structured summary.

    TODO:
    - Implement all step calls once adapters are developed.
    - Define minimum coverage rule (e.g., ≥ 3 annual periods).
    """
    job = Job(company_id=company_id, job_type="prepare")
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            job.mark_failed("Company not found.")
            db.commit()
            return {"error": "company_not_found"}

        logger.info("Preparing data for company %s", company.ticker)

        # TODO: Step 3 — Ensure market prices are up to date
        # prices_updated = ensure_prices_fresh(company, db)

        # TODO: Step 4 — Get filing list
        # filings = fetch_filing_index(company.cik)

        # TODO: Step 5 — For any missing periods:
        #   raw_xbrl = download_xbrl_package(...)
        #   facts = normalize_xbrl(raw_xbrl, {"company_id": ..., "filing_id": ..., "period_end": ...})
        #   Upsert facts → xbrl_fact table

        # TODO: Step 6 — Determine if we now meet required historical coverage
        # coverage_ok = check_required_financial_coverage(company_id, db)

        job.mark_completed(message="Data prepared successfully.", details={})
        db.commit()

        return {
            "company": company.ticker,
            "status": "success",
            # "prices_updated": prices_updated,
            # "coverage_ok": coverage_ok,
        }

    except Exception as e:
        logger.error("Error in prepare_company_data: %s", str(e))
        job.mark_failed(str(e))
        db.commit()
        raise
