# Job Search and Interview Pack Generator

## Current goal

Upgrade job import, popular-role selection, interview-pack generation, and page flow.

---

## Research-Assisted Development Rule

**Applies to every future major implementation iteration** (effective 004E-A-S, 2026-07-03). See also `project_review/00_iteration_log.md`.

From this iteration onward, every major implementation iteration may use web research to improve technical design, architecture, implementation quality, and reliability.

This applies especially when implementing complex features such as:

- job posting link extraction
- company profile extraction
- source ladder design
- web/model/document-library integration
- coverage audit design
- PDF/export generation
- database/document-library storage
- frontend extracted-field review/edit UX
- FastAPI architecture
- React/Vite frontend patterns
- LangGraph or agent workflow design
- parsing, scraping, crawling, and source-citation workflows
- testing strategy and regression coverage

**Allowed research sources:** official documentation; reputable open-source repositories; technical blogs; engineering articles; library/framework docs; examples of job-posting parsers, source citation systems, extraction/retrieval pipelines, and PDF/export workflows.

**Rules:**

- Prefer official documentation and reputable open-source examples.
- Do not copy proprietary code.
- Do not add risky dependencies without justification.
- Do not fake citations, URLs, or web results.
- Do not claim web research was used unless it actually was used.
- Keep tests deterministic.
- Do not require API keys for default tests.
- Document important external ideas in `project_review/` when they influence implementation.
- Use research to improve design, testing, reliability, and user experience.
- If a researched approach is not implemented, document why.

