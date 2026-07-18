# CareerKundi 0053-F30 Scanner Worker Single-Job Orchestration Planning

## Accepted decision

`0053_F30_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_PLAN_ACCEPTED_READY_FOR_F31_PREPARATION`

F30 is **planning and contract definition only**. No F31 implementation is authorised by this document. F31 implementation has **not** started. No backend/frontend application code, model or migration is changed by F30.

Prior accepted gate: `0053_F29_SCANNER_WORKER_RESULT_APPLICATION_GUARD_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_F30_PLANNING`.

---

## 1. Repository baseline

| Field | Value | State |
|---|---|---|
| Worktree | `/Users/tariqnasheed/Desktop/Career_Kundi_2_F3` | `EVIDENCE_BACKED_CURRENT` |
| Branch | `main` | `EVIDENCE_BACKED_CURRENT` |
| HEAD at F30 planning | `296f174f9a733ac45548c6cdfc6c3dfeff717dfc` | `EVIDENCE_BACKED_CURRENT` |
| origin/main at F30 planning | `296f174f9a733ac45548c6cdfc6c3dfeff717dfc` | `EVIDENCE_BACKED_CURRENT` |
| Divergence at F30 planning | `0 0` | `EVIDENCE_BACKED_CURRENT` |
| Prior accepted gate | `0053_F29_SCANNER_WORKER_RESULT_APPLICATION_GUARD_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_F30_PLANNING` | `EVIDENCE_BACKED_CURRENT` |
| Foundation head | `f0011_attachment_scan_queue` (no `f0012*`) | `EVIDENCE_BACKED_CURRENT` |
| Dialect | PostgreSQL (`asyncpg` runtime; `psycopg2` migrations/disposable tests) | `EVIDENCE_BACKED_CURRENT` |
| Configured adapter | `noop_unavailable` (`availability=unavailable`) | `EVIDENCE_BACKED_CURRENT` |
| Known local dirt (preserved) | `.env`, `backend/.env`, `backend/data/knowledge_graph.gpickle`, `documents/`, locally excluded prototype assets | `EVIDENCE_BACKED_CURRENT` |

---

## 2. Capability inventory (what already exists)

| Path / symbol | Role | F31 use |
|---|---|---|
| `attachment_scanner_adapter.py` — `AttachmentScannerAdapter` Protocol, `ScannerAdapterInfo`, `ScannerAdapterCapability`, `get_configured_attachment_scanner_adapter()` | Adapter seam + factory (returns noop) | **Preflight source** |
| `attachment_scan_worker.py` — `ScannerVerdict`, `ScanResultContract`, `ScanJobUpdatePlan`, `ScanWorkerAction`, `build_scan_job_update_from_result`, `plan_when_scanner_unavailable` | F17 result→plan mapping | Post-reservation plan build |
| `attachment_scan_result_persistence.py` — `plan_is_persistable`, `normalize_scan_job_update_plan`, `assert_scan_job_update_allowed` | F22 persistence policy | Reused **inside F29 only** |
| `attachment_scan_worker_reservation.py` — `reserve_attachment_scan_job_for_worker`, `ScanWorkerReservationResult`, `ScanWorkerReservationDecision` | F27 `queued→reserved` | **Boundary 1** |
| `attachment_scan_worker_result_application.py` — `apply_attachment_scan_worker_result`, `ScanWorkerResultApplicationDecision` | F29 guarded terminal apply | **Boundary 3** |
| `attachment_scan_worker_dry_run.py` — disabled runner, `assert_scan_worker_runner_disabled` | F26 dry-run (disabled) | Must stay unchanged |
| `attachment_scan_queue.py` — `get_attachment_scan_job_for_owner`, statuses | Owner-scoped loader | Authoritative reload fallback |
| `app.db.session` — `async_session_factory` / `AsyncSessionLocal` (`async_sessionmaker`) | Session factory | **Three short-lived sessions** |
| `app.db.models.attachment_scan.AttachmentScanJob` | Job row; carries `content_hash_snapshot`, `mime_type_snapshot`, `size_bytes_snapshot`, `evidence_id` | Authoritative snapshot source |

