# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F14 Private Attachment Deletion + Retention Policy** |
| Current Status | Completing / accepted with watch items (ready for F15) |
| Last Completed Slice | **0053-F13** · F12 · F11 · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F13 status | **Completed / accepted** |
| Last Commit | This commit — `feat(evidence): add private attachment deletion` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F15** Scan Queue Skeleton or Runtime Badge-Seed Fix (only after F14 acceptance) |
| Browser viewports | Evidence Library remove attachment |
| Blocked Items | None for F14; do not start F15 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F14 does not call LLM |
| Foundation head | `f0010_review_request_foundation` (unchanged; no new migration) |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F13 attachment safety | `docs/product/careerkundi_0053_f13_attachment_safety_planning.md` |
| F14 deletion/retention | `docs/product/careerkundi_0053_f14_attachment_deletion_retention.md` |

**Pointers:** **0053-F13** Done · **0053-F14** Accepted (watch items) · Next **0053-F15**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F12 | Review Intake Hardening | Done | `~/Desktop/CareerKundi_0053_F12_Review_Intake_Hardening_Evidence.txt` | `e1b86413` | Yes | Linked evidence + bounds |
| 0053-F13 | Attachment Safety / Malware Scan Planning | Done | `~/Desktop/CareerKundi_0053_F13_Attachment_Safety_Planning_Evidence.txt` | `dfd3784e` | Yes | States/warnings only |
| 0053-F14 | Private Attachment Deletion + Retention | Accepted (watch) | `~/Desktop/CareerKundi_0053_F14_Attachment_Deletion_Retention_Evidence.txt` | This commit | With push | Bytes only; metadata kept |
| 0053-F15 | Scan queue skeleton / badge-seed fix | Next | — | — | — | After F14 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F13 | `~/Desktop/CareerKundi_0053_F13_Attachment_Safety_Planning_Evidence.txt` | B ready for F14 | Safety planning |
| 2026-07-17 | 0053-F14 | `~/Desktop/CareerKundi_0053_F14_Attachment_Deletion_Retention_Evidence.txt` | This slice | Attachment deletion |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F13 | `dfd3784e` | Pushed | Attachment safety planning |
| 2026-07-17 | 0053-F14 | This commit | Push with this slice | Attachment deletion |

---

## 6. Decision Updates

- F14: delete private attachment bytes + clear attachment metadata only; evidence/links/reviews/claim statuses remain; deletion ≠ verification; no scanner.

---

## 7. Known Watch Items

- Local uvicorn badge-seed timeout against `careerkundi_f4`
- Malware scan engine still not implemented
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-17 — 0053-F14*
