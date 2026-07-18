# Cursor Prompt Template — Implement an Accepted Prototype-Traceable Slice

Use only after the user approves the phase plan.

## Routing

- Mode: Agent
- Model: Codex high/xhigh or Claude Sonnet/Opus high, based on risk
- Use Auto/Composer only for deterministic documentation or mechanical follow-up tasks.

## Inputs

- Accepted phase:
- Accepted plan decision:
- Repository baseline:
- Relevant prototype pages:
- Relevant prototype sheets:
- Exact allowed files:
- Exact exclusions:
- Required tests:
- Commit/push authority: no, unless stated

## Instructions

1. Re-read the accepted plan, latest evidence, governance rules and relevant prototype sheets.
2. Confirm baseline HEAD and dirty files.
3. Produce the Prototype Impact Matrix.
4. Implement only the accepted delta.
5. Preserve privacy, owner and verification boundaries.
6. Add focused tests before broad regressions.
7. Run compile/build/runtime/browser gates required by the plan.
8. Update docs only after behaviour is proven.
9. Stage exact files only.
10. Stop before commit/push unless explicitly authorised.
11. Produce an evidence report and next-gate decision.
