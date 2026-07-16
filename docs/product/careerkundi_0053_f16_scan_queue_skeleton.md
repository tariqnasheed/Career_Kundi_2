# 0053-F16 — Attachment Scan Queue Skeleton

## What F16 adds

- DB table `attachment_scan_jobs` (`f0011_attachment_scan_queue`)
- Internal service `attachment_scan_queue.py` (create/list/get/cancel)
- Job statuses: `queued`, `reserved`, `completed`, `failed`, `cancelled`
- New jobs use `job_status=queued` and job-row `attachment_safety_status=scan_pending`

## What F16 does not add

- Scanner engine / worker
- External scanner (ClamAV, VirusTotal, etc.)
- Quarantine storage
- File parsing / OCR / LLM review
- User-facing scan API route
- Frontend scan button
- Claim / evidence / review status mutation
- Public sharing

## Safety rule

**A queued scan job is not a completed scan and is not verification.**

Public EvidenceRead / Passport safety fields remain F13 defaults (`scan_not_available`).

## Future scanner slice must define

- Worker execution
- Timeout / retry
- Quarantine policy
- Safe user messaging
- Scanner failure policy

## Next

**0053-F17** Scan Worker Planning / Quarantine Policy — only after F16 acceptance.
