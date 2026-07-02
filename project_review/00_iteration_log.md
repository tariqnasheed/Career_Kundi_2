# Career Kundi — Iteration Log

## Project snapshot

| Field | Value |
|-------|-------|
| **Project name** | Career Kundi (`Career_Kundi_2`) |
| **Current branch** | `main` |
| **Current commit** | `7303e015` (pre-iteration-002 capture) |
| **Date** | 2026-07-03 |
| **Test command** | `cd backend && uv run pytest app/agents/job_search/tests -q` |
| **Test result** | **75 passed** in 81.24s |

## Confirmed backend baseline (job-search)

- Interview-pack generation pipeline
- Study-material quality audits
- Export quality audits
- PDF smoke tests
- PDF text smoke test (skips when `pypdf`/`PyPDF2` unavailable)
- Full-matrix intent alignment tests (15 golden roles)
- Answer-length monitoring
- Flexible 500-word answer policy (quality-first bracket)

---

## Implementation order

1. Project review/reporting system
2. Baseline output capture
3. Job Search + Interview Pack Generator fixes
4. Study Material multi-source architecture
5. Study Material export/fallback improvements
6. CV Builder redesign
7. CV template expansion and section-level AI
8. Roadmap page rebuild
9. Roadmap study material and exports
10. Final regression testing
11. Final cleanup

---

## Iteration template

Copy this block for each future implementation pass.

```markdown
### Iteration NNN — YYYY-MM-DD

**Goal:**

**Feature area:**

**Files changed:**

**Commands run:**

**Sample outputs generated:**
- (path under `project_review/samples/`)

**What passed:**

**What failed:**

**Remaining risks:**

**Next recommended step:**
```

---

## Iteration 001 — 2026-07-02

**Goal:** Create a repeatable project-review and iteration-reporting system so every future implementation step saves page-wise `.md` review files and sample outputs for external review.

**Feature area:** Project infrastructure / documentation (no production feature logic).

**Files created:**
- `project_review/00_iteration_log.md`
- `project_review/01_job_search_and_interview_pack.md`
- `project_review/02_study_material.md`
- `project_review/03_cv_builder_page.md`
- `project_review/04_roadmap_page.md`
- `project_review/05_cleanup_plan.md`
- `project_review/samples/.gitkeep`
- `project_review/screenshots_or_export_notes/.gitkeep`

**Files changed:**
- None (production code untouched)
- `.gitignore` — no changes required (existing rules already cover cache/temp patterns)

**Commands run:**
```bash
git status
cd backend && uv run pytest app/agents/job_search/tests -q
```

**Sample outputs generated:**
- None yet — use `project_review/samples/` in Iteration 002 (baseline output capture).

**What passed:**
- Job-search test suite: **12 passed** in 30.42s

**What failed:**
- None

**Production logic changed:** No

**Remaining risks:**
- Review files are templates until baseline samples are captured in `project_review/samples/`
- Page-specific review docs may drift from code unless updated each iteration
- `project_review/` is not ignored by git — commit intentionally when review artifacts are ready

**Next recommended step:** Iteration 002 — Baseline output capture: run representative interview-pack exports for 3–5 golden roles, save Markdown/PDF samples under `project_review/samples/`, and fill baseline/issue placeholders in `01_job_search_and_interview_pack.md` and `02_study_material.md`.

---

## Iteration 002 — 2026-07-03

**Goal:** Capture honest baseline evidence from the current interview-pack generator without changing production logic.

**Feature area:** Baseline output capture (Job Search + Interview Pack + Study Material).

**Files created:**
- `backend/scripts/generate_baseline_interview_samples.py`
- `project_review/samples/iteration_002_baseline/data_analyst_interview_pack.md`
- `project_review/samples/iteration_002_baseline/electrical_engineer_interview_pack.md`
- `project_review/samples/iteration_002_baseline/clinical_pharmacist_interview_pack.md`
- `project_review/samples/iteration_002_baseline/barista_interview_pack.md`
- `project_review/samples/iteration_002_baseline/devops_engineer_interview_pack.md`
- `project_review/samples/iteration_002_baseline/*_study_only.md` (5 files)
- `project_review/samples/iteration_002_baseline/baseline_summary.md`
- `project_review/samples/iteration_002_baseline/metrics.json`