---

## 3. Configured adapter reality

The configured factory `get_configured_attachment_scanner_adapter()` always returns `NoopUnavailableScannerAdapter`:

- `adapter_info().availability == ScannerAvailability.UNAVAILABLE`
- `adapter_info().capabilities == (ScannerAdapterCapability.UNAVAILABLE,)`
- `scan_attachment(...)` returns `verdict=NOT_RUN`, `safe_error_code="scanner_unavailable"`; it never opens files, spawns processes, calls the network, or returns clean/passed.

The disabled local skeleton (`DisabledLocalProcessScannerAdapter`) advertises `MALWARE_SCAN` **but** keeps `availability=UNAVAILABLE`, and is never selected by the factory. Therefore **`availability` is the authoritative gate** and `MALWARE_SCAN`/`UNAVAILABLE` capabilities are secondary confirmation. Under the current repository the configured adapter is **not executable**, and that is the normal production result until a later scanner-enablement phase.

---

## 4. Capability-preflight predicate

Smallest executable-capability check — a pure predicate over `adapter_info()` only (no `scan_attachment` call, no file read, no DB access):

```
adapter_is_executable(info) :=
    info.availability == ScannerAvailability.AVAILABLE
    and ScannerAdapterCapability.MALWARE_SCAN in info.capabilities
    and ScannerAdapterCapability.UNAVAILABLE not in info.capabilities
```

- Evaluated before F27 reservation.
- Under the current repo this is `False` → orchestrator returns `scanner_unavailable` / `skipped_unavailable` and stops.
- The predicate lives in the F31 module (or a one-line helper beside the adapter). **No separate prerequisite phase is created for it.**

---

## 5. Current noop / unavailable behaviour

When the configured adapter is noop / unavailable / disabled / otherwise incapable of execution, the orchestrator:

- returns a structured `scanner_unavailable` or `skipped_unavailable` decision;
- leaves the `AttachmentScanJob` **QUEUED**;
- does **not** increment `attempt_count`;
- does **not** set `started_at`;
- does **not** call the adapter `scan_attachment` method;
- does **not** build a persistable terminal plan;
- does **not** call F27 reservation;
- does **not** call F29 result application;
- does **not** record `scan_error` merely because the platform has no configured scanner;
- does **not** fabricate `CLEAN`, `scan_passed`, or a successful engine identity.

This is the **normal production result** in this version.

---

## 6. F31 phase name

**0053-F31 Scanner Worker Single-Job Orchestration Guard** — a single supplied-job callable. No selection, polling, loop, scheduler, or real scanner. The capability preflight is folded into F31.

---

## 7. State / data-flow diagram

