# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current accepted scanner checkpoint | **0053-F31 Scanner Worker Single-Job Orchestration Guard** (accepted) |
| Acceptance token | `0053_F31_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_GUARD_ACCEPTED_WITH_WATCH_ITEMS` |
| Last completed documentation task | **Programme 0.4** — complete and accepted (F31 governance reconciliation + F29/F31 evidence canonicalization) |
| Current Status | F31 accepted as current scanner checkpoint; F32 not started; Programme 1 not started |
| Last Completed Slice | **0053-F31** · F30 · F29 · F28 · F27 · F26 · F25 · F24 · F23 · F22 · F21 · F20 · F19 · F18 · F17 · F16 · F15 · F14 · F13 · F12 · F11 · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F31 status | **F0–F31 accepted** (F31 = current scanner checkpoint) |
| Official workspace | `/Users/tariqnasheed/Desktop/Career_Kundi_2` (former F3 worktree and hold branch retired) |
| Canonical F29 evidence | `docs/evidence/0053/CareerKundi_0053_F29_Scanner_Worker_Result_Application_Guard_Evidence.txt` |
| Canonical F31 evidence | `docs/evidence/0053/CareerKundi_0053_F31_Scanner_Worker_Single_Job_Orchestration_Guard_Evidence.txt` |
| Last Commit | `4c8abbd6` — F31 technical implementation already on `main` |
| Last Push Status | `origin/main` aligned (`0 0`) |
| Next gate | **Programme 1** (next authorized planning gate; not started). F32 not started. No scanner capability expansion authorized |
| Browser viewports | No worker/scan/quarantine/audit/admin UI |
| Blocked Items | None blocking Programme 1 planning authorization |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F31 does not call LLM |
| Foundation head | `f0011_attachment_scan_queue` (unchanged; no F31/F32 migration) |
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
| F31 single-job orchestration guard | `docs/product/careerkundi_0053_f31_scanner_worker_single_job_orchestration_guard.md` |

**Pointers:** **0053-F27** Accepted · **0053-F28** Accepted · **0053-F29** Accepted · **0053-F30** Accepted (plan) · **0053-F31** Accepted (current scanner checkpoint) · **F32** not started · **Programme 0.4** complete and accepted · **Programme 1** next authorized planning gate (not started) · feature branch preserved for Programme 8.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F24 | Quarantine Event/Audit Planning | Done | `~/Desktop/CareerKundi_0053_F24_Quarantine_Audit_Planning_Evidence.txt` | `d8b2f316` | Yes | Disabled sink |
| 0053-F25 | Scan/Quarantine Admin Boundary Planning | Done | `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt` | `d88a99f5` | Yes | Disabled surface |
| 0053-F26 | Scanner Worker Dry-Run Planning | Done | `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt` | `ef2682f7` | Yes | Disabled runner |
| 0053-F27 | Scanner Worker Reservation Guard | Accepted / completed | `~/Desktop/CareerKundi_0053_F27_Scanner_Worker_Reservation_Guard_Evidence.txt` | `8fec0617` | Yes | queued→reserved |
| 0053-F28 | Scanner Worker Result Application Planning | Accepted / completed | `~/Desktop/CareerKundi_0053_F28_Prototype_Governance_And_Plan_Acceptance_Evidence.txt` | `a3e7b153` | Yes | Plan only |
| 0053-F29 | Scanner Worker Result Application Guard | Accepted / completed | `docs/evidence/0053/CareerKundi_0053_F29_Scanner_Worker_Result_Application_Guard_Evidence.txt` (canonical; Desktop path historical) | `296f174f` | Yes | reserved→completed\|failed |
| 0053-F30 | Scanner Worker Single-Job Orchestration Planning | Accepted / completed | `~/Desktop/CareerKundi_0053_F30_Scanner_Worker_Single_Job_Orchestration_Plan_Acceptance_Evidence.txt` | `a81b3846` | Yes | Plan only; preflight→F27→adapter→F29 |
| 0053-F31 | Scanner Worker Single-Job Orchestration Guard | Accepted (current scanner checkpoint) | `docs/evidence/0053/CareerKundi_0053_F31_Scanner_Worker_Single_Job_Orchestration_Guard_Evidence.txt` (canonical; Desktop/F3 paths in evidence body are historical) | `4c8abbd6` | Yes | One supplied-job callable; 3 session boundaries; F32 not started |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-18 | 0053-F25 | `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt` | B ready for F26 | Disabled admin surface |
| 2026-07-18 | 0053-F26 | `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt` | B ready for F27 | Disabled worker dry-run |
| 2026-07-18 | 0053-F27 | `~/Desktop/CareerKundi_0053_F27_Scanner_Worker_Reservation_Guard_Evidence.txt` | Accepted | Reservation guard |
| 2026-07-19 | 0053-F28 | `~/Desktop/CareerKundi_0053_F28_Prototype_Governance_And_Plan_Acceptance_Evidence.txt` | Accepted | Governance + F28 plan |
| 2026-07-19 | 0053-F29 | `~/Desktop/CareerKundi_0053_F29_Scanner_Worker_Result_Application_Guard_Evidence.txt` | Accepted | Result application guard (historical Desktop pointer; canonical now under `docs/evidence/0053/`) |
| 2026-07-19 | 0053-F30 | `~/Desktop/CareerKundi_0053_F30_Scanner_Worker_Single_Job_Orchestration_Plan_Acceptance_Evidence.txt` | Accepted | Single-job orchestration plan |
| 2026-07-19 | 0053-F31 | `~/Desktop/CareerKundi_0053_F31_Scanner_Worker_Single_Job_Orchestration_Guard_Evidence.txt` | Ready for review (historical contemporaneous entry) | Single-job orchestration guard — contemporaneous readiness |
| 2026-07-19 | Programme 0.4 | `~/Desktop/CareerKundi_Programme_0_4_F31_Governance_and_F29_F31_Evidence_Implementation_Evidence.txt` | Accepted | F31 accepted token recorded; F29/F31 evidence canonicalized under `docs/evidence/0053/`; F3 retired; F32/Programme 1 not started |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-18 | 0053-F25 | `d88a99f5` | Pushed | Scan admin boundary planning |
| 2026-07-18 | 0053-F26 | `ef2682f7` | Pushed | Scanner worker dry-run planning |
| 2026-07-18 | 0053-F27 | `8fec0617` | Pushed | Scanner worker reservation guard |
| 2026-07-19 | 0053-F28 | `a3e7b153` | Pushed | Prototype governance + F28 plan |
| 2026-07-19 | 0053-F29 | `296f174f` | Pushed | Scanner worker result application guard |
| 2026-07-19 | 0053-F30 | `a81b3846` | Pushed | Scanner single-job orchestration plan (accepted) |
| 2026-07-19 | 0053-F31 | `4c8abbd6` | Pushed | Scanner single-job orchestration guard (technical) |
| 2026-07-19 | Programme 0.4 | Commits A–C (F29 evidence, F31 evidence, governance) | Exact closure sequence; remote verification gate before Programme 1 authorization | Programme 0.4 complete and accepted; no scanner capability expansion; F27 top-level duplicate deferred to Programme 1 |

