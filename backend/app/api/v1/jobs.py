"""
jobs.py — Background Job Metadata & Status Endpoints (API Layer)

Purpose:
- Provide visibility into long-running ingest/modeling operations.
- Since the MVP does NOT use Celery/Redis or async workers, "jobs" here are:
    * Logged process events / workflow checkpoints
    * Stored records representing the status of ingestion/modeling runs
    * Potential future expansion to async/queued execution

Examples of Jobs:
- Running /companies/{id}/prepare may generate a record:
    * status: "running" → "completed" or "error"
    * details: {"fetched_prices": True, "normalized_facts": 2471, ...}

Key Interactions:
- app.models.job → ORM entity representing job runs and their metadata.
- app.services.jobs → helper utilities for recording and updating job status.
- app.services.ingestion.ingest_orchestrator → should create/update job entries.
- app.core.database → session handling for job persistence.

This API module should NOT:
- Execute ingestion or modeling itself.
- Perform any heavy computation.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.core.database import get_db
from app.models.job import Job  # ORM representing workflow/job runs
from app.services.jobs import get_job_by_id, list_jobs_for_company  # Planned utility functions

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

# -----------------------------------------------------------------------------
# Schemas (to be refined as job metadata design stabilizes)
# -----------------------------------------------------------------------------

class JobOut:
    """
    Response schema for reported job status.

    Expected Fields (MVP):
    - id: internal job ID
    - company_id: which company the job is associated with
    - job_type: "prepare", "valuation", etc.
    - status: "running", "completed", "failed"
    - started_at / finished_at timestamps
    - message/log: short text summary or pointer to detailed run log

    TODO:
    - Convert to Pydantic BaseModel and enable orm_mode once Job ORM defined.
    """
    pass


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/{company_id}", response_model=List[JobOut])
async def list_company_jobs(company_id: int, db=Depends(get_db)):
    """
    GET /jobs/{company_id}

    Returns:
    - All job records associated with the given company.

    TODO:
    - Implement real DB query: list_jobs_for_company(company_id, db)
    - Convert ORM records to JobOut schema.
    """
    return []  # placeholder


@router.get("/detail/{job_id}", response_model=JobOut)
async def get_job(job_id: int, db=Depends(get_db)):
    """
    GET /jobs/detail/{job_id}

    Purpose:
    - Retrieve a single job record including status.

    TODO:
    - Implement real DB lookup: get_job_by_id(job_id, db)
    - Raise 404 if not found.
    """
    # placeholder return until schema is defined
    return {"status": "placeholder"}
