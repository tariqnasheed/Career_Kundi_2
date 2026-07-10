"""ClaimRef unit tests."""

from __future__ import annotations

import pytest

from app.platform.claims import ClaimRef, ClaimRefError
from app.platform.kernel import new_entity_id


def test_claim_ref_valid() -> None:
    cid = new_entity_id()
    ref = ClaimRef(claim_id=cid)
    assert ref.claim_id == cid


def test_claim_ref_immutable() -> None:
    ref = ClaimRef(claim_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.claim_id = new_entity_id()  # type: ignore[misc]


def test_claim_ref_malformed_rejected() -> None:
    with pytest.raises(ClaimRefError):
        ClaimRef(claim_id="not-a-uuid")  # type: ignore[arg-type]
