# Evidence domain (0053-F2 / 0053-F3)

Private evidence **metadata** and claim-evidence **links**.

## F2 boundary (domain)

- EvidenceRecord = private metadata (title, kind, privacy, optional storage_uri/hash/mime/size, optional provenance source/snapshot).
- ClaimEvidenceLink = join row (`supports` / `contests` / `context`).
- Linking evidence **does not** mutate claim `support_status` or `verification_status`.
- Source/snapshot on evidence = provenance only, not verification.
- No file upload/download endpoints, no OCR/parsers, no virus scan, no file bytes in DB.
- No verification workflow, issuer review, or VerificationReview table.
- No public sharing, public URLs, share tokens, wallet/DID/blockchain/VC.
- No Passport / CV / Roadmap / Job Search ownership or UI.

## F3 boundary (private API)

Routes under `/api/v1/evidence` (auth required, current-user scoped):

- `POST /api/v1/evidence` — create metadata (`owner_user_id` always current user)
- `GET /api/v1/evidence` — list own evidence
- `GET /api/v1/evidence/{evidence_id}` — get own evidence (404 if not owned)
- `GET /api/v1/evidence/subjects/{subject_id}` — subject evidence if owned
- `POST /api/v1/evidence/links` — link owned evidence to owned claim
- `GET /api/v1/evidence/claims/{claim_id}/links` — list links for owned claim

Still forbidden in F3:

- upload / download / preview / OCR
- public sharing tokens
- verification review routes
- frontend evidence UI / Passport evidence panel

## Privacy

Default `privacy_class=private`. Allowed: `private`, `sensitive`, `restricted`.  
Rejected: `public`, `shared`, and similar visibility tokens.

## Service helpers

- `create_evidence_record` / `get_evidence_record`
- `list_owner_evidence` / `list_subject_evidence`
- `link_evidence_to_claim` / `list_claim_evidence_links`
- Owner-scoped: `get_evidence_for_owner`, `get_claim_for_owner`,
  `list_subject_evidence_for_owner`, `list_claim_evidence_links_for_owner`

## Foundation revision

`f0009_evidence_foundation` → tables `evidence_records`, `claim_evidence_links`.
