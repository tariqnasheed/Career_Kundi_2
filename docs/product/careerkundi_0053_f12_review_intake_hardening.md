# 0053-F12 — Review Intake Hardening

## What F12 adds

- Create review request only for owned claims with at least one linked private evidence record owned by the same user
- Request note: optional, trimmed, blank → null, max 1000 chars
- Cancellation reason: optional, trimmed, blank → null, max 500 chars
- Passport copy: intake requires linked private evidence; request is not verification
- Safe error mapping when linked evidence is missing

## What F12 does not add

- Approve / reject / conflict / under-review endpoints
- Reviewer / admin / issuer workflow
- Claim status mutation
- Verification result workflow
- Public sharing / Verified Passport
- OCR / malware scan / LLM verification
- Wallet / DID / blockchain / VC

## Safety rule

**Review intake hardening is still not verification.**

Malware scan remains deferred to a later slice.

## F13 status

F13 adds attachment safety states/warnings only (default `scan_not_available`). No scan engine. Intake still requires linked evidence but does not require scan pass.

## Next

**0053-F13** and **0053-F14** completed after this slice. Next after F14 acceptance: **0053-F15** Scan Queue Skeleton or Runtime Badge-Seed Fix only.
