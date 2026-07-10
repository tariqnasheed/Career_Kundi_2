"""
CareerKundi identity domain (0050-PF3-S1).

Public exports are reference value objects only. Persistence/API live elsewhere.
"""

from app.platform.identity.refs import (
    ActorRef,
    ActorType,
    IdentityRefError,
    OrganizationRef,
    SubjectRef,
)

__all__ = [
    "ActorRef",
    "ActorType",
    "IdentityRefError",
    "OrganizationRef",
    "SubjectRef",
]
