# CareerKundi 0053-F28 Scanner Worker Result Application Planning

## Accepted decision

`0053_F28_SCANNER_WORKER_RESULT_APPLICATION_PLAN_ACCEPTED_READY_FOR_F29`

F28 is **planning and contract definition only**. No F29 implementation is authorised by this document. F29 implementation has not started.

---

## 1. Repository baseline

| Field | Value | State |
|---|---|---|
| Worktree | `/Users/tariqnasheed/Desktop/Career_Kundi_2_F3` | `EVIDENCE_BACKED_CURRENT` |
| Branch | `main` | `EVIDENCE_BACKED_CURRENT` |
| Accepted HEAD at F28 planning | `8fec0617265e5cd03c41c4622bfc3c4dcbf76c5b` | `EVIDENCE_BACKED_CURRENT` |
| Accepted origin/main at F28 planning | `8fec0617265e5cd03c41c4622bfc3c4dcbf76c5b` | `EVIDENCE_BACKED_CURRENT` |
| Divergence at F28 planning | `0 0` | `EVIDENCE_BACKED_CURRENT` |
| Prior accepted gate | `0053_F27_SCANNER_WORKER_RESERVATION_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_F28` | `EVIDENCE_BACKED_CURRENT` |
| Foundation head | `f0011_attachment_scan_queue` (no `f0012*`) | `EVIDENCE_BACKED_CURRENT` |
| Dialect | PostgreSQL (`asyncpg` runtime; `psycopg2` migrations/disposable tests) | `EVIDENCE_BACKED_CURRENT` |
| Known local dirt (preserved) | `.env`, `backend/.env`, `backend/data/knowledge_graph.gpickle`, `documents/` | `EVIDENCE_BACKED_CURRENT` |

---

## 2. Relevant files and symbols

| Path / symbol | Role |
|---|---|
| `attachment_scan_worker.py` — `ScanResultContract`, `ScanJobUpdatePlan`, `ScanWorkerAction`, `build_scan_job_update_from_result` | F17 result/plan contracts |
| `attachment_scan_result_persistence.py` — `normalize_scan_job_update_plan`, `assert_scan_job_update_allowed`, `apply_scan_job_update_plan`, `ALLOWED_JOB_TRANSITIONS` | F22 persistence policy and unlocked apply |
| `attachment_scan_worker_reservation.py` — `reserve_attachment_scan_job_for_worker` | F27 `queued → reserved` |
| `attachment_scan_queue.py` — statuses, `get_attachment_scan_job_for_owner`, `cancel_attachment_scan_job` | Queue + owner-scoped cancel |
| `attachment_scanner_runtime_policy.py` — F21 normalizers | Safe error code/message |
| `app.db.models.attachment_scan.AttachmentScanJob` | Job row |
| Evidence models / owner-scoped evidence loaders | Live `content_hash` for triple-hash guard |
| F27 evidence + F27/F28 handoff docs | Accepted prior gate |

**F22 commit evidence (current):** unlocked owner fetch → in-memory field writes → `await db.commit()` — no `FOR UPDATE`, no CAS. The active-job unique index constrains concurrent `queued|reserved` rows only; it does **not** serialize competing terminal writes on one reserved row.

---

## 3. Current state machine

`EVIDENCE_BACKED_CURRENT` job machine:

```
queued ──► reserved ──► completed
  │            │
  │            ├──► failed
  │            └──► cancelled   ← queue cancel / F22 CANCEL_JOB
  └──► cancelled
```

- No `retryable` job status. Retry = new job after a terminal state.
- Public API response safety remains `scan_not_available` (F13) until a later approved UX slice.

---

## 4. F29-specific state surface

`PROPOSED_TARGET` for **0053-F29 Scanner Worker Result Application Guard** only:

```
reserved ──► completed
reserved ──► failed
```

F29 **rejects**:

- `CANCEL_JOB` (and any target `cancelled`)
- `RESERVE_JOB` (reservation remains F27 only)
- `NO_OP` persistence

Owner-scoped `cancel_attachment_scan_job` remains the sole product path for `queued|reserved → cancelled` and is **outside** F29.

---

## 5. Prototype Impact Matrix

