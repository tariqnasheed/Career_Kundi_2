# Evidence domain (0053-F2 … F20)

Private evidence **metadata**, claim-evidence **links**, and private **attachment bytes**.

## Boundaries

| Slice | What shipped |
|---|---|
| F2 | Domain models + service (metadata/link only) |
| F3 | Authenticated `/api/v1/evidence` metadata + link APIs |
| F4 | Frontend Evidence Library (metadata UI) |
| F5 | Local private attachment storage + owner-only upload/download |
| F6 | Evidence Library private attach/download UI |
| F7 | Evidence Library private claim selector + linking UI |
| F8 | Passport read-only evidence awareness summary |
| F9 | Review/verification contracts live in `app.platform.verification` (not applied here) |
| F13 | Attachment safety states/warnings only (`attachment_safety.py`); default `scan_not_available` |
| F14 | Owner-only private attachment deletion; metadata record retained |
| F16 | Internal attachment scan queue skeleton (`attachment_scan_jobs`); no scanner/UI |
| F17 | Scan worker contract + quarantine policy (pure; not active; no engine) |
| F18 | Scanner adapter interface + no-op unavailable adapter (no real scan) |
| F19 | Local scanner integration planning + policy constants (still no-op) |
| F20 | Disabled local process scanner adapter skeleton (not selected) |

Hard rules across all slices:

- Linking or uploading evidence **does not** mutate claim `support_status` or `verification_status`.
- Upload / link is **not** verification. Wording remains “Not independently verified”.
- No public sharing, permanent public URLs, signed public URLs, wallet/DID/blockchain/VC.
- No OCR / document parsing / LLM verification of file bytes.
- **F13:** no malware scan engine; attachments are private but not scanned.
- No Passport / CV / Roadmap / Job Search ownership of evidence in these slices.
- No broad ` /api/v1/claims` route; F7 uses evidence-scoped `linkable-claims` only.

## API routes

- `POST /api/v1/evidence` — create metadata
- `GET /api/v1/evidence` — list own evidence
- `GET /api/v1/evidence/{evidence_id}` — get own evidence
- `GET /api/v1/evidence/subjects/{subject_id}` — subject evidence if owned
- `GET /api/v1/evidence/linkable-claims` — current-user claims for linking (F7)
- `POST /api/v1/evidence/links` — link owned evidence to owned claim
- `GET /api/v1/evidence/claims/{claim_id}/links` — list links for owned claim
- `GET /api/v1/evidence/{evidence_id}/links` — list links for owned evidence (F7)
- `POST /api/v1/evidence/{evidence_id}/attachment` — upload one private file (F5)
- `GET /api/v1/evidence/{evidence_id}/attachment` — download own private file (F5)
- `DELETE /api/v1/evidence/{evidence_id}/attachment` — remove private file bytes; clear attachment metadata (F14)

## Frontend note

`/evidence` supports private attach/download (F6) and private claim linking (F7).  
Linking does **not** verify claims. No Passport evidence panel in F7.

## Attachment safety (F13)

Derived response fields only (no DB column, no scanner):

- `attachment_safety_status` = `scan_not_available`
- `attachment_safety_label` = `Scan not available`
- Warning: private attachments are stored but not malware-scanned, parsed, reviewed, or verified

## Attachment deletion (F14)

- Deletes private local file bytes when present
- Clears `storage_uri` / `content_hash` / `mime_type` / `size_bytes`
- Keeps EvidenceRecord, ClaimEvidenceLink, ReviewRequest, claim statuses
- Deletion is not verification

Future retention requirements (not fully implemented): audit-safe event logging later (no raw file contents); retention windows later; orphaned-file cleanup later; backup deletion policy later; scanner quarantine/deletion later.

## Scan queue skeleton (F16)

- Internal service only: `attachment_scan_queue.py`
- Table: `attachment_scan_jobs` via `f0011_attachment_scan_queue`
- No `/scan` API route, no scanner engine, no UI controls
- Queue job `scan_pending` is not a completed scan and not verification
- Public response fields remain `scan_not_available` (F13)

## Scan worker contract + quarantine policy (F17)

- Pure modules: `attachment_scan_worker.py`, `attachment_quarantine_policy.py`
- Default scanner availability: unavailable
- `build_scan_job_update_from_result` returns plans only (`apply_to_database=False`)
- Quarantine handling is planned but not active; no file move/delete
- No worker loop, no startup registration, no scan route/UI

## Scanner adapter + no-op (F18)

- Module: `attachment_scanner_adapter.py`
- Factory returns `NoopUnavailableScannerAdapter` only
- Verdict always `not_run` / `scanner_unavailable`; maps to F17 `NO_OP`
- Does not read file bytes, call network/processes, or apply DB updates
- A no-op adapter is not a scanner and not verification

## Local scanner integration planning (F19)

- Policy module: `attachment_scanner_policy.py`
- `REAL_SCANNER_ENABLED = False`; future family `local_process_scanner`
- External APIs / parsing / OCR / LLM review disallowed for malware scan
- No scanner dependency, route, UI, worker loop, or DB apply
- A scanner plan is not scanning and not verification

## Disabled local scanner adapter skeleton (F20)

- Module: `attachment_local_scanner_adapter.py` (`DisabledLocalProcessScannerAdapter`)
- Availability unavailable; verdict `not_run` / `local_scanner_disabled`
- Active factory still returns `NoopUnavailableScannerAdapter` only
- No subprocess, file read, network, packages, routes/UI, or DB apply
- A disabled adapter skeleton is not scanning and not verification

## Foundation revision

`f0009_evidence_foundation` → tables `evidence_records`, `claim_evidence_links`.  
`f0010_review_request_foundation` → `review_requests`.  
`f0011_attachment_scan_queue` → `attachment_scan_jobs` (queue skeleton only).
