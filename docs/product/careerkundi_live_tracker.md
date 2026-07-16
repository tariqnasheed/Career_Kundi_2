# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F16 Attachment Scan Queue Skeleton** |
| Current Status | Completing / accepted (ready for F17) |
| Last Completed Slice | **0053-F15** · F14 · F13 · F12 · F11 · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F15 status | **Completed / accepted** |
| Last Commit | This commit — `feat(evidence): add attachment scan queue skeleton` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F17** Scan Worker Planning / Quarantine Policy (only after F16 acceptance) |
| Browser viewports | No scan UI; safety warnings unchanged |
| Blocked Items | None for F16; do not start F17 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F16 does not call LLM |
| Foundation head | `f0011_attachment_scan_queue` |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F15 runtime badge-seed fix | `docs/product/careerkundi_0053_f15_runtime_badge_seed_fix.md` |
| F16 scan queue skeleton | `docs/product/careerkundi_0053_f16_scan_queue_skeleton.md` |

**Pointers:** **0053-F15** Done · **0053-F16** Accepted · Next **0053-F17**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F14 | Private Attachment Deletion + Retention | Done | `~/Desktop/CareerKundi_0053_F14_Attachment_Deletion_Retention_Evidence.txt` | `6372ebb0` | Yes | Bytes only |
| 0053-F15 | Runtime Badge-Seed Startup Reliability | Done | `~/Desktop/CareerKundi_0053_F15_Runtime_Badge_Seed_Fix_Evidence.txt` | `d80ce1a3` | Yes | Skip-safe + timeout |
| 0053-F16 | Attachment Scan Queue Skeleton | Accepted | `~/Desktop/CareerKundi_0053_F16_Attachment_Scan_Queue_Skeleton_Evidence.txt` | This commit | With push | Queue only; no scanner |
| 0053-F17 | Scan worker planning / quarantine policy | Next | — | — | — | After F16 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F15 | `~/Desktop/CareerKundi_0053_F15_Runtime_Badge_Seed_Fix_Evidence.txt` | A ready for F16 | Badge seed startup |
| 2026-07-17 | 0053-F16 | `~/Desktop/CareerKundi_0053_F16_Attachment_Scan_Queue_Skeleton_Evidence.txt` | This slice | Scan queue skeleton |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F15 | `d80ce1a3` | Pushed | Badge seed startup bound |
| 2026-07-17 | 0053-F16 | This commit | Push with this slice | Scan queue skeleton |

---

## 6. Decision Updates

- F16: internal `attachment_scan_jobs` queue only; no scanner/route/UI; public safety remains `scan_not_available`; queued job ≠ verification.

---

## 7. Known Watch Items

- Malware scan engine / worker still not implemented (F17+)
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)
- Stale `FOUNDATION_CURRENT_HEAD` constants in some older db/privacy tests outside F16 scope

---

*Tracker updated: 2026-07-17 — 0053-F16*
