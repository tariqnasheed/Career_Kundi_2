# Evidence domain (0053-F2 … F28 planning)

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
| F21 | Local scanner runtime safety contract (disabled; no execution) |
| F22 | AttachmentScanJob result persistence guard (job rows only) |
| F23 | Quarantine storage planning + disabled store contract (inactive) |
| F24 | Quarantine event/audit planning + disabled audit sink (inactive) |
| F25 | Scan/quarantine admin boundary planning + disabled surface (inactive) |
| F26 | Scanner worker dry-run planning + disabled runner (inactive) |
| F27 | Scanner worker reservation guard (`queued` → `reserved` only) — accepted/completed |
| F28 | Scanner worker result application planning (contract only; no F29 code) — accepted |
| F29 | Scanner worker result application guard — **next; not started** |

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

## Local scanner runtime safety contract (F21)

- Module: `attachment_scanner_runtime_policy.py`
- `LOCAL_SCANNER_RUNTIME_ENABLED=False`; shell/network disallowed; binaries empty
- Safe error code/message normalization + path/URI redaction helpers
- No command runner, file read, packages, routes/UI, or DB apply
- A runtime contract is not scanner execution and not verification

## Scanner result persistence guard (F22)

- Module: `attachment_scan_result_persistence.py`
- Applies explicit persistable plans (`apply_to_database=True`) to `AttachmentScanJob` only
- Transition guards; F21 safe error normalization; quarantined status rejected
- No-op / disabled adapter plans are not persisted
- Does not mutate EvidenceRecord / ClaimRecord / ReviewRequest
- Persisting a scan-job result is not verification

## Quarantine storage planning (F23)

- Module: `attachment_quarantine_storage.py`
- `QUARANTINE_STORAGE_ENABLED=False`; movement/deletion/public access all false
- Decision helpers return objects only; no directory creation, move, copy, or delete
- F17 policy references the disabled storage contract; F22 still rejects `quarantined`
- A quarantine contract is not quarantine enforcement and is not verification

## Quarantine event/audit planning (F24)

- Module: `attachment_quarantine_audit.py`
- Audit sink / DB / file log / public access all `False`
- Safe metadata-only event types; F21 redaction for paths/URIs/messages
- Disabled sink returns `persisted=False` / `audit_sink_disabled` (no writes)
- Persistence guard does not auto-emit audit events
- An audit contract is not audit persistence and is not verification

## Scan/quarantine admin boundary (F25)

- Module: `attachment_scan_admin_boundary.py`
- Admin surface / API / UI all `False`; all trust/leak powers `False`
- Planned future actions are visibility-only; forbidden list includes verify/mark-safe/publish
- No admin routes, UI, workflows, or mutation powers
- An admin boundary contract is not an admin feature and is not verification

## Scanner worker dry-run planning (F26)

- Module: `attachment_scan_worker_dry_run.py`
- Worker / dry-run / loop / startup / DB mutation / file access / scanner exec / audit emit all `False`
- Decision objects only (would reserve / skip / reject); does not call F22 persistence or adapters
- No worker loop, startup registration, routes, or UI
- A dry-run contract is not a worker feature and is not verification
- Notes that F27 reservation guard exists; dry-run still does not call it

## Scanner worker reservation guard (F27)

- Module: `attachment_scan_worker_reservation.py`
- Owner-scoped `queued` → `reserved` only; content-hash snapshot must match
- Increments `attempt_count` by 1; sets `started_at` if empty
- Does **not** scan, read files, call adapters, apply F22 persistence, or emit audit
- Mutates `AttachmentScanJob` only; no EvidenceRecord / ClaimRecord / ReviewRequest changes
- No worker loop, startup registration, routes, or UI
- Reservation is not scanning and is not verification
- Accepted; next planning gate was F28

## Scanner worker result application planning (F28)

- Planning/contract only — **no F29 implementation module yet**
- Accepted decision: `0053_F28_SCANNER_WORKER_RESULT_APPLICATION_PLAN_ACCEPTED_READY_FOR_F29`
- Doc: `docs/product/careerkundi_0053_f28_scanner_worker_result_application_planning.md`
- F29 will allow only `reserved → completed|failed`; reject CANCEL_JOB / RESERVE_JOB / NO_OP
- Six-field exact-match idempotency; mandatory owner-scoped DB-only triple-hash
- PostgreSQL one-transaction lock-or-CAS; lock order job → evidence; no migration
- Prototype refs P39/P40/P41/P46 are future UX context only
- Scanner engine, worker loop, quarantine, audit, admin and UI remain absent/deferred
- A result-application plan is not result application and is not verification

## Foundation revision

`f0009_evidence_foundation` → tables `evidence_records`, `claim_evidence_links`.  
`f0010_review_request_foundation` → `review_requests`.  
`f0011_attachment_scan_queue` → `attachment_scan_jobs` (queue skeleton only).
