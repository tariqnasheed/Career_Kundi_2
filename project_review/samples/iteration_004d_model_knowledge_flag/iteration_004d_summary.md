# Iteration 004D Model Knowledge Feature Flag Summary

*Captured: 2026-07-03 05:32 UTC*

## Goal

Add model-knowledge study synthesis behind a disabled-by-default feature flag with deterministic test provider support and random validation sampling — no live web research or fake citations.

## 004D changes

- Added `model_knowledge.py` provider abstraction with `ModelKnowledgeStatus` and `ModelKnowledgeResult`.
- Added `JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE` and `JOB_SEARCH_MODEL_KNOWLEDGE_PROVIDER` settings.
- Integrated model insight into `study_synthesis.py` and Markdown export.
- Source ladder now reports disabled, used, or failed-fallback model-knowledge status transparently.
- Sample generation now includes 5 fixed benchmark roles + 5 deterministic random validation roles.

## Fixed benchmark metrics

| Role | Questions | Study Material Present | Source Status Present | Model Knowledge Used | Document Library Used | Saved Material Insights | Model Insights | Generic Phrase Hits | Internal Label Leaks | Answers Over 500 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Data Analyst | 33 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Electrical Engineer | 33 | 33 | 33 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Clinical Pharmacist | 35 | 35 | 35 | 0 | 26 | 26 | 0 | 0 | 0 | 0 |
| Barista | 32 | 32 | 32 | 0 | 23 | 23 | 0 | 0 | 0 | 0 |
| DevOps Engineer | 36 | 36 | 36 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Random validation metrics

| Role | Category | Questions | Study Material Present | Source Status Present | Model Knowledge Used | Generic Phrase Hits | Internal Label Leaks | Answers Over 500 | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Primary School Teacher | healthcare or education | 35 | 35 | 35 | 0 | 0 | 0 | 0 |  |
| Solicitor | legal, finance, or business | 35 | 35 | 35 | 0 | 0 | 0 | 0 |  |
| Mechanical Engineer | engineering or technical | 36 | 36 | 36 | 0 | 0 | 0 | 0 |  |
| Journalist | creative, media, or communication | 31 | 31 | 31 | 0 | 0 | 0 | 0 |  |
| Social Media Creator | non-traditional/trending | 30 | 30 | 30 | 0 | 0 | 0 | 0 |  |

## Example model-disabled source block

```markdown
### Source / fallback status
- **Used:** Local deterministic study material
- **Web research:** Not configured in this iteration — Web research retrieval is not configured in this iteration.
- **Model knowledge:** Disabled — Model-knowledge synthesis is disabled by feature flag.
- **Document library:** Not configured in this iteration — No saved role pack found in the document library for this role.

_Generated from local deterministic study material. web research and model knowledge retrieval are not configured._
```

## Example model-enabled test insight

*Deterministic test provider output (not a live model call):*

```markdown
### Model knowledge insight

The model-knowledge layer reinforces this DevOps Engineer question by focusing on deployment health checks, rollback criteria, monitoring alerts, and pipeline gates. Use this to practise explaining how you keep releases safe under pressure.
```

## Random validation roles selected

*Seed: 42*

- **Primary School Teacher** — healthcare or education
- **Solicitor** — legal, finance, or business
- **Mechanical Engineer** — engineering or technical
- **Journalist** — creative, media, or communication
- **Social Media Creator** — non-traditional/trending

## 004D-S Random Validation Coverage Stabilization

- Added creative/media, creator/trending, and sports archetype coverage packs in `coverage_planner.py`.
- Added evidence packs and legacy answer paths so creative roles no longer over-block on contract compiler.
- Enforced exportable coverage floor (`MIN_EXPORTABLE_PACK_QUESTIONS = 28`) with meaningful supplemental categories.
- **Journalist:** 17 → 31 questions.
- **Social Media Creator:** 14 → 30 questions.
- Categories added include ethics/copyright, audience/platform/analytics, production workflow, practical tasks, case studies, daily routine, HR/motivation, and seniority/growth.
- Added `test_random_validation_coverage.py`.


## 004D-P Final summary polish

- Normalized model-insight example text (`explaining how` spacing guard in `surface_text_normalize.py`).
- Aligned **Remaining for 004E** with Job Posting Intelligence and Interview Pack Source Ladder roadmap.


## Remaining for 004E

- **Recommended:** Job Posting Intelligence and Interview Pack Source Ladder.
- Complete job-posting/user-input parsing and job posting link extraction.
- Company profile and scope understanding; exhaustive coverage of responsibilities, skills, tools, duties, domain context, and user notes.
- Easy-to-hard question progression; block silly/filler questions; coverage audit before export.
- Interview pack source ladder: user fields → link extraction → web research (real URLs) → model knowledge (flagged) → document library → local fallback.
- Real user packs are coverage-driven; benchmark samples keep the 5+5 comparison rule.
- Final PDF/database regeneration before cleanup (see `05_cleanup_plan.md`).


*Test provider name: `deterministic_test` — used only when feature flag + provider are explicitly enabled.*
