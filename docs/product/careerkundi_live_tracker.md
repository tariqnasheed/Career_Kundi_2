# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F10 Review Request Backend Skeleton** |
| Current Status | Completing / accepted with watch items (ready for F11) |
| Last Completed Slice | **0053-F9** · F8 · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F9 status | **Completed / accepted** |
| Last Commit | This commit — `feat(verification): add review request backend skeleton` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F11** Review Request UI or Evidence Hardening (only after F10 acceptance) |
| Browser viewports | No FE change; page smoke only |
| Blocked Items | None for F10; do not start F11 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F10 does not call LLM |
| Foundation head | `f0010_review_request_foundation` |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F9 state machine | `docs/product/careerkundi_0053_f9_verification_state_machine.md` |
| F10 review request | `docs/product/careerkundi_0053_f10_review_request_backend.md` |

**Pointers:** **0053-F9** Done · **0053-F10** Accepted (watch items) · Next **0053-F11**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F8 | Passport Read-Only Evidence Panel | Done | `~/Desktop/CareerKundi_0053_F8_Passport_Read_Only_Evidence_Panel_Evidence.txt` | `6ab2044b` | Yes | Read-only awareness |
| 0053-F9 | Review/Verification State Machine Planning | Done | `~/Desktop/CareerKundi_0053_F9_Verification_State_Machine_Planning_Evidence.txt` | `1b4fd102` | Yes | Contracts only |
| 0053-F10 | Review Request Backend Skeleton | Accepted (watch) | `~/Desktop/CareerKundi_0053_F10_Review_Request_Backend_Skeleton_Evidence.txt` | This commit | With push | Request/cancel API |
| 0053-F11 | Review request UI / hardening | Next | — | — | — | After F10 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F9 | `~/Desktop/CareerKundi_0053_F9_Verification_State_Machine_Planning_Evidence.txt` | B ready for F10 | Contracts |
| 2026-07-16 | 0053-F10 | `~/Desktop/CareerKundi_0053_F10_Review_Request_Backend_Skeleton_Evidence.txt` | This slice | Review requests |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F9 | `1b4fd102` | Pushed | State machine contracts |
| 2026-07-16 | 0053-F10 | This commit | Push with this slice | Review request backend |

---

## 6. Decision Updates

- F10: private `review_requests` + request/cancel API only; request ≠ verification; no claim mutation; no approve/reject; no FE UI.

---

## 7. Known Watch Items

- Local uvicorn badge-seed timeout against `careerkundi_f4`
- Malware scan deferred
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-16 — 0053-F10*
