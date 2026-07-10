"""Privacy ref unit tests."""

from __future__ import annotations

import pytest

from app.platform.kernel import new_entity_id
from app.platform.privacy import (
    ConsentRecordRef,
    PrivacyPolicyRef,
    PrivacyRefError,
    RetentionPolicyRef,
)


@pytest.mark.parametrize(
    ("cls", "field"),
    [
        (PrivacyPolicyRef, "privacy_policy_id"),
        (ConsentRecordRef, "consent_record_id"),
        (RetentionPolicyRef, "retention_policy_id"),
    ],
)
def test_privacy_ref_valid_immutable_malformed(cls, field: str) -> None:
    eid = new_entity_id()
    ref = cls(**{field: eid})
    assert getattr(ref, field) == eid
    with pytest.raises(AttributeError):
        setattr(ref, field, new_entity_id())
    with pytest.raises(PrivacyRefError):
        cls(**{field: "not-a-uuid"})
