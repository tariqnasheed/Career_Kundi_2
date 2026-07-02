# Career Kundi — Iteration Log

## Project snapshot

| Field | Value |
|-------|-------|
| **Project name** | Career Kundi (`Career_Kundi_2`) |
| **Current branch** | `main` |
| **Current commit** | `7303e015` (pre-iteration-002 capture) |
| **Date** | 2026-07-03 |
| **Test command** | `cd backend && uv run pytest app/agents/job_search/tests -q` |
| **Test result** | **144 passed** in 134.93s |

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
11. **Final content library regeneration** (required before cleanup — see below)
12. Final cleanup

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

## Iteration 004A — 2026-07-03

**Goal:** Add study-material source metadata architecture foundation and render honest source/fallback status in exports — without enabling live web, model, or PDF retrieval.

**Feature area:** Study Material source ladder foundation (metadata + Markdown export).

**Files changed (backend):**
- `backend/app/agents/job_search/knowledge/study_sources.py` (new)
- `backend/app/agents/job_search/mock_data.py` — attach metadata during `_finalize_question`
- `backend/app/schemas/job_search.py` — `StudySourceEntry`, `StudySourcesMetadata`, `InterviewQuestion.study_sources`
- `backend/app/tools/document_export.py` — render `### Source / fallback status` per question
- `backend/app/agents/job_search/tests/test_study_material_source_metadata.py` (new)
- `backend/scripts/generate_iteration_004a_samples.py` (new)

**Files updated (review):**
- `project_review/00_iteration_log.md`
- `project_review/02_study_material.md`
- `project_review/01_job_search_and_interview_pack.md` (export structure note)

**Commands run:**
```bash
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run python scripts/generate_iteration_004a_samples.py
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
git status
```

**Sample outputs generated:**
- `project_review/samples/iteration_004a_study_source_metadata/` (5 packs + summary + metrics)

**Tests run:**
- Backend: **99 passed** in 86.75s

**What passed:**
- Every generated question has `study_sources` metadata with web/model/document_library/local_fallback ladder
- Deterministic generation marks `local_fallback` as used; web/model not faked
- Markdown/PDF export includes source/fallback status section per question
- Study material still present; answers ≤ 500 words; existing coverage tests pass

**What failed:**
- None

**Production logic changed:** Yes (metadata attachment + export section; generation content unchanged)

**Remaining risks:**
- Document library detected but not consumed for study synthesis yet
- Web/model retrieval not implemented
- Saved role packs do not yet persist `study_sources`

**Next recommended step:** Iteration 004B — wire document-library retrieval and model-knowledge draft behind feature flags.

---

## Iteration 004A-S — 2026-07-03

**Goal:** Stabilize Iteration 004A source-status surface wording before commit — fix joined-word artifact in `deterministic` + `mode` phrasing and verify 003B coverage parity.

**Files changed (backend):**
- `backend/app/agents/job_search/knowledge/study_sources.py` — reword model note to `deterministic mode`; normalize source metadata text on export
- `backend/app/agents/job_search/quality/surface_text_normalize.py` — joined-word fixes for source-status phrases
- `backend/app/agents/job_search/tests/test_study_material_source_metadata.py` — coverage + artifact checks
- `backend/scripts/generate_iteration_004a_samples.py` — align with 003B snapshots; coverage + artifact metrics

**Sample outputs regenerated:**
- `project_review/samples/iteration_004a_study_source_metadata/`

**Tests run:**
- Backend: **105 passed** in 92.28s

**What passed:**
- No joined source-status word artifacts in backend or regenerated samples
- HR, daily routine, seniority, case/practical coverage present for all five roles
- Study material + source metadata on every question; local fallback marked used

**Production logic changed:** Yes (source-status wording + text normalization only)

---

## Iteration 004B — 2026-07-03

**Goal:** Retrieve saved role-pack material from `documents/interview_packs/` and attach it as supporting document-library study sources with honest metadata.

**Feature area:** Document-library retrieval for study modules (local deterministic only).

**Files changed (backend):**
- `backend/app/agents/job_search/knowledge/document_library_retriever.py` (new)
- `backend/app/agents/job_search/knowledge/study_sources.py` — per-question retrieval + updated source ladder
- `backend/app/tools/document_export.py` — `Document-library support` section in study export
- `backend/app/agents/job_search/quality/surface_text_normalize.py` — preserve `.json` paths in normalized text
- `backend/app/agents/job_search/tests/test_document_library_study_retrieval.py` (new)
- `backend/scripts/generate_iteration_004b_samples.py` (new)

