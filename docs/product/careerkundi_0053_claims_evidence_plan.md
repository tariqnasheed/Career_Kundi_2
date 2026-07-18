# CareerKundi 0053 — Evidence, Claims, Provenance & Verification Plan

**Slice:** 0053-F0 Planning and Boundary Audit  
**Status:** Planning complete — no implementation in F0  
**Depends on:** 0052 Career & Education Passport (completed / accepted)  
**Foundation head (after F2):** `f0009_evidence_foundation` (was `f0008_passport_persistence` through F1)  
**LLM provider (platform-wide):** Local Ollama 8B (`http://127.0.0.1:11434`); `LLM_PROVIDER=mock` for deterministic tests. Gemini is legacy/deprecated. Local LLM output is **not** verification.

---

## A. Executive summary

0053 will add **evidence and claim-support foundations carefully**, without public sharing or verification claims in the first implementation slices.

CareerKundi already has:

- Provenance (`SourceRecord` / `SourceSnapshot`)
- Claim foundation (`ClaimRecord` on `career_claims`) with independent support and verification axes
- Passport as a **private, unverified**, profile-backed structured career surface

0053 must not pretend that linking a source, snapshot, upload, or claim row makes something true. The hard rule:

> **A source, snapshot, uploaded file, user assertion, or claim record is not verification.**

Early 0053 slices stay private. Verification workflows, issuer review, and any trust language arrive only after explicit later slices and owner approval. No wallet, DID, blockchain, or public Passport in 0053-F0…F6 by default.

---

## B. Current-state inventory

### 1. Provenance

| Field | Value |
|---|---|
| Existing files | `backend/app/platform/provenance/` (`README.md`, `refs.py`, `service.py`, tests); `backend/app/db/models/provenance.py` |
| Data structures | `SourceRecord` → `provenance_sources`; `SourceSnapshot` → `provenance_snapshots`; `SourceKind`; `SourceRef` / `SnapshotRef` |
| Ownership | Platform provenance domain |
| Limitations | No public FastAPI routes; no claims/evidence/verification; no crawlers/file stores/parsers |
| 0053 risk | Confusing “has source” with verified truth |
| Next action | Keep as Source/Snapshot owner; claims/evidence link to it, never absorb it |

### 2. Claims

| Field | Value |
|---|---|
| Existing files | `backend/app/platform/claims/` (`status.py`, `service.py`, `refs.py`, README, tests); `backend/app/db/models/claim.py` |
| Data structures | `ClaimRecord` / table `career_claims`; enums `ClaimKind`, `ClaimOrigin`, `SupportStatus`, `VerificationStatus` |
| Ownership | Platform claims domain (service create/get/list; **no public claim HTTP routes**) |
| Limitations | No evidence objects; no review workflow; no Passport materialization; optional `source_id`/`snapshot_id` are provenance links only |
| 0053 risk | UI or CV treating `verification_status=verified` or `support_status=evidence_backed` as “official truth” |
| Next action | **0053-F1** Claim Service Contract Boundary — lock contracts, forbidden silent upgrades, UI wording map |

### 3. Passport

| Field | Value |
|---|---|
| Existing files | `backend/app/career_passport/`, `db/models/passport.py`, `schemas/passport.py`, `api/routes/passport.py`, `frontend/src/features/passport/*` |
| Data structures | Aggregate + section rows; `PassportRecordMeta` with `verification_status` forced `unverified`; visibility `private` |
| Ownership | Passport feature owns structured career editing; not claims/evidence |
| Limitations | No evidence upload; no claims UI; no public sharing; no scoring |
| 0053 risk | Trust creep if Passport meta syncs to “verified” too early |
| Next action | Later read-only evidence panels only after F3–F4; keep unverified default |

### 4. Profile

| Field | Value |
|---|---|
| Existing files | `frontend/src/pages/ProfilePage.tsx`, profile APIs |
| Data structures | Legacy profile fields; may receive Passport-synced skill **objects** (F8 normalized for display) |
| Ownership | Legacy compatibility surface |
| Limitations | Not claim/evidence owner; FE↔BE shape mismatches partially deferred |
| 0053 risk | Showing object skills/certs as “verified credentials” |
| Next action | Stay compatibility-only; no claims UI on `/profile` in early 0053 |

### 5. CV Builder

| Field | Value |
|---|---|
| Existing files | `frontend/src/pages/CVBuilderPage.tsx`, `backend/app/api/routes/cv_builder.py` |
| Data structures | CV drafts from private Passport/profile data (F7 read awareness) |
| Ownership | CV Builder owns drafts/export |
| Limitations | No evidence IDs in payloads; no verification language |
| 0053 risk | “Evidence-backed CV” marketing language |
| Next action | Optional evidence **summary** only in F8 of this ladder; never verify |

### 6. Roadmap

| Field | Value |
|---|---|
| Existing files | `frontend/src/pages/RoadmapPage.tsx`, roadmap APIs |
| Data structures | Roadmap-owned generate/progress; Passport target prefill only (F7) |
| Ownership | Roadmap feature |
| Limitations | No claim/evidence ownership |
| 0053 risk | Treating Passport targets or evidence as roadmap progress |
| Next action | Optional awareness later (F8); no verification |

### 7. Platform Subjects

| Field | Value |
|---|---|
| Existing files | `backend/app/api/routes/platform.py`, identity service |
| Data structures | `CareerSubject`; claims require `subject_id` |
| Ownership | Platform identity |
| Limitations | Subject picker deferred from Passport; list empty envelope verified in F8 |
| 0053 risk | Auto-creating subjects for claims without consent clarity |
| Next action | F1 must define subject linkage rules for claims |

### 8. Privacy and observability

| Field | Value |
|---|---|
| Existing files | `backend/app/platform/privacy/`, `backend/app/platform/observability/` |
| Data structures | Privacy services; observability boundaries (no new DB storage for observability) |
| Ownership | Platform |
| Limitations | Evidence uploads will increase PII/document risk |
| 0053 risk | Logs leaking document content; retention gaps |
| Next action | F9 hardening for deletion/retention; no observability DB in early slices |

---

## C. Domain definitions