```
orchestrate_single_scan_job(owner_user_id, scan_job_id, expected_content_hash_snapshot)
        │
        ▼
[A] PREFLIGHT  ── adapter_info() only (no scan, no DB, no file)
        │
        ├─ not executable ─► return scanner_unavailable / skipped_unavailable
        │                    • job stays QUEUED
        │                    • attempt_count unchanged   • started_at unset
        │                    • F27 NOT called  • scan_attachment NOT called  • F29 NOT called
        │                    • NO scan_error recorded  • NO persistable plan built
        ▼ executable
[B] BOUNDARY 1: RESERVATION TXN  (short-lived AsyncSession #1)
        │  F27 reserve_attachment_scan_job_for_worker → queued→reserved,
        │  attempt_count +1, started_at set, COMMIT, capture authoritative snapshot
        │
        ├─ not RESERVED (not_found / not_queued / hash_mismatch / …) ─► return structured F27 decision (no execution)
        ▼ RESERVED  (session #1 closed — no txn/lock held)
[C] BOUNDARY 2: ADAPTER EXECUTION  (NO DB session, NO txn, NO lock)
        │  adapter.scan_attachment(**authoritative reserved-job snapshot)
        │  map result → plan
        │
        ├─ CancelledError / KeyboardInterrupt / SystemExit ─► RE-RAISE (job stays reserved → watch item)
        │
        ├─ CLEAN / MALICIOUS / SUSPICIOUS ─► persistable plan via F22 mapping
        └─ NOT_RUN / adapter-now-unavailable / error / timeout / unsupported /
           malformed return / ordinary operational Exception
                              ─► safe **persistable MARK_ERROR** plan (F21 codes)
        ▼
[D] BOUNDARY 3: RESULT-APPLICATION TXN  (short-lived AsyncSession #2)
        │  F29 apply_attachment_scan_worker_result(plan) — triple-hash, lock order, idempotency
        │
        ├─ APPLIED / ALREADY_APPLIED ─► return applied outcome
        └─ rejected (evidence_not_found / hash_mismatch / conflicting_replay /
           not_reserved / action_not_allowed / plan_not_persistable)
                              ─► return **result_application_rejected**; DB unchanged;
                                 reserved row = watch item
```

---

## 8. Three separate transaction boundaries

| Boundary | Session | Holds txn/lock during adapter? | Contents |
|---|---|---|---|
| **1 — Reservation** | short-lived `AsyncSession` #1 (from `async_session_factory`) | N/A (closes before [C]) | F27 reserve → commit → refresh → capture authoritative snapshot; session closed |
| **2 — Adapter execution** | **none** | **No — mandatory** | `adapter.scan_attachment(...)` + result→plan mapping run with **no active DB session, no open transaction, no held lock, no pending mutation** |
| **3 — Result application** | short-lived `AsyncSession` #2 | N/A | F29 opens its own lock order (`AttachmentScanJob` FOR UPDATE → `EvidenceRecord` FOR UPDATE), validates, mutates job only, commits |

**Binding rule:** a database session must not retain an active transaction, lock, or pending mutation while the adapter executes. Use **separate short-lived `AsyncSession`s per boundary** via `async_session_factory` / `AsyncSessionLocal()` (repository-compatible session-factory pattern). F31 must **not** reuse a single caller session that straddles [C].

---

## 9. Authoritative reservation snapshot requirements

- The public orchestration input is **only** `owner_user_id`, `scan_job_id`, and `expected_content_hash_snapshot`.
- Caller-provided `evidence_id`, MIME type, size, and snapshot metadata are **not trusted**.
- Adapter metadata (`evidence_id`, `content_hash_snapshot`, `mime_type_snapshot`, `size_bytes_snapshot`) must come from **the authoritative successfully reserved `AttachmentScanJob`** returned by F27, or an immediate owner-scoped database reload after reservation.
- Values are carried through **memory only**. No attachment file or storage object is read.
- **Result-object gap:** `ScanWorkerReservationResult` currently exposes only `job_id`, `owner_user_id`, `previous_status`, `new_status`, `attempt_count`, `safe_message` — **not** the snapshot fields. The `AttachmentScanJob` row does carry them.
- **Smallest result-object extension for F31 (preferred):** add a minimal immutable authoritative snapshot (`evidence_id`, `content_hash_snapshot`, `mime_type_snapshot`, `size_bytes_snapshot`) to `ScanWorkerReservationResult`, populated from the reserved+refreshed row inside F27's reservation transaction. This is additive only and does not change reservation behaviour.
- **Fallback if the extension is declined:** immediately after reservation, F31 performs an owner-scoped `get_attachment_scan_job_for_owner(...)` reload in a fresh session and reads the snapshot from that authoritative row.

---

## 10. Post-reservation safe failure materialisation

Once F27 successfully reserves the job, an actual worker attempt has started. After reservation, F31 converts each of the following into a **safe persistable `MARK_ERROR` plan** and passes it through F29:

