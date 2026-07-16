# Evidence domain (0053-F2 / F3 / F4 / F5)

Private evidence **metadata**, claim-evidence **links**, and private **attachment bytes**.

## Boundaries

| Slice | What shipped |
|---|---|
| F2 | Domain models + service (metadata/link only) |
| F3 | Authenticated `/api/v1/evidence` metadata + link APIs |
| F4 | Frontend Evidence Library (metadata UI only; no upload) |
| F5 | Local private attachment storage + owner-only upload/download |

Hard rules across all slices:

- Linking or uploading evidence **does not** mutate claim `support_status` or `verification_status`.
- Upload is **not** verification. Wording remains “Not independently verified”.
- No public sharing, permanent public URLs, signed public URLs, wallet/DID/blockchain/VC.
- No OCR / document parsing / LLM verification of file bytes.
- No Passport / CV / Roadmap / Job Search ownership of evidence in these slices.

## API routes

- `POST /api/v1/evidence` — create metadata
- `GET /api/v1/evidence` — list own evidence
- `GET /api/v1/evidence/{evidence_id}` — get own evidence
- `GET /api/v1/evidence/subjects/{subject_id}` — subject evidence if owned
- `POST /api/v1/evidence/links` — link owned evidence to owned claim
- `GET /api/v1/evidence/claims/{claim_id}/links` — list links for owned claim
- `POST /api/v1/evidence/{evidence_id}/attachment` — upload one private file (F5)
- `GET /api/v1/evidence/{evidence_id}/attachment` — download own private file (F5)

## F5 storage

- Backend: `LocalEvidenceStorage` (`storage.py`)
- Default root: `backend/data/evidence_files` (configurable via `EVIDENCE_STORAGE_ROOT`)
- URI format: `local-evidence://<owner_user_id>/<evidence_id>/<hash-based-filename>`
- Limits: 5 MiB; MIME allowlist (pdf/png/jpeg/plain/docx)
- SHA-256 recorded on `EvidenceRecord.content_hash`
- Duplicate attachment without replace → conflict
- Path traversal blocked; no raw bytes logged
- Virus scan: **not implemented** in F5 (documented watch item for later)

## Frontend note

`/evidence` (F6) supports private attach/download against these APIs.  
Upload is **not** verification. No Passport/CV/Roadmap/Jobs attachment UI in F6.

## Foundation revision

`f0009_evidence_foundation` → tables `evidence_records`, `claim_evidence_links`.  
F5 uses existing `storage_uri` / `content_hash` / `mime_type` / `size_bytes` — no new migration.