| Field | Content |
|---|---|
| Phase | 0053-F28 planning (accepted); next impl = 0053-F29 |
| Page references | P39, P40, P41, P46 — **future UX context only** |
| Sheet references | Relevant P39/P40/P41 sheets and P46 recovery/error sheets as context only |
| Current routes | No worker/scan/quarantine/audit/admin result-application routes |
| Current repository paths | F17/F22/F27 modules above; no F29 module yet |
| Approved target | Attachment-safety job terminalization under guarded persistence; not verification UI |
| Delta | F28 locks the F29 contract; no code shipped in F28 |
| Backend dependencies | Existing F22 policy + F27 reservation; PostgreSQL row lock/CAS |
| Privacy/security boundary | Owner-scoped job + evidence; DB-only hash guard; no file read; no EvidenceRecord mutation |
| Tests | See §15 test matrix (for F29) |
| Known limitations | No scanner engine, worker loop, quarantine move, audit, admin/UI |
| Next gate | **0053-F29 Scanner Worker Result Application Guard** |

The approved prototype must **not** be used to invent frontend scan, quarantine, audit or admin UI in F28/F29.

---

## 6. Scope and exclusions

### In scope for F28 (this document)

- Accept and record the binding F29 implementation contract.
- Update governance pointers so the next gate is F29.
- Adopt prototype governance text/reference files as authorised.

### Out of scope / preserved exclusions (F28 and F29)

Do not implement or authorize:

- scanner engine / scanner dependency / adapter execution
- worker loop / startup registration / scheduler / background task
- file or storage read / subprocess / network / external process
- OCR / document parsing / LLM review
- quarantine movement / audit emission
- worker/admin/scan/quarantine/audit API
- frontend scan/quarantine/audit/admin UI
- EvidenceRecord mutation
- claim `support_status` or `verification_status` mutation
- ReviewRequest mutation
- public evidence sharing
- wallet, DID or blockchain work
- `CANCEL_JOB` inside the F29 result-application guard
- database migration (`f0012+`)

---

## 7. Allowed mutation matrix

**Row:** `AttachmentScanJob` only.

**F29 actions:** `COMPLETE_PASSED`, `COMPLETE_FAILED`, `MARK_ERROR`, `QUARANTINE_REQUIRED` (safety stays `scan_failed`; never `quarantined`).

| Field | First apply (`reserved` → terminal) | Exact-match replay |
|---|---|---|
| `job_status` | `completed` or `failed` only | unchanged |
| `attachment_safety_status` | F22-coupled values | unchanged |
| `engine_name`, `engine_version` | set if plan provides non-`None` | unchanged |
| `safe_error_code`, `safe_error_message` | F21-normalized | unchanged |
| `completed_at` | set once (UTC now) on first terminal apply | **never rewrite** |
| `started_at` | leave as-is | unchanged |
| `attempt_count` | **must not change** | unchanged |
| `updated_at` | mixin on real write only | no spurious rewrite on soft replay |

---

## 8. Forbidden mutation matrix

| Forbidden | Rule |
|---|---|
| `CANCEL_JOB` / `reserved→cancelled` / `queued→cancelled` via F29 | Hard reject from F29 surface |
| `RESERVE_JOB` / `queued→reserved` via F29 | F27 only |
| `NO_OP` persistence | Reject |
| `attempt_count` increment | Reserve-only (F27 / F22 reserve path) |
| Rewrite `started_at` / `completed_at` / `cancelled_at` / `updated_at` on exact replay | Never |
| `quarantined` safety | Still rejected by F22 policy |
| Identity/snapshot columns | `owner_user_id`, `evidence_id`, `content_hash_snapshot`, mime/size snapshots, `id`, `created_at` |
| `EvidenceRecord` any field | Load owner-scoped for hash guard only; **no mutation** |
| Claim / ReviewRequest | No mutation |
| Parallel persistence bypassing F22 policy | Forbidden |
| File / storage read | Forbidden |

Queue cancel (`cancel_attachment_scan_job`) remains unchanged and outside F29.

---

## 9. Full six-field idempotency projection

Exact-match terminal replay compares the **complete normalized writable projection**:

1. `job_status`
2. `attachment_safety_status`
3. `engine_name`
4. `engine_version`
5. `safe_error_code`
6. `safe_error_message`

Rules:

- Compare after the same normalization F22 uses (`normalize_scan_job_update_plan` / F21 helpers).
- Timestamps are **not** part of equivalence and must **never** be rewritten on replay.
- `attempt_count` must remain unchanged on result apply and on replay.
- `updated_at` must not be spuriously rewritten on soft replay.
- Exact match → soft success (`already_applied` / equivalent); no field writes required.
- Any mismatch among the six fields → **conflicting replay**; hard reject.