- unexpected `NOT_RUN`
- adapter becomes unavailable after preflight
- `error`
- `timeout`
- `unsupported`
- malformed adapter return
- ordinary operational `Exception` from adapter invocation or result mapping

Rules:

- Use **F21-safe codes and redacted messages**.
- **Never** fabricate `CLEAN`, `scan_passed`, or a successful engine identity.
- `build_scan_job_update_from_result` maps `NOT_RUN → NO_OP` and always emits `apply_to_database=False`; F31 must therefore **materialise a persistable `MARK_ERROR`** (action `MARK_ERROR`, `apply_to_database=True`, F21-normalized code/message) so `plan_is_persistable` passes and F29 accepts it.
- The plan is applied **only through F29** (never a direct write, never a parallel persistence path).

---

## 11. F29 rejection handling

If F29 rejects after adapter execution because of missing evidence, live evidence hash drift, expected hash mismatch, conflicting replay, invalid state, or any other F29 guard, then F31:

- does **not** bypass F29;
- does **not** force a terminal state;
- does **not** auto-cancel;
- returns a structured `result_application_rejected` outcome;
- leaves the current database state unchanged.

A remaining reserved row is an explicit recovery/watch condition until a later lease/reclaim phase.

---

## 12. Process-cancellation behaviour

F31 must **never** catch or suppress:

- `asyncio.CancelledError`
- `KeyboardInterrupt`
- `SystemExit`

These process-level interruptions are re-raised. They may leave the job reserved; that is recorded as the existing crash-recovery watch item. F31 does **not** add cancellation, lease, TTL, or reclaim behaviour.

---

## 13. Crash and recovery analysis

| Event | Handling | Residual state |
|---|---|---|
| Preflight not executable | Return before reservation | Job **QUEUED**, untouched — nothing to recover |
| F27 rejects (`not_queued`/`hash_mismatch`/`not_found`) | Return F27 decision | No mutation |
| Adapter raises ordinary `Exception` | Convert → persistable `MARK_ERROR` → F29 | Job terminalized safely |
| Adapter returns `NOT_RUN` / unavailable / malformed after reservation | Convert → persistable `MARK_ERROR` → F29 | Job terminalized safely |
| **`asyncio.CancelledError` / `KeyboardInterrupt` / `SystemExit`** | **Never swallowed — re-raised** | Job may remain **RESERVED** → documented crash-recovery watch item |
| F29 rejects after execution | Return `result_application_rejected`; no forced state | Job remains **RESERVED** → watch item |

No cancellation, lease, TTL, or reclaim behaviour is added in F31.

---

## 14. Proposed F31 scope

1. One public async callable, e.g. `orchestrate_single_scan_job(owner_user_id, scan_job_id, expected_content_hash_snapshot)`, returning a structured `ScanWorkerOrchestrationResult` (outcome enum + safe message + carried F27/F29 decisions).
2. Adapter-capability preflight over `adapter_info()`.
3. Reservation via F27 in Boundary-1 session; capture authoritative snapshot.
4. Adapter execution in Boundary 2 with **no** DB session/txn/lock.
5. Failure → **persistable `MARK_ERROR`** conversion with F21-safe codes; F29 apply in Boundary-3 session.
6. Structured `result_application_rejected` passthrough on F29 rejection.
7. Re-raise process-level interruptions; document reserved-row watch item.
8. Introspection summary (`orchestration_guard_summary()`) with all capability flags `False`.
9. Minimal, documented F27 `ScanWorkerReservationResult` authoritative snapshot extension (or reload fallback).

---

## 15. Explicit exclusions (F31)

F31 must **not** add any of:

- automatic oldest/next-job selection
- `SKIP LOCKED`
- queue polling
- continuous worker loop
- startup registration
- scheduler / background service
- real scanner dependency
- attachment file / storage read
- subprocess / network / OCR / LLM
- quarantine move
- audit emission
- routes
- frontend scanner UI
- claim or `ReviewRequest` mutation
- `EvidenceRecord` mutation
- database migration (`f0012+`)
- lease / TTL / reclaim behaviour
- recording `scan_error` merely because no scanner is configured
- fabricated `CLEAN` / `scan_passed` / engine identity

