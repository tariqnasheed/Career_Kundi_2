# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F12 Review Intake Hardening** |
| Current Status | Completing / accepted with watch items (ready for F13) |
| Last Completed Slice | **0053-F11** · F10 · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F11 status | **Completed / accepted** |
| Last Commit | This commit — `feat(verification): harden review request intake` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F13** Evidence Attachment Hardening / Malware Scan Planning (only after F12 acceptance) |
| Browser viewports | Passport intake copy + error handling |
| Blocked Items | None for F12; do not start F13 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F12 does not call LLM |
| Foundation head | `f0010_review_request_foundation` (unchanged; no new migration) |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F9 state machine | `docs/product/careerkundi_0053_f9_verification_state_machine.md` |
| F10 review request | `docs/product/careerkundi_0053_f10_review_request_backend.md` |
| F11 review request UI | `docs/product/careerkundi_0053_f11_review_request_ui.md` |
| F12 intake hardening | `docs/product/careerkundi_0053_f12_review_intake_hardening.md` |

**Pointers:** **0053-F11** Done · **0053-F12** Accepted (watch items) · Next **0053-F13**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F10 | Review Request Backend Skeleton | Done | `~/Desktop/CareerKundi_0053_F10_Review_Request_Backend_Skeleton_Evidence.txt` | `e274f9dc` | Yes | Request/cancel API |
| 0053-F11 | Review Request UI | Done | `~/Desktop/CareerKundi_0053_F11_Review_Request_UI_Evidence.txt` | `40e96873` | Yes | Passport request/cancel UI |
| 0053-F12 | Review Intake Hardening | Accepted (watch) | `~/Desktop/CareerKundi_0053_F12_Review_Intake_Hardening_Evidence.txt` | This commit | With push | Linked evidence + note bounds |
| 0053-F13 | Evidence attachment hardening / malware scan planning | Next | — | — | — | After F12 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F11 | `~/Desktop/CareerKundi_0053_F11_Review_Request_UI_Evidence.txt` | B ready for F12 | Passport UI |
| 2026-07-17 | 0053-F12 | `~/Desktop/CareerKundi_0053_F12_Review_Intake_Hardening_Evidence.txt` | This slice | Intake hardening |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-17 | 0053-F11 | `40e96873` | Pushed | Review request UI |
| 2026-07-17 | 0053-F12 | This commit | Push with this slice | Intake hardening |

---

## 6. Decision Updates

- F12: review request requires linked private evidence; note/reason bounded; still not verification; no approve/reject; no claim mutation; malware scan deferred.

---

## 7. Known Watch Items

- Local uvicorn badge-seed timeout against `careerkundi_f4`
- Malware scan deferred to F13 planning / later
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-17 — 0053-F12*