| Term | Is | Is not |
|---|---|---|
| **Source** | Origin/channel of information (`SourceRecord`) | A proof of content at a time; not verification |
| **Snapshot** | Captured observation of a source at a time (`SourceSnapshot`) | A live crawl; not verification of claim truth |
| **Claim** | Statement about a subject (`ClaimRecord`: kind/key/value + axes) | Passport biography row; not verified truth |
| **Evidence** | Material that supports or contests a claim (planned `EvidenceRecord`) | Automatic verification; not “official credential” |
| **Support status** | How much material is linked to a claim | Verification outcome |
| **Verification status** | Review/issuer outcome axis (independent of support) | Implied by upload or source link |
| **Issuer** | Party that asserts or signs a credential/claim (future) | CareerKundi by default |
| **Subject** | Career subject the claim is about (`CareerSubject`) | The authenticated user account alone |
| **Holder** | Party who holds evidence/credentials (usually the user) | Verifier |
| **Verifier** | Party that checks claims/evidence (future workflow) | Automatic AI “truth” agent |
| **Passport credential reference** | Unverified credential **entry** on Passport | Verified credential; not wallet item |
| **Uploaded document** | Binary/file referenced as evidence attachment (future) | Verified certificate |
| **Evidence link** | Join between claim and evidence (future) | Verification record |
| **Verified credential** | Claim/credential after approved verification workflow | Source-linked or evidence-linked claim |

**W3C VC 2.0 alignment (planning only):** W3C Verifiable Credentials Data Model 2.0 describes issuers, holders, verifiers, and registries. Critical warning:

> Verifiability of a credential does not imply the truth of the claims encoded in it.

0053 begins with private evidence and claim-support states. Do **not** jump to VC issuance, DID, wallet, or cryptographic presentation in F0–F6.

---

## D. Truth-state ladder

CareerKundi display ladder (product language). Backend enums may use different tokens (e.g. existing `evidence_backed`); UI must map to honest wording below.

| State | Meaning | Allowed UI wording | Forbidden UI wording | Required backend | Allowed surfaces | Privacy risk |
|---|---|---|---|---|---|---|
| `not_provided` | No assertion | Not provided | Verified | Default / empty | Passport, claims | Low |
| `self_declared` | User said so | Self-declared; Not independently verified | Official; Verified | Claim origin user_asserted / Passport meta | Passport, claims | Medium |
| `profile_backed` | Backed by Profile/Passport row | Profile-backed; Not independently verified | Evidence-backed (as trust) | Passport `profile_supported` | Passport, Profile | Medium |
| `source_linked` | Linked to a Source | Source-linked | Verified by issuer | Claim `source_id` | Claims private UI | Medium |
| `snapshot_linked` | Linked to Snapshot | Snapshot-linked; observed capture | Verified truth | Claim `snapshot_id` (+ source) | Claims private UI | Medium–High |
| `evidence_linked` | Linked to Evidence material | Evidence-linked; Under review if pending | Evidence-backed as “proof of truth”; Official | Future Evidence + link | Evidence library, Passport panel | High |
| `under_review` | Human/system review pending | Under review; Needs review | Approved; Verified | Future VerificationReview | Review queue | High |
| `issuer_verified` | Issuer confirmed | Verified by issuer | Verified by CareerKundi (unless CK did) | Future review outcome | Restricted surfaces | High |
| `careerkundi_verified` | CareerKundi review accepted | Verified by CareerKundi | Public Passport; Official credential | Future review outcome | Restricted; never default | High |
| `rejected` | Review rejected | Rejected | Verified | Future review | Private | Medium |
| `expired` | Past validity | Expired | Verified | Future expiry fields | Private | Medium |

**Mapping note:** Existing `SupportStatus.EVIDENCE_BACKED` must surface as **Evidence-linked** (or equivalent), never as “verified” or “official.” F1 should decide whether to rename the enum or keep token + UI map.

---

## E. Proposed 0053 architecture

Recommended module boundaries (**not implemented in F0**):

| Module | Role |
|---|---|
| `backend/app/platform/provenance/` | Continues to own Source/Snapshot |
| `backend/app/platform/claims/` → evolve toward `backend/app/claims/` contracts | Claim statements + status axes |
| `backend/app/evidence/` (new) | Evidence records + attachment refs |
| `backend/app/verification/` (new, late) | Review / issuer verification workflows only when approved |
| `frontend/src/features/evidence/` (new) | Private evidence library + panels |
| `frontend/src/features/passport/` | May **display** support states; must not own verification |

Rules:

- Provenance continues to own Source/Snapshot.
- Claims own statements about subjects.
- Evidence owns support material references.
- Verification owns review/issuer workflow only when approved.
- Passport may display support states but must not own verification.
- CV/Roadmap may read evidence summaries later but must not verify anything.

Job-search modules (`agents/job_search/quality/evidence_*`) are **interview/pack evidence slots**, not Passport claim evidence — keep namespaces separate.

---

## F. Data model proposal (not implemented in F0)

### EvidenceRecord

| Field | Value |
|---|---|
| Purpose | Private evidence material metadata |
| Owner | Evidence module |
| Key fields | id, owner_user_id, subject_id?, title, evidence_kind, storage_uri?, content_hash?, source_id?, snapshot_id?, privacy_class, created_at |
| Privacy | Private by default; PII-capable |
| Indexes | owner_user_id, subject_id, created_at |
| Relationships | optional Source/Snapshot; many ClaimEvidenceLink |
| Open questions | Bytes in-app vs external object store; virus scan |

### ClaimEvidenceLink

| Field | Value |
|---|---|
| Purpose | Many-to-many claim ↔ evidence |
| Owner | Claims or Evidence (pick in F1/F2) |
| Key fields | claim_id, evidence_id, link_role (supports/contests), created_by |
| Privacy | Inherits claim/evidence privacy |
| Indexes | (claim_id, evidence_id) unique |
| Open questions | Does link auto-upgrade support_status? (**Prefer no auto-upgrade**) |

### VerificationReview

| Field | Value |
|---|---|
| Purpose | Explicit review decision record |
| Owner | Verification module (F7+) |
| Key fields | id, claim_id?, evidence_id?, outcome, reviewer_actor, notes, decided_at |
| Privacy | Restricted; audit-sensitive |
| Open questions | Who may be reviewer in MVP? |

### VerificationActor

| Field | Value |
|---|---|
| Purpose | Reviewer/issuer identity reference |
| Owner | Verification |
| Key fields | actor_type, actor_id, display_label |
| Privacy | Internal |
| Open questions | Org accounts out of scope initially |

### EvidenceAttachmentRef

| Field | Value |
|---|---|
| Purpose | Pointer to uploaded file blob |
| Owner | Evidence |
| Key fields | evidence_id, storage_backend, storage_key, mime, size_bytes, checksum |
| Privacy | High |
| Open questions | Retention/deletion policy (F9) |

