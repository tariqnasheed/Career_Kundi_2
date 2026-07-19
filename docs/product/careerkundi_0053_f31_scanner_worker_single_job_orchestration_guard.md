# CareerKundi 0053-F31 Scanner Worker Single-Job Orchestration Guard

## Status (historical contemporaneous readiness)

`0053_F31_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_GUARD_COMPLETE_READY_FOR_REVIEW`

Implements the single supplied-job orchestration callable accepted by the F30 plan. **No worker loop, queue polling, job selection, startup registration, scheduler, real scanner dependency, file/storage read, quarantine move, audit, routes, UI, or migration.** Orchestrating one guarded scan attempt is not scanning and is not verification.

Historical next gate at completion: **owner review of F31**.

### ACCEPTANCE / CURRENT STATUS (Programme 0.4 — 2026-07-19)

- **Accepted** as the current scanner checkpoint with token
  `0053_F31_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_GUARD_ACCEPTED_WITH_WATCH_ITEMS`.
- Canonical F31 evidence (byte-unchanged copy of approved readable source; historical Desktop/F3 execution paths inside the evidence body are preserved):
  `docs/evidence/0053/CareerKundi_0053_F31_Scanner_Worker_Single_Job_Orchestration_Guard_Evidence.txt`
- Former F3 worktree and hold branch were later retired safely; official repository is `/Users/tariqnasheed/Desktop/Career_Kundi_2`.
- **F32 has not started.**
- **Programme 0.4** implementation is complete and accepted. **Programme 1** is the next authorized planning gate and has not started. **F32 has not started.** No scanner capability expansion occurred. Feature branch remains preserved for Programme 8.
- Watch items and explicit exclusions in §§10–12 remain binding (no engine, polling, lease/TTL/reclaim, quarantine, admin/UI).

---

## 1. Module and entrypoint

| Path / symbol | Role |
|---|---|
| `backend/app/platform/evidence/attachment_scan_worker_orchestration.py` — `orchestrate_attachment_scan_job` | F31 single-job orchestration guard |
| `attachment_scan_worker_orchestration.adapter_is_executable` | Adapter capability preflight predicate |
| `attachment_scan_worker_orchestration.ScanWorkerOrchestrationOutcome` / `ScanWorkerOrchestrationResult` | Structured owner-safe outcome |
| `attachment_scan_worker_orchestration.orchestration_guard_summary` | Safe introspection (all effect flags `False`) |
| `attachment_scan_worker_reservation.ReservedJobSnapshot` (additive) | Immutable authoritative reserved-row snapshot on the F27 result |

Public callable:

```
orchestrate_attachment_scan_job(
    *,
    owner_user_id,
    scan_job_id,
    expected_content_hash_snapshot,
    session_factory=async_session_factory,   # repository session factory
    adapter_factory=get_configured_attachment_scanner_adapter,  # test-only seam
) -> ScanWorkerOrchestrationResult
```

The product-facing input surface is **only** `owner_user_id`, `scan_job_id`, `expected_content_hash_snapshot`. It does not accept `evidence_id`, MIME, size, storage path, attachment bytes, snapshot metadata, or a caller-selected production adapter identity. `adapter_factory` is a test-only injection seam; production resolves the configured factory.

Outcomes: `scanner_unavailable` / `skipped_unavailable`, `reservation_rejected`, `applied`, `already_applied`, `result_application_rejected`. The result never carries file paths, storage URIs, raw exceptions, internal database details, or another owner's resource existence.

---

## 2. Adapter capability preflight

Before any database lookup or F27 reservation, `adapter_info()` (only) is read:

```
adapter_is_executable(info) :=
    info.availability == ScannerAvailability.AVAILABLE
    and ScannerAdapterCapability.MALWARE_SCAN in info.capabilities
    and ScannerAdapterCapability.UNAVAILABLE not in info.capabilities
```

`scan_attachment` is **not** called during preflight. If `adapter_info()` raises an ordinary operational exception, the orchestrator returns the same safe unavailable outcome (redacted; no raw exception) **before** any reservation.

---

## 3. Normal configured noop/unavailable behaviour

The configured factory returns `noop_unavailable` (`availability=unavailable`, `capabilities=(unavailable,)`), so preflight fails and this is the **normal production result**. On the unavailable path the orchestrator:

- returns a generic `scanner_unavailable` / `skipped_unavailable` outcome;
- leaves the `AttachmentScanJob` **queued and untouched**;
- does **not** call F27, `scan_attachment`, or F29;
- does **not** increment `attempt_count` or set `started_at`;
- does **not** create `scan_error`;
- does **not** fabricate `CLEAN` / `scan_passed` / an engine identity;
- opens **no** database session (verified: the unavailable path never touches the DB).

