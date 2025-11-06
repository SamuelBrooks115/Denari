"""
price_bar.py — ORM Model for Daily Price History (EOD Market Data)

Purpose:
- Store daily price data for each company from market data sources (WHERE EVER THE FUCK WE GET IT FROM).
- Supports valuation analysis, performance visualization, and pricing normalization.

Minimum Required Fields:
- company_id (link to Company)
- date (the trading day)
- close_price (EOD closing price)

Optional OHLC fields included now so we can expand easily.

**Important Constraint:**
- (company_id, date) must be UNIQUE — only one price per day per company.

This table is large, so indexing matters.
"""

from sqlalchemy import Column, Integer, Date, Float, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class PriceBar(Base):
    __tablename__ = "price_bar"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    date = Column(Date, nullable=False)

    # Price fields (store raw actuals — no unit scaling, no adjustments)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=False)  # required EOD close price
    volume = Column(Float, nullable=True)

    company = relationship("Company", backref="price_bars")

    # Ensure fast lookup and uniqueness of entries
    __table_args__ = (
        Index("idx_price_company_date", "company_id", "date", unique=True),
        Index("idx_price_date", "date"),  # useful for market-wide queries
    )

    def __repr__(self):
        return f"<PriceBar {self.company_id} @ {self.date} close={self.close}>"
