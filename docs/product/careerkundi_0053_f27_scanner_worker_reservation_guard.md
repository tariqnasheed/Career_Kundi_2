# 0053-F27 — Scanner Worker Reservation Guard

## What F27 adds

- Internal reservation guard: `attachment_scan_worker_reservation.py`
- Allowed transition: `AttachmentScanJob.job_status` `queued` → `reserved` only
- Owner-scoped lookup; content-hash snapshot must match expected snapshot
- On success: increment `attempt_count` by 1; set `started_at` if empty
- Guard flags: reservation guard enabled; scanner execution / file read / worker registration / route exposure all `False`; mutates only scan job `True`

## What F27 does not add

- Worker loop or background scheduler
- Startup registration in `main.py`
- Scanner adapter activation or scanner execution
- File path lookup or file byte reads
- Hash recomputation from file bytes
- F22 scan result persistence apply
- Scan completion / failure marking / quarantine / audit persistence
- Routes / UI / admin workflows
- DB migration
- EvidenceRecord / ClaimRecord / ReviewRequest mutation

## Reservation rules

1. Fetch job through owner-scoped lookup.
2. Missing / other-owner → safe `not_found` (no existence leak).
3. Require `job_status == queued`.
4. Require `content_hash_snapshot` equals caller-provided expected snapshot (snapshot guard, not a file read).
5. Set status to `reserved`; increment attempt count once; set `started_at` if empty.
6. Do not set `completed_at`, safety status to passed/failed/error, engine fields, or safe error fields.

## Future worker flow (planning only)

1. Create job (F16)
2. Reserve job (F27)
3. Scan in a future approved slice
4. Apply result through F22 guard
5. No claim verification

## Safety rules

- Reservation mutates `AttachmentScanJob` only.
- Reservation is not scanning and is not verification.
- F26 dry-run runner remains disabled and does not call reservation.
- Public EvidenceRead remains `scan_not_available`.
- Future scanner execution must be separately approved.

## Next

**0053-F28** Scanner Worker Result Application Planning — only after F27 acceptance. Do not start F28 in this slice.
