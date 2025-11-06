"""
jobs.py — Utilities for Recording and Inspecting Job Run Status

Purpose:
- Provide helper functions to:
    * Create job records
    * Update job status
    * Retrieve job summaries for UI or debugging
- Keeps job logic out of API and orchestrator layers.

This module does NOT:
- Execute ingestion or modeling steps.
- Contain any business workflow logic.

It simply encapsulates DB queries for the Job model.
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.job import Job


def get_job_by_id(job_id: int, db: Session) -> Optional[Job]:
    """
    Retrieve a single job.

    TODO:
    - Implement DB lookup for given job_id.
    """
    raise NotImplementedError("get_job_by_id() must be implemented.")


def list_jobs_for_company(company_id: int, db: Session) -> List[Job]:
    """
    Return job run history for a company.

    TODO:
    - Query Job table where company_id matches, order by started_at desc.
    """
    raise NotImplementedError("list_jobs_for_company() must be implemented.")


def create_job(company_id: int, job_type: str, db: Session) -> Job:
    """
    Create and persist a new job record marked as 'running'.

    TODO:
    - Instantiate and persist new Job object.
    """
    raise NotImplementedError("create_job() must be implemented.")


def complete_job(job: Job, message: str | None, details: dict | None, db: Session) -> None:
    """
    Mark job as completed and commit.

    TODO:
    - Update job record and persist.
    """
    raise NotImplementedError("complete_job() must be implemented.")


def fail_job(job: Job, error_message: str, db: Session) -> None:
    """
    Mark job as failed and commit.

    TODO:
    - Update job record and persist.
    """
    raise NotImplementedError("fail_job() must be implemented.")
