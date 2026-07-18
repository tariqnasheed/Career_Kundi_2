# Cursor Prompt — 0053-F28 Scanner Worker Result Application Planning

## Recommended routing

- Mode: **Plan** custom mode; otherwise **Ask**
- Model: **Claude Opus** at high reasoning, or **Codex** at high/xhigh reasoning
- Write access: **Disabled**
- This is a security-sensitive read-only planning task.
- Do not use Auto for the architecture decision.

## Accepted baseline

- Worktree: `/Users/tariqnasheed/Desktop/Career_Kundi_2_F3`
- Branch: `main`
- Accepted HEAD and origin/main:
  `8fec0617265e5cd03c41c4622bfc3c4dcbf76c5b`
- Accepted decision:
  `0053_F27_SCANNER_WORKER_RESERVATION_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_F28`

## Required reading

Read:

1. `AGENTS.md`
2. All applicable `.cursor/rules/`
3. `docs/product/careerkundi_0053_f27_acceptance_f28_handoff.md`
4. F27 evidence under `docs/evidence/0053/`
5. The 0053 claims/evidence plan
6. F26 and F27 phase documents
7. Live tracker, master build plan and `report.md`
8. Evidence README and all scanner queue/dry-run/reservation/result-persistence modules and tests
9. Relevant models, enums, schemas, migrations and persistence patterns
10. Prototype index and only these future-context references:
    - P39 Evidence Library
    - P40 Claim Management and Evidence Linking
    - P41 Private Review Requests
    - relevant P46 recovery/error states

## Objective

Produce the complete **0053-F28 Scanner Worker Result Application Planning** contract.

Do not implement it.

The plan must determine from repository evidence:

- the existing scan result object/update-plan contract
- valid result-application source and target states
- exact fields permitted to mutate
- exact fields forbidden to mutate
- owner-scoping rules
- hash/reservation/stale-work guards
- atomic transaction and persistence boundary
- idempotent replay behaviour
- attempt-count and retry semantics
- `started_at` and `completed_at` semantics
- engine-name/version persistence rules
- safe error code/message rules
- whether status `completed`, `failed`, retryable or cancelled states exist and how they are represented
- whether a migration is required
- test strategy and evidence gates
- rollback and concurrency risks
- the smallest safe implementation slice for a later F29 or approved F28 implementation gate, based on the existing master plan

## Mandatory preserved boundary

Do not plan or implement:

- real scanner engine
- scanner dependency
- scanner adapter execution
- worker loop
- startup registration
- scheduler/background task
- file or storage read
- subprocess
- network/external process
- OCR or parsing
- LLM review
- quarantine move
- audit emission
- worker/admin/scan/quarantine/audit route or API
- frontend worker/admin/scan/quarantine/audit UI
- EvidenceRecord content/storage mutation
- claim support or verification mutation
- ReviewRequest mutation
- public evidence sharing
- wallet, DID or blockchain work

The approved prototype is future UX context only. It must not expand F28 scope.

## Required output

Return:

1. `F28_REPOSITORY_BASELINE`
2. files and symbols read
3. existing state machine and persistence contracts
4. Prototype Impact Matrix
5. proposed F28 scope
6. explicit exclusions
7. allowed mutation matrix
8. forbidden mutation matrix
9. concurrency/idempotency decision
10. transaction and rollback decision
11. proposed files for a later implementation
12. complete test matrix
13. documentation/evidence update plan
14. risks, ambiguities and owner decisions
15. proposed scope guard string
16. exact next gate
17. final decision token:
    `0053_F28_SCANNER_WORKER_RESULT_APPLICATION_PLAN_READY_FOR_REVIEW`
    or a blocked decision with precise reasons

## Stop condition

Do not edit any repository file.
Do not run destructive commands.
Do not stage, commit or push.
Stop after the read-only plan.
