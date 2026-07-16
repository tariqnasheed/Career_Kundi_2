"""Evidence schema guards (0053-F3)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.evidence import EvidenceCreate


def test_evidence_create_forbids_owner_user_id() -> None:
    with pytest.raises(ValidationError):
        EvidenceCreate.model_validate(
            {
                "title": "Doc",
                "evidence_kind": "document",
                "owner_user_id": "00000000-0000-0000-0000-000000000001",
            }
        )


def test_evidence_create_accepts_metadata_only_fields() -> None:
    body = EvidenceCreate.model_validate(
        {
            "title": "Doc",
            "evidence_kind": "document",
            "privacy_class": "private",
            "storage_uri": "s3://meta/only",
            "size_bytes": 10,
        }
    )
    assert body.title == "Doc"
    assert body.storage_uri == "s3://meta/only"
