# 0053-F24 — Quarantine Event/Audit Planning + Disabled Audit Sink Contract

## What F24 adds

- Disabled quarantine audit contract: `attachment_quarantine_audit.py`
- Explicit flags: sink / DB / file log / public access all `False`
- Safe event types for future scan/quarantine decisions
- Metadata-only payloads with path/URI/raw-output redaction
- Disabled sink that accepts events and returns `persisted=False`
- Tests proving no DB table, file log, routes, UI, or auto-emission

## What F24 does not add

- Audit DB migration or table
- Audit file log
- External logging service
- Scan / quarantine / audit route/API
- Frontend audit or scan/quarantine controls
- Real scanner or quarantine enforcement
- File move/copy/delete or directory creation
- Automatic event emission from the F22 persistence guard
- EvidenceRecord / ClaimRecord / ReviewRequest mutation

## Contract constants

| Flag | Value |
|---|---|
| `QUARANTINE_AUDIT_SINK_ENABLED` | `False` |
| `QUARANTINE_AUDIT_DB_ENABLED` | `False` |
| `QUARANTINE_AUDIT_FILE_LOG_ENABLED` | `False` |
| `QUARANTINE_AUDIT_PUBLIC_ACCESS_ENABLED` | `False` |
| `RAW_FILE_PATH_ALLOWED_IN_AUDIT` | `False` |
| `STORAGE_URI_ALLOWED_IN_AUDIT` | `False` |
| `RAW_SCANNER_OUTPUT_ALLOWED_IN_AUDIT` | `False` |

## Safe payload rules

Allowed: event type/version, evidence/job/owner/actor IDs, job/safety status, safe error code/message, created_at.  
Forbidden: file paths, storage URIs, public URLs, raw scanner output, file bytes, LLM analysis, trust claims.

## Safety rules

- An audit contract is **not** audit persistence.
- Disabled sink does not write DB or files.
- Public EvidenceRead remains `scan_not_available`.
- Future real audit persistence requires a separately approved slice.

## Follow-on

**0053-F25** Scan/Quarantine Admin Boundary Planning — accepted after F24; admin surface remains disabled. Then **0053-F26** only after F25 acceptance.
