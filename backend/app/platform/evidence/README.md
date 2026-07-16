# Evidence domain (0053-F2)

Private evidence **metadata** and claim-evidence **links** only.

## F2 boundary

- EvidenceRecord = private metadata (title, kind, privacy, optional storage_uri/hash/mime/size, optional provenance source/snapshot).
- ClaimEvidenceLink = join row (`supports` / `contests` / `context`).
- Linking evidence **does not** mutate claim `support_status` or `verification_status`.
- Source/snapshot on evidence = provenance only, not verification.
- No file upload/download endpoints, no OCR/parsers, no virus scan, no file bytes in DB.
- No verification workflow, issuer review, or VerificationReview table.
- No public sharing, public URLs, share tokens, wallet/DID/blockchain/VC.
- No HTTP routes (`/api/v1/evidence`, `/api/v1/claims`).
- No Passport / CV / Roadmap / Job Search ownership or UI.

## Privacy

Default `privacy_class=private`. Allowed: `private`, `sensitive`, `restricted`.  
Rejected: `public`, `shared`, and similar visibility tokens.

## Service helpers

- `create_evidence_record` / `get_evidence_record`
- `list_owner_evidence` / `list_subject_evidence`
- `link_evidence_to_claim` / `list_claim_evidence_links`

## Foundation revision

`f0009_evidence_foundation` → tables `evidence_records`, `claim_evidence_links`.
