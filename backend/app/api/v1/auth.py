"""
auth.py — Authentication and Session Handling Endpoints (API Layer)

Purpose:
- Defines HTTP endpoints for user authentication and session management.
- Handles login, logout, and (later) optional signup/invite flows.
- Issues and validates JWT (JSON Web Token) access tokens for session security.
- Delegates password hashing and token encoding to core/security.py.
- Delegates DB access (fetching/verifying users) to models/user.py via core/database.py.

This file should be thin — minimal logic. Do NOT implement hashing or DB lookups here.
Those belong in core/security and the model/service layers respectively.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
# from app.core.security import verify_password, create_access_token  # Token + password utilities
# from app.core.database import get_db  # DB session dependency
# from app.models.user import User  # ORM model representing system users

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# -----------------------------------------------------------------------------
# Request / Response Schemas
# -----------------------------------------------------------------------------

class LoginRequest(BaseModel):
    """
    Schema for login POST.
    - `email`: User's login email.
    - `password`: Raw password supplied by the user.
    """
    email: str
    password: str


class TokenResponse(BaseModel):
    """
    Response schema when issuing JWT access tokens.
    - `access_token`: Encoded JWT string.
    - `token_type`: Typically 'bearer' for Authorization headers.
    """
    access_token: str
    token_type: str = "bearer"


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db=Depends(get_db)):
    """
    POST /auth/login

    High-Level Flow:
    1. Look up user by email.
    2. Verify provided password matches stored hash.
    3. If valid → issue JWT access token using create_access_token().
    4. If invalid → return 401 Unauthorized.

    Notes:
    - Do not directly handle hashing here (use verify_password).
    - Do not manually construct JWT (use create_access_token).
    - Token TTL should be configured in core/config.py.

    TODO:
    - Implement database lookup for user (User.by_email helper or db query).
    - Implement actual password and token checks.
    - Consider rate-limiting or lockouts (not required for MVP).
    """

    # TODO: replace with real DB lookup (User.by_email or equivalent)
    user = None  # placeholder

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # TODO: verify password using verify_password()
    # TODO: create token with create_access_token({"sub": user.id})

    access_token = "placeholder-token"  # TODO replace

    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout():
    """
    POST /auth/logout

    MVP Behavior:
    - Stateless JWT means logout is client-side only (delete token in UI).
    - No action needed server-side unless implementing blacklist/refresh.

    TODO: If refresh tokens are added later, invalidate them here.
    """
    return {"message": "Logout successful (client should delete stored token)"}
