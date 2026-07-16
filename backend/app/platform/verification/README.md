# CareerKundi verification / review contracts (0053-F9)

## Owns

- `ReviewState` — future review workflow states (separate from claim `verification_status`)
- `ReviewerType` / `ReviewActorType` — reviewer org kinds and transition actors
- Transition validator (`validate_review_transition`)
- Explicit outcome → claim status mapping helpers (not applied to DB)
- Safe review display labels

## Does not own

- `VerificationReview` table / migrations
- Verification HTTP routes or admin/issuer UI
- ClaimRecord mutation
- Passport / Evidence Library verify buttons
- OCR, malware scan, LLM verification
- Wallet / DID / blockchain / VC

## Hard rule

> Evidence upload, evidence link, or source/snapshot provenance is **not** verification.

Claim `verification_status` may change only through an explicit future review service that is not implemented in F9.

## Actors

| Actor | May |
|-------|-----|
| `user` | request, cancel |
| `reviewer` | start review; needs-more-evidence; reject; conflict |
| `approver` | approve (and may reject/conflict) |
| `system_policy` | expire approved |

Forbidden actor labels: `self_verified`, `user_verified`, `ai_verified`, `blockchain_verified`, `auto_verified`.

## Next

**0053-F10** may add a review-request backend skeleton only after F9 acceptance — still without public sharing or trust overclaim.
