# CareerKundi Agent Instructions

Read these files before any substantive CareerKundi task:

1. `docs/product/careerkundi_approved_prototype_governance.md`
2. `docs/product/careerkundi_approved_prototype_page_registry.md`
3. `docs/product/careerkundi_prototype_traceability_contract.md`
4. The current phase plan, live tracker, master build plan and `report.md`
5. The relevant prototype index and only the relevant Pxx image folder
6. The latest accepted phase evidence

Core rule:

- Repository evidence defines current reality.
- The approved prototype defines target UX.
- Never confuse target UX with implemented capability.

Current accepted gate:

- 0053-F27 accepted at commit `8fec0617265e5cd03c41c4622bfc3c4dcbf76c5b`.
- 0053-F28 Scanner Worker Result Application Planning accepted:
  `0053_F28_SCANNER_WORKER_RESULT_APPLICATION_PLAN_ACCEPTED_READY_FOR_F29`.
- 0053-F29 Scanner Worker Result Application Guard accepted:
  `0053_F29_SCANNER_WORKER_RESULT_APPLICATION_GUARD_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_F30_PLANNING`.
- 0053-F30 Scanner Worker Single-Job Orchestration Planning accepted:
  `0053_F30_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_PLAN_ACCEPTED_READY_FOR_F31_PREPARATION`.
- 0053-F31 Scanner Worker Single-Job Orchestration Guard **accepted** (current scanner checkpoint):
  `0053_F31_SCANNER_WORKER_SINGLE_JOB_ORCHESTRATION_GUARD_ACCEPTED_WITH_WATCH_ITEMS`.
- F31 technical scope (accepted, deliberately limited): configured-adapter capability preflight;
  safe unavailable/noop behaviour; F27 owner-scoped reservation; authoritative reserved-job
  snapshot; adapter execution outside DB transactions; F29 guarded result application;
  owner/attachment/job/hash validation; triple-hash; PostgreSQL locking; atomic apply;
  idempotent exact replay; conflicting replay rejection; safe error materialization;
  no double attempt increment; no false clean when scanner unavailable.
- F31 does **not** include: real malware scanner engine; ClamAV/YARA/third-party scanning;
  attachment byte reading; private-storage retrieval; queue polling; oldest-job / SKIP LOCKED
  selection; continuous worker loop; startup/production worker registration; quarantine
  movement; scanner administrator routes; scanner frontend; reservation lease / expiry /
  heartbeat / TTL / reclaim; abandoned-job recovery; complete retry lifecycle; scheduled
  worker execution.
- Official repository: `/Users/tariqnasheed/Desktop/Career_Kundi_2`. Former F3 worktree
  (`Career_Kundi_2_F3`) and hold branch `worktree/f3-consolidation-hold-2026-07-19` are
  retired and absent. Canonical F29/F31 evidence: `docs/evidence/0053/`.
- **Programme 0.4** implementation is complete and accepted (F31 governance reconciliation
  and F29/F31 evidence canonicalization). No scanner capability expansion occurred.
- F31 remains the accepted current scanner checkpoint.
- **F32 has not started.** **Programme 1 has not started.**
- Next authorized planning gate: **Programme 1** (repository safety cleanup /
  deferred housekeeping). Feature branch `feat/interview-pack-llm-authoring` remains
  preserved for Programme 8. Informational questions do not change the active phase.
- Stuck-reserved recovery (after interruption or F29 rejection) remains a watch item.

Always:

- state model/mode and task scope
- inspect before editing
- create a Prototype Impact Matrix
- preserve owner/privacy/verification boundaries
- use exact file staging
- protect known local dirt
- stop at the named gate