---

## 10. Triple-hash validation

Mandatory **database-only** triple-hash guard before terminal apply:

```
EvidenceRecord.content_hash
  ==
AttachmentScanJob.content_hash_snapshot
  ==
expected_content_hash_snapshot
```

Additional rules:

- `EvidenceRecord` must be loaded **owner-scoped** for `job.evidence_id`.
- Missing evidence or any hash mismatch → reject; **no commit**.
- **No file read** and **no EvidenceRecord mutation**.

---

## 11. Concurrency and transaction contract

Ordinary unlocked status checks are **insufficient**. F29 must not inherit F22’s unlocked read→mutate→commit race for the worker result path.

**Binding requirements:**

- PostgreSQL concurrency protection is mandatory.
- Validation and mutation must occur inside **one transaction**.
- The active-job unique index **does not** serialize competing terminal writes.

**Preferred F29 approach:**

1. Lock the `AttachmentScanJob` row (`SELECT … FOR UPDATE`, owner-scoped).
2. Protect the owner-scoped `EvidenceRecord` row/hash in the **same** transaction.
3. Revalidate state and hashes after locks.
4. Reuse F22 normalization and policy guards.
5. Use a shared mutate-without-commit helper.
6. Commit once.

Do **not** call today’s `apply_scan_job_update_plan` as the F29 outer path (it re-fetches unlocked and commits itself, breaking the lock boundary). Leave public `apply_scan_job_update_plan` behaviour for non-worker callers **unchanged**.

**CAS alternative:** An atomic compare-and-set is allowed only if it:

- protects the live evidence hash in the same transaction,
- still runs F22 asserts on the pre-image,
- does not duplicate or weaken F22 policy,
- uses `rowcount` (or equivalent) checks for first-apply serialization.

---

## 12. Consistent lock-order requirement

To avoid deadlocks, F29 must document and obey a single lock order:

1. **`AttachmentScanJob`** — owner-scoped `FOR UPDATE` first.
2. **`EvidenceRecord`** — owner-scoped lock or equivalent protection for the live hash **after** the job lock, in the same transaction.

Never reverse this order in F29 callers. Do not lock additional unrelated rows. Soft exact-match replay may return without further writes after revalidation under the same order.

---

## 13. Rollback behaviour

| Topic | Decision |
|---|---|
| Boundary | One transaction: lock job → protect/read evidence → validate → mutate job only → commit |
| Guard failure | No commit; session clean / rollback |
| Soft replay | No mutation of writable fields or timestamps; may return without commit |
| Evidence | Read-only inside txn; never mutate |
| F22 reuse | Normalize + assert + shared mutate helper; no unsafe parallel writer |
| Migration | **Not required** |
| Queue cancel | Separate existing path; not inside F29 |

---

## 14. Proposed F29 files

| Path | Role |
|---|---|
| `backend/app/platform/evidence/attachment_scan_worker_result_application.py` | F29 guard entrypoint (`PROPOSED_TARGET`) |
| Small F22 internal helper (same module or extract) | Shared mutate-without-commit for locked job; **do not weaken** public F22 API |
| `backend/app/platform/evidence/tests/test_attachment_scan_worker_result_application.py` | Test matrix below |
| Tracker / master plan / claims plan / README / report / evidence | After F29 implementation acceptance |

Slice name: **0053-F29 Scanner Worker Result Application Guard**.  
**F29 implementation has not started.**

---

## 15. Complete test matrix

