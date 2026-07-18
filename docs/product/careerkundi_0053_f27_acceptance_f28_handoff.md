# CareerKundi 0053-F27 Acceptance and 0053-F28 Handoff

## Accepted decision

`0053_F27_SCANNER_WORKER_RESERVATION_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_F28`

## Accepted repository state

- Worktree: `/Users/tariqnasheed/Desktop/Career_Kundi_2_F3`
- Branch: `main`
- Accepted HEAD: `8fec0617265e5cd03c41c4622bfc3c4dcbf76c5b`
- Accepted origin/main: `8fec0617265e5cd03c41c4622bfc3c4dcbf76c5b`
- Divergence: `0 0`
- Known local dirt only:
  - `.env`
  - `backend/.env`
  - `backend/data/knowledge_graph.gpickle`
  - `documents/`

## F27 accepted behaviour

- Reservation module: `attachment_scan_worker_reservation.py`
- Allowed row: `AttachmentScanJob`
- Allowed transition: `queued -> reserved`
- Owner-scoped lookup
- Hash snapshot guard without file read
- Attempt count increments once on successful reservation
- `started_at` is set when empty
- `completed_at`, safety status, engine fields and safe error fields remain untouched
- No persistence helper call from the reservation guard
- No scanner adapter or scanner execution
- No file, storage, subprocess, network, OCR, parsing or LLM access
- No worker loop, startup registration, scheduler, route, API or frontend worker/admin UI
- No EvidenceRecord, claim or ReviewRequest mutation
- No audit emission or public sharing
- Migration head remains `f0011_attachment_scan_queue`

## Relevant approved prototype references

These references are future UX context only and do not expand F28 scope:

- `P39` Evidence Library
- `P40` Claim Management and Evidence Linking
- `P41` Private Review Requests
- `P46` Empty, Loading, Error and Success State Library

For F28, the prototype must not be used to invent frontend scan, quarantine, audit or admin UI.

## F28 gate

Next phase: **0053-F28 Scanner Worker Result Application Planning**

F28 begins as a read-only planning and contract-definition task unless the user explicitly approves implementation.

F28 must preserve these boundaries:

- No real scan engine
- No worker loop or startup registration
- No scanner dependency
- No file read, subprocess, network or external process
- No OCR, document parsing or LLM review
- No quarantine move or storage mutation
- No audit emission
- No worker/admin/scan/quarantine/audit route or UI
- No EvidenceRecord, claim or ReviewRequest mutation unless a later accepted plan explicitly authorises it
- No public evidence sharing
- No wallet, DID or blockchain work

## F28 planning questions

Cursor must derive answers from repository evidence rather than assume them:

1. What result object or update plan already exists?
2. Which transitions from `reserved` are valid?
3. What fields may result application mutate?
4. What is the atomic persistence boundary?
5. How are stale reservations, owner mismatches and hash mismatches rejected?
6. How is idempotent replay handled?
7. Which engine and safe-error fields may be persisted?
8. When is `completed_at` set?
9. What retry/attempt semantics apply?
10. Is a migration required? Default assumption: no, unless evidence proves otherwise.
11. Which tests and evidence gates are required before any implementation?

Do not begin F28 implementation in the same task as this planning handoff.
