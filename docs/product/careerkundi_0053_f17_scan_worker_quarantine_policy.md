# 0053-F17 — Scan Worker Contract + Quarantine Policy

## What F17 adds

- Pure worker contract module: `attachment_scan_worker.py`
- Pure quarantine policy module: `attachment_quarantine_policy.py`
- Result → proposed job update plan mapping (`build_scan_job_update_from_result`)
- Default scanner availability: **unavailable**

## What F17 does not add

- Scanner engine / worker loop / startup registration
- ClamAV / VirusTotal / third-party scanning
- File parsing / OCR / LLM review
- Quarantine storage movement/deletion
- Scan route/API or frontend scan controls
- Claim / evidence / review mutation
- DB migration

## Safety rules

- A scan contract is not a scan result.
- A scan plan is not verification.
- Quarantine handling is planned but not active in this version.
- Public EvidenceRead remains `scan_not_available`.

## Mapping (plans only; not applied)

| Verdict | Proposed job status | Proposed safety | Quarantine required |
|---|---|---|---|
| clean | completed | scan_passed | no |
| malicious / suspicious | completed | scan_failed | yes (policy only) |
| timeout / error / unsupported | failed | scan_error | no |
| not_run / unavailable | no-op | scan_not_available | no |

## Next

**0053-F18** Scanner Adapter Interface + No-Op Adapter — accepted; **0053-F19** Local Scanner Integration Planning — next planning seam; then **0053-F20** only after F19 acceptance.
