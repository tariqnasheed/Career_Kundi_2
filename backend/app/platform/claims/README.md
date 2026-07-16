# CareerKundi claim domain (0050-PF5-S1 / 0053-F1)

## Owns

- `ClaimRef` — durable claim addressing
- `ClaimKind` / `ClaimOrigin` / `SupportStatus` / `VerificationStatus`
- `ClaimRecord` persistence + create/get/list service helpers
- **0053-F1 create-time contracts** (`contracts.py`)
- **Safe display labels** (`display.py`) for future UI wording

## Does not own

- Evidence items / `EvidenceRecord` / `ClaimEvidenceLink`
- Verification review workflows / `VerificationReview`
- Claim scoring / Passport UI
- Taxonomy mappings / skill graph
- Public FastAPI claim routes (`/api/v1/claims` — not in F1)
- Provenance fetch/storage (PF4)
- Passport / CV Builder / Roadmap / Job Search

## 0053-F1 create-time boundary

| Axis | Allowed at create | Disallowed at create |
|------|-------------------|----------------------|
| `verification_status` | `unverified` only | `verified`, `rejected`, `conflicting`, `unknown` |
| `support_status` | `not_provided`, `profile_supported`, `source_linked` | `evidence_backed`, `assessment_demonstrated`, `unknown` |

### Source / snapshot

- `snapshot_id` requires `source_id`
- `support_status=source_linked` requires `source_id`
- Source/snapshot links are **provenance only**
- Source/snapshot-linked claims **remain** `verification_status=unverified`
- No silent upgrade to `evidence_backed` or `verified`

### Display language

Use `display.py` labels. Support labels never say “verified”, “official”, “truth”, “trusted”, “wallet”, “blockchain”, or “DID”.

- `source_linked` → “Source-linked”
- `evidence_backed` (future only) → “Evidence-linked”
- `unverified` → “Not independently verified”

## Semantics

| Concept | Meaning |
|---------|---------|
| Claim | Statement asserted about a subject |
| Evidence | Material supporting/contesting a claim (later — F2+) |
| Verification | Assessment that a claim/evidence link was checked (later) |
| Source/Snapshot | Provenance primitives (PF4); optional claim links |

**Claim ≠ Evidence ≠ Verification ≠ Passport.**

Status axes are independent:

- `source_linked` ≠ `evidence_backed`
- `evidence_backed` ≠ `verified`
- `profile_supported` ≠ `verified`

No helper silently upgrades status. Local Ollama output is not verification.
