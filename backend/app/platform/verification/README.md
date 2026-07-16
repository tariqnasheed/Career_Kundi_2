# CareerKundi verification / review (0053-F9 / F10 / F12)

## Owns

- `ReviewState` / `ReviewActorType` / `ReviewerType` (F9 contracts)
- Transition validator + safe review labels (F9)
- **F10:** private `ReviewRequest` persistence + request/list/get/cancel service
- **F10:** authenticated `/api/v1/review-requests` routes (request/cancel only)
- **F12:** intake eligibility (owned claim + linked private evidence), note/reason bounds

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

## F12 intake rules

- Owned claim required
- At least one `ClaimEvidenceLink` to evidence owned by the same user
- Duplicate active (`requested`) request blocked; cancelled history does not block a new request
- `request_note` optional, trimmed, max 1000 chars
- `cancellation_reason` optional, trimmed, max 500 chars

## API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/review-requests` | Request review for eligible owned claim |
| GET | `/api/v1/review-requests` | List own requests |
| GET | `/api/v1/review-requests/{id}` | Get own request |
| POST | `/api/v1/review-requests/{id}/cancel` | Cancel requested → cancelled |

Starts at `requested`. Cancel only from `requested`.

## Next

**0053-F13** Evidence Attachment Hardening / Malware Scan Planning — only after F12 acceptance. Still no approve/reject trust UI.
