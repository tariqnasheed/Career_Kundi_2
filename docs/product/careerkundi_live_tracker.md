# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F28 Scanner Worker Result Application Planning** (accepted) |
| Current Status | F28 plan accepted; ready for F29 (implementation not started) |
| Last Completed Slice | **0053-F28** · F27 · F26 · F25 · F24 · F23 · F22 · F21 · F20 · F19 · F18 · F17 · F16 · F15 · F14 · F13 · F12 · F11 · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F28 status | **F0–F27 completed/accepted; F28 planning accepted** |
| Last Commit | This commit — `docs(prototype): adopt approved interface governance and F28 plan` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F29** Scanner Worker Result Application Guard (implementation not started) |
| Browser viewports | No worker/scan/quarantine/audit/admin UI |
| Blocked Items | None for F28; do not start F29 until explicitly approved |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F28 does not call LLM |
| Foundation head | `f0011_attachment_scan_queue` (unchanged; no F28/F29 migration) |
| Prototype refs | P39, P40, P41, P46 — future UX context only |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F27 reservation guard | `docs/product/careerkundi_0053_f27_scanner_worker_reservation_guard.md` |
| F27 acceptance / F28 handoff | `docs/product/careerkundi_0053_f27_acceptance_f28_handoff.md` |
| F28 result application plan | `docs/product/careerkundi_0053_f28_scanner_worker_result_application_planning.md` |

**Pointers:** **0053-F27** Accepted · **0053-F28** Accepted · Next **0053-F29**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F24 | Quarantine Event/Audit Planning | Done | `~/Desktop/CareerKundi_0053_F24_Quarantine_Audit_Planning_Evidence.txt` | `d8b2f316` | Yes | Disabled sink |
| 0053-F25 | Scan/Quarantine Admin Boundary Planning | Done | `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt` | `d88a99f5` | Yes | Disabled surface |
| 0053-F26 | Scanner Worker Dry-Run Planning | Done | `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt` | `ef2682f7` | Yes | Disabled runner |
| 0053-F27 | Scanner Worker Reservation Guard | Accepted / completed | `~/Desktop/CareerKundi_0053_F27_Scanner_Worker_Reservation_Guard_Evidence.txt` | `8fec0617` | Yes | queued→reserved |
| 0053-F28 | Scanner Worker Result Application Planning | Accepted / completed | `~/Desktop/CareerKundi_0053_F28_Prototype_Governance_And_Plan_Acceptance_Evidence.txt` | This commit | With push | Plan only |
| 0053-F29 | Scanner Worker Result Application Guard | Next | — | — | — | Not started |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-18 | 0053-F25 | `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt` | B ready for F26 | Disabled admin surface |
| 2026-07-18 | 0053-F26 | `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt` | B ready for F27 | Disabled worker dry-run |
| 2026-07-18 | 0053-F27 | `~/Desktop/CareerKundi_0053_F27_Scanner_Worker_Reservation_Guard_Evidence.txt` | Accepted | Reservation guard |
| 2026-07-19 | 0053-F28 | `~/Desktop/CareerKundi_0053_F28_Prototype_Governance_And_Plan_Acceptance_Evidence.txt` | Accepted | Governance + F28 plan |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-18 | 0053-F25 | `d88a99f5` | Pushed | Scan admin boundary planning |
| 2026-07-18 | 0053-F26 | `ef2682f7` | Pushed | Scanner worker dry-run planning |
| 2026-07-18 | 0053-F27 | `8fec0617` | Pushed | Scanner worker reservation guard |
| 2026-07-19 | 0053-F28 | This commit | Push with this slice | Prototype governance + F28 plan |

---

## 6. Decision Updates

- F27: internal scan-job reservation guard only; owner-scoped queued→reserved; hash snapshot match; no scan/file/adapter/audit/route/UI.
- F28: accepted F29 contract — `reserved→completed|failed` only; six-field exact-match replay; triple-hash; PostgreSQL one-txn lock/CAS; no CANCEL/RESERVE/NO_OP in F29; no migration; F29 not started.

---

## 7. Known Watch Items

- Real malware scan engine / worker loop / quarantine / audit / admin feature still not implemented (deferred past F29 guard)
- F29 implementation has not started
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-19 — 0053-F28*
