"""
job.py — ORM Model for Workflow / Ingestion / Modeling Run Records

Purpose:
- Record the status of *long-running or multi-step operations* such as:
    * /companies/{id}/prepare (data ingestion pipeline)
    * model computation runs (three-statement, DCF, comps)
- Provide auditability and internal debugging visibility.
- Eventually drive a UI “Job History” or “Pipeline Logs” page.

This is **not** a background queue worker job (because MVP has no Celery).
It is simply a log of pipeline executions.

Key Points:
- Tracks start/end timestamps, status, type, and a short human-readable message.
- Stores structured details in JSON (ex: counts of facts ingested, updated, skipped).
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()


class Job(Base):
    __tablename__ = "job"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key → company processed (jobs are always tied to a company)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)

    # Classification of job
    # Examples: "prepare", "ingestion", "three-statement", "dcf", "comps"
    job_type = Column(String, nullable=False)

    # Status lifecycle: "running" → "completed" | "failed"
    status = Column(String, nullable=False, default="running")

    # Timestamps
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    # Short officer-readable message (ex: "Fetched 3 new filings, updated prices")
    message = Column(String, nullable=True)

    # Structured run details (ex: {"filings_added": 3, "price_rows_ingested": 5182})
    details = Column(JSON, nullable=True)

    # ORM Relationship
    company = relationship("Company", backref="jobs")

    def mark_completed(self, message: str = None, details: dict = None):
        """
        Helper to finalize a successful job.
        """
        self.status = "completed"
        self.finished_at = datetime.datetime.utcnow()
        if message:
            self.message = message
        if details:
            self.details = details

    def mark_failed(self, message: str):
        """
        Helper to finalize a failed job.
        """
        self.status = "failed"
        self.finished_at = datetime.datetime.utcnow()
        self.message = message

    def __repr__(self):
        return f"<Job {self.job_type} | {self.status} | {self.company_id}>"
