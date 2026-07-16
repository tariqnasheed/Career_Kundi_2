# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F15 Runtime Badge-Seed Startup Reliability Fix** |
| Current Status | Completing / accepted (ready for F16) |
| Last Completed Slice | **0053-F14** · F13 · F12 · F11 · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F14 status | **Completed / accepted** |
| Last Commit | This commit — `fix(runtime): bound badge seed startup` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F16** Scan Queue Skeleton or Evidence Scanner Planning (only after F15 acceptance) |
| Browser viewports | Local uvicorn OpenAPI readiness restored |
| Blocked Items | None for F15; do not start F16 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F15 does not call LLM |
| Foundation head | `f0010_review_request_foundation` (unchanged; no new migration) |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F14 deletion/retention | `docs/product/careerkundi_0053_f14_attachment_deletion_retention.md` |
| F15 runtime badge-seed fix | `docs/product/careerkundi_0053_f15_runtime_badge_seed_fix.md` |

**Pointers:** **0053-F14** Done · **0053-F15** Accepted · Next **0053-F16**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F13 | Attachment Safety / Malware Scan Planning | Done | `~/Desktop/CareerKundi_0053_F13_Attachment_Safety_Planning_Evidence.txt` | `dfd3784e` | Yes | States/warnings only |
| 0053-F14 | Private Attachment Deletion + Retention | Done | `~/Desktop/CareerKundi_0053_F14_Attachment_Deletion_Retention_Evidence.txt` | `6372ebb0` | Yes | Bytes only; metadata kept |
| 0053-F15 | Runtime Badge-Seed Startup Reliability | Accepted | `~/Desktop/CareerKundi_0053_F15_Runtime_Badge_Seed_Fix_Evidence.txt` | This commit | With push | Skip-safe + timeout |
| 0053-F16 | Scan queue skeleton / scanner planning | Next | — | — | — | After F15 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F14 | `~/Desktop/CareerKundi_0053_F14_Attachment_Deletion_Retention_Evidence.txt` | B ready for F15 | Attachment deletion |
| 2026-07-17 | 0053-F15 | `~/Desktop/CareerKundi_0053_F15_Runtime_Badge_Seed_Fix_Evidence.txt` | This slice | Badge seed startup |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F14 | `6372ebb0` | Pushed | Attachment deletion |
| 2026-07-17 | 0053-F15 | This commit | Push with this slice | Badge seed startup bound |

---

## 6. Decision Updates

- F15: badge seed is one-query skip-safe when current; lifespan timeout 15s; OpenAPI readiness must not hang on catalogue seed; no product feature change.

---

## 7. Known Watch Items

- Malware scan engine still not implemented (F16+)
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)
- APP_DEBUG SQL echo still noisy during cold seed (non-blocking)

---

*Tracker updated: 2026-07-17 — 0053-F15*
