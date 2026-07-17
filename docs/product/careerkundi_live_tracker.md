# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F27 Scanner Worker Reservation Guard** |
| Current Status | Completing / accepted with watch items (ready for F28) |
| Last Completed Slice | **0053-F26** · F25 · F24 · F23 · F22 · F21 · F20 · F19 · F18 · F17 · F16 · F15 · F14 · F13 · F12 · F11 · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F26 status | **Completed / accepted** |
| Last Commit | This commit — `feat(evidence): guard scanner worker reservation` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F28** Scanner Worker Result Application Planning (only after F27 acceptance) |
| Browser viewports | No worker/scan/quarantine/audit/admin UI |
| Blocked Items | None for F27; do not start F28 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F27 does not call LLM |
| Foundation head | `f0011_attachment_scan_queue` (unchanged; no F27 migration) |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F25 scan admin boundary | `docs/product/careerkundi_0053_f25_scan_quarantine_admin_boundary.md` |
| F26 scanner worker dry-run | `docs/product/careerkundi_0053_f26_scanner_worker_dry_run_planning.md` |
| F27 reservation guard | `docs/product/careerkundi_0053_f27_scanner_worker_reservation_guard.md` |

**Pointers:** **0053-F26** Done · **0053-F27** Accepted (watch items) · Next **0053-F28**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F24 | Quarantine Event/Audit Planning | Done | `~/Desktop/CareerKundi_0053_F24_Quarantine_Audit_Planning_Evidence.txt` | `d8b2f316` | Yes | Disabled sink |
| 0053-F25 | Scan/Quarantine Admin Boundary Planning | Done | `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt` | `d88a99f5` | Yes | Disabled surface |
| 0053-F26 | Scanner Worker Dry-Run Planning | Done | `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt` | `ef2682f7` | Yes | Disabled runner |
| 0053-F27 | Scanner Worker Reservation Guard | Accepted (watch) | `~/Desktop/CareerKundi_0053_F27_Scanner_Worker_Reservation_Guard_Evidence.txt` | This commit | With push | queued→reserved |
| 0053-F28 | Scanner Worker Result Application Planning | Next | — | — | — | After F27 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-18 | 0053-F25 | `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt` | B ready for F26 | Disabled admin surface |
| 2026-07-18 | 0053-F26 | `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt` | B ready for F27 | Disabled worker dry-run |
| 2026-07-18 | 0053-F27 | `~/Desktop/CareerKundi_0053_F27_Scanner_Worker_Reservation_Guard_Evidence.txt` | This slice | Reservation guard |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-18 | 0053-F25 | `d88a99f5` | Pushed | Scan admin boundary planning |
| 2026-07-18 | 0053-F26 | `ef2682f7` | Pushed | Scanner worker dry-run planning |
| 2026-07-18 | 0053-F27 | This commit | Push with this slice | Scanner worker reservation guard |

---

## 6. Decision Updates

- F27: internal scan-job reservation guard only; owner-scoped queued→reserved; hash snapshot match; no scan/file/adapter/audit/route/UI.

---

## 7. Known Watch Items

- Real malware scan engine / worker loop / quarantine / audit / admin feature still not implemented (F28+)
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-18 — 0053-F27*