**Files updated (review):**
- `project_review/00_iteration_log.md`
- `project_review/02_study_material.md`
- `project_review/01_job_search_and_interview_pack.md`

**Commands run:**
```bash
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run python scripts/generate_iteration_004b_samples.py
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
git status
```

**Sample outputs generated:**
- `project_review/samples/iteration_004b_document_library_retrieval/`

**Tests run:**
- Backend: **131 passed** in 106.10s

**What passed:**
- Document-library retrieval from structured JSON for saved roles
- Skill/question overlap matching; no fake URLs
- `document_library` marked `used` only when useful matches found
- Data Analyst (no saved pack) remains `not_configured`
- Study material + source metadata preserved; answers ≤ 500 words

**Production logic changed:** Yes (document-library retrieval + export support sections)

**Next recommended step:** Iteration 004C — model-knowledge study synthesis behind a feature flag.

---

## Iteration 004B-S — 2026-07-03

**Goal:** Stabilize document-library retrieval so `used` is not applied broadly to every question when a role pack exists.

**Feature area:** Document-library matching threshold, snippet quality filtering, supporting-focus generation.

**Files changed (backend):**
- `backend/app/agents/job_search/knowledge/document_library_retriever.py` — tightened matching, HR/generic handling, snippet/focus filters
- `backend/app/agents/job_search/tests/test_document_library_study_retrieval.py` — 7 new stabilization tests
- `backend/scripts/generate_iteration_004b_samples.py` — 004B-S summary notes

**Files updated (review):**
- `project_review/00_iteration_log.md`
- `project_review/02_study_material.md`
- `project_review/samples/iteration_004b_document_library_retrieval/` (regenerated)

**Commands run:**
```bash
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run python scripts/generate_iteration_004b_samples.py
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
git status
```

**What passed:**
- Matching requires strong skill-tag overlap, two or more meaningful skill overlaps, or meaningful question-text overlap — not job-level skill inflation
- HR/behavioral/role-specific prompts remain `available_not_used` with explicit note
- Short, heading-only, and generic process snippets filtered (≥ 80 chars for body snippets)
- Supporting focus generated from matched skills and question terms
- **138 passed** in 110.11s

**004B-S sample metrics (document library used / questions):**

| Role | Used | Available not used |
|------|-----:|-------------------:|
| Data Analyst | 0/35 | 0 (not_configured) |
| Electrical Engineer | 1/37 | 36 |
| Clinical Pharmacist | 26/36 | 10 |
| Barista | 25/34 | 9 |
| DevOps Engineer | 29/37 | 8 |

**Why broad matching was corrected:** Saved-question matching previously inflated overlap using job-level extracted skills, so nearly every question matched when a role folder existed.

**Current limitations:** Electrical Engineer saved pack skills (e.g. Circuit design) often do not align with generated question skills (e.g. Cable sizing), so library use stays low despite pack presence. Legacy saved snippets can still be templated.

**Next recommended step:** Iteration 004C — model-knowledge study synthesis behind a feature flag.

**Production logic changed:** Yes (document-library matching and export support quality only)

---

## Iteration 004B-F — 2026-07-03

**Goal:** Filter generic Core Terminology-only document-library matches and weak vocabulary snippets.

**Feature area:** Document-library retrieval polish (local deterministic only).

**Files changed (backend):**
- `backend/app/agents/job_search/knowledge/document_library_retriever.py` — core-terminology-only gate, snippet filtering, quality-ranked snippet source selection
- `backend/app/agents/job_search/tests/test_document_library_study_retrieval.py` — 4 new/strengthened tests
- `backend/scripts/generate_iteration_004b_samples.py` — showcase block picker prefers substantive technical matches

**Commands run:**
```bash
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run python scripts/generate_iteration_004b_samples.py
```

**004B-F sample metrics (document library used / questions):**

| Role | Used | Available not used |
|------|-----:|-------------------:|
| Data Analyst | 0/35 | 0 (`not_configured`) |
| Electrical Engineer | 0/36 | 36 |
| Clinical Pharmacist | 26/36 | 10 |
| Barista | 23/32 | 9 |
| DevOps Engineer | 29/37 | 8 |

**What passed:**
- `Core Terminology` alone no longer marks document library as `used`
- Generic core-terminology snippets filtered (`Core terminology for Core Terminology`, interview-definition boilerplate)
- Substantive technical matches (AWS/CI/CD/Docker/Kubernetes, medication review, espresso/hygiene) still mark `used`
- **142 passed** in 126.05s

