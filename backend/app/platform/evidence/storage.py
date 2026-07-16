"""
Private local evidence attachment storage (0053-F5).

Stores file bytes under a private backend root. Not verification.
No public URLs, OCR, parsing, or LLM inspection of file contents.
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

LOCAL_EVIDENCE_SCHEME = "local-evidence"

DEFAULT_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MiB

DEFAULT_ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)

_MIME_TO_EXT: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "text/plain": ".txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


class EvidenceStorageError(Exception):
    """Raised for storage validation / containment failures (not trust claims)."""


@dataclass(frozen=True)
class EvidenceStoredObject:
    storage_uri: str
    content_hash: str
    mime_type: str
    size_bytes: int
    absolute_path: Path
    download_filename: str


def _normalize_mime(mime_type: str | None) -> str:
    if mime_type is None:
        raise EvidenceStorageError("MIME type is required.")
    cleaned = mime_type.split(";", 1)[0].strip().lower()
    if not cleaned:
        raise EvidenceStorageError("MIME type is required.")
    return cleaned


def sanitize_download_filename(
    *,
    evidence_id: uuid.UUID,
    mime_type: str,
    original_filename: str | None = None,
) -> str:
    """Build a download filename that never influences storage paths."""
    ext = _MIME_TO_EXT.get(mime_type, "")
    if original_filename:
        stem = Path(original_filename).name
        stem = _SAFE_NAME_RE.sub("_", stem).strip("._")
        if stem:
            # Drop client extension; use allowlisted extension only.
            stem = Path(stem).stem[:64] or "evidence"
            return f"{stem}{ext}" if ext else stem
    return f"evidence-{str(evidence_id)[:8]}{ext}"


def parse_local_evidence_uri(storage_uri: str) -> tuple[uuid.UUID, uuid.UUID, str]:
    """
    Parse ``local-evidence://<owner>/<evidence>/<safe_filename>``.

    Raises EvidenceStorageError on invalid / traversal-prone values.
    """
    if not isinstance(storage_uri, str) or not storage_uri.strip():
        raise EvidenceStorageError("storage_uri is required.")
    uri = storage_uri.strip()
    prefix = f"{LOCAL_EVIDENCE_SCHEME}://"
    if not uri.startswith(prefix):
        raise EvidenceStorageError("Unsupported storage_uri scheme.")
    remainder = uri[len(prefix) :]
    parts = remainder.split("/")
    if len(parts) != 3:
        raise EvidenceStorageError("Malformed local evidence storage_uri.")
    owner_s, evidence_s, filename = parts
    if not owner_s or not evidence_s or not filename:
        raise EvidenceStorageError("Malformed local evidence storage_uri.")
    if any(p in ("", ".", "..") for p in parts):
        raise EvidenceStorageError("Invalid path segment in storage_uri.")
    if "/" in filename or "\\" in filename or filename.startswith("."):
        raise EvidenceStorageError("Invalid filename in storage_uri.")
    try:
        owner_id = uuid.UUID(owner_s)
        evidence_id = uuid.UUID(evidence_s)
    except ValueError as exc:
        raise EvidenceStorageError("Invalid UUID in storage_uri.") from exc
    if _SAFE_NAME_RE.search(filename):
        raise EvidenceStorageError("Unsafe filename in storage_uri.")
    return owner_id, evidence_id, filename


class LocalEvidenceStorage:
    """Filesystem-backed private evidence blob store for local development."""

    def __init__(
        self,
        root: Path | str,
        *,
        max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
        allowed_mime_types: frozenset[str] | set[str] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.max_upload_bytes = int(max_upload_bytes)
        self.allowed_mime_types = frozenset(
            allowed_mime_types
            if allowed_mime_types is not None
            else DEFAULT_ALLOWED_MIME_TYPES
        )
        if self.max_upload_bytes <= 0:
            raise EvidenceStorageError("max_upload_bytes must be positive.")

    def ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def _contained(self, path: Path) -> Path:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise EvidenceStorageError(
                "Resolved path escapes evidence storage root."
            ) from exc
        return resolved

    def _object_path(
        self,
        *,
        owner_user_id: uuid.UUID,
        evidence_id: uuid.UUID,
        filename: str,
    ) -> Path:
        if ".." in filename or "/" in filename or "\\" in filename:
            raise EvidenceStorageError("Invalid storage filename.")
        candidate = self.root / str(owner_user_id) / str(evidence_id) / filename
        return self._contained(candidate)

    def store_evidence_file(
        self,
        *,
        owner_user_id: uuid.UUID,
        evidence_id: uuid.UUID,
        data: bytes,
        mime_type: str | None,
        original_filename: str | None = None,
    ) -> EvidenceStoredObject:
        """
        Write bytes under the private root. Never logs raw file content.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise EvidenceStorageError("File payload must be bytes.")
        payload = bytes(data)
        size = len(payload)
        if size == 0:
            raise EvidenceStorageError("Empty file rejected.")
        if size > self.max_upload_bytes:
            raise EvidenceStorageError(
                f"File exceeds maximum size of {self.max_upload_bytes} bytes."
            )

        mime = _normalize_mime(mime_type)
        if mime not in self.allowed_mime_types:
            raise EvidenceStorageError(f"MIME type not allowed: {mime}")

        digest = hashlib.sha256(payload).hexdigest()
        ext = _MIME_TO_EXT.get(mime, "")
        # Storage name is hash-based — never the client filename.
        stored_name = f"{digest}{ext}"
        self.ensure_root()
        target = self._object_path(
            owner_user_id=owner_user_id,
            evidence_id=evidence_id,
            filename=stored_name,
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            # Same content for same evidence is fine; overwrite identical bytes only.
            existing = target.read_bytes()
            if existing != payload:
                raise EvidenceStorageError(
                    "Storage object name collision with different content."
                )
        else:
            target.write_bytes(payload)

        # Containment re-check after write.
        self._contained(target)

        uri = (
            f"{LOCAL_EVIDENCE_SCHEME}://"
            f"{owner_user_id}/{evidence_id}/{stored_name}"
        )
        download_name = sanitize_download_filename(
            evidence_id=evidence_id,
            mime_type=mime,
            original_filename=original_filename,
        )
        logger.info(
            "evidence_file_stored owner=%s evidence=%s size=%s mime=%s hash=%s",
            owner_user_id,
            evidence_id,
            size,
            mime,
            digest,
        )
        return EvidenceStoredObject(
            storage_uri=uri,
            content_hash=digest,
            mime_type=mime,
            size_bytes=size,
            absolute_path=target,
            download_filename=download_name,
        )

    def open_evidence_file(
        self,
        storage_uri: str,
        *,
        owner_user_id: uuid.UUID,
        evidence_id: uuid.UUID,
    ) -> Path:
        """Resolve a private local URI to a contained path after ownership match."""
        uri_owner, uri_evidence, filename = parse_local_evidence_uri(storage_uri)
        if uri_owner != owner_user_id or uri_evidence != evidence_id:
            raise EvidenceStorageError("storage_uri ownership mismatch.")
        path = self._object_path(
            owner_user_id=owner_user_id,
            evidence_id=evidence_id,
            filename=filename,
        )
        if not path.is_file():
            raise EvidenceStorageError("Stored evidence file not found.")
        return path

    def delete_evidence_file(
        self,
        storage_uri: str,
        *,
        owner_user_id: uuid.UUID,
        evidence_id: uuid.UUID,
    ) -> bool:
        """
        Delete a stored object if present (0053-F14).

        Returns True when a file was removed, False when already missing.
        Does not delete directories. Never logs raw file bytes.
        """
        uri_owner, uri_evidence, filename = parse_local_evidence_uri(storage_uri)
        if uri_owner != owner_user_id or uri_evidence != evidence_id:
            raise EvidenceStorageError("storage_uri ownership mismatch.")
        path = self._object_path(
            owner_user_id=owner_user_id,
            evidence_id=evidence_id,
            filename=filename,
        )
        if not path.is_file():
            logger.info(
                "evidence_file_delete_missing owner=%s evidence=%s",
                owner_user_id,
                evidence_id,
            )
            return False
        path.unlink()
        logger.info(
            "evidence_file_deleted owner=%s evidence=%s",
            owner_user_id,
            evidence_id,
        )
        return True


def get_default_storage() -> LocalEvidenceStorage:
    """Build storage from application settings (lazy import avoids cycles)."""
    from app.core.config import settings

    return LocalEvidenceStorage(
        settings.resolved_evidence_storage_root,
        max_upload_bytes=settings.evidence_max_upload_bytes,
        allowed_mime_types=settings.evidence_allowed_mime_types_set,
    )


# Module-level helpers matching the F5 contract names.
def store_evidence_file(
    *,
    owner_user_id: uuid.UUID,
    evidence_id: uuid.UUID,
    data: bytes,
    mime_type: str | None,
    original_filename: str | None = None,
    storage: LocalEvidenceStorage | None = None,
) -> EvidenceStoredObject:
    backend = storage or get_default_storage()
    return backend.store_evidence_file(
        owner_user_id=owner_user_id,
        evidence_id=evidence_id,
        data=data,
        mime_type=mime_type,
        original_filename=original_filename,
    )


def open_evidence_file(
    storage_uri: str,
    *,
    owner_user_id: uuid.UUID,
    evidence_id: uuid.UUID,
    storage: LocalEvidenceStorage | None = None,
) -> Path:
    backend = storage or get_default_storage()
    return backend.open_evidence_file(
        storage_uri,
        owner_user_id=owner_user_id,
        evidence_id=evidence_id,
    )


def delete_evidence_file(
    storage_uri: str,
    *,
    owner_user_id: uuid.UUID,
    evidence_id: uuid.UUID,
    storage: LocalEvidenceStorage | None = None,
) -> bool:
    backend = storage or get_default_storage()
    return backend.delete_evidence_file(
        storage_uri,
        owner_user_id=owner_user_id,
        evidence_id=evidence_id,
    )
