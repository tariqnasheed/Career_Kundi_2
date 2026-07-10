"""
Provenance source/snapshot service helpers (0050-PF4-S1).

Create/read only. No update_snapshot. No external fetch or file I/O.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.provenance import SourceRecord, SourceSnapshot
from app.platform.provenance.refs import ProvenanceRefError, parse_source_kind


def sha256_text(value: str) -> str:
    """Pure SHA-256 hex digest of a string (no file/network I/O)."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _trim_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _validate_hash_pair(
    content_hash: str | None, hash_algorithm: str | None
) -> tuple[str | None, str | None]:
    ch = _trim_optional(content_hash)
    ha = _trim_optional(hash_algorithm)
    if (ch is None) ^ (ha is None):
        raise ProvenanceRefError(
            "content_hash and hash_algorithm must both be supplied or both omitted"
        )
    return ch, ha


async def create_source(
    db: AsyncSession,
    *,
    source_kind: object,
    label: str | None = None,
    uri: str | None = None,
) -> SourceRecord:
    kind = parse_source_kind(source_kind)
    row = SourceRecord(
        source_kind=kind.value,
        label=_trim_optional(label),
        uri=_trim_optional(uri),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_source(
    db: AsyncSession, source_id: uuid.UUID
) -> SourceRecord | None:
    result = await db.execute(
        select(SourceRecord).where(SourceRecord.id == source_id)
    )
    return result.scalar_one_or_none()


async def create_snapshot(
    db: AsyncSession,
    *,
    source_id: uuid.UUID,
    captured_at: datetime | None = None,
    content_hash: str | None = None,
    hash_algorithm: str | None = None,
    storage_uri: str | None = None,
) -> SourceSnapshot:
    source = await get_source(db, source_id)
    if source is None:
        raise ProvenanceRefError(f"source does not exist: {source_id}")

    ch, ha = _validate_hash_pair(content_hash, hash_algorithm)
    when = captured_at if captured_at is not None else datetime.now(UTC)
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)

    row = SourceSnapshot(
        source_id=source_id,
        captured_at=when,
        content_hash=ch,
        hash_algorithm=ha,
        storage_uri=_trim_optional(storage_uri),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_snapshot(
    db: AsyncSession, snapshot_id: uuid.UUID
) -> SourceSnapshot | None:
    result = await db.execute(
        select(SourceSnapshot).where(SourceSnapshot.id == snapshot_id)
    )
    return result.scalar_one_or_none()
