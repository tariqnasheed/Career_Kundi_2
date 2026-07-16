# 0053-F19 — Local Scanner Integration Planning

## What F19 adds

- Planning doc for future local scanner integration
- Pure policy module: `attachment_scanner_policy.py`
- Constants proving real scanning remains disabled
- Documented future adapter / timeout / failure / job-update boundaries
- Tests proving no real scanner, dependency, route, or UI is enabled

## What F19 does not add

- Real scanner adapter or engine
- Worker loop / scheduler / startup registration
- ClamAV binaries or Python scanner packages
- VirusTotal or any third-party scanner API
- File parsing / OCR / LLM review
- Quarantine storage movement/deletion
- Scan route/API or frontend scan controls
- Claim / evidence / review mutation
- DB migration
- Env/config toggles that enable real scanning

## Decision

| Item | Decision |
|---|---|
| Current adapter | `noop_unavailable` only |
| Real scanner enabled | `False` |
| Future adapter family | `local_process_scanner` (local-only, bounded) |
| External / cloud scanner APIs | Not allowed under current product boundary |
| File parsing / OCR / LLM as “scan” | Not allowed |
| Public EvidenceRead | Remains `scan_not_available` |

## Future local scanner requirements (not implemented)

1. Accept only storage-managed paths; verify containment before scan.
2. Run with bounded timeout; timeout → `scan_error` (not clean).
3. Normalize to safe error codes; never expose raw scanner output or paths.
4. Never log raw file bytes.
5. Only update `AttachmentScanJob` rows via a separately approved worker.
6. Never mutate Claim / Evidence trust / ReviewRequest / Passport verification.
7. Refuse scan when content hash differs from job snapshot.
8. Never publish files; never mark claims or Passports verified.
9. Keep public wording conservative until a later approved exposure slice.

## Scan result application policy (future only)

May update on `AttachmentScanJob`: `job_status`, `attachment_safety_status`, `engine_name`, `engine_version`, `safe_error_code`, `safe_error_message`, `started_at`, `completed_at`, `attempt_count`.

Must not update: EvidenceRecord trust fields, ClaimRecord statuses, ReviewRequest state, Passport verification, public sharing.

## Safety rules

- A scanner integration plan is **not** scanning and is **not** verification.
- Even future successful scan results must **not** verify claims or Passports.
- Current factory still returns the no-op adapter.
- Future implementation requires a separately approved slice (F20+).

## Next

**0053-F20** Disabled Local Scanner Adapter Skeleton — accepted after F19; then **0053-F21** Local Scanner Runtime Contract Tests only after F20 acceptance.
