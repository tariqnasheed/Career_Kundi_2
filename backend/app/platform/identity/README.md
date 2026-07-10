# CareerKundi identity domain (0050-PF3-S1)

## Owns

- `ActorRef` / `ActorType` — who performs an action
- `SubjectRef` — career subject addressing
- `OrganizationRef` — future-safe org stub (no table yet)
- `CareerSubject` persistence + minimal subject API (application layer)

## Does not own

- User authentication / IAM / OIDC
- Profile / Passport biography fields
- Claims, evidence, provenance
- B2B membership, guardianship, delegation
- Taxonomy, geo, consent

## Semantics

| Concept | Meaning |
|---------|---------|
| User | Login/account (`users` table) |
| CareerSubject | Entity career records are *about* |
| Actor | Entity performing an action |
| Organization | Employer/agency/tenant (ref only in PF3-S1) |

**User ≠ Subject.** A user may own multiple subjects. `owner_user_id` is control, not identity equality.
