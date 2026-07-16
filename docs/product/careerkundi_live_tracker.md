# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F4 Private Evidence Library UI + Attachment Storage Decision** |
| Current Status | Accepted with watch items (ready for F5) |
| Last Completed Slice | **0053-F3** · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F3 status | **Completed / accepted** |
| Last Commit | This commit — `feat(evidence): add private evidence library ui` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F5 Attachment Storage Backend** (only after F4 acceptance) |
| Browser viewports | `/evidence` + existing page smoke |
| Blocked Items | None for F4; do not start F5 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F4 does not call LLM |
| Foundation head | `f0009_evidence_foundation` |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F4 storage decision | `docs/product/careerkundi_0053_f4_attachment_storage_decision.md` |

**Pointers:** **0053-F3** Done · **0053-F4** Accepted (watch items) · Next **0053-F5**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F3 | Private Evidence Service/API Boundary | Done | `~/Desktop/CareerKundi_0053_F3_Private_Evidence_API_Boundary_Evidence.txt` | `dd3c4bdb` | Yes | Auth API |
| 0053-F4 | Private Evidence Library UI + Storage Decision | Accepted (watch) | `~/Desktop/CareerKundi_0053_F4_Private_Evidence_Library_UI_Evidence.txt` | This commit | With push | Metadata UI only |
| 0053-F5 | Attachment Storage Backend | Next | — | — | — | After F4 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F3 | `~/Desktop/CareerKundi_0053_F3_Private_Evidence_API_Boundary_Evidence.txt` | A ready for F4 | Private API |
| 2026-07-16 | 0053-F4 | `~/Desktop/CareerKundi_0053_F4_Private_Evidence_Library_UI_Evidence.txt` | This slice | No upload |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F3 | `dd3c4bdb` | Pushed | Private evidence API |
| 2026-07-16 | 0053-F4 | This commit | Push with this slice | Evidence Library UI |

---

## 6. Decision Updates

| Date | Decision | Impact | Status |
|---|---|---|---|
| 2026-07-16 | F4 = metadata UI only | No file upload/storage | Implemented |
| 2026-07-16 | No claim linker UUID form | Wait for claim selection UI | Implemented |
| 2026-07-16 | F5 owns storage backend + safeguards | Documented | Documented |

---

## 7. Active Blockers

None for accepting F4.

**Do not start in F5 prematurely:** public sharing, verification UI, Passport evidence panel, wallet/DID/blockchain.

**Watch:** pre-existing local `documents/` dirt — never stage. `JobSearchPage.test.tsx` still missing.

---

## 8. Next Action

| Field | Value |
|---|---|
| Next | **0053-F5 Attachment Storage Backend** (only after F4 accepted) |
| Reason | Library UI exists; uploads still blocked until storage decision implemented |
| Do not start | Upload endpoints, OCR, public URLs, Passport evidence panel |
| Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| Evidence | `~/Desktop/CareerKundi_0053_F4_Private_Evidence_Library_UI_Evidence.txt` |

---

*Tracker updated: 2026-07-16 — 0053-F4*
