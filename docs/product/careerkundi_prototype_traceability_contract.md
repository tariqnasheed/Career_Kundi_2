# CareerKundi Prototype-to-Repository Traceability Contract

## Required rule

No prototype sheet is considered implemented merely because a similar page exists. A sheet becomes implementation-backed only when its required behaviour is mapped to code, tests and accepted evidence.

## Required traceability record

Create or update one record per implementation slice:

```yaml
phase: "0053-Fxx"
status: "planned | implemented | evidence-reviewed | accepted"
prototype:
  pages: ["P39", "P40", "P41"]
  sheets:
    - "P39-A4-03"
    - "P39-A4-04"
current_repository:
  routes: []
  frontend_paths: []
  backend_paths: []
  models: []
  migrations: []
target_delta:
  included: []
  excluded: []
security:
  owner_scoping: ""
  evidence_verification_boundary: ""
  attachment_safety_boundary: ""
tests:
  unit: []
  integration: []
  frontend: []
  browser: []
evidence:
  file: ""
limitations: []
next_gate: ""
```

## Review questions

Before accepting a slice, answer:

1. Does the change implement only the approved prototype delta?
2. Is every current-path statement evidence-backed?
3. Are future paths clearly marked as proposed or create-required?
4. Are owner, privacy and verification boundaries preserved?
5. Are empty/loading/error/success states covered where relevant?
6. Are user-visible controls linked to real, tested actions?
7. Were unrelated prototype features left untouched?
8. Did the phase stop at its named gate?