**Files updated:**
- `project_review/00_iteration_log.md`
- `project_review/01_job_search_and_interview_pack.md`
- `project_review/02_study_material.md`

**Commands run:**
```bash
cd backend && uv run python scripts/generate_baseline_interview_samples.py
cd backend && uv run pytest app/agents/job_search/tests -q
git status
```

**Sample outputs generated:**
- 5 full interview-pack Markdown files + 5 study-only Markdown files + `baseline_summary.md`

**Tests run:**
- `cd backend && uv run pytest app/agents/job_search/tests -q` — **12 passed** in 30.43s

**What passed:**
- All job-search quality tests unchanged
- All five baseline packs generated with study material on every question

**What failed:**
- None (capture-only iteration)

**Production logic changed:** No

**Remaining risks:**
- Baseline shows missing HR/daily-routine/seniority/company-specific coverage
- Behavioral answers remain much shorter than technical answers
- Study material is compiler-only with no source ladder metadata

**Next recommended step:** Implementation order step 3 — Job Search + Interview Pack Generator fixes (frontend workflow, job import fields, expanded question categories).

---

## Iteration 003 — 2026-07-03

**Goal:** First implementation pass after baseline — expand interview-pack category coverage, fix frontend generate/download flow, lengthen behavioral answers, add tests and comparison samples.

**Feature area:** Job Search + Interview Pack Generator (backend coverage + frontend workflow).

**Files changed (backend):**
- `backend/app/agents/job_search/knowledge/coverage_planner.py` (new)
- `backend/app/agents/job_search/mock_data.py`
- `backend/app/agents/job_search/knowledge/content_engine.py`
- `backend/app/agents/job_search/knowledge/question_intent.py`
- `backend/app/schemas/job_search.py`
- `backend/app/api/routes/job_search.py`
- `backend/app/agents/job_search/tests/test_interview_pack_coverage_expansion.py` (new)
- `backend/scripts/generate_iteration_003_samples.py` (new)

**Files changed (frontend):**
- `frontend/src/pages/JobSearchPage.tsx`
- `frontend/src/components/features/PopularJobRolesPanel.tsx`
- `frontend/src/components/features/JobDetailsForm.tsx`
- `frontend/src/lib/popularJobRoles.ts`

**Files updated (review):**
- `project_review/00_iteration_log.md`
- `project_review/01_job_search_and_interview_pack.md`
- `project_review/02_study_material.md`

**Commands run:**
```bash
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run python scripts/generate_iteration_003_samples.py
cd frontend && npm test -- --run
git status
```

**Sample outputs generated:**
- `project_review/samples/iteration_003_interview_pack_fix/*_interview_pack.md` (5 roles)
- `project_review/samples/iteration_003_interview_pack_fix/iteration_003_summary.md`
- `project_review/samples/iteration_003_interview_pack_fix/metrics.json`

**Tests run:**
- Backend: **54 passed** in 76.11s
- Frontend: **2 passed** (api surface tests only)

**What passed:**
- HR, daily-routine, seniority, case/practical coverage for five representative roles
- Study material on every exportable question
- All answers ≤ 500 words
- Popular role selection fills form only (no auto-generate)
- Company optional for generation

**What failed:**
- None in automated suites

**Production logic changed:** Yes (coverage planner, new categories, behavioral answer expansion, job snapshot fields, frontend flow)

**Remaining risks:**
- Study material still compiler/deterministic only (no source ladder)
- HR salary answer uses bracket placeholder for notice period
- Pasted job URL extraction not fully validated in this iteration
- Download UI still only inside pack preview section

**Next recommended step:** Implementation order step 4 — Study Material multi-source architecture.

---

## Iteration 003A — 2026-07-03

**Goal:** Stabilize Iteration 003 interview-pack output — fix spacing artifacts, role-specific HR questions, bracket placeholders, clinical domain contamination, and live/mock coverage parity.

**Feature area:** Interview-pack surface quality stabilization (no study-material source ladder).