The unavailable result is generic and reveals nothing about whether the supplied job exists, belongs to another owner, or has another state.

---

## 4. Authoritative reservation snapshot (F27 additive extension)

`ScanWorkerReservationResult` gained an additive, immutable `snapshot: ReservedJobSnapshot | None` field, populated from the reserved-and-refreshed row inside F27:

- `job_id`, `owner_user_id`, `evidence_id`, `content_hash_snapshot`, `mime_type_snapshot`, `size_bytes_snapshot`.

Rules:

- Additive only — existing F27 decisions, result fields, and callers are unchanged; the field defaults to `None` and is populated **only** on a successful reservation.
- Failure results carry `snapshot=None` (no other-owner metadata leak).
- The adapter receives adapter metadata **only** from this snapshot (or, equivalently, an owner-scoped reload). Caller-provided metadata is never trusted, and no file or storage object is read.

---

## 5. Three separate database boundaries

| Boundary | Session | Active during adapter? | Work |
|---|---|---|---|
| 1 — reservation | short-lived `AsyncSession` | closed before boundary 2 | F27 `reserve_attachment_scan_job_for_worker` → commit/refresh → capture immutable snapshot |
| 2 — adapter execution | **none** | **no** active session / transaction / lock / pending mutation | `adapter.scan_attachment(**authoritative snapshot)` + result→plan mapping |
| 3 — result application | new short-lived `AsyncSession` | n/a | F29 `apply_attachment_scan_worker_result(plan)` |

Sessions come from the repository session factory (`async_session_factory` / `AsyncSessionLocal`). A tracking-session test proves the adapter observes **zero** active sessions during execution and that reservation and application use **two distinct** short-lived sessions.

---

## 6. Post-reservation safe error materialisation

After a successful reservation an actual worker attempt has started. Legitimate verdicts reuse the F17 result→plan mapping (`build_scan_job_update_from_result`) rebuilt as persistable through the F22 helper (no duplicated normalization):

- `CLEAN` → `COMPLETE_PASSED` / `scan_passed` (real engine identity carried);
- `MALICIOUS` / `SUSPICIOUS` → `QUARANTINE_REQUIRED` / **`scan_failed`** (never `quarantined`, no file move);
- `TIMEOUT` / `ERROR` / `UNSUPPORTED` → `MARK_ERROR` / `scan_error` (real engine identity carried).

These outcomes are converted to a safe **persistable `MARK_ERROR`** plan (F21-safe code, no fabricated engine identity):

- unexpected `NOT_RUN`;
- adapter becomes unavailable after preflight;
- malformed return type or malformed result object;
- ordinary operational exception from adapter invocation;
- ordinary operational exception during result mapping.

Safe codes are drawn from the F21 allow-list (`scanner_unavailable`, `scanner_timeout`, `scanner_error`, `scanner_unsupported`, `scanner_output_unavailable`); messages are F21-normalized and path/URI-redacted. The orchestrator never converts unavailable/malformed output to `CLEAN` or `scan_passed`, and never fabricates an engine name/version on these paths.

---

## 7. F29-only application and rejection handling

Every persistable terminal result is applied **only** through F29 (`apply_attachment_scan_worker_result`). The orchestrator never imports or calls the public unlocked `apply_scan_job_update_plan`, never locks rows itself, and never mutates the job outside F29.

F29 outcome mapping:

- `APPLIED` → `applied`;
- `ALREADY_APPLIED` → `already_applied`;
- every guard rejection (`EVIDENCE_NOT_FOUND`, `HASH_MISMATCH`, `CONFLICTING_REPLAY`, `NOT_RESERVED`, `ACTION_NOT_ALLOWED`, `PLAN_NOT_PERSISTABLE`) → `result_application_rejected`.

On rejection the orchestrator does **not** bypass F29, does **not** force a terminal state, does **not** auto-cancel, does **not** call F22 directly, and does **not** retry with weakened guards. The database state is left unchanged and the row remains reserved (a documented recovery/watch item).

---

## 8. Process-cancellation behaviour

`asyncio.CancelledError`, `KeyboardInterrupt`, and `SystemExit` are **never** caught or suppressed (no `except BaseException`); they propagate. An interruption after reservation may leave the job reserved — the existing crash-recovery watch item. No cancellation, lease, TTL, or reclaim behaviour is added in F31.

---

## 9. Crash / recovery

