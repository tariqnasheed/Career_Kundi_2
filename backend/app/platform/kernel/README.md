# CareerKundi platform kernel (0050-PF2-S1)

## Kernel owns

- Canonical entity IDs (`CanonicalEntityId` / UUID helpers)
- External identifier value shape (`ExternalIdentifier`)
- Small domain-neutral shared typing for the platform package

## Kernel does not own

- User / account
- Actor / Subject / Organization
- Source / Snapshot
- Claim / Evidence
- Taxonomy content or mappings
- Geo / Jurisdiction / Locale
- Consent
- Audit persistence
- Workflow engines
- Agents / feature modules

## Phase ownership (do not dump here)

| Phase | Owns |
|-------|------|
| PF3 | Actor / Subject |
| PF4 | Source / Provenance / Freshness |
| PF5 | Claim doctrine |
| PF6 | Geo / Jurisdiction / Locale |
| PF7 | Thin lifecycle refs (Goal / Recommendation / Outcome) |

## Dependency policy

Kernel code is dependency-light: Python stdlib + typing only.
It must not import `app.agents`, `app.api`, `app.services`, feature domains,
or future platform domain packages beyond this kernel.
