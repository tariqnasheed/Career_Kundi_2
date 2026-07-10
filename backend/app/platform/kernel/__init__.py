"""
Canonical platform kernel public surface (0050-PF2-S1).

Import from here rather than deep module paths.
"""

from app.platform.kernel.external_identifiers import ExternalIdentifier
from app.platform.kernel.ids import (
    CanonicalEntityId,
    EntityIdError,
    entity_id_to_str,
    new_entity_id,
    parse_entity_id,
)

__all__ = [
    "CanonicalEntityId",
    "EntityIdError",
    "ExternalIdentifier",
    "entity_id_to_str",
    "new_entity_id",
    "parse_entity_id",
]
