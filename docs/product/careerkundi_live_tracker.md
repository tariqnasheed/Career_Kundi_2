# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F11 Review Request UI** |
| Current Status | Completing / accepted with watch items (ready for F12) |
| Last Completed Slice | **0053-F10** · F9 · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F10 status | **Completed / accepted** |
| Last Commit | This commit — `feat(passport): add private review request ui` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F12** Review Intake Hardening or Evidence Hardening (only after F11 acceptance) |
| Browser viewports | Passport review request/cancel on `/passport` |
| Blocked Items | None for F11; do not start F12 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F11 does not call LLM |
| Foundation head | `f0010_review_request_foundation` (unchanged) |

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

**Pointers:** **0053-F10** Done · **0053-F11** Accepted (watch items) · Next **0053-F12**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F8 | Passport Read-Only Evidence Panel | Done | `~/Desktop/CareerKundi_0053_F8_Passport_Read_Only_Evidence_Panel_Evidence.txt` | `6ab2044b` | Yes | Read-only awareness |
| 0053-F9 | Review/Verification State Machine Planning | Done | `~/Desktop/CareerKundi_0053_F9_Verification_State_Machine_Planning_Evidence.txt` | `1b4fd102` | Yes | Contracts only |
| 0053-F10 | Review Request Backend Skeleton | Done | `~/Desktop/CareerKundi_0053_F10_Review_Request_Backend_Skeleton_Evidence.txt` | `e274f9dc` | Yes | Request/cancel API |
| 0053-F11 | Review Request UI | Accepted (watch) | `~/Desktop/CareerKundi_0053_F11_Review_Request_UI_Evidence.txt` | This commit | With push | Passport request/cancel UI |
| 0053-F12 | Review intake / evidence hardening | Next | — | — | — | After F11 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F10 | `~/Desktop/CareerKundi_0053_F10_Review_Request_Backend_Skeleton_Evidence.txt` | B ready for F11 | Review requests |
| 2026-07-17 | 0053-F11 | `~/Desktop/CareerKundi_0053_F11_Review_Request_UI_Evidence.txt` | This slice | Passport UI |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F10 | `e274f9dc` | Pushed | Review request backend |
| 2026-07-17 | 0053-F11 | This commit | Push with this slice | Review request UI |

---

## 6. Decision Updates

- F11: Passport private review request/cancel UI only; review request ≠ verification; no approve/reject; no claim mutation; no public sharing; no backend changes.

---

## 7. Known Watch Items

- Local uvicorn badge-seed timeout against `careerkundi_f4`
- Malware scan deferred
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-17 — 0053-F11*
