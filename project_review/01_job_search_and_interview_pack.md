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

## Current issues found (baseline inspection)

| ID | Area | Issue | Severity | Status |
|----|------|-------|----------|--------|
| JS-001 | Coverage | No explicit HR question category in generated packs | high | open |
| JS-002 | Coverage | No daily-routine / day-one question category | medium | open |
| JS-003 | Coverage | No case-study category; seniority tiers sparse | medium | open |
| JS-004 | Answers | Behavioral STAR answers ~40–80 words vs richer technical answers | medium | open |
| JS-005 | Skills | Secondary requirement skills get fewer technical questions than primary focus skill | medium | open |
| JS-006 | Frontend | Popular-role selection / generate / download workflow not yet separated | high | open |
| JS-007 | Import | Pasted job link/description field extraction not validated in this baseline | high | open |
| JS-008 | Company | Company-specific questions absent without company profile data | low | expected |

---

## Next implementation notes

**Next Cursor task:** Implementation order step 3 — Job Search + Interview Pack Generator fixes.

- [ ] Add HR and daily-routine question templates to generation pipeline
- [ ] Expand seniority-variant prompts (junior / senior / lead)
- [ ] Decouple popular-role auto-generate/export on frontend
- [ ] Validate pasted job link/description fills all required fields
- [ ] Lengthen behavioral answers without generic padding (separate pass after workflow fixes)