**Files changed (backend):**
- `backend/app/agents/job_search/quality/surface_text_normalize.py` (new)
- `backend/app/agents/job_search/knowledge/coverage_planner.py`
- `backend/app/agents/job_search/knowledge/content_engine.py`
- `backend/app/agents/job_search/knowledge/core_technical_content.py`
- `backend/app/agents/job_search/knowledge/expert_content_library.py`
- `backend/app/agents/job_search/quality/domain_contamination_audit.py`
- `backend/app/agents/job_search/mock_data.py`
- `backend/app/agents/job_search/tests/test_interview_pack_surface_stability.py` (new)
- `backend/scripts/generate_iteration_003a_samples.py` (new)
- `jobsearch_report.md` (metric sync)

**Files updated (review):**
- `project_review/00_iteration_log.md`
- `project_review/01_job_search_and_interview_pack.md`
- `project_review/02_study_material.md`

**Commands run:**
```bash
rm -rf frontend/node_modules/.vite/vitest
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run python scripts/generate_iteration_003a_samples.py
cd frontend && npm run build
cd frontend && npm test -- --run
git status
```

**Sample outputs generated:**
- `project_review/samples/iteration_003a_interview_pack_stabilization/` (5 packs + summary + metrics)

**Tests run:**
- Backend: **72 passed** in 79.20s

**What passed:**
- No joined-word artifacts in regenerated samples
- No unresolved bracket placeholders in answers
- Role-specific HR motivation questions (unique per role)
- Clinical Pharmacist packs free of GHS/CLP contamination
- `finalize_questions_list` applies coverage planner (live path parity)

**What failed:**
- None

**Production logic changed:** Yes (stabilization fixes only)

**Remaining risks:**
- Study-material source ladder still not implemented
- Secondary skill depth still uneven
- Job URL paste extraction not fully QA’d

**Next recommended step:** Implementation order step 4 — Study Material multi-source architecture.

---

## Iteration 003B — 2026-07-03

**Goal:** Final interview-pack surface cleanup before commit — eliminate remaining joined-word artifacts (especially `operationaldata`), fix summary truncation cutoffs, and confirm role-specific HR question keywords.

**Feature area:** Interview-pack surface normalization and review sample regeneration (no study-material source ladder).

**Files changed (backend):**
- `backend/app/agents/job_search/quality/surface_text_normalize.py` — added `operationaldata`, `sitecoordination`, and related compound fixes; `truncate_at_word` now appends ellipsis
- `backend/app/agents/job_search/knowledge/coverage_planner.py` — Data Analyst HR question mentions data quality checks
- `backend/app/agents/job_search/tests/test_interview_pack_surface_stability.py` — HR keyword checks, normalization tests, truncation test
- `backend/scripts/generate_iteration_003b_samples.py` (new)
- `backend/scripts/generate_iteration_003a_samples.py` — word-boundary truncation in summary

**Files updated (review):**
- `project_review/00_iteration_log.md`
- `project_review/01_job_search_and_interview_pack.md`
- `project_review/02_study_material.md`

**Commands run:**
```bash
git restore frontend/dist && git clean -fd frontend/dist/assets
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run python scripts/generate_iteration_003b_samples.py
cd frontend && npm run build
git restore frontend/dist && git clean -fd frontend/dist/assets
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
git status
```

**Sample outputs generated:**
- `project_review/samples/iteration_003b_interview_pack_surface_cleanup/` (5 packs + summary + metrics)

**Tests run:**
- Backend: **75 passed** in 81.24s

**What passed:**
- No `operationaldata`, `systemsand`, `milksteaming`, or `strongfit` in regenerated samples
- Summary weak-example previews truncate at word boundaries with ellipsis (no `site coordi` / `using tools` cutoffs)
- Role-specific HR questions include required domain keywords per role
- All answers ≤ 500 words; no bracket placeholders; Clinical Pharmacist free of GHS/CLP

**What failed:**
- None

**Production logic changed:** Yes (surface normalization + HR copy tweak only)

**Remaining risks:**
- Study-material source ladder still not implemented
- Secondary skill depth still uneven
- Job URL paste extraction not fully QA’d

**Next recommended step:** Implementation order step 4 — Study Material multi-source architecture.

---

## Test result (latest)

```
cd backend && uv run pytest app/agents/job_search/tests -q
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 81.24s
```
