# 0053-F4 — Attachment Storage Decision

**Status:** Decided for F4 / deferred implementation to F5  
**Date:** 2026-07-16  
**Depends on:** 0053-F3 private evidence metadata API

---

## F4 decision

**No file upload or attachment storage in F4.**

The Evidence Library UI creates and lists **private metadata only** via existing F3 APIs. `storage_uri` remains an optional metadata/reference string, not an upload or download action.

---

## F5 must decide before uploads

F5 (Attachment Storage Backend) must choose and implement a storage backend **before** any upload endpoint ships.

Candidate backends:

1. Local development storage (dev-only; never public)
2. S3-compatible object storage (private buckets)
3. Encrypted external object store

---

## Required F5 safeguards

- Private by default; per-user ownership enforced server-side
- File size limits and MIME allowlist
- Checksum / content hash recorded on EvidenceRecord
- Malware / virus scan plan before bytes are considered usable
- Deletion and retention policy aligned with privacy module
- No public buckets; no permanent public URLs
- No raw file content in logs or observability payloads
- No LLM-based verification from uploaded files
- Download only for the owning authenticated user (if download is ever added)

---

## Explicit no-go (until separately approved)

- Public sharing tokens
- Permanent public URL for evidence files
- Wallet / DID / blockchain / VC issuance
- “Verified document” or official/trusted language
- OCR / document parsing (later explicit slice only)
- Silent claim `support_status` / `verification_status` upgrades on upload

---

## Next

After F4 acceptance only: **0053-F5 Attachment Storage Backend**.
