"""
org.py — ORM Model for Organizations / Workspaces

Purpose:
- Represent an organization (e.g., a firm, investment group, fund, or account).
- Allow grouping:
    * Users under the same org
    * Companies tracked by one org vs another (optional)
    * Saved models and snapshots under org scope

This enables:
- Multi-tenant capability (future)
- Logical separation of users
- Permissions / sharing controls later

MVP:
- One org is fine (no authorization logic enforced yet)
- But model exists to avoid redesign when adding multi-user support
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Org(Base):
    __tablename__ = "org"

    id = Column(Integer, primary_key=True, index=True)

    # Human-friendly organization name
    name = Column(String, unique=True, nullable=False)

    # Optional metadata — helpful in enterprise / team usage later
    account_contact_email = Column(String, nullable=True)

    def __repr__(self):
        return f"<Org {self.name} ({self.id})>"
