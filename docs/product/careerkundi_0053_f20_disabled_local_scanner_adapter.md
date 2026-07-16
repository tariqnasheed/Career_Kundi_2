# 0053-F20 — Disabled Local Scanner Adapter Skeleton

## What F20 adds

- Disabled local-process adapter skeleton: `attachment_local_scanner_adapter.py`
- Class: `DisabledLocalProcessScannerAdapter`
- Adapter name: `local_process_disabled`
- Safe error: `local_scanner_disabled` / “Local scanner is disabled in this version.”
- Tests proving the scaffold is unavailable and never selected by the factory

## What F20 does not add

- Real scanner command execution / subprocess
- ClamAV / VirusTotal / scanner packages
- File parsing / OCR / LLM review
- Worker loop / scheduler / startup registration
- Quarantine storage movement/deletion
- Scan route/API or frontend scan controls
- Claim / evidence / review mutation
- DB migration
- Env/config toggles that enable scanning

## Behavior

| Item | Value |
|---|---|
| Active factory adapter | `noop_unavailable` (unchanged) |
| Disabled skeleton name | `local_process_disabled` |
| Availability | `unavailable` |
| Verdict | `not_run` |
| Real scanner enabled | `False` |
| File / subprocess / network | none |

## Safety rules

- A disabled local scanner adapter is **not** an active scanner and is **not** verification.
- The scaffold must not be mistakable for a working scanner.
- Future real local scanner implementation requires a separately approved slice.

## Next

**0053-F21** Local Scanner Runtime Safety Contract — accepted after F20; then **0053-F22** Scanner Result Persistence Guard only after F21 acceptance.
