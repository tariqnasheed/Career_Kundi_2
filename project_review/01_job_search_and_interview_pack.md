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

## Baseline sample placeholder

_Paste or link representative generated output here after Iteration 002._

**Sample paths (to be filled):**

| Role | Markdown | PDF | Notes |
|------|----------|-----|-------|
| _e.g. Data Analyst_ | `samples/job_search/data_analyst_pack.md` | `samples/job_search/data_analyst_pack.pdf` | |
| _e.g. DevOps Engineer_ | | | |
| _e.g. Barista_ | | | |

**Sample question block (template):**

```markdown
## Q001: [Question text]

**Category:** technical  
**Skill:** SQL  
**Why asked:** …

### Model answer
…

### Study material
**Core idea:** …
```

---

## Current issues placeholder

_Document issues found during baseline inspection._

| ID | Area | Issue | Severity | Status |
|----|------|-------|----------|--------|
| JS-001 | _TBD_ | | | open |

---

## Next implementation notes placeholder

_Next Cursor task: Job Search + Interview Pack Generator fixes (Implementation order step 3)._

- [ ] Verify pasted-link extraction fills all required fields
- [ ] Decouple popular-role selection from auto-generate/export
- [ ] Implement explicit Generate vs Download UX on frontend
- [ ] Rearrange page into five workflow sections above
- [ ] Capture baseline samples into `project_review/samples/`
