"""
company.py — ORM Model for Company Entities

Purpose:
- Represent a company tracked in the Denari system.
- Provides stable identifiers for linking:
    * Price history (PRICE_EOD)
    * Financial statements & facts (XBRL normalization tables)
    * Valuation model runs / snapshots
    * Job history records

Minimum MVP Fields:
- id: Primary key
- ticker: Public ticker symbol (unique)
- name: Display name
- exchange: Optional (e.g., NASDAQ, NYSE)
- cik: SEC Central Index Key (required for EDGAR lookup)
- sector: high-level classification (e.g., "Technology")
- industry: more granular classification (e.g., "Application Software")

Important Design Rule:
- This table stores *metadata only*, not financial values.
- Financial values live in price_bar / xbrl_fact tables.
"""

from sqlalchemy import Column, Integer, String, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Company(Base):
    __tablename__ = "company"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Identifiers
    ticker = Column(String, unique=True, index=True, nullable=False)
    cik = Column(String, nullable=True)  # SEC CIK for EDGAR filings

    # Display Metadata
    name = Column(String, nullable=False)
    exchange = Column(String, nullable=True)

    # Required for comps
    sector = Column(String, nullable=False)     # e.g., "Technology"
    industry = Column(String, nullable=False)   # e.g., "Application Software"

    # Indexes for faster comps queries
    __table_args__ = (
        Index("idx_company_sector", "sector"),
        Index("idx_company_industry", "industry"),
    )

    def __repr__(self):
        return f"<Company {self.ticker} | {self.sector}/{self.industry}>"
