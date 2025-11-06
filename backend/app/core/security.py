"""
security.py — Authentication Utilities (Password Hashing & JWT Encoding)

Purpose:
- Provide reusable security helpers across the backend.
- Hash & verify passwords (never store raw passwords).
- Issue and validate JWT access tokens for authentication.
- Extract the current user from a request (once the user repo is implemented).

Key Constraints (MVP):
- We only need access tokens (no refresh tokens yet).
- Authentication is stateless — logout just means deleting the token client-side.
- User lookup is deferred to models/user.py or a user service wrapper.

This module does NOT:
- Define API routes → that lives in app/api/v1/auth.py
- Query the database directly (except via injected deps)
"""

import datetime
from typing import Optional, Dict, Any

from jose import jwt, JWTError  # `python-jose` library recommended for JWT
from passlib.context import CryptContext  # password hashing
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User  # ORM model


# -----------------------------------------------------------------------------
# Password Hashing
# -----------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(raw_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """
    return pwd_context.hash(raw_password)

def verify_password(raw_password: str, hashed_password: str) -> bool:
    """
    Verify that a raw password matches its hashed stored version.
    """
    return pwd_context.verify(raw_password, hashed_password)


# -----------------------------------------------------------------------------
# JWT Token Handling
# -----------------------------------------------------------------------------

def create_access_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT access token with expiration.

    Expected payload format:
        data = {"sub": user_id}

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire_at})

    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )
    return token


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.
    Returns the payload dict if valid, None if invalid.
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None


# -----------------------------------------------------------------------------
# Current User Dependency (used across authenticated endpoints later)
# -----------------------------------------------------------------------------

def get_current_user(db: Session = Depends(get_db), token: str = None) -> User:
    """
    Extract and return the authenticated user from a JWT token.

    Flow:
    - Decode token.
    - Validate 'sub' (user_id).
    - Lookup user in DB.
    - Return user object.
    
    TODO (MVP later):
    - Hook into FastAPI's OAuth2PasswordBearer dependency to extract token
      from Authorization: Bearer <token> header.
    - Implement DB lookup: db.query(User).filter(User.id == user_id).first()

    For now → placeholder until the login route + user creation are implemented.
    """
    # TODO: extract token from Authorization header via OAuth2PasswordBearer
    # TODO: decode token → payload = decode_token(token)
    # TODO: lookup user by payload["sub"]
    raise NotImplementedError("get_current_user will be implemented after auth login is finalized.")
