# 0053-F13 — Evidence Attachment Safety / Malware Scan Planning

## What F13 adds

- Domain `AttachmentSafetyStatus` + safe labels/warning (`attachment_safety.py`)
- Default derived status: `scan_not_available` (no scan engine)
- Evidence API + Passport summary derived fields:
  - `attachment_safety_status`
  - `attachment_safety_label`
  - `attachment_safety_warning`
- Evidence Library + Passport warnings that attachments are not malware-scanned, parsed, reviewed, or verified

## What F13 does not add

- Malware scan engine / ClamAV / VirusTotal / external scanners
- Quarantine storage
- File parsing / OCR / LLM file review
- Scan/rescan endpoints
- DB migration
- Approve/reject/conflict or claim status mutation
- Public sharing / Verified Passport

## Safety rule

**An uploaded attachment is not scanned, not reviewed, and not verified in F13.**

Review request remains not verification. Linked evidence is still required for intake; scan pass is not required.

## Future scanner requirements (not implemented)

- Private scan queue; no public file exposure
- Keep max size and MIME checks
- No raw bytes in logs
- Failure / quarantine policy
- Deletion / retention policy → **F14 implements user-initiated attachment deletion + retention notes**
- Scanner timeout / failure behavior
- User-safe messaging only

## Later slices

- **F14** Private attachment deletion + retention — accepted
- **F15** Runtime badge-seed startup reliability — accepted
- **F16** Attachment scan queue skeleton — accepted (queue only; still no scanner)
- **Next after F16:** **0053-F17** Scan Worker Planning / Quarantine Policy only
