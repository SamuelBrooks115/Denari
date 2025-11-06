"""
valuation_model.py — ORM Model for Active Valuation Model Inputs

Purpose:
- Store the *current* editable modeling assumptions for a company.
- These are the values analysts modify before generating projections.
- When a scenario is finalized, these assumptions are copied into ModelSnapshot.

Examples of fields stored here:
- revenue growth assumptions
- margin / cost structure assumptions
- working capital / capex ratios
- discount rate (WACC)
- terminal value assumption (growth or exit multiple)

This allows:
- Persistent editable state between UI sessions
- One “working model” per company
"""

from sqlalchemy import Column, Integer, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ValuationModel(Base):
    __tablename__ = "valuation_model"

    id = Column(Integer, primary_key=True, index=True)

    # Company this working model belongs to
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    company = relationship("Company", backref="valuation_model", uselist=False)

    # The *editable assumptions* currently in use.
    # Expected format:
    # {
    #   "revenue_growth": 0.07,
    #   "operating_margin": 0.18,
    #   "capex_pct_revenue": 0.05,
    #   "discount_rate": 0.09,
    #   "terminal_growth_rate": 0.025
    # }
    assumptions = Column(JSON, nullable=False)

    def __repr__(self):
        return f"<ValuationModel {self.company_id}>"
