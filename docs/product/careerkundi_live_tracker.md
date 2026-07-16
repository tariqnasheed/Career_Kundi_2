# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F8 Passport Read-Only Evidence Panel** |
| Current Status | Completing / accepted with watch items (ready for F9) |
| Last Completed Slice | **0053-F7** · F6 · F5 · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F7 status | **Completed / accepted** |
| Last Commit | This commit — `feat(passport): add read-only evidence panel` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F9** Review/Verification State Machine Planning or Evidence Hardening (only after F8 acceptance) |
| Browser viewports | `/passport` evidence panel + page smoke |
| Blocked Items | None for F8; do not start F9 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F8 does not call LLM |
| Foundation head | `f0009_evidence_foundation` (no new migration) |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| Storage / attachment notes | `docs/product/careerkundi_0053_f4_attachment_storage_decision.md` |

**Pointers:** **0053-F7** Done · **0053-F8** Accepted (watch items) · Next **0053-F9**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F6 | Evidence Upload UI | Done | `~/Desktop/CareerKundi_0053_F6_Evidence_Upload_UI_Evidence.txt` | `671b6878` | Yes | FE attach/download |
| 0053-F7 | Evidence-to-Claim Linking UI | Done | `~/Desktop/CareerKundi_0053_F7_Evidence_To_Claim_Linking_UI_Evidence.txt` | `ff084051` | Yes | Private claim selector |
| 0053-F8 | Passport Read-Only Evidence Panel | Accepted (watch) | `~/Desktop/CareerKundi_0053_F8_Passport_Read_Only_Evidence_Panel_Evidence.txt` | This commit | With push | Read-only awareness |
| 0053-F9 | Review / hardening | Next | — | — | — | After F8 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F7 | `~/Desktop/CareerKundi_0053_F7_Evidence_To_Claim_Linking_UI_Evidence.txt` | B ready for F8 | Claim linking |
| 2026-07-16 | 0053-F8 | `~/Desktop/CareerKundi_0053_F8_Passport_Read_Only_Evidence_Panel_Evidence.txt` | This slice | Passport panel |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F7 | `ff084051` | Pushed | Claim linking UI |
| 2026-07-16 | 0053-F8 | This commit | Push with this slice | Passport evidence panel |

---

## 6. Decision Updates

- F8: evidence-scoped `GET /private-awareness-summary` for Passport read-only awareness (path avoids `/passport` substring); Passport does not own evidence, does not upload/download/link/verify, does not mutate claim axes; no public sharing.

---

## 7. Known Watch Items

- Local uvicorn badge-seed timeout against `careerkundi_f4`
- Malware scan deferred
- `JobSearchPage.test.tsx` still missing
- `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-16 — 0053-F8*
