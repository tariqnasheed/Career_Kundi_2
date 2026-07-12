"""
db/models/user.py
=====================
The `User` model — authentication identity + subscription/plan state.

Deliberately kept separate from `Profile` (db/models/profile.py): `User` is
about *who can log in and what they're allowed to do* (credentials, plan,
RBAC role), while `Profile` is about *the CV/career data they've entered*.
This separation means we can support multiple profiles per user in the
future (e.g. "Profile for tech roles" vs "Profile for consulting roles")
without touching auth at all.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SubscriptionPlan(str, PyEnum):
    """Subscription tiers gating feature access and rate limits (see core/config.py rate limits)."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserRole(str, PyEnum):
    """RBAC roles. `admin` unlocks the (future) internal ops dashboard."""

    USER = "user"
    ADMIN = "admin"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A registered Careerkundi account."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan), default=SubscriptionPlan.FREE, nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # API key for power users (encrypted at rest by the application layer
    # before being stored — see app/services/api_keys.py).
    personal_api_key_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # --- Relationships ---------------------------------------------------------
    profile: Mapped["Profile"] = relationship(  # noqa: F821
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    saved_jobs: Mapped[list["SavedJob"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    cvs: Mapped[list["GeneratedCV"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    roadmaps: Mapped[list["Roadmap"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    generation_jobs: Mapped[list["GenerationJob"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    generated_assets: Mapped[list["GeneratedAsset"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    user_badges: Mapped[list["UserBadge"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    job_applications: Mapped[list["JobApplication"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    passport: Mapped["CareerPassport | None"] = relationship(  # noqa: F821
        back_populates="owner",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User id={self.id} email={self.email!r} plan={self.plan}>"