**Next recommended step:** Iteration 004C — model-knowledge study synthesis behind a feature flag.

**Production logic changed:** Yes (document-library matching/snippet quality only)

---

## Iteration 004B-G — 2026-07-03

**Goal:** Filter generic Role Specific snippets and normalize technical skill label casing in document-library support blocks.

**Feature area:** Document-library snippet filtering + skill label polish (local deterministic only).

**Files changed (backend):**
- `backend/app/agents/job_search/knowledge/document_library_retriever.py` — Role Specific / procedure boilerplate filters; substantive-skill snippet requirement; `title_case_skill` labels
- `backend/app/agents/job_search/knowledge/normalize.py` — extended abbreviation map (`KPIs`, `LV`, `HV`, `BIM`)
- `backend/app/tools/document_export.py` — skip empty snippet lines
- `backend/app/agents/job_search/tests/test_document_library_study_retrieval.py` — 004B-G tests
- `backend/scripts/generate_iteration_004b_samples.py` — showcase picker rejects generic placeholders

**004B-G sample metrics (document library used / questions):**

| Role | Used | Available not used |
|------|-----:|-------------------:|
| Data Analyst | 0/35 | 0 (`not_configured`) |
| Electrical Engineer | 0/35 | 35 |
| Clinical Pharmacist | 26/36 | 10 |
| Barista | 23/32 | 9 |
| DevOps Engineer | 0/36 | 36 |

**What passed:**
- Generic Role Specific / intermediate quality checks / structured verification snippets filtered
- Matched skill labels render as `AWS`, `CI/CD`, `SQL`, `HACCP`, etc.
- Clinical Pharmacist and Barista substantive matches still mark `used`; DevOps saved pack has no non-generic snippets under current filters (conservative `available_not_used`)
- **144 passed** in 134.93s

**Next recommended step:** Iteration 004C — model-knowledge study synthesis behind a feature flag.

**Production logic changed:** Yes (document-library snippet filtering and skill label display)

---

**Status:** Documented requirement only — **not executed yet**. No deletions performed in this iteration.

This phase must run **after** all corrections are complete for:

- Interview Pack Generator
- Interview Question and Answer quality
- Interview Study Material
- Roadmap Generator
- Roadmap Study Material

…and **before** final cleanup (Implementation order step 12).

### Required generated final outputs

1. Interview question-and-answer PDFs
2. Interview study-material PDFs
3. Full interview-pack PDFs
4. Roadmap PDFs
5. Roadmap study-material PDFs
6. Matching Markdown/JSON structured files used by the backend for fallback or indexing

### Required behavior

- Remove outdated previously generated PDFs **only after** new final PDFs are successfully generated
- Do **not** delete source templates, code, seed data, or `.env.example`
- Rebuild document indexes after regeneration (`documents/indexes/role_index.json`, `skill_index.json`, `document_index.json`)
- Ensure database/document-library metadata points to the latest regenerated files
- Ensure fallback retrieval uses the latest generated material, not stale PDFs
- Ensure frontend download buttons serve the latest final PDFs

### Planned verification commands (to run during regeneration phase)

```bash
# Full interview-pack library regeneration (structured JSON + Markdown + PDFs + indexes)
make seed-role-packs-force

# PDF-only rebuild from existing structured JSON (when content JSON is already final)
make seed-role-packs-pdf-force

# Skill/role knowledge rebuild after catalog or knowledge-engine changes
make build-skill-knowledge

# Backend regression after regeneration
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run pytest -q

# Inspect library layout and index freshness
cd backend && uv run python -c "from app.services.role_pack_library import list_library_roles; print(len(list_library_roles()))"
ls -la documents/indexes/
```

Roadmap regeneration commands will be added to this section when the roadmap export pipeline is finalized (see `project_review/04_roadmap_page.md`).

### Sample output notes (to capture in `project_review/`)

- Regeneration run log with role counts, PDF success/failure counts, and timestamp
- Spot-check notes for download buttons (interview pack + study material + Q&A + roadmap exports)
- Index verification snippet showing updated `role_index.json` / `document_index.json` entries
- Before/after file-count summary under `project_review/samples/final_content_library_regeneration/` (to be created during the phase)

**Next recommended step:** Continue feature iterations (004C+); execute this regeneration gate immediately before final cleanup.

---

## Test result (latest)

```
cd backend && uv run pytest app/agents/job_search/tests -q
........................................................................ [ 50%]
........................................................................ [100%]
144 passed in 134.93s
```
