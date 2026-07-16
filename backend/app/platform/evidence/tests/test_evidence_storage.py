"""Local evidence storage guards (0053-F5)."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest

from app.platform.evidence.storage import (
    DEFAULT_MAX_UPLOAD_BYTES,
    EvidenceStorageError,
    LocalEvidenceStorage,
    parse_local_evidence_uri,
)


def test_store_accepts_allowed_mime_and_computes_sha256(tmp_path: Path) -> None:
    storage = LocalEvidenceStorage(tmp_path, max_upload_bytes=1024)
    owner = uuid.uuid4()
    evidence_id = uuid.uuid4()
    payload = b"hello evidence"
    stored = storage.store_evidence_file(
        owner_user_id=owner,
        evidence_id=evidence_id,
        data=payload,
        mime_type="text/plain",
        original_filename="../../evil.txt",
    )
    assert stored.size_bytes == len(payload)
    assert stored.content_hash == hashlib.sha256(payload).hexdigest()
    assert stored.mime_type == "text/plain"
    assert stored.storage_uri.startswith("local-evidence://")
    assert stored.absolute_path.is_file()
    assert stored.absolute_path.resolve().is_relative_to(tmp_path.resolve())
    # Client filename must not appear in the storage path.
    assert "evil" not in stored.absolute_path.as_posix()
    assert ".." not in stored.absolute_path.as_posix()
    uri_owner, uri_evidence, filename = parse_local_evidence_uri(stored.storage_uri)
    assert uri_owner == owner
    assert uri_evidence == evidence_id
    assert filename == stored.absolute_path.name


def test_store_rejects_empty_too_large_and_disallowed_mime(tmp_path: Path) -> None:
    storage = LocalEvidenceStorage(tmp_path, max_upload_bytes=16)
    owner = uuid.uuid4()
    evidence_id = uuid.uuid4()
    with pytest.raises(EvidenceStorageError, match="Empty"):
        storage.store_evidence_file(
            owner_user_id=owner,
            evidence_id=evidence_id,
            data=b"",
            mime_type="text/plain",
        )
    with pytest.raises(EvidenceStorageError, match="maximum size"):
        storage.store_evidence_file(
            owner_user_id=owner,
            evidence_id=evidence_id,
            data=b"x" * 17,
            mime_type="text/plain",
        )
    with pytest.raises(EvidenceStorageError, match="MIME"):
        storage.store_evidence_file(
            owner_user_id=owner,
            evidence_id=evidence_id,
            data=b"x",
            mime_type="application/x-msdownload",
        )


def test_path_traversal_rejected_in_uri_and_open(tmp_path: Path) -> None:
    storage = LocalEvidenceStorage(tmp_path)
    owner = uuid.uuid4()
    evidence_id = uuid.uuid4()
    with pytest.raises(EvidenceStorageError):
        parse_local_evidence_uri(
            f"local-evidence://{owner}/{evidence_id}/../escape.txt"
        )
    with pytest.raises(EvidenceStorageError):
        parse_local_evidence_uri("https://example.com/public/file.pdf")
    with pytest.raises(EvidenceStorageError):
        storage.open_evidence_file(
            f"local-evidence://{owner}/{evidence_id}/../../etc/passwd",
            owner_user_id=owner,
            evidence_id=evidence_id,
        )


def test_open_requires_matching_owner_and_existing_file(tmp_path: Path) -> None:
    storage = LocalEvidenceStorage(tmp_path)
    owner = uuid.uuid4()
    other = uuid.uuid4()
    evidence_id = uuid.uuid4()
    stored = storage.store_evidence_file(
        owner_user_id=owner,
        evidence_id=evidence_id,
        data=b"payload",
        mime_type="text/plain",
    )
    path = storage.open_evidence_file(
        stored.storage_uri,
        owner_user_id=owner,
        evidence_id=evidence_id,
    )
    assert path.read_bytes() == b"payload"
    with pytest.raises(EvidenceStorageError, match="ownership"):
        storage.open_evidence_file(
            stored.storage_uri,
            owner_user_id=other,
            evidence_id=evidence_id,
        )
    # Missing file after delete → not found.
    path.unlink()
    with pytest.raises(EvidenceStorageError, match="not found"):
        storage.open_evidence_file(
            stored.storage_uri,
            owner_user_id=owner,
            evidence_id=evidence_id,
        )


def test_default_max_bytes_is_five_mib() -> None:
    assert DEFAULT_MAX_UPLOAD_BYTES == 5 * 1024 * 1024
