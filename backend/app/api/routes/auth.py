"""
api/routes/auth.py
======================
Authentication endpoints: register, login, token refresh, logout.

Endpoint summary
----------------
POST /api/v1/auth/register  — Create a new account. Body: UserCreate.
                               Auth: none. Rate limit: unauthenticated tier.
POST /api/v1/auth/login     — Exchange email+password for a token pair.
                               Auth: none. Rate limit: unauthenticated tier.
POST /api/v1/auth/refresh   — Exchange a refresh token for a new access token.
                               Auth: refresh token in body. Rate limit: unauthenticated tier.
POST /api/v1/auth/logout    — Client-side token discard (stateless JWT, so
                               there's nothing to revoke server-side here;
                               a production deployment would additionally
                               blacklist the refresh token in Redis).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import AuthenticationError, ValidationFailedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.profile import Profile
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import RefreshRequest, TokenPair, UserCreate, UserLogin, UserRead
from app.tools.cache import get_cache

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """Create a new user account + an empty Profile row, ready for the Profile page to populate."""
    
    # 1. Check if the email is already in use
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise ValidationFailedError("An account with this email already exists.")

    # 2. Hash the password before saving (NEVER save plain text passwords)
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    
    # 3. Flush sends the INSERT to Postgres to get the new user's ID, 
    # but doesn't commit the transaction yet.
    await db.flush()

    # 4. Create an empty profile linked to the new user. We do this here so 
    # every user is guaranteed to have a profile row from day one.
    db.add(Profile(user_id=user.id))
    
    # 5. Commit saves both the User and Profile to the database permanently.
    await db.commit()
    
    # 6. Refresh fetches the latest data (including generated fields like created_at)
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenPair:
    """Verify credentials and issue a fresh access + refresh token pair."""
    
    # 1. Look up the user by email
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    
    # 2. Check password. We use a generic error message for both "user not found" 
    # and "wrong password" so attackers can't guess valid emails.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise AuthenticationError("Incorrect email or password.")

    # 3. Issue a fresh pair of tokens. 
    # Access token = short lived (15 min) for API calls.
    # Refresh token = long lived (7 days) to get new access tokens without logging in again.
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest) -> TokenPair:
    """Exchange a valid, non-expired refresh token for a brand new token pair (rotation)."""
    claims = decode_token(payload.refresh_token)
    if claims is None or claims.get("type") != "refresh":
        raise AuthenticationError("Invalid or expired refresh token.")

    jti = claims.get("jti")
    if jti:
        cache = await get_cache()
        if await cache.get(f"blacklist:{jti}"):
            raise AuthenticationError("Refresh token has been revoked.")

    user_id = claims["sub"]
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/logout", status_code=204)
async def logout(
    payload: RefreshRequest | None = None,
    authorization: str | None = Header(default=None),
) -> None:
    """
    Logout route. Adds the current access and refresh tokens' JTIs to the
    Redis blacklist until they expire, preventing them from being reused
    if intercepted.
    """
    cache = await get_cache()
    now = datetime.now(timezone.utc).timestamp()

    # Blacklist the access token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        access_claims = decode_token(token)
        if access_claims and "jti" in access_claims:
            ttl = int(access_claims["exp"] - now)
            if ttl > 0:
                await cache.set(f"blacklist:{access_claims['jti']}", "1", ttl_seconds=ttl)

    # Blacklist the refresh token
    if payload and payload.refresh_token:
        refresh_claims = decode_token(payload.refresh_token)
        if refresh_claims and "jti" in refresh_claims:
            ttl = int(refresh_claims["exp"] - now)
            if ttl > 0:
                await cache.set(f"blacklist:{refresh_claims['jti']}", "1", ttl_seconds=ttl)

    return None


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user's public profile."""
    return user
