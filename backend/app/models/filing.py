"""
filing.py — ORM Model for SEC Filings Metadata

Purpose:
- Represent an individual financial filing (10-K, 10-Q, etc.) for a company.
- Used to track:
    * what periods are covered,
    * where the data came from,
    * whether the filing has been normalized into XBRL facts yet.

This table is essential for:
- Determining whether a company has full historical coverage (≥ X years).
- Knowing when to fetch additional or updated filings.
- Linking normalized GAAP facts (xbrl_fact) to source filings.

This table does NOT store:
- The actual financial numbers (those go in xbrl_fact.py).
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Filing(Base):
    __tablename__ = "filing"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key → company.id
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)

    # Filing Attributes
    form_type = Column(String, nullable=False)     # e.g., "10-K", "10-Q"
    filing_date = Column(Date, nullable=False)     # Date filed with SEC
    period_end = Column(Date, nullable=False)      # Financial period being reported
    source_url = Column(String, nullable=True)     # Where raw filing was pulled from

    # Normalization Status
    normalized = Column(Boolean, default=False, nullable=False)

    # Relationship back to Company (optional, but useful in ORM)
    company = relationship("Company", backref="filings")

    # Indexes useful for ingestion lookups
    __table_args__ = (
        Index("idx_filing_company_period", "company_id", "period_end"),
    )

    def __repr__(self):
        return f"<Filing {self.form_type} | {self.period_end} | normalized={self.normalized}>"
