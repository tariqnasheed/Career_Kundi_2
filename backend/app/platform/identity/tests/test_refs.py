"""ActorRef / SubjectRef / OrganizationRef unit tests."""

from __future__ import annotations

import pytest

from app.platform.identity import (
    ActorRef,
    ActorType,
    IdentityRefError,
    OrganizationRef,
    SubjectRef,
)
from app.platform.kernel import new_entity_id, parse_entity_id


def test_valid_user_actor() -> None:
    aid = new_entity_id()
    ref = ActorRef(actor_type=ActorType.USER, actor_id=aid)
    assert ref.actor_type is ActorType.USER
    assert ref.actor_id == aid


def test_valid_system_actor() -> None:
    ActorRef(actor_type=ActorType.SYSTEM, actor_id=new_entity_id())


def test_valid_service_actor() -> None:
    ActorRef(actor_type=ActorType.SERVICE, actor_id=new_entity_id())


def test_valid_organization_member_actor() -> None:
    ActorRef(actor_type=ActorType.ORGANIZATION_MEMBER, actor_id=new_entity_id())


def test_actor_immutable() -> None:
    ref = ActorRef(actor_type=ActorType.USER, actor_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.actor_type = ActorType.SYSTEM  # type: ignore[misc]


def test_invalid_actor_id_rejected() -> None:
    with pytest.raises(IdentityRefError):
        ActorRef(actor_type=ActorType.USER, actor_id="not-a-uuid")  # type: ignore[arg-type]


def test_invalid_actor_type_rejected() -> None:
    with pytest.raises(IdentityRefError):
        ActorRef(actor_type="user", actor_id=new_entity_id())  # type: ignore[arg-type]


def test_subject_ref_valid() -> None:
    sid = new_entity_id()
    ref = SubjectRef(subject_id=sid)
    assert ref.subject_id == parse_entity_id(sid)


def test_subject_immutable() -> None:
    ref = SubjectRef(subject_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.subject_id = new_entity_id()  # type: ignore[misc]


def test_subject_malformed_rejected() -> None:
    with pytest.raises(IdentityRefError):
        SubjectRef(subject_id="")  # type: ignore[arg-type]


def test_organization_ref_valid() -> None:
    oid = new_entity_id()
    ref = OrganizationRef(organization_id=oid)
    assert ref.organization_id == oid


def test_organization_immutable() -> None:
    ref = OrganizationRef(organization_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.organization_id = new_entity_id()  # type: ignore[misc]


def test_organization_malformed_rejected() -> None:
    with pytest.raises(IdentityRefError):
        OrganizationRef(organization_id="bad")  # type: ignore[arg-type]
