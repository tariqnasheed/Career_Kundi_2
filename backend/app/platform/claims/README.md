# CareerKundi claim domain (0050-PF5-S1)

## Owns

- `ClaimRef` — durable claim addressing
- `ClaimKind` / `ClaimOrigin` / `SupportStatus` / `VerificationStatus`
- `ClaimRecord` persistence + create/get/list service helpers

## Does not own

- Evidence items / verification workflows
- Claim scoring / passport UI
- Taxonomy mappings / skill graph
- Public FastAPI claim routes
- Provenance fetch/storage (PF4)

## Semantics

| Concept | Meaning |
|---------|---------|
| Claim | Statement asserted about a subject |
| Evidence | Material supporting/contesting a claim (later) |
| Verification | Assessment that a claim/evidence link was checked (later) |
| Source/Snapshot | Provenance primitives (PF4); optional claim links |

**Claim ≠ Evidence.** Optional `source_id`/`snapshot_id` means provenance linkage only.

Status axes are independent:

- `source_linked` ≠ `evidence_backed`
- `evidence_backed` ≠ `verified`
- `profile_supported` ≠ `verified`

No helper silently upgrades status.
