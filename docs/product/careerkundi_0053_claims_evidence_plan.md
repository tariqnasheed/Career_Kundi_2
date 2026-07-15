# CareerKundi 0053 — Evidence, Claims, Provenance & Verification Plan

**Slice:** 0053-F0 Planning and Boundary Audit  
**Status:** Planning complete — no implementation in F0  
**Depends on:** 0052 Career & Education Passport (completed / accepted)  
**Foundation head (unchanged):** `f0008_passport_persistence`

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
- **Purpose:** Lock claim contracts, status axes, forbidden silent upgrades, UI wording map; clarify subject linkage  
- **Allowed:** claims contracts/tests/docs; no public routes unless thin and private  
- **Forbidden:** evidence tables, uploads, Passport verification UI, public sharing  
- **Tests:** unit + boundary  
- **Browser:** optional  
- **Gate:** contracts accepted; no trust creep  
- **Deferred:** evidence persistence  

### 0053-F2 Evidence Record Persistence
- **Purpose:** Evidence tables/models/migrations  
- **Allowed:** evidence models + migrations + tests  
- **Forbidden:** public URLs, verification outcomes, frontend upload UI (unless stub)  
- **Tests:** persistence + migration policy  
- **Browser:** no  
- **Gate:** foundation head advances safely  
- **Deferred:** upload bytes pipeline  

### 0053-F3 Private Evidence API MVP
- **Purpose:** Authenticated private evidence CRUD  
- **Allowed:** evidence routes + client types  
- **Forbidden:** public sharing, verification stamps  
- **Tests:** API ownership + empty/list  
- **Browser:** API smoke optional  
- **Gate:** owner-only access  
- **Deferred:** Passport UI  

### 0053-F4 Passport Evidence Read UI
- **Purpose:** Read-only Passport panel for evidence-linked states  
- **Allowed:** passport frontend read panel  
- **Forbidden:** mutation of verification; “Verified Passport”  
- **Tests:** FE + boundary audit  
- **Browser:** required  
- **Gate:** Private/Not independently verified preserved  
- **Deferred:** uploads in Passport  

### 0053-F5 Claim-to-Passport Linking
- **Purpose:** Safe links between Passport sections and claims  
- **Allowed:** link APIs + UI affordances  
- **Forbidden:** auto-verify; Subject picker expansion without approval  
- **Tests:** ownership + wording  
- **Browser:** required  
- **Gate:** Passport remains private/unverified by default  
- **Deferred:** review workflow  

### 0053-F6 Evidence Upload / Attachment References
- **Purpose:** Attachment refs + upload constraints  
- **Allowed:** storage refs, limits, virus-scan hooks if present  
- **Forbidden:** public CDN URLs without auth; AI auto-verify  
- **Tests:** upload/retention unit  
- **Browser:** required  
- **Gate:** private-only  
- **Deferred:** issuer verification  

### 0053-F7 Review and Verification State Machine
- **Purpose:** Explicit review outcomes (`under_review` → issuer/CK verified/rejected)  
- **Allowed:** verification module + restricted UI  
- **Forbidden:** self-serve “Verified by CareerKundi” without policy; public profiles  
- **Tests:** state machine + authz  
- **Browser:** required  
- **Gate:** independent axes preserved  
- **Deferred:** employer/university portals  

### 0053-F8 CV/Roadmap Evidence Awareness
- **Purpose:** Optional read-only summaries  
- **Allowed:** CV/Roadmap FE copy + reads  
- **Forbidden:** verified CV/roadmap claims; Passport mutation  
- **Tests:** payload boundaries  
- **Browser:** required  
- **Gate:** no passport_id ownership leakage  

### 0053-F9 Hardening, Privacy, Deletion and Final Regression
- **Purpose:** Retention, deletion, abuse, regression, close phase  
- **Allowed:** tests/docs/bounded repairs  
- **Forbidden:** new product features without approval  
- **Tests:** full FE/BE + browser  
- **Browser:** required  
- **Gate:** 0053 accepted with deferred watches  

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
