# 0053-F14 — Private Attachment Deletion + Retention Policy

## What F14 adds

- `DELETE /api/v1/evidence/{evidence_id}/attachment` (owner-only)
- Clears attachment metadata fields after safe local file deletion
- Evidence Library “Remove private attachment” control + confirmation
- Retention/deletion policy notes for future cleanup

## What F14 does not add

- EvidenceRecord deletion
- ClaimEvidenceLink deletion
- ReviewRequest deletion
- Claim status mutation
- Malware scan engine / quarantine
- Parsing / OCR / LLM review
- Public sharing / Verified Passport
- DB migration

## Safety rule

**Deleting an attachment is not verification and does not change claim trust state.**

Evidence metadata and claim links remain after attachment removal.

## Retention / future requirements

- User-initiated deletion (this slice)
- Audit-safe event logging later, without raw file contents
- Retention windows to be decided later
- Orphaned-file cleanup later
- Backup deletion policy later
- Scanner quarantine/deletion policy later

## Next

**0053-F15** Scan Queue Skeleton or Runtime Badge-Seed Fix — only after F14 acceptance.
