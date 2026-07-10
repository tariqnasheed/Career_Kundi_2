"""
Geo / jurisdiction / locale / work-authorization area service (0050-PF6-S1).

Create/get only. No cross-domain linking. No visa/status logic.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.geo import (
    GeoArea,
    JurisdictionArea,
    LocaleProfile,
    WorkAuthorizationArea,
)
from app.platform.geo.kinds import (
    parse_geo_area_kind,
    parse_jurisdiction_kind,
    parse_locale_kind,
    parse_work_authorization_area_kind,
)
from app.platform.geo.refs import GeoRefError


def _trim_required(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise GeoRefError(f"{label} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise GeoRefError(f"{label} must not be empty")
    return cleaned


def _trim_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


async def create_geo_area(
    db: AsyncSession,
    *,
    geo_kind: object,
    name: str,
    code: str | None = None,
    parent_geo_id: uuid.UUID | None = None,
) -> GeoArea:
    kind = parse_geo_area_kind(geo_kind)
    if parent_geo_id is not None:
        parent = await get_geo_area(db, parent_geo_id)
        if parent is None:
            raise GeoRefError(f"parent geo does not exist: {parent_geo_id}")
    row = GeoArea(
        geo_kind=kind.value,
        name=_trim_required(name, "name"),
        code=_trim_optional(code),
        parent_geo_id=parent_geo_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_geo_area(db: AsyncSession, geo_id: uuid.UUID) -> GeoArea | None:
    result = await db.execute(select(GeoArea).where(GeoArea.id == geo_id))
    return result.scalar_one_or_none()


async def create_jurisdiction_area(
    db: AsyncSession,
    *,
    jurisdiction_kind: object,
    name: str,
    code: str | None = None,
    parent_jurisdiction_id: uuid.UUID | None = None,
) -> JurisdictionArea:
    kind = parse_jurisdiction_kind(jurisdiction_kind)
    if parent_jurisdiction_id is not None:
        parent = await get_jurisdiction_area(db, parent_jurisdiction_id)
        if parent is None:
            raise GeoRefError(
                f"parent jurisdiction does not exist: {parent_jurisdiction_id}"
            )
    row = JurisdictionArea(
        jurisdiction_kind=kind.value,
        name=_trim_required(name, "name"),
        code=_trim_optional(code),
        parent_jurisdiction_id=parent_jurisdiction_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_jurisdiction_area(
    db: AsyncSession, jurisdiction_id: uuid.UUID
) -> JurisdictionArea | None:
    result = await db.execute(
        select(JurisdictionArea).where(JurisdictionArea.id == jurisdiction_id)
    )
    return result.scalar_one_or_none()


async def create_locale_profile(
    db: AsyncSession,
    *,
    locale_kind: object,
    locale_code: str,
    display_name: str | None = None,
) -> LocaleProfile:
    kind = parse_locale_kind(locale_kind)
    row = LocaleProfile(
        locale_kind=kind.value,
        locale_code=_trim_required(locale_code, "locale_code"),
        display_name=_trim_optional(display_name),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_locale_profile(
    db: AsyncSession, locale_id: uuid.UUID
) -> LocaleProfile | None:
    result = await db.execute(
        select(LocaleProfile).where(LocaleProfile.id == locale_id)
    )
    return result.scalar_one_or_none()


async def create_work_authorization_area(
    db: AsyncSession,
    *,
    authorization_kind: object,
    name: str,
    code: str | None = None,
) -> WorkAuthorizationArea:
    kind = parse_work_authorization_area_kind(authorization_kind)
    row = WorkAuthorizationArea(
        authorization_kind=kind.value,
        name=_trim_required(name, "name"),
        code=_trim_optional(code),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_work_authorization_area(
    db: AsyncSession, authorization_area_id: uuid.UUID
) -> WorkAuthorizationArea | None:
    result = await db.execute(
        select(WorkAuthorizationArea).where(
            WorkAuthorizationArea.id == authorization_area_id
        )
    )
    return result.scalar_one_or_none()