**Do not create migrations in F0.**

---

## G. API proposal (not implemented in F0)

| Endpoint | Purpose | Auth | Ownership | Privacy risk | Not allowed yet |
|---|---|---|---|---|---|
| `GET /api/v1/claims` | List own claims | Required | Subject/owner scoped | Medium | Cross-user list; public |
| `POST /api/v1/claims` | Create claim | Required | Creator owns | Medium | Auto-verified |
| `GET /api/v1/evidence` | List private evidence | Required | Owner scoped | High | Public URLs |
| `POST /api/v1/evidence` | Register evidence metadata | Required | Owner | High | Unbounded uploads without limits |
| `POST /api/v1/claims/{id}/evidence` | Link evidence | Required | Claim+evidence owners | High | Silent verification upgrade |
| `POST /api/v1/verification/reviews` | Record review (F7+) | Required + role | Reviewer policy | High | Self-verify to “Verified by CareerKundi” without process |

Request/response shapes: Pydantic envelopes matching existing platform patterns; exact schemas in F1–F3. No routes in F0.

---

## H. UI proposal (not implemented in F0)

| Surface | Shows | Must not say | User action | Data source | Privacy | Phase |
|---|---|---|---|---|---|---|
| Passport evidence panel | Linked evidence counts/labels | Verified Passport; Official | Open evidence library | Evidence + links | Private | F4 |
| Claim-support badges | Support/verification ladder labels | Evidence-backed as truth | View detail | Claims | Private | F5 |
| Private evidence library | Uploads/refs | Public Passport | Add/link evidence | Evidence API | Private | F3–F6 |
| Evidence review queue | Pending reviews | Auto-approved | Decide | VerificationReview | Restricted | F7 |
| CV evidence summary | Optional “evidence linked” note | Verified CV | None / link out | Read-only | Private | F8 |
| Roadmap evidence awareness | Optional context | Progress from evidence | None | Read-only | Private | F8 |

---

## I. Security, privacy, and abuse risks

- **PII exposure** in uploaded CVs, certificates, IDs
- **Document upload** malware, oversized files, untrusted parsers
- **Fake evidence** (forged PDFs, screenshots)
- **Misleading verification** language (highest product risk)
- **Credential fraud** / stolen documents
- **Overtrust in AI extraction** from documents (must stay `document_extracted`, never verified)
- **Correlation risk** across subjects, jobs, and documents
- **Public sharing risk** if URLs leak
- **Reviewer abuse** if review roles are weak
- **Deletion/retention** gaps for GDPR-style erasure
- **Minor-user** safety: extra caution on documents and sharing

Mitigations belong in F3/F6/F7/F9 — not F0.

---

## J. Proposed 0053 slice ladder

### 0053-F0 Planning and Boundary Audit
- **Purpose:** This document; inventory; ladder; no-go list  
- **Allowed:** docs only  
- **Forbidden:** code, migrations, UI, routes  
- **Tests:** docs-only / scope / foundation smoke  
- **Browser:** not required  
- **Gate:** owner accepts plan  
- **Deferred:** all implementation  

### 0053-F1 Claim Service Contract Boundary
- **Status:** Implemented (`contracts.py`, `display.py`, create-time allowlists in `create_claim`)  
- **Purpose:** Lock claim contracts, status axes, forbidden silent upgrades, UI wording map; clarify subject linkage  
- **Create allowlist:** `verification_status=unverified` only; `support_status` ∈ {`not_provided`, `profile_supported`, `source_linked`}  
- **Create denylist:** verified/rejected/conflicting/unknown verification; evidence_backed/assessment_demonstrated/unknown support  
- **Source/snapshot:** provenance only; `source_linked` requires `source_id`; snapshot requires source; never implies verified  
- **Allowed:** claims contracts/tests/docs; **no** public `/api/v1/claims` routes  
- **Forbidden:** evidence tables, uploads, Passport verification UI, public sharing, migrations  
- **Tests:** unit + boundary + display language  
- **Browser:** smoke only (no UI change)  
- **Gate:** contracts accepted; no trust creep  
- **Deferred:** evidence persistence (F2)  
- **Evidence:** `~/Desktop/CareerKundi_0053_F1_Claim_Service_Contract_Boundary_Evidence.txt`

### 0053-F2 Evidence Domain Skeleton
- **Status:** Implemented (`platform/evidence/`, `EvidenceRecord`, `ClaimEvidenceLink`, `f0009_evidence_foundation`)  
- **Purpose:** Private evidence metadata + claim-evidence link foundation  
- **Allowed:** evidence models/migrations/service/contracts/tests/docs  
- **Forbidden:** upload/download endpoints, file bytes, OCR, verification workflow, public sharing, HTTP routes, frontend, Passport/CV/Roadmap/Job Search changes  
- **Hard rule:** linking evidence does **not** mutate claim `support_status` / `verification_status`  
- **Privacy:** `private` (default) / `sensitive` / `restricted` only — no public  
- **Tests:** contracts + service + migration + no-routes guards  
- **Browser:** smoke only (no UI change)  
- **Gate:** foundation head `f0009_evidence_foundation`; no trust overclaim  
- **Deferred:** private HTTP API (F3); upload bytes pipeline  
- **Evidence:** `~/Desktop/CareerKundi_0053_F2_Evidence_Domain_Skeleton_Evidence.txt`

### 0053-F3 Private Evidence Service/API Boundary
- **Status:** Implemented (`/api/v1/evidence` create/list/get/subject/link; schemas; ownership helpers)  
- **Purpose:** Authenticated private evidence metadata + claim-link API (no public sharing)  
- **Allowed:** private evidence routes + ownership checks; safe labels/warnings  
- **Forbidden:** upload/download, public sharing, verification stamps, frontend UI, Passport panel  
- **Hard rule:** link endpoint does **not** mutate claim `support_status` / `verification_status`  
- **Tests:** API ownership + contracts + platform regression  
- **Browser:** page smoke only (no UI change)  
- **Gate:** owner-only access; cross-user 404  
- **Deferred:** F4 library UI / attachment storage decision  
- **Evidence:** `~/Desktop/CareerKundi_0053_F3_Private_Evidence_API_Boundary_Evidence.txt`

