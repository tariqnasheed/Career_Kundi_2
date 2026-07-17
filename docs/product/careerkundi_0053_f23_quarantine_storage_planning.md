# 0053-F23 — Quarantine Storage Planning + Disabled Store Contract

## What F23 adds

- Disabled quarantine storage contract: `attachment_quarantine_storage.py`
- Explicit flags: storage / file movement / file deletion / public access all `False`
- Plan helpers and quarantine decision objects (no file operations)
- Safe warning: quarantine storage is planned but not active
- F17 policy wires to storage `enabled=False`
- Tests proving inactive storage, no dirs/move/delete, F22 still rejects `quarantined`

## What F23 does not add

- Actual quarantine directory
- File movement, copy, or deletion
- Real scanner command execution / process spawning
- ClamAV / VirusTotal / scanner packages
- File parsing / OCR / LLM review
- Worker loop / scheduler / startup registration
- Scan or quarantine route/API
- Frontend scan or quarantine controls
- EvidenceRecord / ClaimRecord / ReviewRequest mutation
- DB migration
- Allowing `AttachmentSafetyStatus.QUARANTINED` persistence

## Contract constants

| Flag | Value |
|---|---|
| `QUARANTINE_STORAGE_ENABLED` | `False` |
| `QUARANTINE_FILE_MOVEMENT_ENABLED` | `False` |
| `QUARANTINE_FILE_DELETION_ENABLED` | `False` |
| `QUARANTINE_PUBLIC_ACCESS_ENABLED` | `False` |

Mode: `disabled` (planned future: `planned_local_private_store`).

## Safety rules

- A quarantine contract is **not** quarantine enforcement.
- Quarantine-required decisions do not move or delete files.
- Public EvidenceRead remains `scan_not_available`.
- Future real quarantine implementation requires a separately approved slice.

## Next

**0053-F24** Quarantine Event/Audit Planning — only after F23 acceptance. Do not start F24 in this slice.
