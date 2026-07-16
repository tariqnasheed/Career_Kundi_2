# 0053-F11 — Private Review Request UI

## What F11 adds

- Passport evidence panel controls to request/cancel a private review for an evidence-linked claim
- Frontend client: `reviewRequestApi.listReviewRequests` / `createReviewRequest` / `cancelReviewRequest`
- Safe copy: requesting a review does not verify a claim
- Merge review requests by `claim_id`; active = `review_state === "requested"`

## What F11 does not add

- Approve / reject / conflict UI
- Reviewer / admin / issuer workflow
- Claim `support_status` / `verification_status` mutation
- “Verified Passport” / public sharing / public Passport
- Passport upload/download/link
- CV / Roadmap / Job Search review UI
- OCR, malware scan, LLM verification, wallet/DID/blockchain
- Backend approve/reject endpoints (F10 unchanged)

## Safety rule

**A review request is not verification.**

Allowed “verified” wording only inside “Not independently verified”.

## Entry point

`/passport` → Private evidence awareness panel (per linked claim card).

## F12 status

F12 hardens intake (linked private evidence required; note/reason bounds). Passport UI remains request/cancel only. Still not verification.

## Next

**0053-F13** Evidence Attachment Hardening / Malware Scan Planning — only after F12 acceptance.
