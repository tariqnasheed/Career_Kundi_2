"""
Canonical entity identifiers for CareerKundi (0050-PF2-S1).

Runtime representation is uuid.UUID. CanonicalEntityId is a NewType for
static distinction from other UUIDs — not a separate wire format.
"""

from __future__ import annotations

import uuid
from typing import NewType
from uuid import UUID

CanonicalEntityId = NewType("CanonicalEntityId", UUID)


class EntityIdError(ValueError):
    """Raised when a value cannot be parsed as a CanonicalEntityId."""


def new_entity_id() -> CanonicalEntityId:
    """Create a new canonical UUID entity id (no DB, no global counter)."""
    return CanonicalEntityId(uuid.uuid4())


def parse_entity_id(value: CanonicalEntityId | UUID | str) -> CanonicalEntityId:
    """
    Parse a canonical entity id.

    Accepts CanonicalEntityId, uuid.UUID, or a UUID string.
    Rejects empty/whitespace strings, malformed UUIDs, ints, None, etc.
    """
    if isinstance(value, UUID):
        return CanonicalEntityId(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise EntityIdError("entity id string must be non-empty")
        try:
            return CanonicalEntityId(UUID(text))
        except (ValueError, AttributeError, TypeError) as exc:
            raise EntityIdError(f"invalid entity id string: {value!r}") from exc
    raise EntityIdError(
        f"entity id must be CanonicalEntityId, UUID, or str; got {type(value).__name__}"
    )


def entity_id_to_str(value: CanonicalEntityId | UUID) -> str:
    """Serialize to the canonical lowercase UUID string form."""
    if not isinstance(value, UUID):
        raise EntityIdError(
            f"entity_id_to_str requires CanonicalEntityId or UUID; got {type(value).__name__}"
        )
    return str(value)
