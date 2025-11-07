"""
model_snapshot.py — ORM Model for Saved Valuation Model States

Purpose:
- Store the *state* of a valuation model (inputs + outputs) at a specific point in time.
- Allows analysts to:
    * Save a scenario ("Base Case", "Bull", "Bear")
    * Return to it later
    * Compare model results over time

This table stores:
- Company association
- Human-friendly version label
- The input assumptions used
- The computed model outputs
- Timestamp of when the snapshot was recorded

This is *not* the live / current model evaluation.
It is a historical / referential artifact.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()


class ModelSnapshot(Base):
    __tablename__ = "model_snapshot"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key → which company this model refers to
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)

    # Human-readable version label (e.g., "Base Case Q4-2024")
    version_name = Column(String, nullable=False)

    # Timestamp model was generated
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # The assumptions that drove the model:
    # Example structure:
    # {
    #   "revenue_growth": 0.08,
    #   "operating_margin_target": 0.22,
    #   "capex_as_pct_revenue": 0.05,
    #   "wacc": 0.10,
    #   "terminal_growth": 0.025
    # }
    assumptions = Column(JSON, nullable=False)

    # The computed results of the model:
    # Example:
    # {
    #   "projected_free_cash_flows": [...],
    #   "dcf_valuation": 123456789,
    #   "comps_valuation_range": [110e6, 150e6],
    #   "ev_to_revenue_multiple": 7.3
    # }
    outputs = Column(JSON, nullable=False)

    # Relationship back to company
    company = relationship("Company", backref="model_snapshots")

    # Optional / useful index for fast lookup
    __table_args__ = (
        Index("idx_snapshot_company_version", "company_id", "version_name"),
    )

    def __repr__(self):
        return f"<ModelSnapshot {self.company_id} | {self.version_name}>"
