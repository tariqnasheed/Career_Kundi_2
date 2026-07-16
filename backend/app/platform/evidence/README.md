# Evidence domain (0053-F2 … F7)

Private evidence **metadata**, claim-evidence **links**, and private **attachment bytes**.

## Boundaries

| Slice | What shipped |
|---|---|
| F2 | Domain models + service (metadata/link only) |
| F3 | Authenticated `/api/v1/evidence` metadata + link APIs |
| F4 | Frontend Evidence Library (metadata UI) |
| F5 | Local private attachment storage + owner-only upload/download |
| F6 | Evidence Library private attach/download UI |
| F7 | Evidence Library private claim selector + linking UI |
| F8 | Passport read-only evidence awareness summary |
| F9 | Review/verification contracts live in `app.platform.verification` (not applied here) |

Hard rules across all slices:

- Linking or uploading evidence **does not** mutate claim `support_status` or `verification_status`.
- Upload / link is **not** verification. Wording remains “Not independently verified”.
- No public sharing, permanent public URLs, signed public URLs, wallet/DID/blockchain/VC.
- No OCR / document parsing / LLM verification of file bytes.
- No Passport / CV / Roadmap / Job Search ownership of evidence in these slices.
- No broad ` /api/v1/claims` route; F7 uses evidence-scoped `linkable-claims` only.

## API routes

- `POST /api/v1/evidence` — create metadata
- `GET /api/v1/evidence` — list own evidence
- `GET /api/v1/evidence/{evidence_id}` — get own evidence
- `GET /api/v1/evidence/subjects/{subject_id}` — subject evidence if owned
- `GET /api/v1/evidence/linkable-claims` — current-user claims for linking (F7)
- `POST /api/v1/evidence/links` — link owned evidence to owned claim
- `GET /api/v1/evidence/claims/{claim_id}/links` — list links for owned claim
- `GET /api/v1/evidence/{evidence_id}/links` — list links for owned evidence (F7)
- `POST /api/v1/evidence/{evidence_id}/attachment` — upload one private file (F5)
- `GET /api/v1/evidence/{evidence_id}/attachment` — download own private file (F5)

## Frontend note

`/evidence` supports private attach/download (F6) and private claim linking (F7).  
Linking does **not** verify claims. No Passport evidence panel in F7.

## Foundation revision

`f0009_evidence_foundation` → tables `evidence_records`, `claim_evidence_links`.  
No new migration for F5–F7.
