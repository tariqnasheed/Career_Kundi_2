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
- Next gate is **0053-F31 Scanner Worker Single-Job Orchestration Guard** (not started).
  Configured adapter remains noop/unavailable; scanner engine / worker loop / file read /
  quarantine / audit / routes / UI remain deferred. Stuck-reserved recovery is a watch item.

Always:

- state model/mode and task scope
- inspect before editing
- create a Prototype Impact Matrix
- preserve owner/privacy/verification boundaries
- use exact file staging
- protect known local dirt
- stop at the named gate
