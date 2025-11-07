"""
user.py — ORM Model for Application Users

Purpose:
- Represent authenticated users of the system.
- Links to Org for multi-user / multi-organization setups (future safe).
- Stores hashed passwords only — never raw.

Used by:
- auth.py (login)
- security.py (password + token validation)
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)

    # Authentication fields
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Display
    full_name = Column(String, nullable=True)

    # Organization linkage (optional, enables multi-tenant model later)
    org_id = Column(Integer, ForeignKey("org.id"), nullable=True)
    org = relationship("Org", backref="users")

    def __repr__(self):
        return f"<User {self.email}>"