---

## 16. Proposed F31 files

| Path | Role |
|---|---|
| `backend/app/platform/evidence/attachment_scan_worker_orchestration.py` | F31 single-job orchestration guard (`PROPOSED_TARGET`) |
| `backend/app/platform/evidence/attachment_scan_worker_reservation.py` | **Minimal** additive `ScanWorkerReservationResult` snapshot extension |
| `backend/app/platform/evidence/tests/test_attachment_scan_worker_orchestration.py` | Test contracts §17 |
| Tracker / master plan / claims plan / README / report / evidence | After F31 implementation acceptance only |

**F31 implementation has not started.**

---

## 17. Complete test matrix

| # | Contract | Expect |
|---|---|---|
| TC1 | Configured noop preflight | Job stays **QUEUED**, unchanged; `scanner_unavailable`/`skipped_unavailable` |
| TC2 | Unavailable preflight | `attempt_count` **not incremented** |
| TC3 | Unavailable preflight | `started_at` **not set** |
| TC4 | Unavailable preflight | F27 **and** F29 **not called** (mocks unused) |
| TC5 | Executable **test** adapter (`available` + `MALWARE_SCAN`) | Passes preflight, reserves via F27 |
| TC6 | Post-reservation `NOT_RUN` | Converted to persistable **MARK_ERROR** through F29 |
| TC7 | Adapter operational exception after reservation | Converted to **MARK_ERROR** through F29 (not swallowed as success) |
| TC8 | Malformed adapter return | Safe **MARK_ERROR** through F29 (no crash, no CLEAN) |
| TC9 | `timeout` / `unsupported` / `error` verdicts | Terminalize safely via F29 MARK_ERROR |
| TC10 | Unavailable/noop path | **No** `CLEAN` / `scan_passed` / engine identity fabricated |
| TC11 | Adapter invocation args | Only **authoritative reserved-job snapshots**, never caller-supplied metadata |
| TC12 | During adapter invocation | **No active DB transaction/lock/pending mutation** (session boundary asserted) |
| TC13 | F29 live-hash drift after execution | Returns **`result_application_rejected`**; DB unchanged |
| TC14 | F29 rejection | **No** auto-cancel, **no** forced terminal state, guards not bypassed |
| TC15 | Process cancellation (`CancelledError`/`KeyboardInterrupt`/`SystemExit`) | Re-raised; reserved-row **watch item** documented (not swallowed) |
| TC16 | F26 dry-run | Runner remains **disabled**; behaviour unchanged |
| TC17 | Structural | No queue polling / loop / startup / routes / UI / migration (AST + OpenAPI + smoke) |
| TC18 | Authoritative-snapshot reservation | Adapter receives reserved-job values even when caller passes wrong mime/size/evidence_id |
| TC19 | F27 rejection (`not_queued`/`hash_mismatch`) | Adapter **not** invoked; structured F27 decision returned |
| TC20 | Three-boundary sessions | Reservation, execution, and application use distinct short-lived sessions |

---

## 18. Risks and watch items

| ID | Item | Status |
|---|---|---|
| D1 | Adapter-capability preflight over `adapter_info()`; no separate phase | **Accepted** |
| D2 | Post-reservation failures → persistable `MARK_ERROR` via F29; F21-safe codes; never fake CLEAN | **Accepted** |
| D3 | Authoritative snapshot from reserved row / owner-scoped reload; caller metadata untrusted; carried in memory only | **Accepted** (F27 result extension documented) |
| D4 | Three separate boundaries; no txn/lock during adapter; separate short-lived `AsyncSession`s | **Accepted** |
| D5 | F29 rejection → `result_application_rejected`; no bypass/force/auto-cancel; reserved row = watch item | **Accepted** |
| D6 | F31 = one supplied-job callable; no selection/polling/loop/scheduler/scanner/migration | **Accepted** |
| W1 | Stuck-reserved after process interruption or F29 rejection | **Watch** — deferred to later lease/reclaim phase |
| W2 | `build_scan_job_update_from_result` emits `apply_to_database=False`; F31 must force persistable `MARK_ERROR` | **Accepted** — explicit in mapping |
| W3 | Real scanner engine, worker loop, quarantine, audit, admin, UI | Deferred |
| W4 | Configured adapter remains noop/unavailable until a later scanner-enablement phase | Confirmed |

