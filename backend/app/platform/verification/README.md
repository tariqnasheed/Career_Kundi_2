# CareerKundi verification / review (0053-F9 / F10)

## Owns

- `ReviewState` / `ReviewActorType` / `ReviewerType` (F9 contracts)
- Transition validator + safe review labels (F9)
- **F10:** private `ReviewRequest` persistence + request/list/get/cancel service
- **F10:** authenticated `/api/v1/review-requests` routes (request/cancel only)

## Does not own

- Approval / rejection / conflict workflow
- Reviewer / admin / issuer portals
- ClaimRecord `support_status` / `verification_status` mutation
- Passport / Evidence Library verify UI
- OCR, malware scan, LLM verification
- Wallet / DID / blockchain / VC
- Public sharing

## Hard rule

> A review request is **not** verification.

Evidence upload, evidence link, or source/snapshot provenance is also not verification.

## F10 API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/review-requests` | Request review for owned claim |
| GET | `/api/v1/review-requests` | List own requests |
| GET | `/api/v1/review-requests/{id}` | Get own request |
| POST | `/api/v1/review-requests/{id}/cancel` | Cancel requested → cancelled |

Starts at `requested`. Cancel only from `requested` in F10.

## Next

**0053-F11** may add review-request UI or evidence hardening — only after F10 acceptance. Still no approve/reject trust UI.