---

## 6. Decision Updates

- F27: internal scan-job reservation guard only; owner-scoped queued→reserved; hash snapshot match; no scan/file/adapter/audit/route/UI.
- F28: accepted F29 contract — `reserved→completed|failed` only; six-field exact-match replay; triple-hash; PostgreSQL one-txn lock/CAS; no CANCEL/RESERVE/NO_OP in F29; no migration.
- F29: result application guard shipped — owner-scoped FOR UPDATE job→evidence; triple-hash; F22 policy reuse; six-field exact-match soft replay; no scanner/loop/quarantine/audit/admin/UI/migration. **Accepted.**
- F30: single-job orchestration plan accepted — preflight (adapter_info only: AVAILABLE + MALWARE_SCAN, no UNAVAILABLE) → F27 reservation → adapter execution with no held txn/lock → F29 apply; noop/unavailable leaves job queued (no F27/scan/F29, no attempt/started_at, no scan_error, no fake CLEAN); post-reservation failures → persistable MARK_ERROR (F21 codes) via F29; F29 rejection → result_application_rejected (DB unchanged); Cancelled/KeyboardInterrupt/SystemExit re-raised (reserved-row watch item); three separate short-lived sessions; authoritative snapshot from reserved job / reload only; F31 = one supplied-job callable; no selection/SKIP LOCKED/poll/loop/startup/scheduler/scanner/file/quarantine/audit/routes/UI/mutation/migration/lease.
- F31: single-job orchestration guard shipped — `orchestrate_attachment_scan_job` (public input owner+job+expected-hash only); adapter_info-only preflight; F27 result carries an additive immutable `ReservedJobSnapshot`; three distinct short-lived sessions (reservation / adapter with no active session / F29); noop/unavailable leaves job queued with no DB touch; post-reservation NOT_RUN/unavailable/timeout/error/unsupported/malformed/exception → persistable MARK_ERROR (F21 codes, no fake CLEAN, no fabricated engine); F29-only application; rejection → result_application_rejected (state unchanged, reserved-row watch item); interrupts propagate. 41 tests (19 static + 22 disposable-PostgreSQL, incl. real concurrency). No loop/poll/select/SKIP LOCKED/startup/scheduler/scanner/file/quarantine/audit/routes/UI/mutation/migration/lease.
- **Programme 0.4 (2026-07-19):** Owner accepted F31 with token `0053_F31_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_GUARD_ACCEPTED_WITH_WATCH_ITEMS`. F31 is the current accepted scanner checkpoint. F29 evidence remains byte-unchanged; F31 evidence copied byte-unchanged into `docs/evidence/0053/`. Former F3 worktree and hold branch retired. Programme 0.4 implementation is complete and accepted. Programme 1 is the next authorized planning gate and has not started. F32 has not started. No scanner capability expansion occurred. Top-level untracked F27 duplicate remains deferred to Programme 1. Feature branch `feat/interview-pack-llm-authoring` remains preserved for Programme 8.

---

## 7. Known Watch Items

- Real malware scan engine / worker loop / queue polling / quarantine / audit / admin feature still not implemented (deferred)
- Configured adapter remains noop/unavailable until a later scanner-enablement phase
- Stuck-reserved recovery (after process interruption or F29 rejection) remains a watch item; no lease/TTL/reclaim in F31
- F32 not started — no lease/recovery/engine/polling/quarantine/admin/UI work authorized
- Pre-existing (unrelated to F31): `test_mapping_helper_not_imported_by_api_routes` `rglob`s `app/api/routes/` and reaches `routes/tests/test_evidence_attachment_delete_api.py`; F31 touches no routes
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)
- Top-level F27 evidence duplicate: defer deletion to Programme 1

---

*Tracker updated: 2026-07-19 — Programme 0.4 complete and accepted; F31 remains current scanner checkpoint; Programme 1 next (not started)*
