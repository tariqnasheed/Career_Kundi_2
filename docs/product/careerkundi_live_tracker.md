# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F13 Evidence Attachment Safety / Malware Scan Planning** |
| Current Status | Completing / accepted with watch items (ready for F14) |
| Last Completed Slice | **0053-F12** · F11 · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F12 status | **Completed / accepted** |
| Last Commit | This commit — `feat(evidence): add attachment safety planning` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F14** Attachment Deletion/Retention or Scan Queue Skeleton (only after F13 acceptance) |
| Browser viewports | Evidence + Passport attachment safety warnings |
| Blocked Items | None for F13; do not start F14 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F13 does not call LLM |
| Foundation head | `f0010_review_request_foundation` (unchanged; no new migration) |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F12 intake hardening | `docs/product/careerkundi_0053_f12_review_intake_hardening.md` |
| F13 attachment safety | `docs/product/careerkundi_0053_f13_attachment_safety_planning.md` |

**Pointers:** **0053-F12** Done · **0053-F13** Accepted (watch items) · Next **0053-F14**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F11 | Review Request UI | Done | `~/Desktop/CareerKundi_0053_F11_Review_Request_UI_Evidence.txt` | `40e96873` | Yes | Passport request/cancel |
| 0053-F12 | Review Intake Hardening | Done | `~/Desktop/CareerKundi_0053_F12_Review_Intake_Hardening_Evidence.txt` | `e1b86413` | Yes | Linked evidence + bounds |
| 0053-F13 | Attachment Safety / Malware Scan Planning | Accepted (watch) | `~/Desktop/CareerKundi_0053_F13_Attachment_Safety_Planning_Evidence.txt` | This commit | With push | States/warnings only |
| 0053-F14 | Attachment deletion/retention or scan queue skeleton | Next | — | — | — | After F13 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F12 | `~/Desktop/CareerKundi_0053_F12_Review_Intake_Hardening_Evidence.txt` | B ready for F13 | Intake hardening |
| 2026-07-17 | 0053-F13 | `~/Desktop/CareerKundi_0053_F13_Attachment_Safety_Planning_Evidence.txt` | This slice | Safety planning |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F12 | `e1b86413` | Pushed | Intake hardening |
| 2026-07-17 | 0053-F13 | This commit | Push with this slice | Attachment safety planning |

---

## 6. Decision Updates

- F13: attachment safety states/warnings only; default `scan_not_available`; no scanner engine; no parsing/OCR/LLM review; no DB migration.

---

## 7. Known Watch Items

- Local uvicorn badge-seed timeout against `careerkundi_f4`
- Malware scan engine still not implemented (planned only)
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-17 — 0053-F13*
