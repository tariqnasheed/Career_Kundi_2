# CareerKundi 0053-F29 Scanner Worker Result Application Guard

## Decision (pending owner review)

`0053_F29_SCANNER_WORKER_RESULT_APPLICATION_GUARD_COMPLETE_READY_FOR_REVIEW`

F29 implements the smallest safe worker-result application guard. It applies an
already-produced, persistable `ScanJobUpdatePlan` to an `AttachmentScanJob` only
when owner, state, triple-hash, policy, idempotency and PostgreSQL concurrency
requirements pass.

Applying a worker result is **not** scanning and **not** verification.

---

## 1. Prototype Impact Matrix

| Field | Content |
|---|---|
| Phase | 0053-F29 Scanner Worker Result Application Guard |
| Page references | P39, P40, P41, P46 — **future UX context only** |
| Sheet references | Relevant P39/P40/P41 sheets and P46 recovery/error sheets as context only |
| Current routes | No worker/scan/quarantine/audit/admin result-application routes |
| Current repository paths | `attachment_scan_worker_result_application.py`; F22 shared mutate helper |
| Approved target | Attachment-safety job terminalization under guarded persistence; not verification UI |
| Delta | Locked apply for `reserved → completed|failed` with triple-hash + six-field replay |
| Backend dependencies | F22 normalize/assert/mutate; F27 reservation; PostgreSQL `FOR UPDATE` |
| Privacy/security boundary | Owner-scoped job + evidence; DB-only hash guard; no file read; EvidenceRecord read-only |
| Tests | `test_attachment_scan_worker_result_application.py` |
| Known limitations | No scanner engine, worker loop, quarantine move, audit, admin/UI |
| Next gate | Owner review of F29 |

The approved prototype must **not** be used to invent frontend scan, quarantine,
audit or admin UI in F29.

---

## 2. Exact F29 state surface

```
reserved ──► completed
reserved ──► failed
```

Allowed actions:

- `COMPLETE_PASSED`
- `COMPLETE_FAILED`
- `QUARANTINE_REQUIRED` (job `completed`, safety stays `scan_failed`; never `quarantined`)
- `MARK_ERROR`

Rejected:

- `CANCEL_JOB` / target `cancelled`
- `RESERVE_JOB` / source `queued` (reservation remains F27)
- `NO_OP` / `apply_to_database=False`
- any unsupported target or action

Owner-scoped `cancel_attachment_scan_job` remains unchanged and outside F29.

---

## 3. Owner and triple-hash guards

Transaction loads:

1. Owner-scoped `AttachmentScanJob` (`FOR UPDATE`)
2. Owner-scoped linked `EvidenceRecord` (`FOR UPDATE`)

Require:

```
EvidenceRecord.content_hash
  ==
AttachmentScanJob.content_hash_snapshot
  ==
expected_content_hash_snapshot
```

Rules:

- Missing job → safe `not_found` (no other-owner leak)
- Missing / other-owner evidence → `evidence_not_found`
- Any hash mismatch → `hash_mismatch`
- No file or storage object opened
- `EvidenceRecord` is read-only; never mutated

---

## 4. Transaction and lock order

Mandatory lock order (deadlock avoidance):

1. `AttachmentScanJob` first
2. `EvidenceRecord` second

Flow inside one transaction:

1. Lock job
2. Lock evidence
3. Revalidate status + triple-hash
4. Normalize plan (F21 safe-error helpers via F22)
5. Exact-match terminal soft replay or conflicting reject
6. Assert F22 policy on reserved pre-image
7. Mutate job via shared helper (no fetch/commit inside helper)
8. Commit exactly once on first apply

F29 does **not** call public unlocked `apply_scan_job_update_plan` as the outer
transaction (that path re-fetches and commits, breaking the lock boundary).

Rejected paths roll back; no partial job mutation remains.

---

## 5. Full six-field idempotency projection

Exact-match terminal replay compares the effective normalized post-application
projection (F22 non-`None` write semantics):

1. `job_status`
2. `attachment_safety_status`
3. `engine_name`
4. `engine_version`
5. `safe_error_code`
6. `safe_error_message`

- Exact match → `already_applied` (no field writes; no `completed_at` /
  `updated_at` rewrite; no `attempt_count` change)
- Any mismatch → `conflicting_replay` (no mutation)
- Timestamps are not part of equivalence

---

## 6. F22 policy reuse

Reused from `attachment_scan_result_persistence.py`:

- `normalize_scan_job_update_plan`
- `assert_scan_job_update_allowed`
- `ALLOWED_JOB_TRANSITIONS` / `ALLOWED_SCAN_JOB_UPDATE_FIELDS` (via assert)
- F21 safe-error normalization
- New internal helper: `apply_normalized_scan_job_update_to_loaded_job`

Public `apply_scan_job_update_plan` behaviour for non-worker callers is unchanged
(now delegates field writes to the shared helper).

---

## 7. Allowed and forbidden mutations

**Allowed on first apply from `reserved`:**

- `job_status`, `attachment_safety_status`
- `engine_name` / `engine_version` when plan provides non-`None`
- `safe_error_code` / `safe_error_message` (F21-normalized)
- `completed_at` set once for `completed` or `failed`
- `updated_at` via mixin on real write

**Must not change:**

- `attempt_count`, `started_at`, `cancelled_at`
- snapshot / identity fields
- `EvidenceRecord`, claim `support_status` / `verification_status`, `ReviewRequest`

---

## 8. Public entrypoint

Module: `backend/app/platform/evidence/attachment_scan_worker_result_application.py`

```
apply_attachment_scan_worker_result(
    db,
    *,
    owner_user_id,
    scan_job_id,
    expected_content_hash_snapshot,
    plan: ScanJobUpdatePlan,
) -> ScanWorkerResultApplicationResult
```

Decisions: `applied`, `already_applied`, `not_found`, `evidence_not_found`,
`hash_mismatch`, `not_reserved`, `action_not_allowed`, `plan_not_persistable`,
`conflicting_replay`.

---

## 9. Absent / deferred

Not implemented in F29:

- scanner engine / adapter execution
- worker loop / startup registration
- file or storage read / subprocess / network / OCR / parsing / LLM
- quarantine movement / audit emission
- worker/admin/scan/quarantine/audit API
- frontend scan/quarantine/audit/admin UI
- `f0012+` migration

---

## 10. Tests and evidence

- Tests: `backend/app/platform/evidence/tests/test_attachment_scan_worker_result_application.py`
- Evidence: `~/Desktop/CareerKundi_0053_F29_Scanner_Worker_Result_Application_Guard_Evidence.txt`
- Scope token: `0053_F29_SCOPE_OK`

---

## 11. Next gate

Owner review of F29. Do not mark later scanner work implemented.
