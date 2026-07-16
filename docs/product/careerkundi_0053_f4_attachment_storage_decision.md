# 0053-F4 / F5 — Attachment Storage Decision

**Status:** F4 decided · F5 storage · F6 upload UI · F7 claim linking UI implemented  
**Date:** 2026-07-16  
**Depends on:** 0053-F3 private evidence metadata API

---

## F4 decision

**No file upload or attachment storage in F4.**

The Evidence Library UI creates and lists **private metadata only**. `storage_uri` remained an optional metadata/reference string until F5.

---

## F5 decision (implemented)

**Local private development storage** for evidence file bytes.

| Item | Value |
|---|---|
| Backend | `LocalEvidenceStorage` (`backend/app/platform/evidence/storage.py`) |
| Root | `backend/data/evidence_files` (override: `EVIDENCE_STORAGE_ROOT`) |
| URI | `local-evidence://<owner_user_id>/<evidence_id>/<hash-filename>` |
| Upload | `POST /api/v1/evidence/{evidence_id}/attachment` (auth + owner) |
| Download | `GET /api/v1/evidence/{evidence_id}/attachment` (auth + owner) |
| Size limit | 5 MiB |
| MIME allowlist | pdf, png, jpeg, text/plain, docx |
| Checksum | SHA-256 → `EvidenceRecord.content_hash` |
| Replace | Rejected by default (conflict) |
| Frontend upload UI | **Enabled on `/evidence` only (F6)** |

Candidate backends deferred beyond local:

1. S3-compatible private object storage
2. Encrypted external object store

---

## F6 UI (implemented)

- Evidence Library selected-record controls: `Attach private file` / `Download private attachment`
- Client validation: empty / over 5 MB / MIME allowlist
- Authenticated blob download; no public URL shown
- Safe copy: upload does not verify evidence or claims; Not independently verified
- No Passport / CV / Roadmap / Job Search attachment UI

---

## Safeguards in F5/F6

- Private by default; per-user ownership enforced server-side
- File size limits and MIME allowlist
- Checksum / content hash on EvidenceRecord
- Path traversal protection; storage root containment
- No public buckets; no permanent/signed public URLs
- No raw file content in logs
- No LLM-based verification from uploaded files
- Download only for owning authenticated user
- Upload does **not** mutate claim support/verification axes

## Still deferred

- Malware / virus scan engine (watch item)
- Deletion / retention product UX (privacy module alignment)
- OCR / document parsing
- Public sharing
- Passport / CV / Roadmap / Job Search evidence panels

---

## Explicit no-go (until separately approved)

- Public sharing tokens
- Permanent public URL for evidence files
- Wallet / DID / blockchain / VC issuance
- “Verified document” or official/trusted language
- OCR / document parsing (later explicit slice only)
- Silent claim `support_status` / `verification_status` upgrades on upload

---

## F7 linking note

Evidence Library can privately link evidence to current-user claims via `GET /api/v1/evidence/linkable-claims` + `POST /api/v1/evidence/links`. Linking does **not** verify claims or auto-upgrade claim status axes. Passport evidence panel remains deferred.

## Next

After F7 acceptance only: **0053-F8** (Passport read-only evidence panel or review/verification state machine).
