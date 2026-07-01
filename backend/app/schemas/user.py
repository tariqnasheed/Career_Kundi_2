"""
schemas/user.py
===================
Pydantic schemas for authentication + user account endpoints. Every field
here has a corresponding TypeScript type in frontend/src/types/user.ts so
the API contract is consistent across the stack.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Request body for POST /api/v1/auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)


class UserLogin(BaseModel):
    """Request body for POST /api/v1/auth/login."""

    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Public-safe user representation returned by the API (never includes the password hash)."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    plan: str
    is_email_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenPair(BaseModel):
    """Response body for login/refresh: short-lived access + long-lived refresh token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