### 0053-F4 Private Evidence Library UI / Attachment Storage Decision
- **Status:** Implemented (`/evidence` metadata UI; `evidenceApi`; storage decision doc; no upload)  
- **Purpose:** Private Evidence Library using F3 metadata APIs; document F5 storage requirements  
- **Allowed:** FE route/page, API client/types, create/list metadata, safe wording, nav entry, storage decision doc  
- **Forbidden:** file upload/download/preview, storage backend, Passport evidence panel, claim UUID linker, verification, public sharing  
- **Storage decision:** see `docs/product/careerkundi_0053_f4_attachment_storage_decision.md`  
- **Tests:** EvidenceLibraryPage vitest + backend evidence API regression  
- **Browser:** `/evidence` + existing page smoke  
- **Gate:** metadata-only UI; no trust overclaim  
- **Deferred:** F5 attachment storage backend  
- **Evidence:** `~/Desktop/CareerKundi_0053_F4_Private_Evidence_Library_UI_Evidence.txt`

### 0053-F5 Attachment Storage Backend
- **Status:** Implemented (local private storage + owner-only upload/download APIs)  
- **Purpose:** Persist one private file per EvidenceRecord; update storage_uri/hash/mime/size  
- **Allowed:** `LocalEvidenceStorage`, `POST/GET …/attachment`, size/MIME/SHA-256 guards, path containment  
- **Forbidden:** frontend upload UI (until F6), public/signed URLs, OCR/parsing, virus-scan engine, verification, Passport/CV/Roadmap/Jobs integrations, LLM file review  
- **Hard rule:** upload does **not** mutate claim `support_status` / `verification_status`  
- **Tests:** storage unit + attachment API + evidence/claims regression  
- **Browser:** page smoke only in F5  
- **Gate:** auth + owner scoping; cross-user 404; no public URL  
- **Deferred:** virus scan; cloud object store  
- **Evidence:** `~/Desktop/CareerKundi_0053_F5_Attachment_Storage_Backend_Evidence.txt`

### 0053-F6 Evidence Upload UI
- **Status:** Implemented (`/evidence` attach + download UI; `uploadEvidenceAttachment` / `downloadEvidenceAttachment`)  
- **Purpose:** Private file attachment UI against F5 APIs on Evidence Library only  
- **Allowed:** file input, Attach private file, Download private attachment, client size/MIME guards, safe wording  
- **Forbidden:** public URLs, OCR/parsing, verification, Passport/CV/Roadmap/Jobs integrations, LLM file review, backend storage changes  
- **Hard rule:** upload ≠ verified; Not independently verified preserved  
- **Tests:** EvidenceLibraryPage vitest + backend attachment regression  
- **Browser:** `/evidence` + existing page smoke (uvicorn badge-seed timeout remains a watch item)  
- **Gate:** private-only; no trust overclaim  
- **Deferred:** F7 linking / Passport evidence read; malware scan  
- **Evidence:** `~/Desktop/CareerKundi_0053_F6_Evidence_Upload_UI_Evidence.txt`

### 0053-F7 Evidence-to-Claim Linking UI
- **Status:** Implemented (`GET /evidence/linkable-claims`, `GET /evidence/{id}/links`, Evidence Library claim selector)  
- **Purpose:** Link private evidence to current-user claims without verification overclaim  
- **Allowed:** evidence-scoped claim selector; supports/contests/context; existing links display; safe wording  
- **Forbidden:** `/api/v1/claims`, claim creation UI, claim axis auto-upgrade, Passport evidence panel, public sharing, OCR, LLM verification  
- **Hard rule:** linking ≠ verified; support_status / verification_status unchanged  
- **Tests:** linking API + EvidenceLibraryPage vitest + evidence/claims regression  
- **Browser:** `/evidence` + page smoke (uvicorn badge-seed timeout remains a watch item)  
- **Gate:** current-user ownership; cross-user 404  
- **Deferred:** F8 Passport read-only evidence panel; review workflow  
- **Evidence:** `~/Desktop/CareerKundi_0053_F7_Evidence_To_Claim_Linking_UI_Evidence.txt`

### 0053-F8 Passport Read-Only Evidence Panel
- **Status:** Implemented (`GET /evidence/private-awareness-summary` + PassportEvidencePanel on `/passport`)  
- **Purpose:** Private read-only evidence-linked claim awareness inside Career Passport  
- **Allowed:** evidence-scoped summary API; Passport FE panel; Open Evidence Library link; safe labels  
- **Forbidden:** Passport upload/download/link/verify; claim creation; claim axis mutation; public sharing; OCR; LLM verification  
- **Hard rule:** Passport does not own evidence; linking ≠ verified; no “Verified Passport”  
- **Tests:** passport-summary API + PassportEvidencePanel vitest + evidence/claims/Passport regression  
- **Browser:** `/passport` + page smoke (uvicorn badge-seed timeout remains a watch item)  
- **Gate:** current-user ownership; no storage path / public URL exposure  
- **Deferred:** F10 review-request skeleton / hardening (F9 contracts done)  
- **Evidence:** `~/Desktop/CareerKundi_0053_F8_Passport_Read_Only_Evidence_Panel_Evidence.txt`

### 0053-F9 Review/Verification State Machine Planning + Contract Skeleton
- **Status:** Implemented (`backend/app/platform/verification/` + `careerkundi_0053_f9_verification_state_machine.md`)  
- **Purpose:** Define review states, actors, transitions, and mapping rules before any review workflow  
- **Allowed:** pure domain contracts, safe labels, transition tests, policy doc  
- **Forbidden:** VerificationReview DB/migration; verification API/UI; claim status mutation; Passport/Evidence verify buttons; public sharing; OCR; LLM verification  
- **Hard rule:** upload/link/source ≠ verification; claim verification changes require future explicit review service  
- **Tests:** state machine + display language + no routes/UI boundary  
- **Browser:** no UI change; page smoke only  
- **Gate:** no user can mark anything verified after F9  
- **Deferred:** F11 review-request UI / hardening (F10 backend done)  
- **Evidence:** `~/Desktop/CareerKundi_0053_F9_Verification_State_Machine_Planning_Evidence.txt`