**004E-B note:** From **004E-B onward**, use web research where useful **before** implementing job posting link extraction and company profile capture (real URLs only; no fake citations in product output).

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
- Popular job-role selection should auto-fill required role fields (today: limited popular list; **future:** comprehensive searchable role catalog — see [§ Future Feature — Comprehensive Role Catalog Dropdown](#future-feature--comprehensive-role-catalog-dropdown-deferred)).
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
- choose role from searchable grouped catalog (future) or limited popular roles (current)
- optional **Autofill interview-pack fields** checkbox when a catalog role is selected (future)
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

### Iteration 004B export note (2026-07-03)

Interview-pack Markdown now includes **`### Document-library support`** under study material when saved pack material matches a question. Source/fallback status shows document-library `used` with relative `documents/interview_packs/...` paths.

Samples: [iteration_004b_summary.md](../samples/iteration_004b_document_library_retrieval/iteration_004b_summary.md)

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
| JS-007 | Import | Pasted job link extraction QA | high | open → **004E** |
| JS-008 | Company | Company-specific without data | low | expected → **004E** improves when profile present |
| JS-009 | UX | Download only in pack preview | low | open |
| JS-010 | Surface | Joined-word artifacts | medium | **fixed (003B)** |
| JS-011 | HR | Generic motivation copy | medium | **fixed (003A)** |
| JS-012 | Answers | Bracket placeholders | medium | **fixed (003A)** |
| JS-013 | Domain | Clinical GHS/CLP contamination | high | **fixed (003A)** |
| JS-014 | Pipeline | Live path coverage parity | medium | **fixed (003A)** |

---

## Next implementation notes

**Active focus:** Complete **Interview Pack Generator** and **Interview Study Material** before any Job Search work.

**Next major phases (in order):**

1. **004E-B** — Job posting link extraction for interview packs (**implemented**)
2. **004E-C** — Company profile + source-cited web research for interview packs (**implemented**)
3. **004E-D** — Full interview pack source ladder integration (**implemented**)
4. **004E-E** — Study material finalization for interview packs (**implemented**)
5. **004E-F** — Final regression gate (samples + metrics)
6. **Then** — **Job Search / Role Selection improvements** (deferred — after 004E-F):
   - **Comprehensive Role Catalog Dropdown** — searchable grouped catalog + optional autofill (see [§ Future Feature — Comprehensive Role Catalog Dropdown](#future-feature--comprehensive-role-catalog-dropdown-deferred))
   - **004F — Global Job Search Agent** (deferred)

> **004F Global Job Search Agent is intentionally deferred until Interview Pack Generator and Interview Study Material are fully completed.**

See [§ Interview Pack + Study Material Completion Track (004E-B–004E-F)](#interview-pack--study-material-completion-track-004e-b004e-f) and [§ Iteration 004F](#iteration-004f--global-job-search-agent-and-location-aware-search-page-deferred) below.

**Do not implement yet:** 004F, global job search, job-search web provider architecture, provider APIs, Job Search page redesign, comprehensive role catalog dropdown.

**Not in 004E-D:** role catalog autofill, `role_catalog_autofill` source tier, or Popular Job Roles UI redesign — deferred to Job Search / Role Selection work after 004E-F.

Deferred until after 004E-B–004E-F:

- [ ] Final content library regeneration (pre-cleanup gate — **do not run unless explicitly instructed**)
- [ ] Optional: surface download actions in job form quick actions after pack exists

---

## Iteration 004E — Job Posting Intelligence and Interview Pack Source Ladder (IN PROGRESS)

**004E-A (implemented, `1fb45af5`):** Job Intelligence Profile, completeness warnings, coverage audit, missing-coverage questions, silly-question guard, API metadata fields, minimal frontend hint.

**Active completion track:** **004E-B → 004E-C → 004E-D → 004E-E → 004E-F** (see [§ Interview Pack + Study Material Completion Track](#interview-pack--study-material-completion-track-004e-b004e-f)). **004F is deferred** until this track is complete.

**004E-B research expectation:** Before 004E-B implementation, apply the [Research-Assisted Development Rule](#research-assisted-development-rule) — review official docs and reputable open-source examples for job-posting parsers, HTML extraction, company-profile capture, and source-citation patterns. Document chosen approach and rejected alternatives in `project_review/`.

**Status:** 004E-A foundation done; 004E-B and 004E-C implemented; 004E-D–004E-F documented — implement when explicitly instructed.

### Problem statement

The generator must not create vague, generic, or silly interview questions from only a role title. It must deeply read and use the full job posting, company profile, user notes, job-link extraction, web research (when enabled), model knowledge (when enabled), and document-library fallback before export.

No important useful information from the posting or company profile should be silently skipped unless duplicate, irrelevant, unsafe, or impossible to verify.

### 1. Job Intelligence Profile (backend)

Before generation, build a **Job Intelligence Profile** from user input and/or job posting link.

| Field group | Profile fields |
|-------------|----------------|
| Role | job title, seniority, experience level, department/team, location/regional context |
| Company | company name, profile, what the company does, products/services, industry/domain, scope/market |
| Posting | job description, daily responsibilities, required skills, preferred skills, tools/software, qualifications |
| Compliance | ethics/safety/regulation clues where relevant |
| User | extra notes |
| Extracted | job-posting link content (structured + text fallback) |
| Sources | web research metadata, model knowledge metadata, document-library matches, local fallback notes |

The profile drives company-specific, responsibility-specific, and skill-specific questions — not title-only generics.

### 2. User guidance (frontend)

**Before generation — best-results hint:**

> For best results, enter the complete job posting details, including job description, responsibilities, requirements, company profile, tools, skills, and any extra notes. The more complete and accurate your input is, the more accurate, company-specific, and responsibility-specific your interview pack will be.

**Title-only warning:**

> You entered only a role title. The generated pack may be more general. For a stronger interview pack, add the complete job description, responsibilities, company profile, tools, skills, and extra notes.

**Partial link extraction warning:**

> We extracted partial information from the job link. For better results, paste the full job description or add missing responsibilities, skills, tools, and company details manually.

### 3. Exhaustive information coverage rule

The generator must analyse and use, where meaningful:

- every responsibility, required skill, preferred skill, tool/software mention
- every qualification and experience requirement
- every daily duty, department/team clue, company-profile detail
- every product/service/scope/domain clue
- every compliance/safety/ethics clue
- every soft-skill and technical-skill requirement
- every location/regional context clue
- every extra user note

Convert each into interview preparation material where reasonable. No silent skipping of useful information.

### 4. Required generation behavior

Questions and answers must connect to:

1. Exact job posting content  
2. Company profile and what the company does  
3. Products/services and market scope  
4. Daily responsibilities  
5. Required and preferred skills  
6. Tools/software mentioned  
7. Industry/domain  
8. Seniority level  
9. Web research (when enabled, real URLs only)  
10. Model knowledge (when enabled, not cited as fact)  
11. Document-library fallback  
12. Local deterministic fallback only when stronger sources unavailable  

**Required question categories:** HR, motivation, behavioral, technical, conceptual, responsibility-specific, daily routine, scenario, case-study, practical task, problem-solving, tools/software, company/domain-specific, ethics/safety/compliance (where relevant), seniority variations, follow-ups, beginner→advanced study progression.

### 5. Difficulty progression rule

Per major responsibility, skill, tool, and domain requirement — where relevant:

| Level | Example focus |
|-------|----------------|
| Easy/basic | What does this mean in this role? |
| Practical/medium | How applied in daily responsibilities? |
| Scenario | What if something goes wrong? |
| Advanced | Optimise, troubleshoot, defend approach |
| Senior | Trade-offs, judgement, guiding others |

### 6. No silly or shallow questions rule

**Reject filler** such as: “Do you like this job?”, “Are you good at teamwork?”, “Can you use a computer?”, generic “Why should we hire you?” without job-profile connection, unstructured “Tell me about yourself”.

**Require job-connected prompts** such as KPI-definition conflicts, cable-sizing verification, clinical allergy counselling, content-calendar planning for a product launch, tailoring answers to enterprise vs SMB clients.

### 7. Question count rule

| Context | Rule |
|---------|------|
| **Real user packs** | Coverage-driven — expand with responsibilities, skills, tools, domain complexity, seniority, posting depth; no artificial small cap |
| **Dev/sample packs** | Keep 5 fixed benchmark + 5 random validation roles (deterministic seed) for comparison |

More questions only when they add real coverage — never filler for count.

### 8. Information coverage audit (backend)

Run **before finalising export**. Audit:

- responsibilities, required/preferred skills, tools/software
- company profile, products/services, domain context
- daily workflow, practical tasks, scenarios
- ethics/safety/compliance (where relevant)
- difficulty progression, seniority variations
- source/fallback status per question

**Metadata per extracted item:** item, type, covered/not covered, related question IDs, missing reason, action taken.

If important items are uncovered, add questions before export. Record why items cannot be used safely.

### 9. Source ladder (interview pack generation)

Priority order:

1. User-provided job posting fields  
2. Extracted job posting link content  
3. Company profile from reliable web research (**real URLs only**)  
4. Model knowledge synthesis (feature-flagged; not presented as cited fact)  
5. Saved document-library / project database material  
6. Local deterministic fallback  

**Rules:** no fake web citations, company facts, or URLs; never claim web/model use unless actually contributed; user posting remains highest priority.

### 10. Job posting link extraction

When user provides a link, fetch and parse before generation. Extract at minimum:

- job title, company name, company description/profile  
- full job description, responsibilities, requirements  
- required/preferred qualifications, skills, tools/software  
- employment type, seniority, location, benefits (if relevant)  
- structured metadata; page-text fallback if structured parse fails  

### 11. Interview pack output requirement

Each final pack includes:

- role introduction, company/context summary, **extracted job intelligence summary**
- what employers likely expect, skill map, responsibility map
- beginner→advanced skill breakdown
- all question categories listed in §4
- answer guidance, **dedicated study material per question** (not one generic block for the whole role)
- source/fallback status per question
- **coverage audit summary**

### 12. Frontend layout and UX

Required sections/fields: job title, company name, job posting link, company profile, job description, responsibilities, required/preferred skills, tools/software, seniority, industry/domain, location, extra notes.

Support: paste full posting, link extraction with manual edit, completeness score/checklist, missing-field warnings, **explicit Generate click only** (no auto-generate on popular role select).

Message: **“More complete input = more accurate interview pack.”**

### 13. Testing and samples

**Samples (unchanged):** 5 fixed benchmark + 5 deterministic random validation roles.

**Tests to add in 004E:**

- [ ] Full posting parses into Job Intelligence Profile  
- [ ] Title-only input produces warning metadata  
- [ ] Job link extraction fills maximum fields; partial extraction warns  
- [ ] Responsibilities → questions; required/preferred skills → questions  
- [ ] Tools/software and company profile affect questions  
- [ ] Difficulty progression present  
- [ ] Silly/filler question guard  
- [ ] Coverage audit detects gaps; gaps trigger supplemental questions  
- [ ] Source/fallback transparency; no fake URLs/citations  
- [ ] No user-facing internal labels; no blocked generic phrases  
- [ ] Answers within quality limits  
- [ ] Real user path not capped to sample-size limits  
- [ ] Existing `app/agents/job_search/tests` suite still passes  

### 14. Final Content Library Regeneration dependency

After 004E **and** corrections for interview Q&A, study material, roadmap generator, and roadmap study material:

1. Generate new final PDFs (interview Q&A, study material, full packs, roadmap PDFs)  
2. Save to storage/database/document library  
3. Rebuild indexes and metadata  
4. Point fallback retrieval and frontend downloads at latest files  
5. Remove outdated PDFs **only after** new files verified  
6. Capture verification under `project_review/samples/final_content_library_regeneration/`  

See `project_review/05_cleanup_plan.md`.

### 15. Planned implementation files (reference)

| Area | Likely touchpoints |
|------|-------------------|
| Job intelligence | new `job_intelligence.py` or extend `mock_data` / job snapshot schema |
| Link extraction | scraper routes, job import agents |
| Coverage audit | extend `coverage_planner.py` |
| Source ladder | extend `study_sources.py`, web research stub |
| Export | `document_export.py`, API routes |
| Frontend | job search page, form validation, warnings |
| Tests | `test_job_intelligence_profile.py`, `test_coverage_audit.py`, sample generators |

### Acceptance criteria (planning update)

- [x] Roadmap includes 004E as next major phase after 004D  
- [x] Requirement: deep read of all job/company/user input  
- [x] Requirement: no silent skip of useful information  
- [x] Requirement: coverage audit before export  
- [x] Requirement: easy→hard difficulty progression  
- [x] Requirement: block silly/filler questions  
- [x] Requirement: job posting link extraction  
- [x] Requirement: web + model + document-library source ladder  
- [x] Requirement: sample count vs real user coverage-driven generation distinguished  
- [x] Requirement: final PDF/database regeneration before cleanup documented  
- [x] Roadmap includes 004F as planned major phase (deferred until 004E-B–004E-F complete)

---

## Interview Pack + Study Material Completion Track (004E-B–004E-F)

**Priority:** Complete this track **before** starting Job Search / 004F.

> **004F Global Job Search Agent is intentionally deferred until Interview Pack Generator and Interview Study Material are fully completed.**

### 004E-B — Job Posting Link Extraction for Interview Packs (IMPLEMENTED)

**Status:** Implemented (2026-07-03). **Next active phase:** 004E-D.

**Goal:** If the user provides a job posting URL for interview-pack generation, extract posting content before generation.

**Module:** `backend/app/agents/job_search/job_posting_extractor.py`

**Extraction strategy (research-assisted):**

1. **JSON-LD `JobPosting`** — parse `application/ld+json` blocks; handle `@graph`, nested objects, and `@type` as string or list ([Schema.org JobPosting](https://schema.org/JobPosting)).
2. **OpenGraph/meta fallback** — `og:title`, `og:description`, `og:site_name`, page title.
3. **HTML section headings** — Responsibilities, Requirements, Preferred qualifications, Tools, etc.
4. **Light cleanup** — dedupe bullets, strip noise, cap bullet length.

**Merge priority:** user-provided fields → extracted structured data → HTML fallback → existing local deterministic paths.

**API:** `InterviewPackRequest.job_posting_url`, `extract_from_url`; response `job_posting_extraction` on `InterviewPackRead`.

**Tests:** `test_job_posting_extractor.py`, `test_job_posting_url_integration.py` — mocked/static HTML only; no live internet in default suite.

**Samples:** `project_review/samples/iteration_004e_b_job_posting_extraction/`

**Metrics (samples):** fake URLs = 0, silly question hits = 0, generic phrase hits = 0.

**Not in 004E-B:** global job search (004F deferred), company web research (moved to **004E-C**, now implemented), extracted-field review UI beyond warnings.

**Remaining touchpoints for later:** dedicated extracted-field review/edit UI polish (004E-C+).

### 004E-C — Company Profile and Source-Cited Web Research for Interview Packs (IMPLEMENTED)

**Status:** Implemented (2026-07-03). **Next active phase:** 004E-D.

**Goal:** When company name/domain is available, capture reliable company context for interview-pack generation.

**Implementation:**

- Added `company_research.py` — user profile → job posting derived → Organization JSON-LD → meta → HTML sections
- `CompanyResearchResult` with `source_status`, `research_confidence`, real `source_urls` only
- `fetch_and_research_company_url` reuses 004E-B safe fetch (SSRF redirect validation, DNS/IP checks, 2 MB cap)
- Integrated in `POST /job-search/{job_id}/interview-pack` when `research_company` and `company_url` present
- Extended schemas: `CompanyResearchRead`, `InterviewPackRequest.company_url` / `research_company`, `InterviewPackRead.company_research`
- `job_intelligence.py` — `web_research` source status; company items tagged by source layer
- `mock_data.py` — company-specific questions from researched products/industries
- Frontend: minimal company context block in `InterviewPackView`
- Tests: `test_company_research.py`, `test_company_research_integration.py` (mocked HTML)
- Samples: `project_review/samples/iteration_004e_c_company_research/`

**Research notes (Schema.org Organization):** Prefer `application/ld+json` with types `Organization`, `Corporation`, `LocalBusiness`, `EducationalOrganization`, `NGO`, and `@graph` arrays. Map `name`/`legalName`, `description`, `url`, `sameAs`, `location`, `areaServed`, `makesOffer`/`brand`, `knowsAbout`/`keywords`. OpenGraph/meta and HTML headings (`About`, `Products`, `Services`, `Industries`, `Markets`, `Mission`) are fallback only. User-provided `company_profile` always wins over extracted text.

**Rules enforced:**

- No invented company facts or fake citations
- Model knowledge disabled unless configured
- Transparent warnings when research is partial or unavailable
- Tests use mocked/captured sources — no live internet in default suite

**Not in 004E-C:** global job search (004F deferred), model-knowledge company facts, search provider APIs, persisting `company_research` / `job_posting_extraction` on `SavedJob` rows (deferred — returned on pack response only for now).

**Future improvements (deferred):** persist merged `company_research` and `job_posting_extraction` metadata on saved jobs to avoid repeated fetches on regenerate.

**Scope:**

- company overview, what the company does, products/services
- industry/domain, company market/scope
- relevant company context for interview questions
- real captured URLs only; source/fallback status

**Planned touchpoints:** ~~company research agent/module, source metadata on profile, transparent `source_status` in pack output~~ **Done in 004E-C.**

---

### 004E-D — Full Interview Pack Source Ladder Integration (IMPLEMENTED)

**Status:** Implemented (2026-07-03). **Next active phase:** 004E-E.

**Goal:** Connect all source layers directly into interview-pack question and answer generation.

**Implementation:**

- Added `knowledge/source_ladder.py` — 6-tier status, source-derived audit items, ladder questions, per-question metadata
- Integrated in `mock_generate_questions` / `finalize_questions_list` and `job_intelligence._build_source_status`
- Coverage audit exports `audit_items` with `item_id`, `source_type`, `source_label`, `action`
- Questions carry `question_source_items`, `question_source_types`, `source_priority_used`, `coverage_item_ids`
- API: `SourceLadderStatusRead`, `CoverageAuditItemRead`, extended `JobIntelligenceProfileRead` / `CoverageAuditRead`
- Frontend: minimal source ladder line in `InterviewPackView`
- Tests: `test_interview_pack_source_ladder.py`, `test_interview_pack_full_coverage.py`
- Samples: `project_review/samples/iteration_004e_d_source_ladder_integration/`

**004E-D risk controls (pre-implementation):**

1. **Source priority inversion** — user fields remain primary; URL/company items are additive audit rows, never overwriting manual profile text.
2. **Fake citations** — no new URLs or facts invented; ladder reads only existing 004E-B/004E-C metadata.
3. **Over-scope** — no 004F, no provider APIs, no Job Search page redesign.
4. **Backward compatibility** — additive schema fields only; `web_research` alias retained on `source_status`.
5. **Test determinism** — mocked HTML jobs only; model knowledge disabled by default.
6. **Generic output regression** — silly/generic guards unchanged; sample metrics target zero hits.
7. **Schema drift** — `api.ts` updated to match backend ladder fields.
8. **Coverage audit** — URL/company/document items appear in `audit_items` with source labels.
9. **Network fetch** — **no new HTTP clients** in 004E-D; fetch remains isolated in 004E-B/004E-C modules.

**Quality gate — network import scan (excludes tests, `__pycache__`, and 004E-B/004E-C fetch modules):**

```bash
grep -R -E "(^|\s)(import httpx|import requests|from httpx|from requests|import urllib\.request|from urllib\.request import|urllib\.request\.urlopen|urlopen\()" -n backend/app/agents/job_search \
  --exclude-dir="__pycache__" \
  --exclude="*.pyc" \
  --exclude="test_*" \
  | grep -v "job_posting_extractor.py" \
  | grep -v "company_research.py" || true
```

**Source priority (004E-D implemented):**

1. User-provided job posting fields
2. Extracted job posting link content
3. Company profile from reliable web research
4. Model knowledge where enabled
5. Saved document-library / project database material
6. Local deterministic fallback

**Future source tier (not in 004E-D — Role Catalog feature):** When the comprehensive role catalog ships, add **`role_catalog_autofill`** between document library and local fallback:

1. User-provided fields
2. Job posting URL extraction
3. Company research
4. Model knowledge where enabled
5. Document library
6. **Role catalog autofill** (`role_catalog_autofill`)
7. Local deterministic fallback

User-edited values always override catalog autofill. Autofill must be marked as fallback/catalog-sourced, not user-provided facts.

**Required behavior:**

- Every responsibility, required skill, preferred skill (where relevant), and tool/software item is considered
- Company profile and daily duties affect questions
- Easy-to-hard progression exists
- No silly/filler questions
- Real user packs are coverage-driven — not capped to small sample counts
- Coverage audit runs before export; gaps trigger supplemental questions where safe

**Planned touchpoints:** ~~`mock_data.py` / generation pipeline, `coverage_planner.py`, `silly_question_guard.py`, source ladder wiring~~ **Done in 004E-D.**

**Study material handoff:** per-question `question_source_*` metadata prepared for 004E-E; no generic whole-role study notes added in this phase.

---

### 004E-E — Study Material Finalization for Interview Packs (IMPLEMENTED)

**Status:** Implemented (2026-07-03). **Next active phase:** 004E-F.

**Goal:** Ensure every generated interview question has dedicated study material directly connected to that exact question and answer.

**Implementation:**

- Added `knowledge/question_study_material.py` — per-question module finalization with source-ladder trace metadata
- Integrated in `mock_data._finalize_question` after `synthesize_study_module` and source annotation
- Extended `InterviewStudyMaterial` schema and `api.ts` with 004E-E module fields
- Export: `document_export.py` renders interview application, company/document/model insights
- Minimal study source status in `InterviewPackView` study panel
- Tests: `test_interview_pack_study_material_finalization.py`, `test_question_specific_study_material.py`
- Samples: `project_review/samples/iteration_004e_e_study_material_finalization/`

**004E-E risk controls:**

1. **Generic study material** — each question gets its own module; `what_this_question_tests` includes question hook text.
2. **Q&A mismatch** — modules carry `question_text`, `answer_summary`, and source items from the generating question.
3. **Source mismatch** — `source_items_used`, `source_types_used`, `source_priority_used`, `source_status` mirror 004E-D metadata.
4. **Fake citations** — company/document insights use captured 004E-B/C metadata only; no new URLs.
5. **Over-scope** — no 004F, role catalog, or content-library regeneration.
6. **Model/API** — model knowledge disabled by default; deterministic tests only.
7. **Network** — no new HTTP clients; reuses existing extraction/research metadata.
8. **Schema drift** — backend schema and `api.ts` aligned.
9. **Regression** — blocked-phrase, internal-label, and empty-section guards in samples/tests.

**Each question's study module includes:**

- `question_id`, `question_text`, `answer_summary`, source ladder fields
- `core_idea`, `what_this_question_tests`, skills/definitions/principles, step-by-step method
- beginner/intermediate/advanced explanations, `interview_application`, `likely_follow_ups`
- `saved_material_insight`, `document_library_insight`, `model_insight`, `web_or_company_source_insight` where available
- `source_status`, `fallback_status`

**Rules:**

- No generic study notes disconnected from the question
- No one-size-fits-all study material for the whole role
- No fake citations; no vague filler; no user-facing internal labels like `Role Specific`

**Study-material detail:** `project_review/02_study_material.md` § 004E-E.

---

### 004E-F — Final Interview Pack and Study Material Regression Gate

**Goal:** Create final regression samples and checks **before** moving to Job Search (004F).

**Required sample scenarios:**

| Scenario | Purpose |
|----------|---------|
| Role-title-only | Warning path; limited coverage |
| Rich pasted job posting | Full profile-driven pack |
| Job posting URL extraction (mocked source) | 004E-B path |
| Company web research (mocked/captured source) | 004E-C path |
| Technical role | Deep skill/tool coverage |
| Healthcare/compliance role | Ethics/safety clues |
| Creative/trending role | Random-validation parity |
| Non-technical / odd-job style role | Safe odd-job coverage |

**Metrics to capture:**

- extracted items, covered items, coverage score, missing coverage, added coverage questions
- study material present; source status present
- web source URLs where used; model source status; document-library status
- silly question hits; generic phrase hits; fake URL hits; answers over 500

**Acceptance (gate before 004F):**

- [ ] No silly/filler questions
- [ ] No fake URLs/citations
- [ ] No blocked generic phrases
- [ ] No `Role Specific` leaks
- [ ] Every question has study material
- [ ] Every source status is transparent
- [ ] Backend tests pass
- [ ] Frontend build passes if frontend changed

**Planned samples folder:** `project_review/samples/iteration_004e_final_regression_gate/`

**Do not run Final Content Library Regeneration** as part of 004E-F unless explicitly instructed. Full library regeneration remains after roadmap generator + roadmap study material completion (`05_cleanup_plan.md`).

---

## Future Feature — Comprehensive Role Catalog Dropdown (DEFERRED)

**Status:** Documented requirement only — **do not implement** during 004E-D or the Interview Pack + Study Material completion track (004E-E, 004E-F).

**Scope:** Future **Job Search / frontend role-selection** improvement on the Job Search / Interview Pack page. Can ship alongside or before **004F** once the 004E-F gate passes. Does **not** require global job search or provider APIs.

> **004F Global Job Search Agent is intentionally deferred until Interview Pack Generator and Interview Study Material are fully completed.** This role-catalog feature is also deferred until **004E-F** passes; it must not interrupt 004E-E or 004E-F work.

### Product goal

Replace or enhance the current **Popular Job Roles** section with a **searchable grouped dropdown/catalog** covering professional, part-time, odd/gig, and educational-department roles across sectors.

**Current behavior:** Users select from a limited popular-role list.

**Required future behavior:** Searchable catalog with grouped categories, employment-type filters, popular shortcuts, and custom-role fallback.

### UI requirements

The catalog UI must support:

1. **Searchable dropdown** — type to filter role titles
2. **Grouped categories/sectors** — browse by industry/department
3. **Popular roles** — quick-access shortcuts (existing behavior, expanded)
4. **Full-time roles**
5. **Part-time roles**
6. **Odd/gig job roles** (safe/legal only)
7. **Educational department roles**
8. **Custom role input** when the role is not listed
9. Optional **“Autofill interview-pack fields”** checkbox

**Search behavior:**

- Type to search role titles
- Filter by category and employment type
- Show **“No exact role found — use custom role”** when no match
- Custom role always available

### Autofill UX (critical)

When the user selects any role from the catalog, show:

```text
[ ] Autofill interview-pack fields for this role
```

| Checkbox | Behavior |
|----------|----------|
| **Checked** | Autofill interview-pack fields from role-specific catalog/mock profile data: title, overview, typical responsibilities, required skills, tools/software, seniority hints, department/industry context, ethics/safety/compliance hints where relevant. Mark values as **editable** and source as `role_catalog_autofill`. |
| **Unchecked** | Set **job title / role only**; user manually fills all other fields. |

The user must **always** be able to edit autofilled fields before generating the interview pack. User-edited values become **user-provided** and take priority over catalog autofill in the source ladder.

### Maintainable role catalog structure

Store the catalog in a **data file or shared module** — not hardcoded inside a React component.

Suggested record shape:

```text
category
subcategory
role_title
role_type
employment_type
default_responsibilities
default_skills
default_tools
default_seniority_options
default_industry_context
```

**Possible `role_type` / `employment_type` values:**

```text
full_time
part_time
contract
internship
freelance
odd_job
gig_job
student_job
apprenticeship
volunteer
```

**Suggested touchpoints (when implemented):**

| Layer | Path |
|-------|------|
| Catalog data | `backend/app/agents/job_search/data/role_catalog.json` (or equivalent module) |
| Catalog API | `GET /api/v1/job-search/role-catalog` (search, filter, categories) |
| Autofill service | Backend helper mapping catalog entry → job snapshot fields |
| Frontend | `JobDetailsForm.tsx` / role-selection component on Job Search page |

### Suggested categories

Broad sectors (expand into concrete `role_title` entries):

- Information Technology & Telecommunications
- Healthcare & Life Sciences
- Financial Services & Insurance
- Sales & Business Development
- Marketing, Advertising & Public Relations
- Retail & Wholesale Trade
- Education & Training
- Human Resources & Recruiting
- Hospitality, Tourism & Leisure
- Manufacturing, Industrial & Engineering
- Logistics, Transportation & Warehousing
- Media, Design & Entertainment
- Music Industry
- Architecture & Construction
- Real Estate & Facilities Management
- Government & Public Administration
- Energy & Utilities
- Home & Personal Services
- Nonprofit & Charities
- Environmental Services
- Aerospace & Aviation
- Science & R&D
- Agriculture, Forestry & Fishing
- Defense & Military
- Public Safety & Emergency Services
- Private Security Services
- Mining & Natural Resources
- Sports & Athletics
- Legal & Compliance
- Customer Service & Call Center
- Data & Analytics
- Product & Project Management
- Skilled Trades
- Beauty & Wellness
- Childcare & Elder Care
- Cleaning & Domestic Services
- Delivery & Local Services
- Freelance & Creator Economy

### Example roles to include

**IT:** Software Engineer, Frontend Developer, Backend Developer, Full Stack Developer, Data Analyst, Data Scientist, Cybersecurity Analyst, Network Engineer, Cloud Engineer, DevOps Engineer, IT Support Technician, QA Tester, UI/UX Designer, Product Manager, Business Analyst

**Engineering:** Electrical Engineer, Mechanical Engineer, Civil Engineer, MEP Engineer, HVAC Engineer, Electrical Design Engineer, Site Engineer, Estimation Engineer, Maintenance Engineer, Automation Engineer, PLC Engineer, Draftsman / CAD Technician

**Healthcare:** Nurse, Pharmacist, Clinical Pharmacist, Healthcare Assistant, Medical Laboratory Technician, Physiotherapist, Radiographer, Dentist, Medical Receptionist

**Education:** Teacher, Teaching Assistant, Lecturer, Tutor, Academic Counselor, School Administrator, Special Education Teacher, Online Instructor

**Business/Sales:** Sales Executive, Business Development Executive, Account Manager, Customer Success Executive, Operations Executive, Office Administrator, Procurement Officer

**Finance:** Accountant, Auditor, Financial Analyst, Insurance Advisor, Bank Teller, Payroll Officer, Tax Associate

**Hospitality/Retail:** Barista, Waiter / Waitress, Chef, Hotel Receptionist, Housekeeper, Retail Assistant, Cashier, Store Manager, Travel Consultant

**Part-time / odd / gig (safe only):** Delivery Driver, Food Delivery Rider, Dog Walker, Babysitter, Nanny, Event Staff, Domestic Cleaner, Gardening Helper, Moving Helper, Handyman, Tutor, Grocery Picker, Warehouse Picker, Freelance Content Writer, Freelance Graphic Designer, Social Media Creator, Video Editor, Photographer

### Safety restrictions

**Do not include:** unsafe, illegal, adult, gambling, drug-related, weapon-related, cybercrime, extremist, or dangerous-challenge roles.

**Odd jobs allowed only when safe and legal:** cleaning, tutoring, delivery, gardening, dog walking, babysitting/nannying, moving help, event staffing, freelance creative work.

### Interview-pack autofill behavior

When autofill is enabled, populate fields similar to existing mock/profile data:

- Job title, role overview, typical responsibilities, required skills, tools/software
- Seniority level hints, department/industry context
- Ethics/safety/compliance hints where relevant
- Source status: `role_catalog_autofill` (not `user_field`)

Generated packs must treat catalog values as **fallback/autofill**, not user-provided facts. Any user edit promotes that field to user-provided priority.

### Source ladder integration (when implemented)

Add `role_catalog_autofill` as a lower-priority source than user fields, URL extraction, company research, model knowledge, and document library:

1. User-provided fields
2. Job posting URL extraction
3. Company research
4. Model knowledge where enabled
5. Document library
6. **Role catalog autofill**
7. Local deterministic fallback

### Tests required (when implemented)

1. Role catalog contains major categories
2. Role catalog contains full-time roles
3. Role catalog contains part-time roles
4. Role catalog contains odd/gig roles
5. Unsafe role categories are **not** included
6. Search finds roles by title
7. Search finds roles by category
8. Custom role option works
9. Autofill **unchecked** → only job title set
10. Autofill **checked** → interview-pack fields populated
11. User-edited values override autofill values
12. Autofill marked as `role_catalog_autofill`, not user-provided
13. Interview pack generation works from selected role
14. Existing tests still pass

### Acceptance criteria (planning — deferred)

- [x] Roadmap documents comprehensive searchable role catalog
- [x] Catalog includes professional, part-time, odd/gig, and education roles
- [x] Autofill checkbox UX and override rules documented
- [x] `role_catalog_autofill` source tier documented
- [x] Safety restrictions documented
- [x] Test plan documented
- [ ] **Implementation** — not started

---

## Iteration 004F — Global Job Search Agent and Location-Aware Search Page (DEFERRED)

**Status:** Documented requirement only — **do not implement**. **Intentionally deferred** until Interview Pack Generator and Interview Study Material are fully completed (004E-B through 004E-F).

> **004F Global Job Search Agent is intentionally deferred until Interview Pack Generator and Interview Study Material are fully completed.**

**Do not implement yet:** global job search, `backend/app/agents/job_search/web_search/` provider architecture, job-search provider APIs, or Job Search page redesign.

**004E-A is committed** (`1fb45af5`). When 004F eventually starts, apply [Research-Assisted Development Rule](#research-assisted-development-rule) before provider implementation.

**Current codebase touchpoints (inspect before editing):**

| Layer | Path |
|-------|------|
| Page | `frontend/src/pages/JobSearchPage.tsx` |
| Discovery UI | `frontend/src/components/features/JobDiscoveryPanel.tsx` (`Use this job`, open posting link) |
| Job form | `frontend/src/components/features/JobDetailsForm.tsx` |
| API client | `frontend/src/lib/api.ts` (`jobApi`) |
| Discover route | `POST /api/v1/job-search/discover` — `JobDiscoverRequest` in `backend/app/schemas/job_search.py` |
| Discovery service | `backend/app/services/job_discovery.py` |

### 1. Product requirement

The Job Search page must support a rigorous web job search experience. The user searches any job role and optionally specifies:

- city, country
- remote / hybrid / onsite preference
- full-time, part-time, contract, internship, freelance, odd/gig jobs
- entry-level or senior roles where available
- date posted window
- whether to search only the selected/nearest location or expand worldwide (`search_worldwide`)

The page must **not** search only by vague job title. It builds a structured **`JobSearchIntent`** and runs a multi-source search agent to retrieve, deduplicate, rank, and display results.

### 2. Frontend layout requirement

Add dedicated search fields to the Job Search page (extend or replace current discovery panel):

| Field | Options / notes |
|-------|-----------------|
| Job role / keyword | Required for search |
| City | Optional |
| Country | Optional |
| Job type | Any, Full-time, Part-time, Contract, Internship, Freelance, Odd jobs / gig jobs |
| Work mode | Any, Remote, Hybrid, Onsite |
| Date posted | Any, Last 24h, Last 3 days, Last 7 days, Last 30 days |
| **Search around the world** | Checkbox, **default unchecked** |

**Helper text (worldwide checkbox):**

> Leave unchecked to search deeply in your selected or nearest location. Enable worldwide search to expand beyond your location after local results.

**UX rules:**

- If city/country entered → search that location first.
- If no city/country → start nearest to user when browser geolocation (with permission), profile location, or saved user location is available.
- If no location and worldwide **unchecked** → warn user to enter city/country or enable worldwide search.
- **Do not** auto-expand worldwide unless checkbox is checked.
- **Do not** auto-generate interview packs from search results.
- Each result card keeps **Use this job** and **Open original link** (existing `JobDiscoveryPanel` pattern).
- **Use this job** → populate Job Intelligence Profile / interview-pack fields with extracted data.
- **Open original link** → real original posting or provider redirect URL (new tab).

Optional: prompt *“Use my current location to show nearest jobs first?”* — browser geolocation **only with explicit permission**; never silent tracking.

### 3. Worldwide search checkbox rule

**Correct wording:**

> The default search deeply searches the selected or nearest location. Worldwide expansion only happens when the user enables Search around the world.

Backend field: `search_worldwide: bool = False`

| Condition | Behavior |
|-----------|----------|
| City/country + `search_worldwide=False` | Search only that location deeply; rank nearest/relevant first |
| City/country + `search_worldwide=True` | Target location first, then regional/country/global/remote |
| No location + `search_worldwide=False` | Use user coordinates/profile if available; else **warning** |
| No location + `search_worldwide=True` | Global search via configured providers; include remote where relevant |

When unchecked: paginate configured providers until provider limit, rate limit, depth, timeout, duplicate saturation, or user stop — show provider coverage transparently.

When checked: local/nearest first, then broader results — label by location/source; still do not claim literal worldwide completeness.

### 4. Realistic “all jobs” rule

**Exhaustive configured-source search** — retrieve all available results from configured providers until:

- provider has no more pages
- API/page limit, rate limit, timeout, or duplicate saturation
- user stops pagination

**UI copy:**

> Showing results from configured job sources. Continue loading to search deeper.

**Backend exposes:** `total_fetched`, `total_after_deduplication`, `providers_searched`, `providers_failed`, `provider_page_depth_reached`, `has_more`, `next_cursor`, `warnings`, `coverage_note` (whether more results may be available). Never fake searching the entire internet.

### 5. Location-aware search rule

- Provided city/country → search first; rank closer jobs higher when coordinates exist; expand only if worldwide enabled.
- No location → geolocation with permission, else profile/saved location, else compliant IP/country hint if already available — else warn or require worldwide.
- Do not silently track location.

### 6. Job type and odd/gig job support

**Standard jobs:** Software Engineer, Electrical Engineer, Data Analyst, Nurse, Teacher, Accountant.

**Part-time / hourly:** Barista, Cashier, Delivery Driver, Tutor, Retail Assistant.

**Odd / gig (safe categories only):** Dog Walker, Babysitter/Nanny, Event Staff, Domestic Cleaner, Handyman/Odd Jobs, Gardening Helper, Moving Helper, Freelance Content Writer, Freelance Graphic Designer.

**Query expansion** for odd jobs → safe categories (handyman, cleaning, event staff, dog walking, gardening, moving help, delivery, freelance creative, etc.).

**Block unsafe categories:** weapons, illegal drugs, pornography/adult sexual services, gambling/betting, dangerous challenges/stunts, illegal hacking/cybercrime, scams/fraud, extremist activity.

### 7. Multi-agent search architecture

Planned module: `backend/app/agents/job_search/web_search/`

| # | Agent | Responsibility |
|---|-------|----------------|
| 1 | `SearchIntentParserAgent` | Parse user input into `JobSearchIntent`: role keywords, job type, city/country, work mode, date posted, salary if provided, user location, `search_worldwide`, odd-job intent, seniority hints, excluded unsafe categories |
| 2 | `LocationResolverAgent` | Resolve city/country text, user coordinates, country codes, distance/ranking fields, nearest-first sorting — graceful fallback without requiring location permission |
| 3 | `QueryExpansionAgent` | Build provider-specific queries (e.g. `data analyst Power BI SQL London`, `part time barista Hyderabad`, `freelance content writer remote`, `dog walker part time Dubai`) |
| 4 | `ProviderSearchAgent` | Call configured providers: Adzuna, SerpApi Google Jobs (if API key), USAJOBS (if configured), remote jobs provider (later), **local deterministic mock provider for tests** |
| 5 | `PaginationCrawlerAgent` | Fetch pages until exhausted or limit; track pages fetched, provider limits, `has_more`, `next_page_token`, timeouts, errors |
| 6 | `JobNormalizerAgent` | Map provider payloads to `NormalizedJobResult` (see below) |
| 7 | `DeduplicationAgent` | Dedupe by title, company, location, normalized URL, provider job ID, text similarity |
| 8 | `RankingAgent` | Rank by role match, location proximity, date posted, job type match, source confidence, description quality, remote preference; local dominance when `search_worldwide=False` |
| 9 | `ResultActionAgent` | Attach **Use this job** (→ Job Intelligence Profile / interview-pack fields) and **Open original link** (real `original_url` or provider redirect) |
| 10 | `SearchAuditAgent` | Transparent metadata: providers searched/failed, pages fetched, dedup counts, coverage limits, warnings, rate-limit notes, worldwide flag status |

**Provider rules:** prefer official APIs and compliant providers; do not scrape sites that disallow scraping; API keys via environment variables only; tests use mock providers with no real API keys.

#### Planned `NormalizedJobResult`

```python
class NormalizedJobResult:
    id: str
    title: str
    company: str | None
    location: str | None
    city: str | None
    country: str | None
    remote_mode: str | None
    job_type: str | None
    salary: str | None
    description_snippet: str | None
    full_description: str | None
    posted_at: str | None
    source_provider: str
    original_url: str
    apply_url: str | None
    distance_km: float | None
    relevance_score: float
    freshness_score: float
    location_score: float
    source_confidence: str
```

### 8. Provider research notes (pre-implementation)

Apply [Research-Assisted Development Rule](#research-assisted-development-rule). Document sources in `project_review/` when they influence design.

- **Adzuna** — job keyword/location search, pagination-style access, metadata (title, company, location, salary, contract type, redirect URL)
- **USAJOBS** — U.S. federal roles; keyword/title, location, schedule type, page, results per page, radius
- **SerpApi Google Jobs** — location parameter; pagination via `next_page_token` (page-limited — must be explicit)
- **Remote jobs provider** — consider later where compliant APIs exist
- **Mock provider** — required for deterministic tests; no real API keys in default test suite
- **Browser geolocation** — permission-gated nearest-first only; never silent tracking
- Do not scrape sites that disallow scraping

### 9. Backend API requirement

Suggested endpoints (adapt to existing `/api/v1/job-search` conventions):

```text
POST /api/v1/job-search/web/search
GET  /api/v1/job-search/web/search/{search_id}
POST /api/v1/job-search/web/search/{search_id}/load-more
POST /api/v1/job-search/web/use-job
```

**Request (`WebJobSearchRequest`):** `query`, `city`, `country`, `job_type`, `work_mode`, `date_posted`, `search_worldwide=False`, `user_latitude`, `user_longitude`, `max_pages_per_provider`, `include_remote=True`

**Response (`WebJobSearchResponse`):** `results`, `total_fetched`, `total_after_deduplication`, `providers_searched`, `providers_failed`, `provider_statuses` (per-provider page depth, errors, limits), `has_more`, `next_cursor`, `warnings`, `coverage_note`

### 10. Frontend result card requirement

Display: title, company, location, job type, work mode, posted date, source provider, salary, snippet, confidence, distance.

**Required actions:** Use this job · Open original link

Optional (do not remove required): Save job, Copy link, Generate pack, View extracted details.

### 11. Search depth and pagination UX

- Initial results + Load more + progress indicator
- Provider status and “more results may exist” notes
- **Worldwide unchecked:** *“Searching deeply in your selected or nearest location. Enable ‘Search around the world’ to expand beyond this location.”*
- **Worldwide checked:** *“Searching your selected or nearest location first, then expanding to broader global and remote results from configured job sources.”*
- **Provider limit:** *“Results are fetched from configured job sources. Some providers may limit pages or require API keys. Use ‘Load more’ to continue searching deeper.”*

### 12. Safety and quality rules

Block or safely handle restricted categories (see §6). Normal jobs proceed.

### 13. Planned tests (when implemented)

Under `backend/app/agents/job_search/tests/`:

- `test_web_job_search_intent.py`
- `test_web_job_search_providers.py`
- `test_web_job_search_ranking.py`
- `test_web_job_search_use_job.py`

**Backend tests must verify:**

1. City and country fields are parsed.
2. Job type filters work.
3. Full-time search builds correct provider queries.
4. Part-time search builds correct provider queries.
5. Odd-job intent expands safely.
6. Unsafe job categories are blocked or safely handled.
7. Location-specific search prioritizes specified city/country.
8. No-location search starts nearest-first when user coordinates exist.
9. No-location/no-user-location warns when `search_worldwide=False`.
10. No-location/no-user-location can proceed when `search_worldwide=True`.
11. Worldwide search checkbox defaults to false.
12. Worldwide search expands beyond local only when enabled.
13. Provider pagination continues until exhausted or configured limit.
14. Results are deduplicated.
15. Ranking prioritizes role match and location match.
16. `Use this job` maps a result into Job Intelligence Profile fields.
17. `Open original link` contains original/provider URL only.
18. No fake URLs are generated.
19. Tests do not require real API keys.
20. Mock providers can simulate multiple pages.
21. Provider failures return warnings, not crashes.
22. Existing `app/agents/job_search/tests` suite still passes.

**Frontend checks (later):** city/country fields; job type selector; `Search around the world` checkbox default unchecked; **Use this job** and **Open original link** remain visible.

### 14. Planned samples (when implemented)

Folder: `project_review/samples/iteration_004f_global_job_search_agent/`

| File | Purpose |
|------|---------|
| `iteration_004f_summary.md` | Metrics table + example UI/provider/result blocks |
| `metrics.json` | Machine-readable scenario metrics |
| `sample_search_data_analyst_no_location_worldwide_false.json` | No location, worldwide off → warning path |
| `sample_search_data_analyst_worldwide_true.json` | Worldwide on → expansion path |
| `sample_search_barista_city_filter.json` | City-filtered part-time search |
| `sample_search_part_time_odd_jobs.json` | Safe odd/gig expansion |
| `sample_search_social_media_creator_country_filter.json` | Country filter |
| `sample_use_this_job_to_intelligence_profile.md` | Use this job → intelligence profile mapping |

**Summary metrics table columns:** Scenario | Query | City | Country | Job Type | Search Worldwide | Providers Searched | Pages Fetched | Results Fetched | Deduplicated Results | Has More | Warnings | Unsafe Blocked | Fake URLs

### 15. Remaining after 004F (future phases)

- Persistent saved jobs and search history
- **Use this job** from search results → Job Intelligence Profile (depends on 004E-B–004E-D being complete first)
- **Comprehensive Role Catalog Dropdown** — see [§ Future Feature — Comprehensive Role Catalog Dropdown](#future-feature--comprehensive-role-catalog-dropdown-deferred) (can ship before or with 004F; same 004E-F gate)

### Acceptance criteria (004F planning — deferred)

Requirements preserved for future implementation after 004E-F gate passes:

- [x] Roadmap includes 004F as planned major phase
- [x] City/country and job-type filters documented
- [x] `Search around the world` default unchecked; local-deep default
- [x] Worldwide expansion only when enabled
- [x] No-location warning when worldwide off
- [x] Exhaustive configured-provider rule (not fake unlimited)
- [x] Multi-agent architecture documented
- [x] Use this job + Open original link preserved
- [x] Pagination, dedup, ranking, provider transparency
- [x] Safety restrictions for unsafe categories
- [x] Tests and sample requirements documented
- [x] Research-assisted development required before providers
- [ ] **Implementation** — not started
