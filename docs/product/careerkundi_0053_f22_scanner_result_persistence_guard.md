# 0053-F22 — Scanner Result Persistence Guard

## What F22 adds

- Internal persistence guard: `attachment_scan_result_persistence.py`
- Explicit persistable update plans (`apply_to_database=True` required)
- Strict `AttachmentScanJob` status transition validation
- Reuse of F21 safe error-code/message normalization
- Tests proving only scan-job rows change

## What F22 does not add

- Real scanner command execution / process spawning
- ClamAV / VirusTotal / scanner packages
- File parsing / OCR / LLM review
- Worker loop / scheduler / startup registration
- Quarantine storage movement/deletion
- Scan route/API or frontend scan controls
- EvidenceRecord / ClaimRecord / ReviewRequest mutation
- DB migration
- Env/config toggles that enable scanning

## Allowed mutations

| Row | Fields |
|---|---|
| `AttachmentScanJob` only | `job_status`, `attachment_safety_status`, `engine_name`, `engine_version`, `attempt_count`, `safe_error_code`, `safe_error_message`, `started_at`, `completed_at`, `cancelled_at`, `updated_at` |

## Allowed transitions

- `queued` → `reserved`
- `reserved` → `completed` / `failed` / `cancelled`
- `queued` → `cancelled`

Terminal statuses (`completed`, `failed`, `cancelled`) cannot change.  
`quarantined` safety status is rejected in F22.  
No-op / disabled adapter plans are never persisted.

## Safety rules

- Persisting a scan-job result is **not** verification.
- Public EvidenceRead remains `scan_not_available`.
- Future real scanner implementation requires a separately approved slice.

## Next

**0053-F23** Quarantine Storage Planning — only after F22 acceptance. Do not start F23 in this slice.
