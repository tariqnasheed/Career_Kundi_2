# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F30 Scanner Worker Single-Job Orchestration Planning** (accepted) |
| Current Status | F29 accepted; F30 planning accepted; F31 implementation not started |
| Last Completed Slice | **0053-F30** · F29 · F28 · F27 · F26 · F25 · F24 · F23 · F22 · F21 · F20 · F19 · F18 · F17 · F16 · F15 · F14 · F13 · F12 · F11 · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F30 status | **F0–F30 accepted; F31 not started** |
| Last Commit | This commit — `docs(evidence): accept scanner single-job orchestration plan` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F31 Scanner Worker Single-Job Orchestration Guard** (not started); configured adapter remains noop/unavailable |
| Browser viewports | No worker/scan/quarantine/audit/admin UI |
| Blocked Items | None for F29 review |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F29 does not call LLM |
| Foundation head | `f0011_attachment_scan_queue` (unchanged; no F30 migration) |
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
| F29 result application guard | `docs/product/careerkundi_0053_f29_scanner_worker_result_application_guard.md` |
| F30 single-job orchestration plan | `docs/product/careerkundi_0053_f30_scanner_worker_single_job_orchestration_planning.md` |

**Pointers:** **0053-F27** Accepted · **0053-F28** Accepted · **0053-F29** Accepted · **0053-F30** Accepted (plan).

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F24 | Quarantine Event/Audit Planning | Done | `~/Desktop/CareerKundi_0053_F24_Quarantine_Audit_Planning_Evidence.txt` | `d8b2f316` | Yes | Disabled sink |
| 0053-F25 | Scan/Quarantine Admin Boundary Planning | Done | `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt` | `d88a99f5` | Yes | Disabled surface |
| 0053-F26 | Scanner Worker Dry-Run Planning | Done | `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt` | `ef2682f7` | Yes | Disabled runner |
| 0053-F27 | Scanner Worker Reservation Guard | Accepted / completed | `~/Desktop/CareerKundi_0053_F27_Scanner_Worker_Reservation_Guard_Evidence.txt` | `8fec0617` | Yes | queued→reserved |
| 0053-F28 | Scanner Worker Result Application Planning | Accepted / completed | `~/Desktop/CareerKundi_0053_F28_Prototype_Governance_And_Plan_Acceptance_Evidence.txt` | `a3e7b153` | Yes | Plan only |
| 0053-F29 | Scanner Worker Result Application Guard | Accepted / completed | `~/Desktop/CareerKundi_0053_F29_Scanner_Worker_Result_Application_Guard_Evidence.txt` | `296f174f` | Yes | reserved→completed\|failed |
| 0053-F30 | Scanner Worker Single-Job Orchestration Planning | Accepted / completed | `~/Desktop/CareerKundi_0053_F30_Scanner_Worker_Single_Job_Orchestration_Plan_Acceptance_Evidence.txt` | This commit | With push | Plan only; preflight→F27→adapter→F29 |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-18 | 0053-F25 | `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt` | B ready for F26 | Disabled admin surface |
| 2026-07-18 | 0053-F26 | `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt` | B ready for F27 | Disabled worker dry-run |
| 2026-07-18 | 0053-F27 | `~/Desktop/CareerKundi_0053_F27_Scanner_Worker_Reservation_Guard_Evidence.txt` | Accepted | Reservation guard |
| 2026-07-19 | 0053-F28 | `~/Desktop/CareerKundi_0053_F28_Prototype_Governance_And_Plan_Acceptance_Evidence.txt` | Accepted | Governance + F28 plan |
| 2026-07-19 | 0053-F29 | `~/Desktop/CareerKundi_0053_F29_Scanner_Worker_Result_Application_Guard_Evidence.txt` | Accepted | Result application guard |
| 2026-07-19 | 0053-F30 | `~/Desktop/CareerKundi_0053_F30_Scanner_Worker_Single_Job_Orchestration_Plan_Acceptance_Evidence.txt` | Accepted | Single-job orchestration plan |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-18 | 0053-F25 | `d88a99f5` | Pushed | Scan admin boundary planning |
| 2026-07-18 | 0053-F26 | `ef2682f7` | Pushed | Scanner worker dry-run planning |
| 2026-07-18 | 0053-F27 | `8fec0617` | Pushed | Scanner worker reservation guard |
| 2026-07-19 | 0053-F28 | `a3e7b153` | Pushed | Prototype governance + F28 plan |
| 2026-07-19 | 0053-F29 | `296f174f` | Pushed | Scanner worker result application guard |
| 2026-07-19 | 0053-F30 | This commit | Push with this slice | Scanner single-job orchestration plan (accepted) |

---

## 6. Decision Updates

- F27: internal scan-job reservation guard only; owner-scoped queued→reserved; hash snapshot match; no scan/file/adapter/audit/route/UI.
- F28: accepted F29 contract — `reserved→completed|failed` only; six-field exact-match replay; triple-hash; PostgreSQL one-txn lock/CAS; no CANCEL/RESERVE/NO_OP in F29; no migration.
- F29: result application guard shipped — owner-scoped FOR UPDATE job→evidence; triple-hash; F22 policy reuse; six-field exact-match soft replay; no scanner/loop/quarantine/audit/admin/UI/migration. **Accepted.**
- F30: single-job orchestration plan accepted — preflight (adapter_info only: AVAILABLE + MALWARE_SCAN, no UNAVAILABLE) → F27 reservation → adapter execution with no held txn/lock → F29 apply; noop/unavailable leaves job queued (no F27/scan/F29, no attempt/started_at, no scan_error, no fake CLEAN); post-reservation failures → persistable MARK_ERROR (F21 codes) via F29; F29 rejection → result_application_rejected (DB unchanged); Cancelled/KeyboardInterrupt/SystemExit re-raised (reserved-row watch item); three separate short-lived sessions; authoritative snapshot from reserved job / reload only; F31 = one supplied-job callable; no selection/SKIP LOCKED/poll/loop/startup/scheduler/scanner/file/quarantine/audit/routes/UI/mutation/migration/lease.

---

## 7. Known Watch Items

- Real malware scan engine / worker loop / quarantine / audit / admin feature still not implemented (deferred)
- Configured adapter remains noop/unavailable until a later scanner-enablement phase
- Stuck-reserved recovery (after process interruption or F29 rejection) remains a watch item; no lease/TTL/reclaim in F31
- Pre-existing: `test_mapping_helper_not_imported_by_api_routes` scans `routes/tests/` (unrelated to F30)
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-19 — 0053-F30*
