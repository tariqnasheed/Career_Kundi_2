# 0053-F26 — Scanner Worker Dry-Run Planning + Disabled Runner Contract

## What F26 adds

- Disabled scanner worker dry-run contract: `attachment_scan_worker_dry_run.py`
- Explicit flags: worker / dry-run / loop / startup / DB mutation / file access / scanner exec / audit emit all `False`
- Decision objects describing what a future worker would do (object only)
- Tests proving no loop, startup registration, persistence call, adapter call, or file access

## What F26 does not add

- Worker loop or background scheduler
- Startup registration in `main.py`
- Scan job reservation or F22 persistence calls
- Scanner adapter activation
- File path/byte access
- Routes / UI / admin workflows
- Audit persistence or quarantine enforcement
- DB migration
- EvidenceRecord / ClaimRecord / ReviewRequest / AttachmentScanJob mutation

## Contract constants

| Flag | Value |
|---|---|
| `SCAN_WORKER_ENABLED` | `False` |
| `SCAN_WORKER_DRY_RUN_ENABLED` | `False` |
| `SCAN_WORKER_BACKGROUND_LOOP_ENABLED` | `False` |
| `SCAN_WORKER_STARTUP_REGISTRATION_ENABLED` | `False` |
| `SCAN_WORKER_DB_MUTATION_ENABLED` | `False` |
| `SCAN_WORKER_FILE_ACCESS_ENABLED` | `False` |
| `SCAN_WORKER_SCANNER_EXECUTION_ENABLED` | `False` |
| `SCAN_WORKER_AUDIT_EMIT_ENABLED` | `False` |

## Safety rules

- A dry-run contract is **not** a worker feature.
- Dry-run decisions do not reserve jobs or call persistence.
- Public EvidenceRead remains `scan_not_available`.
- Future scanner worker implementation requires a separately approved slice.

## Next

**0053-F27** Scanner Worker Reservation Guard — only after F26 acceptance. Do not start F27 in this slice.
