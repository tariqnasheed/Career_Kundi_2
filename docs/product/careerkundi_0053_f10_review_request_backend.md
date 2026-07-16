# 0053-F10 — Private Review Request Backend Skeleton

## What F10 adds

- Table `review_requests` via `f0010_review_request_foundation`
- Service: create / list / get / cancel for current-user owned claims
- API: `/api/v1/review-requests` (+ `/{id}`, `/{id}/cancel`)
- Starts at `requested`; cancel → `cancelled`
- Partial unique index: one active `requested` row per claim

## What F10 does not add

- Approve / reject / conflict / under-review endpoints
- Reviewer / admin / issuer UI
- Claim `support_status` / `verification_status` mutation
- Verification UI / Passport verify / Evidence verify
- Public sharing, OCR, malware scan, LLM verification, wallet/DID/blockchain

## Safety rule

**A review request is not verification.**

## F11 status

F11 adds Passport private review request/cancel UI on top of this API. No approve/reject. No claim mutation. Review request remains not verification.

## Next

**0053-F12** Review Intake Hardening or Evidence Hardening — only after F11 acceptance.
