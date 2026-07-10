# CareerKundi privacy domain (0050-PF9-S1)

## Owns

- `PrivacyPolicyRef` / `ConsentRecordRef` / `RetentionPolicyRef`
- Controlled classification, visibility, purpose, consent, retention kinds
- Storage stubs: `privacy_policies`, `consent_records`, `retention_policies`
- Create/get/list service helpers

## Does not own

- Legal compliance engines (GDPR/DPDP)
- Rights-request workflows
- Data export / deletion automation
- Privacy admin console or frontend
- Public privacy API

## Semantics

| Concept | Meaning |
|---------|---------|
| Data classification | Sensitivity/risk class of data |
| Visibility | Who may see a record inside the product |
| Consent | Allowed processing/share/use for a purpose |
| Retention policy | Retention category / planned retain-until |

**Classification ≠ visibility ≠ consent ≠ retention.**

These primitives support future privacy/compliance workflows.
They do not by themselves make CareerKundi legally compliant.
