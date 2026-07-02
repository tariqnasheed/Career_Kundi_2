# Job Search and Interview Pack Generator

## Current goal

Upgrade job import, popular-role selection, interview-pack generation, and page flow.

---

## Required job-search changes

- Pasted job links should extract job data accurately.
- Pasted job descriptions should fill all relevant fields correctly.
- Extracted fields should include:
  - job title
  - company name if available
  - location
  - employment type
  - remote/on-site status
  - salary if available
  - responsibilities
  - requirements
  - benefits
  - extracted skills
  - company profile if available
- Company information should **not** be required to generate an interview pack.
- Popular job-role selection should auto-fill required role fields.
- Popular role selection should **not** automatically generate, download, or export the interview pack.
- Interview pack generation should happen only when the user clicks a clear **Generate** button.
- Downloads should happen only when the user clicks a **Download/Export** button.
- Page layout should be rearranged into a clear workflow.

---

## Required interview-pack generation changes

The interview pack should be comprehensive for the job role and should cover:

- HR questions
- behavioral questions
- technical questions
- conceptual questions
- scenario-based questions
- problem-solving questions
- case-study questions where relevant
- practical task questions where relevant
- daily job routine questions
- responsibility-specific questions
- skill-specific questions
- tool/software questions
- industry/domain-specific questions
- ethics/safety questions where relevant
- regulations/standards questions where relevant
- seniority-level variations
- company-specific questions only if company data is available

---

## Required output behavior

For every generated question:

| Field | Required |
|-------|----------|
| question text | yes |
| question category | yes |
| skill tag | yes |
| why it is asked | yes |
| model answer | yes |
| answer explanation | yes |
| dedicated study material | yes |
| evaluation criteria | yes |
| common mistakes | yes |
| follow-up questions | yes |
| estimated answer time | yes |

---

## Desired frontend layout

Suggested page flow:

### 1. Job input area

- paste job link
- paste job description
- choose popular role
- direct custom role input

### 2. Extracted job review area

- editable job title
- editable responsibilities
- editable requirements
- editable skills
- optional company information

### 3. Interview pack controls

- focus areas
- difficulty
- include study material toggle
- **Generate** button (explicit user action)

### 4. Generated interview pack preview

- questions grouped by category
- expand/collapse answers
- expand/collapse study material

### 5. Export/download area

- full pack PDF
- study material PDF
- questions and answers PDF
- Markdown export if available

---

## Backend / quality baseline (confirmed)

Current automated coverage includes:

- Golden and broad-role regression
- Full-matrix question-intent alignment (15 roles)
- Study-material quality audit
- Export quality audit (Markdown)
- PDF generation smoke
- PDF text smoke (optional, tooling-dependent)
- Flexible answer-length policy (500-word maximum)

Test command:

```bash
cd backend && uv run pytest app/agents/job_search/tests -q
```

---

## Baseline sample (Iteration 002)

Captured 2026-07-03 via `backend/scripts/generate_baseline_interview_samples.py`.

| Role | Full pack | Study only | Questions |
|------|-----------|------------|-----------|
| Data Analyst | [data_analyst_interview_pack.md](../samples/iteration_002_baseline/data_analyst_interview_pack.md) | [data_analyst_study_only.md](../samples/iteration_002_baseline/data_analyst_study_only.md) | 29 |
| Electrical Engineer | [electrical_engineer_interview_pack.md](../samples/iteration_002_baseline/electrical_engineer_interview_pack.md) | [electrical_engineer_study_only.md](../samples/iteration_002_baseline/electrical_engineer_study_only.md) | 28 |
| Clinical Pharmacist | [clinical_pharmacist_interview_pack.md](../samples/iteration_002_baseline/clinical_pharmacist_interview_pack.md) | [clinical_pharmacist_study_only.md](../samples/iteration_002_baseline/clinical_pharmacist_study_only.md) | 28 |
| Barista | [barista_interview_pack.md](../samples/iteration_002_baseline/barista_interview_pack.md) | [barista_study_only.md](../samples/iteration_002_baseline/barista_study_only.md) | 24 |
| DevOps Engineer | [devops_engineer_interview_pack.md](../samples/iteration_002_baseline/devops_engineer_interview_pack.md) | [devops_engineer_study_only.md](../samples/iteration_002_baseline/devops_engineer_study_only.md) | 32 |

Summary: [baseline_summary.md](../samples/iteration_002_baseline/baseline_summary.md)

---

## Iteration 003 changes (2026-07-03)

### Backend

- Added `coverage_planner.apply_coverage_plan()` — minimum HR, daily-routine, seniority, scenario, case/practical, tool, standards, responsibility, and skill-gap coverage.
- New categories: `hr`, `daily_routine` in schema and generator.
- Expanded behavioral/HR/daily-routine/seniority answers to structured STAR-style responses (typically 120+ words).
- Interview-pack API job snapshot now passes location, employment type, remote, salary, benefits, company profile.
- New test file: `test_interview_pack_coverage_expansion.py`.