Prototype refs P39, P40, P41, P46 remain **future UX context only**.

---

## 19. Scope token

```
0053_F30_SCOPE_OK:
  planning_only=true;
  mutates_code=false;
  f31_name=0053-F31_Scanner_Worker_Single_Job_Orchestration_Guard;
  f31_shape=single_supplied_job_callable;
  preflight=adapter_info_availability_and_capability_only;
  preflight_availability_must_be_available=true;
  preflight_malware_scan_capability_required=true;
  preflight_unavailable_capability_forbidden=true;
  preflight_no_scan_call=true; preflight_no_file_read=true; preflight_no_db=true;
  noop_result=scanner_unavailable_or_skipped_unavailable;
  unavailable_leaves_job_queued=true;
  unavailable_no_attempt_increment=true; unavailable_no_started_at=true;
  unavailable_no_f27_call=true; unavailable_no_scan_attachment_call=true; unavailable_no_f29_call=true;
  unavailable_no_scan_error_record=true; unavailable_no_persistable_plan=true;
  post_reservation_failures=persistable_mark_error_through_f29;
  post_reservation_failure_set=not_run,unavailable,timeout,unsupported,error,malformed,operational_exception;
  failure_codes=f21_safe_redacted; never_fabricate_clean_or_scan_passed=true;
  do_not_swallow=CancelledError,KeyboardInterrupt,SystemExit;
  interruption_reserved_row=documented_watch_item;
  public_input=owner_user_id,scan_job_id,expected_content_hash_snapshot;
  snapshot_source=reserved_job_or_owner_scoped_reload; caller_metadata_untrusted=true;
  snapshot_carried_in_memory_only=true; no_file_or_storage_read=true;
  f27_result_extension=minimal_immutable_additive_snapshot_or_reload_fallback;
  boundaries=three_separate: reservation_txn|adapter_execution_no_txn|f29_result_application_txn;
  no_txn_lock_or_pending_mutation_during_adapter=true;
  session_pattern=separate_short_lived_asyncsessions_via_async_session_factory;
  f29_rejection=result_application_rejected; no_bypass=true; no_force_terminal=true; no_auto_cancel=true;
  db_unchanged_on_rejection=true; reserved_row_on_rejection=watch_item;
  no_oldest_job_selection; no_skip_locked; no_queue_polling; no_worker_loop;
  no_startup_registration; no_scheduler_or_background_service;
  no_real_scanner_dependency; no_attachment_file_or_storage_read;
  no_quarantine_move; no_audit_emit; no_routes; no_frontend_scanner_ui;
  no_claim_or_reviewrequest_mutation; no_evidence_mutation; no_migration;
  no_lease_ttl_reclaim_in_f31;
  f26_dry_run_unchanged=true;
  configured_adapter=noop_unavailable
```

---

## 20. Exact next gate

**0053-F31 Scanner Worker Single-Job Orchestration Guard** — implement only the single supplied-job callable per this accepted contract: preflight → F27 reservation → adapter execution (no held transaction) → F29 result application or `result_application_rejected`. Do not expand into selection, polling, loops, scheduling, a real scanner, file reads, quarantine, audit, routes, UI, or migration.

`0053_F30_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_PLAN_ACCEPTED_READY_FOR_F31_PREPARATION`
