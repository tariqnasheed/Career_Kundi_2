# CareerKundi Live Tracker

**Keep this file short.** Architecture lives in the [Master Build Plan](careerkundi_master_build_plan.md).  
Readable in under 2 minutes. Update every slice. No secrets.

---

## 1. Current Position

| Field | Value |
|---|---|
| Current Phase | **0053 Evidence, Claims, Provenance and Verification Foundations** |
| Current Slice | **0053-F6 Evidence Upload UI** |
| Current Status | Accepted with watch items (ready for F7) |
| Last Completed Slice | **0053-F5** · F4 · F3 · F2 · F1 · POST-CLAUDE-R2 · ROADMAP-RICH · JOB-INT-R1 · CORE-VALUE-R1 · LLM-R1 · F0 · 0052 |
| F0–F5 status | **Completed / accepted** |
| Last Commit | This commit — `feat(evidence): add private attachment upload ui` |
| Last Push Status | Push with this slice |
| Next Slice | **0053-F7** Evidence-to-Claim Linking UI or Passport Read-Only Evidence Panel (only after F6 acceptance) |
| Browser viewports | `/evidence` upload/download + page smoke |
| Blocked Items | None for F6; do not start F7 until accepted |
| Frozen Items | Old 004E Interview Pack repair; old Auto Apply |
| LLM provider | **Local Ollama 8B**; F6 does not call LLM |
| Foundation head | `f0009_evidence_foundation` (no new migration) |

---

## 2. Source of Truth Files

| File | Path |
|---|---|
| Master Build Plan | `docs/product/careerkundi_master_build_plan.md` |
| Live Tracker | `docs/product/careerkundi_live_tracker.md` |
| 0053 Plan | `docs/product/careerkundi_0053_claims_evidence_plan.md` |
| F4/F5/F6 storage notes | `docs/product/careerkundi_0053_f4_attachment_storage_decision.md` |

**Pointers:** **0053-F5** Done · **0053-F6** Accepted (watch items) · Next **0053-F7**.

---

## 3. Slice Status Table

| Slice | Name | Status | Evidence | Commit | Pushed | Notes |
|---|---|---|---|---|---|---|
| 0053-F4 | Private Evidence Library UI + Storage Decision | Done | `~/Desktop/CareerKundi_0053_F4_Private_Evidence_Library_UI_Evidence.txt` | `cd0194fe` | Yes | Metadata UI |
| 0053-F5 | Attachment Storage Backend | Done | `~/Desktop/CareerKundi_0053_F5_Attachment_Storage_Backend_Evidence.txt` | `c298d33c` | Yes | Local private bytes |
| 0053-F6 | Evidence Upload UI | Accepted (watch) | `~/Desktop/CareerKundi_0053_F6_Evidence_Upload_UI_Evidence.txt` | This commit | With push | FE attach/download |
| 0053-F7 | Linking UI / Passport evidence read | Next | — | — | — | After F6 accepted |

---

## 4. Evidence Log

| Date | Slice | Evidence Path | Verdict | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F5 | `~/Desktop/CareerKundi_0053_F5_Attachment_Storage_Backend_Evidence.txt` | B ready for F6 | Backend only |
| 2026-07-16 | 0053-F6 | `~/Desktop/CareerKundi_0053_F6_Evidence_Upload_UI_Evidence.txt` | This slice | FE upload UI |

---

## 5. Commit Log

| Date | Slice | Commit | Push Status | Notes |
|---|---|---|---|---|
| 2026-07-16 | 0053-F5 | `c298d33c` | Pushed | Attachment storage |
| 2026-07-16 | 0053-F6 | This commit | Push with this slice | Upload UI |

---

## 6. Decision Updates

- F6: private attach/download on `/evidence` only; upload ≠ verified; no public URL; no OCR; malware scan still deferred.

---

## 7. Known Watch Items

- Local uvicorn badge-seed timeout against `careerkundi_f4` (F5); attachment APIs proven via pytest
- Malware scan not implemented
- `JobSearchPage.test.tsx` still missing
- Pre-existing `documents/` local dirt (do not stage)

---

*Tracker updated: 2026-07-16 — 0053-F6*