| Event | Handling | Residual state |
|---|---|---|
| Preflight not executable | return before reservation | job **queued**, untouched |
| adapter_info exception | safe unavailable, before reservation | job **queued**, untouched |
| F27 rejects (not_found/not_queued/hash_mismatch) | `reservation_rejected`; adapter not invoked | no mutation |
| Adapter error / NOT_RUN / malformed / operational exception | persistable `MARK_ERROR` via F29 | job terminalized safely |
| `CancelledError` / `KeyboardInterrupt` / `SystemExit` | re-raised | job may stay **reserved** → watch item |
| F29 guard rejection | `result_application_rejected`; state unchanged | job stays **reserved** → watch item |

---

## 10. Allowed and forbidden effects

**Allowed:** read `adapter_info()`; F27 reservation (queued→reserved); invoke the configured adapter seam with authoritative snapshot; build a persistable plan via F17/F22 helpers; apply via F29; return a structured owner-safe outcome.

**Forbidden (and absent):** worker loop; queue polling; automatic/oldest-job selection; `SKIP LOCKED`; startup registration; scheduler/background service; real scanner dependency; attachment file/storage read; subprocess/network/OCR/LLM; quarantine move; audit emission; routes; frontend scanner UI; claim/`ReviewRequest`/`EvidenceRecord` mutation; database migration (`f0012+`); lease/TTL/reclaim; direct F22 apply; `scan_error` merely because no scanner is configured; fabricated `CLEAN`/`scan_passed`/engine identity.

---

## 11. Tests and evidence

`backend/app/platform/evidence/tests/test_attachment_scan_worker_orchestration.py` — **41 tests** (19 static/non-DB + 22 disposable-PostgreSQL), covering the F30 test contract 1–55 (see the requirement map in the test module docstring). Highlights:

- configured noop preflight → unavailable, no DB, no scan, no F27/F29 (BoomSession);
- unavailable preflight leaves a queued job unchanged (status/attempt/started_at);
- executable test adapter passes preflight, reserves, applies CLEAN → completed/scan_passed;
- adapter receives only authoritative reserved-row snapshot; public surface rejects attachment metadata;
- reservation session closed and **zero** active sessions during adapter; application uses a new session;
- MALICIOUS/SUSPICIOUS → scan_failed (never quarantined); TIMEOUT/ERROR/UNSUPPORTED → MARK_ERROR;
- NOT_RUN / adapter-now-unavailable / malformed return / adapter exception / mapping exception → safe MARK_ERROR, no fake CLEAN, no fabricated engine, redacted messages;
- F29 decision mapping (parametrized) incl. `conflicting_replay` → result_application_rejected; real hash-drift rejection leaves the job reserved (no auto-cancel);
- `CancelledError` / `KeyboardInterrupt` / `SystemExit` propagate and leave the job reserved;
- two concurrent same-job calls use independent PostgreSQL sessions; the adapter runs only for a reserved call; final state is one coherent terminal projection with `attempt_count == 1`;
- no worker loop / startup / routes / UI / migration / forbidden imports; F26 dry-run unchanged.

Evidence (canonical): `docs/evidence/0053/CareerKundi_0053_F31_Scanner_Worker_Single_Job_Orchestration_Guard_Evidence.txt`.
Historical Desktop pointer (may remain inside the evidence body): `~/Desktop/CareerKundi_0053_F31_Scanner_Worker_Single_Job_Orchestration_Guard_Evidence.txt`.

---

## 12. Remaining watch items

- **Stuck-reserved recovery** after process interruption or F29 rejection remains a watch item; no lease/TTL/reclaim (deferred).
- Configured adapter remains **noop/unavailable** until a later scanner-enablement phase; no scanner engine, worker loop, quarantine, audit, admin, or UI.
- Pre-existing, unrelated: `test_mapping_helper_not_imported_by_api_routes` fails because it `rglob`s `app/api/routes/` and reaches `routes/tests/test_evidence_attachment_delete_api.py` — not caused by F31 (F31 touches no routes).
- Pre-existing: `JobSearchPage.test.tsx` still absent.

Prototype pages P39, P40, P41, P46 remain **future UX context only**; F31 creates no UI from them.

---

## 13. Next gate

**Historical (at F31 completion):** owner review of 0053-F31; consolidation into `/Users/tariqnasheed/Desktop/Career_Kundi_2`.

**Live:** F31 is accepted (`0053_F31_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_GUARD_ACCEPTED_WITH_WATCH_ITEMS`) as the current scanner checkpoint. Official workspace consolidation is complete; F3 is retired. **Programme 0.4** implementation is complete and accepted. Next authorized planning gate: **Programme 1** (not started). **Do not begin F32.**