### Frontend

- Popular role click → fills form only; clears stale job/pack; scrolls to job form.
- Company name no longer auto-filled with “Various employers”.
- Section layout: role selection → job review → pack preview/export.
- Generate remains explicit button; download remains separate (in pack view).

### Before / after (question counts)

| Role | Iteration 002 | Iteration 003 |
|------|---------------|---------------|
| Data Analyst | 29 | 35 |
| Electrical Engineer | 28 | 36 |
| Clinical Pharmacist | 28 | 36 |
| Barista | 24 | 34 |
| DevOps Engineer | 32 | 37 |

Samples: [iteration_003_summary.md](../samples/iteration_003_interview_pack_fix/iteration_003_summary.md)

### Iteration 003A stabilization (2026-07-03)

| Role | Iter 003 | Iter 003A | Joined artifacts | Bracket placeholders | GHS/CLP (pharmacist) |
|------|----------|-----------|------------------|----------------------|----------------------|
| Data Analyst | 35 | 35 | 0 | 0 | n/a |
| Electrical Engineer | 36 | 36 | 0 | 0 | n/a |
| Clinical Pharmacist | 36 | 36 | 0 | 0 | 0 |
| Barista | 34 | 34 | 0 | 0 | n/a |
| DevOps Engineer | 37 | 36 | 0 | 0 | n/a |

Samples: [iteration_003a_summary.md](../samples/iteration_003a_interview_pack_stabilization/iteration_003a_summary.md)

### Iteration 003B surface cleanup (2026-07-03)

| Role | Iter 003A | Iter 003B | Joined artifacts | Bracket placeholders | GHS/CLP (pharmacist) |
|------|-----------|-----------|------------------|----------------------|----------------------|
| Data Analyst | 35 | 35 | 0 | 0 | n/a |
| Electrical Engineer | 36 | 35 | 0 | 0 | n/a |
| Clinical Pharmacist | 36 | 36 | 0 | 0 | 0 |
| Barista | 34 | 34 | 0 | 0 | n/a |
| DevOps Engineer | 36 | 35 | 0 | 0 | n/a |

**003B fixes:** `operationaldata` normalization rule, word-boundary summary truncation, Data Analyst HR data-quality keyword.

Samples: [iteration_003b_summary.md](../samples/iteration_003b_interview_pack_surface_cleanup/iteration_003b_summary.md)

### Iteration 004A export note (2026-07-03)

Interview-pack Markdown/PDF export now includes a per-question **`### Source / fallback status`** section after study material, driven by `question.study_sources` metadata. No fake URLs or citations are added.

Samples: [iteration_004a_summary.md](../samples/iteration_004a_study_source_metadata/iteration_004a_summary.md)

### Frontend manual verification notes

1. Open `/jobs` → click a popular role → confirm form fills, **no** pack generates, **no** download.
2. Leave company blank → click **Generate interview pack** → pack should generate successfully.
3. After generation → use **Full pack PDF** / **Study PDF** in pack section only.
4. Click **Save job** before or with generate — job should persist with optional company null.

---

## Current issues found (post–Iteration 003)

| ID | Area | Issue | Severity | Status |
|----|------|-------|----------|--------|
| JS-001 | Coverage | HR category | high | **fixed** |
| JS-002 | Coverage | Daily-routine category | medium | **fixed** |
| JS-003 | Coverage | Seniority + case/practical | medium | **fixed** |
| JS-004 | Answers | Short behavioral answers | medium | **improved** |
| JS-005 | Skills | Secondary skill depth | medium | open |
| JS-006 | Frontend | Auto-generate on role select | high | **fixed** |
| JS-007 | Import | Pasted job link extraction QA | high | open |
| JS-008 | Company | Company-specific without data | low | expected |
| JS-009 | UX | Download only in pack preview | low | open |
| JS-010 | Surface | Joined-word artifacts | medium | **fixed (003B)** |
| JS-011 | HR | Generic motivation copy | medium | **fixed (003A)** |
| JS-012 | Answers | Bracket placeholders | medium | **fixed (003A)** |
| JS-013 | Domain | Clinical GHS/CLP contamination | high | **fixed (003A)** |
| JS-014 | Pipeline | Live path coverage parity | medium | **fixed (003A)** |

---

## Next implementation notes

**Next Cursor task:** Implementation order step 4 — Study Material multi-source architecture.

- [ ] Implement source ladder orchestrator (web → model → library → fallback)
- [ ] Add `source/fallback status` to study modules
- [ ] Validate pasted job URL/description field extraction (remaining step 3 item)
- [ ] Optional: surface download actions in job form quick actions after pack exists
