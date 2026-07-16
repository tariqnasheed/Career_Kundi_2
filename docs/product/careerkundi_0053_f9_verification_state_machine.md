# 0053-F9 — Review / Verification State Machine (contract only)

## What F9 defines

- `ReviewState` values separate from claim `verification_status`
- `ReviewActorType` / `ReviewerType`
- Allowed / forbidden transitions (`validate_review_transition`)
- Explicit outcome → claim status mapping helper (not applied to DB)
- Safe review labels and policy warning

Module: `backend/app/platform/verification/`

## What F9 does not implement

- VerificationReview table / migration
- Verification API routes
- Admin / issuer UI
- User-facing review workflow
- Passport / Evidence verify buttons
- Claim status mutation
- Public sharing / public Passport
- OCR, malware scan, LLM verification
- Wallet / DID / blockchain / VC

## States

`not_requested` → `requested` → `under_review` → (`needs_more_evidence` | `approved` | `rejected` | `conflicted` | `cancelled`)  
`approved` → `expired` (system_policy only)

## Actors

| Actor | Allowed |
|-------|---------|
| user | request, cancel |
| reviewer | start review; needs-more-evidence; reject; conflict |
| approver | approve (also reject/conflict) |
| system_policy | expire approved |

No `self_verified` / `user_verified` / `ai_verified` / `blockchain_verified` / `auto_verified`.

## Safety rule

**Upload / link / source ≠ verification.**

Claim `verification_status` may change only through an explicit future review service.

## F10 status

**Implemented separately:** private review-request backend (`review_requests`, `/api/v1/review-requests` request/cancel only). Still no approve/reject, no claim mutation, no verification UI.

## F11 / F12 status

Passport private review request/cancel UI uses F10 APIs. F12 hardens intake (linked evidence + note/reason bounds). Still no approve/reject, no claim verification mutation, no public trust UI.

## Future F13

Evidence attachment hardening / malware scan planning — only after F12 acceptance. Still no public trust UI.
