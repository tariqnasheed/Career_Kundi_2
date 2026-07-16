# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F17 Scan Worker Contract + Quarantine Policy** |
| Current Status | Completing / accepted with watch items (ready for F18) |
| Last Completed Slice | **0053-F16** · F15 · F14 · F13 · F12 · F11 · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F16 status | **Completed / accepted** |
| Last Commit | This commit — `feat(evidence): add scan worker policy contracts` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F18** Scanner Adapter Selection / Local Scanner Integration Planning (only after F17 acceptance) |
| Browser viewports | No scan/quarantine UI |
| Blocked Items | None for F17; do not start F18 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F17 does not call LLM |
| Foundation head | `f0011_attachment_scan_queue` (unchanged; no F17 migration) |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F16 scan queue skeleton | `docs/product/careerkundi_0053_f16_scan_queue_skeleton.md` |
| F17 worker/quarantine policy | `docs/product/careerkundi_0053_f17_scan_worker_quarantine_policy.md` |

**Pointers:** **0053-F16** Done · **0053-F17** Accepted (watch items) · Next **0053-F18**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F15 | Runtime Badge-Seed Startup Reliability | Done | `~/Desktop/CareerKundi_0053_F15_Runtime_Badge_Seed_Fix_Evidence.txt` | `d80ce1a3` | Yes | Skip-safe + timeout |
| 0053-F16 | Attachment Scan Queue Skeleton | Done | `~/Desktop/CareerKundi_0053_F16_Attachment_Scan_Queue_Skeleton_Evidence.txt` | `8ecff0e3` | Yes | Queue only |
| 0053-F17 | Scan Worker Contract + Quarantine Policy | Accepted (watch) | `~/Desktop/CareerKundi_0053_F17_Scan_Worker_Quarantine_Policy_Evidence.txt` | This commit | With push | Pure contracts |
| 0053-F18 | Scanner adapter / local scanner planning | Next | — | — | — | After F17 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F16 | `~/Desktop/CareerKundi_0053_F16_Attachment_Scan_Queue_Skeleton_Evidence.txt` | B ready for F17 | Scan queue skeleton |
| 2026-07-17 | 0053-F17 | `~/Desktop/CareerKundi_0053_F17_Scan_Worker_Quarantine_Policy_Evidence.txt` | This slice | Worker/quarantine policy |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F16 | `8ecff0e3` | Pushed | Scan queue skeleton |
| 2026-07-17 | 0053-F17 | This commit | Push with this slice | Worker/quarantine contracts |

---

## 6. Decision Updates

- F17: scanner availability unavailable; update plans never auto-applied; quarantine planned but not active; no engine/route/UI.

---

## 7. Known Watch Items

- Malware scan engine / worker still not implemented (F18+)
- Quarantine storage not implemented
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-17 — 0053-F17*