### 0053-F10 Review Request Backend Skeleton
- **Status:** Implemented (`review_requests`, `f0010_review_request_foundation`, `/api/v1/review-requests`)  
- **Purpose:** Private user request/cancel for owned claims without verification power  
- **Allowed:** model/migration/service/API for request/list/get/cancel; safe wording  
- **Forbidden:** approve/reject/conflict; claim status mutation; verification UI; public sharing; OCR; LLM verification  
- **Hard rule:** review request ≠ verification  
- **Tests:** service + API + migration + no-verification-power + F9/evidence/claims regression  
- **Browser:** no FE change; page smoke only  
- **Gate:** current-user ownership; duplicate active request rejected  
- **Deferred:** F11 review-request UI or evidence hardening  
- **Evidence:** `~/Desktop/CareerKundi_0053_F10_Review_Request_Backend_Skeleton_Evidence.txt`

### 0053-F11 Review Request UI
- **Status:** Implemented (PassportEvidencePanel request/cancel + `reviewRequestApi`)  
- **Purpose:** Private user request/cancel UI for evidence-linked claims on Passport  
- **Allowed:** FE types/client; Passport panel state merge by `claim_id`; request/cancel; safe wording; tests/docs  
- **Forbidden:** approve/reject/conflict UI; reviewer/admin/issuer UI; claim status mutation; “Verified Passport”; public sharing; Passport upload/download; CV/Roadmap/Jobs review UI; OCR; LLM verification  
- **Hard rule:** review request ≠ verification; only “Not independently verified” for verified wording  
- **Tests:** PassportEvidencePanel vitest + boundary audit + Evidence Library + F10/F9/evidence/claims regression  
- **Browser:** `/passport` request/cancel + page smoke (uvicorn badge-seed timeout remains a watch item)  
- **Gate:** no claim axis mutation; no verify/approve/reject/share controls  
- **Deferred:** F12 review intake hardening or evidence hardening  
- **Evidence:** `~/Desktop/CareerKundi_0053_F11_Review_Request_UI_Evidence.txt`

### 0053-F12 Review Intake Hardening
- **Status:** Implemented (service eligibility + note/reason bounds + Passport intake copy)  
- **Purpose:** Harden review-request create path before any reviewer workflow  
- **Allowed:** owned claim + linked private evidence required; note/reason trim and length limits; safe errors; Passport copy/error handling; tests/docs  
- **Forbidden:** approve/reject/conflict; claim status mutation; verification result; public sharing; OCR; malware scan implementation; LLM verification  
- **Hard rule:** intake hardening ≠ verification; malware scan remains deferred  
- **Tests:** review intake hardening + review-request API/service + F9/evidence/claims + Passport vitest  
- **Browser:** `/passport` intake copy + page smoke (uvicorn badge-seed timeout remains a watch item)  
- **Gate:** no claim axis mutation; no new verification routes  
- **Deferred:** F13 evidence attachment hardening / malware scan planning  
- **Evidence:** `~/Desktop/CareerKundi_0053_F12_Review_Intake_Hardening_Evidence.txt`

### 0053-F13 Evidence Attachment Safety / Malware Scan Planning
- **Status:** Implemented (`attachment_safety.py` + derived API fields + Evidence/Passport warnings)  
- **Purpose:** Make malware-scan gap explicit and safe before any reviewer workflow  
- **Allowed:** domain safety states/labels/warning; derived response fields; FE warnings; tests/docs  
- **Forbidden:** scan engine; ClamAV/VirusTotal; quarantine storage; parsing/OCR/LLM review; DB migration; approve/reject; claim mutation; public sharing  
- **Hard rule:** uploaded attachment is not scanned, not reviewed, and not verified in F13  
- **Tests:** attachment safety contracts + evidence/passport/review regressions + FE vitest  
- **Browser:** `/evidence` + `/passport` warnings + page smoke (uvicorn badge-seed watch remains)  
- **Gate:** no scanner; default `scan_not_available`; review intake still does not require scan pass  
- **Deferred:** F14 attachment deletion/retention or scan queue skeleton  
- **Evidence:** `~/Desktop/CareerKundi_0053_F13_Attachment_Safety_Planning_Evidence.txt`

### 0053-F14 Private Attachment Deletion + Retention Policy
- **Status:** Implemented (`DELETE .../attachment` + Evidence Library remove UI + retention doc)  
- **Purpose:** Let owners remove private attachment bytes and clear attachment metadata safely  
- **Allowed:** owner-only delete endpoint; storage delete helper; clear `storage_uri`/`content_hash`/`mime_type`/`size_bytes`; Evidence Library remove UI; retention policy docs; tests  
- **Forbidden:** EvidenceRecord deletion; ClaimEvidenceLink/ReviewRequest deletion; claim status mutation; scan engine; parsing/OCR/LLM review; public sharing; DB migration  
- **Hard rule:** deleting an attachment is not verification and does not change claim trust state  
- **Tests:** attachment delete API + storage + evidence/passport/review regressions + FE vitest  
- **Browser:** `/evidence` remove attachment; Passport remains read-only (uvicorn badge-seed watch remains)  
- **Gate:** file bytes removed; metadata/links/reviews/claim statuses retained; no scanner  
- **Deferred:** F15 scan queue skeleton or runtime badge-seed fix  
- **Evidence:** `~/Desktop/CareerKundi_0053_F14_Attachment_Deletion_Retention_Evidence.txt`

### 0053-F15 Runtime Badge-Seed Startup Reliability Fix
- **Status:** Implemented (skip-safe seed + lifespan timeout bound)  
- **Purpose:** Fix local uvicorn/OpenAPI readiness blocked by badge catalogue seed  
- **Allowed:** idempotent/fast badge seed; startup timeout guard; tests/docs  
- **Forbidden:** new badge product features; evidence/review/Passport changes; claim mutation; scan queue; malware scan; LLM provider changes; DB migration  
- **Hard rule:** no product trust-state change; OpenAPI must become ready even if badge seed stalls  
- **Tests:** `platform/badges/tests/test_badge_seed_startup.py` + evidence/review/claims regressions  
- **Browser:** uvicorn OpenAPI `/api/openapi.json` readiness + page smoke  
- **Gate:** foundation head remains `f0010_review_request_foundation`  
- **Deferred:** F16 scan queue skeleton / evidence scanner planning  
- **Evidence:** `~/Desktop/CareerKundi_0053_F15_Runtime_Badge_Seed_Fix_Evidence.txt`

