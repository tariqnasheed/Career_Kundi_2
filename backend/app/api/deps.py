"""
api/deps.py
===============
Shared FastAPI dependencies: extracting + validating the current user from
a JWT bearer token, and a convenience dependency for routes that require an
admin role.
"""

import uuid

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthenticationError, AuthorizationError
from app.core.security import decode_token
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.tools.cache import get_cache


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve the authenticated `User` from the `Authorization: Bearer <token>`
    header. Raises `AuthenticationError` (-> HTTP 401) for any failure mode:
    missing header, malformed token, expired token, wrong token type
    (refresh token used where an access token is required), or unknown user.
    """
    # 1. Check if the frontend sent the Authorization header at all
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationError("Missing or malformed Authorization header.")

    # 2. Extract the token string (remove the "Bearer " prefix)
    token = authorization.split(" ", 1)[1]
    
    # 3. Decode the token to see who it belongs to (throws error if fake or expired)
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise AuthenticationError("Invalid or expired access token.")

    # 4. Check if this specific token was revoked (logged out)
    jti = payload.get("jti")
    if jti:
        cache = get_cache()
        if await cache.get(f"blacklist:{jti}"):
            raise AuthenticationError("Token has been revoked.")

    # 5. Get the user ID from the token's "sub" (subject) field
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise AuthenticationError("Malformed token subject.") from exc

    # 6. Look up the user in the database to ensure their account still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive.")
        
    # 7. Return the full user object. Any route that depends on this function 
    # will now have access to the user's data (email, role, etc).
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency for admin-only routes — raises 403 for non-admin users."""
    # Depends(get_current_user) runs first. If the user is valid, we then check their role.
    if user.role != UserRole.ADMIN:
        raise AuthorizationError("Admin privileges required.")
    return user