| # | Case | Expect |
|---|---|---|
| T1 | Other owner / missing job | not_found; no leak |
| T2 | Live EvidenceRecord missing | reject; no commit |
| T3 | Live evidence hash drift (`content_hash ≠ snapshot`) | reject; no commit |
| T4 | Expected snapshot mismatch | reject; no commit |
| T5 | All three hashes align; `reserved→completed` / `scan_passed` | apply; `completed_at` set once; attempt unchanged |
| T6 | `reserved→completed` / `scan_failed` | apply; not quarantined |
| T7 | `reserved→failed` / `scan_error` | apply; F21-normalized errors |
| T8 | Exact-match terminal replay (all 6 fields) | soft success; timestamps stable; attempt unchanged |
| T9 | Conflicting terminal replay (any of 6 fields) | hard reject |
| T10 | Concurrent identical double-apply | one first apply or both converge to exact-match soft success; no double timestamp rewrite |
| T11 | Concurrent conflicting double-apply | one wins; other hard-rejects or loses CAS; no torn projection |
| T12 | `CANCEL_JOB` / target `cancelled` via F29 | rejected |
| T13 | Existing `cancel_attachment_scan_job` queued/reserved | still works; unchanged |
| T14 | F22 non-worker callers via `apply_scan_job_update_plan` | behaviour not weakened |
| T15 | F29 does not bump `attempt_count` / clear `started_at` | proof |
| T16 | Evidence/claim/review unchanged | DB proof |
| T17 | No adapter/file/audit/subprocess; no routes/UI; no f0012 | AST/OpenAPI/smoke |
| T18 | No-op / non-persistable / `RESERVE_JOB` via F29 | rejected |
| T19 | F26/F27 regressions | dry-run disabled; reservation independent |
| T20 | Engine null-preservation | F22 `is not None` write rules preserved through shared mutate |

---

## 16. Risks and watch items

| ID | Status |
|---|---|
| D1 Idempotent full six-field projection | **Accepted** |
| D2 No CANCEL / RESERVE / NO_OP in F29 | **Accepted** |
| D3 Live evidence hash mandatory (triple) | **Accepted** |
| Concurrency lock/CAS + one txn | **Accepted** — prefer `FOR UPDATE` + shared F22 mutate |
| Consistent lock order | **Accepted** — job then evidence |
| D8 Phase name F29 | **Accepted** |
| Dual reserve (F27 vs F22) | Workers reserve via F27; F22 public reserve unchanged |
| Queue cancel `safe_error_code` vs F21 allowlist | Out of F29 |
| Stuck reserved / no TTL | Out of F28/F29 |
| No retryable status | Confirmed |

**Watch:** F29 must extract/share F22 mutate logic carefully so public F22 is not silently given terminal soft-replay or narrowed transitions. Scanner engine, worker loop, quarantine, audit, admin and UI remain absent/deferred.

---

## 17. Scope guard

```
0053_F28_SCOPE_OK:
  planning_only=true;
  mutates_code=false;
  f29_name=0053-F29_Scanner_Worker_Result_Application_Guard;
  f29_transitions=reserved->completed|reserved->failed;
  f29_cancel_job=false;
  f29_reserve_job=false;
  f29_no_op=false;
  queue_cancel_remains=true;
  idempotent_replay=exact_match_full_normalized_writable_projection;
  projection=job_status,attachment_safety_status,engine_name,engine_version,safe_error_code,safe_error_message;
  timestamps_not_in_equivalence=true;
  timestamps_never_rewritten_on_replay=true;
  attempt_count_unchanged_on_result_apply=true;
  live_evidence_hash_guard=mandatory_db_only;
  triple_hash=evidence.content_hash==job.snapshot==expected_snapshot;
  evidence_owner_scoped_read_only=true;
  concurrency=row_lock_for_update_or_atomic_cas_in_one_txn;
  lock_order=attachment_scan_job_then_evidence_record;
  reuse_f22_policy_guards=true;
  shared_mutate_without_commit=true;
  no_parallel_persistence_path=true;
  f22_non_worker_api_not_weakened=true;
  active_unique_index_insufficient_for_terminal_writes=true;
  no_migration;
  no_scanner_engine; no_adapter_execution; no_worker_loop; no_startup_registration;
  no_file_read; no_subprocess_network_ocr_llm; no_quarantine_move; no_audit_emit;
  no_routes_ui; no_evidence_claim_review_mutation;
  public_safety_remains=scan_not_available
```

---

## 18. Accepted decision

`0053_F28_SCANNER_WORKER_RESULT_APPLICATION_PLAN_ACCEPTED_READY_FOR_F29`

- F27 = accepted and completed.
- F28 planning = accepted and completed.
- F29 implementation has **not** started.
- All scanner-engine, worker-loop, quarantine, audit, admin and UI work remains absent/deferred.

---

## 19. Exact next gate

**0053-F29 Scanner Worker Result Application Guard**

Implement only the F29 guard per this accepted contract. Do not expand into scanner execution, worker loop, quarantine move, audit emission, admin routes or frontend scan UI.