### 0053-F16 Attachment Scan Queue Skeleton
- **Status:** Implemented (`attachment_scan_jobs` + internal `attachment_scan_queue.py`)  
- **Purpose:** DB-backed private scan queue foundation before any scanner engine  
- **Allowed:** model/migration `f0011_attachment_scan_queue`; enqueue/list/get/cancel helpers; tests/docs  
- **Forbidden:** scan worker/engine; ClamAV/VirusTotal; quarantine; parsing/OCR/LLM review; scan API route; scan UI; claim/evidence/review mutation; public sharing  
- **Hard rule:** a queued scan job is not a completed scan and is not verification; public safety remains `scan_not_available`  
- **Tests:** scan queue + migration + attachment safety + evidence/review/claims/badge regressions  
- **Browser:** no scan controls; OpenAPI has no `/scan` route  
- **Gate:** foundation head `f0011_attachment_scan_queue`; no scanner imports  
- **Deferred:** F17 scan worker planning / quarantine policy  
- **Evidence:** `~/Desktop/CareerKundi_0053_F16_Attachment_Scan_Queue_Skeleton_Evidence.txt`

### 0053-F17 Scan Worker Contract + Quarantine Policy
- **Status:** Implemented (pure `attachment_scan_worker.py` + `attachment_quarantine_policy.py`)  
- **Purpose:** Define future scan worker result mapping and quarantine policy without running a scanner  
- **Allowed:** contract enums/dataclasses; update plans (`apply_to_database=False`); quarantine policy helpers; tests/docs  
- **Forbidden:** worker loop; startup registration; ClamAV/VirusTotal; file I/O; OCR/parsing/LLM review; quarantine move/delete; scan route/UI; claim mutation; DB migration  
- **Hard rule:** a scan plan is not verification; quarantine is planned but not active  
- **Tests:** worker contract + quarantine policy + F16 queue/safety + evidence/review/claims/badge regressions  
- **Browser:** no scan/quarantine controls; OpenAPI unchanged for scan routes  
- **Gate:** scanner availability unavailable; no f0012 migration  
- **Deferred:** F18 scanner adapter interface + no-op adapter  
- **Evidence:** `~/Desktop/CareerKundi_0053_F17_Scan_Worker_Quarantine_Policy_Evidence.txt`

### 0053-F18 Scanner Adapter Interface + No-Op Adapter
- **Status:** Implemented (`attachment_scanner_adapter.py` — protocol + no-op only)  
- **Purpose:** Define the scanner adapter seam and ship a no-op unavailable adapter that never scans  
- **Allowed:** adapter protocol; `NoopUnavailableScannerAdapter`; factory returning no-op; capability metadata; F17 `ScanResultContract` mapping tests; docs  
- **Forbidden:** real scanner engine; ClamAV/VirusTotal; worker loop; file I/O; OCR/parsing/LLM review; scan route/UI; claim mutation; DB apply; f0012 migration  
- **Hard rule:** a no-op adapter is not a scanner and is not verification; verdict is always `not_run`  
- **Tests:** adapter + F17 worker/quarantine + F16 queue/safety + evidence/review/claims/badge regressions  
- **Browser:** no scan controls; OpenAPI has no `/scan` route  
- **Gate:** factory returns no-op only; no file-byte access; no external scanner imports  
- **Deferred:** F19 local scanner integration planning  
- **Evidence:** `~/Desktop/CareerKundi_0053_F18_Scanner_Adapter_Noop_Evidence.txt`

### 0053-F19 Local Scanner Integration Planning
- **Status:** Implemented (planning/policy only — `attachment_scanner_policy.py`)  
- **Purpose:** Decide and document the safest future local scanner path without enabling scanning  
- **Allowed:** policy constants/helpers; future requirements list; job-update boundaries; tests proving no-op remains; docs  
- **Forbidden:** real scanner adapter/engine; scanner packages; ClamAV/VirusTotal; worker loop; file I/O; OCR/parsing/LLM; scan route/UI; claim mutation; config enable toggles; f0012  
- **Hard rule:** a scanner integration plan is not scanning and is not verification; `REAL_SCANNER_ENABLED=False`  
- **Tests:** policy + adapter + F17/F16/safety + evidence/review/claims/badge regressions  
- **Browser:** no scan controls; OpenAPI unchanged for scan routes  
- **Gate:** factory still no-op; future family `local_process_scanner`; no dependency changes  
- **Deferred:** F20 disabled local scanner adapter skeleton  
- **Evidence:** `~/Desktop/CareerKundi_0053_F19_Local_Scanner_Integration_Planning_Evidence.txt`

### 0053-F20 Disabled Local Scanner Adapter Skeleton
- **Status:** Implemented (`attachment_local_scanner_adapter.py` — disabled scaffold only)  
- **Purpose:** Add a disabled local-process adapter skeleton that cannot scan  
- **Allowed:** `DisabledLocalProcessScannerAdapter`; unavailable/not_run results; factory remains no-op; tests/docs  
- **Forbidden:** subprocess execution; ClamAV/VirusTotal; scanner packages; file I/O; OCR/parsing/LLM; worker loop; scan route/UI; claim mutation; enable toggles; f0012  
- **Hard rule:** disabled skeleton is not an active scanner and is not verification; factory stays no-op  
- **Tests:** local adapter + policy/adapter + F17/F16/safety + evidence/review/claims/badge regressions  
- **Browser:** no scan controls; OpenAPI unchanged for scan routes  
- **Gate:** `REAL_SCANNER_ENABLED=False`; no-op remains active; no dependency changes  
- **Deferred:** F21 local scanner runtime safety contract  
- **Evidence:** `~/Desktop/CareerKundi_0053_F20_Disabled_Local_Scanner_Adapter_Evidence.txt`

### 0053-F21 Local Scanner Runtime Safety Contract
- **Status:** Implemented (`attachment_scanner_runtime_policy.py` — contracts only)  
- **Purpose:** Define disabled-by-default runtime safety rails for a future local scanner  
- **Allowed:** runtime/command/output policy helpers; timeout bounds; safe error normalization; redaction; tests/docs  
- **Forbidden:** command execution; subprocess; ClamAV/VirusTotal; packages; file I/O; OCR/parsing/LLM; worker loop; scan route/UI; claim mutation; enable toggles; f0012  
- **Hard rule:** a runtime contract is not scanner execution and is not verification; `LOCAL_SCANNER_RUNTIME_ENABLED=False`  
- **Tests:** runtime policy + F20 local adapter + F19/F18/F17/F16/safety + evidence/review/claims/badge regressions  
- **Browser:** no scan controls; OpenAPI unchanged for scan routes  
- **Gate:** factory still no-op; shell/network disallowed; allowed binaries empty  
- **Deferred:** F22 scanner result persistence guard  
- **Evidence:** `~/Desktop/CareerKundi_0053_F21_Local_Scanner_Runtime_Safety_Contract_Evidence.txt`

