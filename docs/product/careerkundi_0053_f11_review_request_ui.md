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

## Next

**0053-F12** Review Intake Hardening or Evidence Hardening — only after F11 acceptance. Do not start F12 in F11.
