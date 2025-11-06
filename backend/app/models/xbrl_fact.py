"""
xbrl_fact.py — ORM Model for Normalized GAAP Financial Facts

Purpose:
- Store standardized financial statement line items extracted from XBRL filings.
- Every row represents ONE GAAP tag value for ONE period for ONE company.
- This is what the DCF, three-statement model, and comps all operate on.

Key Columns:
- company_id: which company the fact belongs to
- filing_id: traceability to the specific 10-K / 10-Q
- period_end: financial period the value applies to
- statement_type: 'IS' (Income Statement), 'BS' (Balance Sheet), 'CF' (Cash Flow)
- tag: GAAP concept name (e.g., Revenues, NetIncomeLoss, Assets)
- value: the reported numeric value

This table is **queried constantly** — indexing and cleanliness matter.
"""

from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class XbrlFact(Base):
    __tablename__ = "xbrl_fact"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    filing_id = Column(Integer, ForeignKey("filing.id"), nullable=False)

    # Reporting period this fact applies to (e.g., 2023-12-31)
    period_end = Column(Date, nullable=False)

    # IS, BS, or CF — allows grouping facts by statement type efficiently
    statement_type = Column(String, nullable=False)

    # GAAP/XBRL tag name — standardized across all filings
    tag = Column(String, nullable=False)

    # The numeric value reported
    value = Column(Float, nullable=False)

    # Optional: unit (e.g., USD, shares)
    unit = Column(String, nullable=True)

    # Links back
    company = relationship("Company", backref="xbrl_facts")
    filing = relationship("Filing", backref="facts")

    __table_args__ = (
        # Fast lookup for modeling queries (company + statement + period)
        Index("idx_xbrl_company_type_period", "company_id", "statement_type", "period_end"),
        # Speed up tag searches (used heavily in normalization QA & debugging)
        Index("idx_xbrl_tag", "tag"),
    )

    def __repr__(self):
        return f"<XbrlFact {self.company_id} {self.statement_type} {self.tag} {self.period_end} = {self.value}>"