### 0053-F22 Scanner Result Persistence Guard
- **Status:** Implemented (`attachment_scan_result_persistence.py` — AttachmentScanJob only)  
- **Purpose:** Guarded internal apply of explicit persistable scan-job update plans  
- **Allowed:** transition validation; F21 safe error normalization; apply to AttachmentScanJob fields only; tests/docs  
- **Forbidden:** scanner execution; subprocess; packages; file I/O; OCR/parsing/LLM; quarantine storage; scan route/UI; Evidence/Claim/Review mutation; f0012  
- **Hard rule:** persisting a scan-job result is not verification; no-op/disabled plans are never persisted  
- **Tests:** persistence guard + F21–F16/safety + evidence/review/claims/badge regressions  
- **Browser:** no scan controls; OpenAPI unchanged for scan routes  
- **Gate:** `apply_to_database=True` required; quarantined status rejected; public safety stays `scan_not_available`  
- **Deferred:** F23 quarantine storage planning  
- **Evidence:** `~/Desktop/CareerKundi_0053_F22_Scanner_Result_Persistence_Guard_Evidence.txt`

### 0053-F23 Quarantine Storage Planning
- **Status:** Implemented (`attachment_quarantine_storage.py` — disabled contract only)  
- **Purpose:** Define future quarantine storage contract while keeping storage inactive  
- **Allowed:** disabled flags/plan/decision helpers; safe warning; F17 policy reference; tests/docs  
- **Forbidden:** quarantine directory; file move/copy/delete; scanner execution; subprocess; packages; file I/O; OCR/parsing/LLM; scan/quarantine route/UI; Evidence/Claim/Review mutation; f0012; allowing `quarantined` persistence  
- **Hard rule:** a quarantine contract is not quarantine enforcement and is not verification  
- **Tests:** quarantine storage + F22–F16/safety + evidence/review/claims/badge regressions  
- **Browser:** no scan/quarantine controls; OpenAPI unchanged for scan/quarantine routes  
- **Gate:** all storage flags `False`; no `evidence_quarantine/` directory; F22 still rejects `quarantined`  
- **Deferred:** F24 quarantine event/audit planning  
- **Evidence:** `~/Desktop/CareerKundi_0053_F23_Quarantine_Storage_Planning_Evidence.txt`

### 0053-F24 Quarantine Event/Audit Planning
- **Status:** Implemented (`attachment_quarantine_audit.py` — disabled sink only)  
- **Purpose:** Define future scan/quarantine audit event types and a disabled audit sink  
- **Allowed:** safe event types; metadata-only payloads; F21 redaction; disabled sink result; tests/docs  
- **Forbidden:** audit DB/table; file log; routes/UI; scanner/quarantine enforcement; subprocess; packages; file I/O; OCR/parsing/LLM; Evidence/Claim/Review mutation; f0012; auto-emit from persistence  
- **Hard rule:** an audit contract is not audit persistence and is not verification  
- **Tests:** quarantine audit + F23–F16/safety + evidence/review/claims/badge regressions  
- **Browser:** no scan/quarantine/audit controls; OpenAPI unchanged for those routes  
- **Gate:** all audit flags `False`; sink returns `persisted=False`; no audit files/dirs  
- **Deferred:** F25 scan/quarantine admin boundary planning  
- **Evidence:** `~/Desktop/CareerKundi_0053_F24_Quarantine_Audit_Planning_Evidence.txt`

### 0053-F25 Scan/Quarantine Admin Boundary Planning
- **Status:** Implemented (`attachment_scan_admin_boundary.py` — disabled surface only)  
- **Purpose:** Define future scan/quarantine admin-operations boundary and forbidden powers  
- **Allowed:** disabled flags/plan/role/action enums; safe warning; summary; tests/docs  
- **Forbidden:** admin routes/UI/workflows; scanner/quarantine/audit activation; subprocess; packages; file I/O; OCR/parsing/LLM; Evidence/Claim/Review mutation; f0012; trust/verify powers  
- **Hard rule:** an admin boundary contract is not an admin feature and is not verification  
- **Tests:** admin boundary + F24–F16/safety + evidence/review/claims/badge regressions  
- **Browser:** no scan/quarantine/audit/admin controls; OpenAPI unchanged for those routes  
- **Gate:** all admin flags `False`; forbidden list includes verify/mark-safe/publish/expose  
- **Deferred:** F26 scanner worker dry-run planning  
- **Evidence:** `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt`

### 0053-F26 Scanner Worker Dry-Run Planning
- **Status:** Implemented (`attachment_scan_worker_dry_run.py` — disabled runner only)  
- **Purpose:** Define future scanner-worker dry-run decisions while keeping the runner inactive  
- **Allowed:** disabled flags/plan/decision helpers; safe warning; summary; tests/docs  
- **Forbidden:** worker loop; startup registration; scheduler; DB mutation; file access; scanner execution; audit emit; routes/UI; F22 auto-apply; Evidence/Claim/Review mutation; f0012  
- **Hard rule:** a dry-run contract is not a worker feature and is not verification  
- **Tests:** dry-run + F25–F16/safety + evidence/review/claims/badge regressions  
- **Browser:** no worker/scan/quarantine/audit/admin controls; OpenAPI unchanged for those routes  
- **Gate:** all worker flags `False`; no `apply_scan_job_update_plan` / adapter calls from dry-run  
- **Deferred:** F27 scanner worker reservation guard  
- **Evidence:** `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt`

### 0053-F27 Scanner Worker Reservation Guard
- **Status:** Accepted and completed (`attachment_scan_worker_reservation.py` — reservation guard only)  
- **Purpose:** Guarded internal reserve of `AttachmentScanJob` for a future worker  
- **Allowed:** owner-scoped `queued` → `reserved`; hash snapshot match; attempt_count +1; set `started_at` if empty  
- **Forbidden:** worker loop; startup registration; scanner execution; file read; F22 auto-apply; audit emit; routes/UI; Evidence/Claim/Review mutation; f0012  
- **Hard rule:** reservation is not scanning and is not verification  
- **Tests:** reservation guard + F26–F16/safety + evidence/review/claims/badge regressions  
- **Browser:** no worker/scan/quarantine/audit/admin controls; OpenAPI unchanged for those routes  
- **Gate:** mutates `AttachmentScanJob` only; no adapter/persistence/audit/file access from reservation  
- **Evidence:** `~/Desktop/CareerKundi_0053_F27_Scanner_Worker_Reservation_Guard_Evidence.txt`  
- **Accepted decision:** `0053_F27_SCANNER_WORKER_RESERVATION_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_F28`

