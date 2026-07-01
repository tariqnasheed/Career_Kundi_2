"""
core/security.py
===================
Authentication primitives: password hashing and JWT access/refresh tokens.

Design notes:
- Access tokens are short-lived (default 15 min, see JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
  to limit the blast radius if one is ever leaked.
- Refresh tokens are long-lived (default 7 days) and are the only tokens
  capable of minting a new access token, via POST /api/v1/auth/refresh.
- Passwords are hashed with bcrypt (via the `bcrypt` package directly rather
  than passlib, which has had maintenance issues) using a per-password
  random salt baked into the hash output itself.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt, returning a storable string."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_token(subject: str, expires_delta: timedelta, token_type: Literal["access", "refresh"]) -> str:
    """Internal helper: build + sign a JWT with standard claims."""
    import uuid
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    """Mint a short-lived access token for the given user ID."""
    return _create_token(
        user_id,
        timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "access",
    )


def create_refresh_token(user_id: str) -> str:
    """Mint a long-lived refresh token for the given user ID."""
    return _create_token(
        user_id,
        timedelta(days=settings.jwt_refresh_token_expire_days),
        "refresh",
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode + verify a JWT, returning its payload or None if invalid/expired.

    Callers (see app/api/deps.py) check the `type` claim to ensure an access
    token wasn't swapped in where a refresh token is required, and vice versa.
    """
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
