# 0053-F25 — Scan/Quarantine Admin Boundary Planning

## What F25 adds

- Disabled admin surface contract: `attachment_scan_admin_boundary.py`
- Explicit flags: surface / API / UI and all trust/leak powers `False`
- Planned future visibility-only actions (not implemented)
- Explicit forbidden powers (verify, mark safe/clean, publish, expose paths/URIs/output)
- Tests proving no admin routes/UI/workflows or mutation powers

## What F25 does not add

- Backend admin route or frontend admin UI
- Scan / quarantine / audit admin APIs
- Reviewer / issuer / trust operator workflows
- Scanner activation, quarantine enforcement, or audit persistence
- DB migration
- File movement/deletion/copy
- Claim / evidence / review mutation
- Public sharing or Passport verification

## Contract constants

| Flag | Value |
|---|---|
| `SCAN_ADMIN_SURFACE_ENABLED` | `False` |
| `SCAN_ADMIN_API_ENABLED` | `False` |
| `SCAN_ADMIN_UI_ENABLED` | `False` |
| Force scan / mark safe / mark clean / verify / release / delete / raw path/URI/output | all `False` |

## Boundary rules

Future operators may eventually gain safe visibility powers only (separately approved).  
They must never mark files safe/clean/trusted, verify documents/claims/Passports, publish evidence, expose raw paths/URIs/scanner output, or override claim/review state through scan/quarantine tooling.

## Safety rules

- An admin boundary contract is **not** an admin feature.
- Admin controls remain inactive.
- Public EvidenceRead remains `scan_not_available`.
- Future admin implementation requires a separately approved slice.

## Next

**0053-F26** Scanner Worker Dry-Run Planning — only after F25 acceptance. Do not start F26 in this slice.