### 0053-F28 Scanner Worker Result Application Planning
- **Status:** Accepted and completed (planning/contract only; no application code)  
- **Purpose:** Lock the F29 worker result-application guard contract  
- **Allowed:** docs/governance; binding F29 transitions `reserved→completed|failed`; six-field idempotency; triple-hash; PostgreSQL one-txn lock/CAS  
- **Forbidden:** F29 implementation in this slice; scanner engine; worker loop; file read; Evidence/Claim/Review mutation; CANCEL/RESERVE/NO_OP in F29 surface; f0012; scan/quarantine/audit/admin UI  
- **Hard rule:** planning is not result application and is not verification  
- **Prototype refs:** P39, P40, P41, P46 as future UX context only  
- **Deferred (then implemented in F29):** F29 Scanner Worker Result Application Guard  
- **Plan doc:** `docs/product/careerkundi_0053_f28_scanner_worker_result_application_planning.md`  
- **Accepted decision:** `0053_F28_SCANNER_WORKER_RESULT_APPLICATION_PLAN_ACCEPTED_READY_FOR_F29`

### 0053-F29 Scanner Worker Result Application Guard
- **Status:** Accepted / completed  
- **Purpose:** Apply terminal scan-job results under locked F22 policy + triple-hash  
- **Allowed:** `AttachmentScanJob` only; `reserved→completed|failed`; exact-match soft replay; conflicting replay reject; PostgreSQL `FOR UPDATE` job→evidence  
- **Forbidden (preserved):** CANCEL_JOB/RESERVE_JOB/NO_OP in F29 surface; EvidenceRecord mutation; file read; worker loop; scanner engine; quarantine/audit/admin/UI; f0012  
- **Module:** `backend/app/platform/evidence/attachment_scan_worker_result_application.py`  
- **Doc:** `docs/product/careerkundi_0053_f29_scanner_worker_result_application_guard.md`  
- **Evidence:** `~/Desktop/CareerKundi_0053_F29_Scanner_Worker_Result_Application_Guard_Evidence.txt`  
- **Decision:** `0053_F29_SCANNER_WORKER_RESULT_APPLICATION_GUARD_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_F30_PLANNING`  
- **Hard rule:** result application is not scanning and is not verification  
- **Deferred:** scanner engine; worker loop; quarantine move; audit emission; admin/UI  
- **Prototype refs:** P39, P40, P41, P46 as future UX context only  

---

### 0053-F30 Scanner Worker Single-Job Orchestration Planning
- **Status:** Accepted / completed (planning + contract only; F31 not started)  
- **Purpose:** Lock the F31 contract for a single supplied-job orchestration callable: preflight → F27 reservation → adapter execution → F29 apply  
- **Preflight:** `adapter_info()` only — `availability=AVAILABLE`, `MALWARE_SCAN` present, `UNAVAILABLE` absent; no scan call / file read / DB  
- **Noop/unavailable (normal production):** return `scanner_unavailable|skipped_unavailable`; leave job queued; no F27/scan/F29; no attempt_count/started_at; no scan_error; no fake CLEAN/scan_passed  
- **Post-reservation failures:** `NOT_RUN`/unavailable/timeout/unsupported/error/malformed/operational Exception → persistable `MARK_ERROR` (F21-safe codes) applied only through F29  
- **Boundaries:** three separate — reservation txn / adapter execution with no active txn or lock / new F29 txn (separate short-lived `AsyncSession`s)  
- **Authoritative metadata:** input is owner_user_id + scan_job_id + expected hash only; evidence_id/hash/MIME/size from the reserved `AttachmentScanJob` (or owner-scoped reload); no caller metadata trusted; no file/storage read  
- **F29 rejection:** return `result_application_rejected`; no bypass/force/auto-cancel; DB unchanged; reserved row is a watch item  
- **Cancellation:** never swallow `asyncio.CancelledError`/`KeyboardInterrupt`/`SystemExit` (reserved-row crash-recovery watch item)  
- **Forbidden (F31):** job selection; SKIP LOCKED; polling; loop; startup; scheduler; real scanner; file/storage read; quarantine move; audit; routes; UI; claim/ReviewRequest/EvidenceRecord mutation; migration; lease/TTL/reclaim  
- **Doc:** `docs/product/careerkundi_0053_f30_scanner_worker_single_job_orchestration_planning.md`  
- **Evidence:** `~/Desktop/CareerKundi_0053_F30_Scanner_Worker_Single_Job_Orchestration_Plan_Acceptance_Evidence.txt`  
- **Decision:** `0053_F30_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_PLAN_ACCEPTED_READY_FOR_F31_PREPARATION`  
- **Next gate:** 0053-F31 Scanner Worker Single-Job Orchestration Guard (not started)  
- **Prototype refs:** P39, P40, P41, P46 as future UX context only  

---

## K. Hard no-go list (until specifically approved)

- Public Passport sharing / public URL / public profile
- Employer / university / government/license verification portals
- Credential wallet
- DID / blockchain / cryptographic VC issuance
- AI-only verification
- Automatic public trust score / Passport strength / completion pressure
- Treating taxonomy confidence as verification
- Cross-user evidence access

---

## L. Recommended immediate next slice

**0053-F1 Claim Service Contract Boundary** — after owner accepts this F0 plan.

F1 should resolve (or bound) open questions:

1. Claim vs Passport materialization strategy  
2. Whether `evidence_backed` enum token is renamed or UI-mapped to Evidence-linked  
3. Subject linkage / lazy subject create rules  
4. Whether F1 ships any HTTP routes or contracts-only  
5. Separation from job-search “evidence slot” modules  

---

## Open questions (carry to F1)

1. Do Passport section saves ever auto-create `ClaimRecord` rows, or only explicit “assert as claim”?  
2. Evidence storage: DB URI vs object store; who owns encryption keys?  
3. Can support_status upgrade automatically when a link is created? (**Plan default: no**)  
4. Who may set `verification_status` ≠ `unverified` in the first year of product?  
5. Is `/proof` the same as evidence library, or a separate skills-proof surface (0060)?  
6. How do we delete evidence when a user deletes their account (F9)?  

---

*Document created: 0053-F0 — planning only. No code, migrations, routes, or UI shipped.*
