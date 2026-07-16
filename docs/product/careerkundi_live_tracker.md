# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F9 Review/Verification State Machine Planning** |
| Current Status | Completing / accepted with watch items (ready for F10) |
| Last Completed Slice | **0053-F8** · F7 · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F8 status | **Completed / accepted** |
| Last Commit | This commit — `feat(verification): add review state machine contract` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F10** Review Request Backend Skeleton or Evidence Hardening (only after F9 acceptance) |
| Browser viewports | No UI change; page smoke only |
| Blocked Items | None for F9; do not start F10 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F9 does not call LLM |
| Foundation head | `f0009_evidence_foundation` (no new migration) |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F9 state machine | `docs/product/careerkundi_0053_f9_verification_state_machine.md` |
| Storage / attachment notes | `docs/product/careerkundi_0053_f4_attachment_storage_decision.md` |

**Pointers:** **0053-F8** Done · **0053-F9** Accepted (watch items) · Next **0053-F10**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F7 | Evidence-to-Claim Linking UI | Done | `~/Desktop/CareerKundi_0053_F7_Evidence_To_Claim_Linking_UI_Evidence.txt` | `ff084051` | Yes | Private claim selector |
| 0053-F8 | Passport Read-Only Evidence Panel | Done | `~/Desktop/CareerKundi_0053_F8_Passport_Read_Only_Evidence_Panel_Evidence.txt` | `6ab2044b` | Yes | Read-only awareness |
| 0053-F9 | Review/Verification State Machine Planning | Accepted (watch) | `~/Desktop/CareerKundi_0053_F9_Verification_State_Machine_Planning_Evidence.txt` | This commit | With push | Contract only |
| 0053-F10 | Review request skeleton / hardening | Next | — | — | — | After F9 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F8 | `~/Desktop/CareerKundi_0053_F8_Passport_Read_Only_Evidence_Panel_Evidence.txt` | B ready for F9 | Passport panel |
| 2026-07-16 | 0053-F9 | `~/Desktop/CareerKundi_0053_F9_Verification_State_Machine_Planning_Evidence.txt` | This slice | State machine |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F8 | `6ab2044b` | Pushed | Passport evidence panel |
| 2026-07-16 | 0053-F9 | This commit | Push with this slice | Review contracts |

---

## 6. Decision Updates

- F9: pure domain `ReviewState` machine; no verification workflow/UI/API; upload/link/source ≠ verification; no claim mutation; no DB/migration.

---

## 7. Known Watch Items

- Local uvicorn badge-seed timeout against `careerkundi_f4`
- Malware scan deferred
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-16 — 0053-F9*
