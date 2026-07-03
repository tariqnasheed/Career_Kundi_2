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

**Next major phase:** **Iteration 004E — Job Posting Intelligence and Interview Pack Source Ladder** (**004E-A foundation implemented**; 004E-B for link extraction + web research).

**Following major phase (planned):** **Iteration 004F — Global Job Search Agent and Location-Aware Search Page** (after 004E-A commit — see § Iteration 004F).

See full specification and task checklist in [§ Iteration 004E](#iteration-004e--job-posting-intelligence-and-interview-pack-source-ladder-in-progress) and [§ Iteration 004F](#iteration-004f--global-job-search-agent-and-location-aware-search-page-planned) below.

Deferred until after 004E:

- [ ] Final content library regeneration (pre-cleanup gate)
- [ ] Optional: surface download actions in job form quick actions after pack exists

---

## Iteration 004E — Job Posting Intelligence and Interview Pack Source Ladder (IN PROGRESS)

**004E-A (implemented):** Job Intelligence Profile, completeness warnings, coverage audit, missing-coverage questions, silly-question guard, API metadata fields, minimal frontend hint.

**004E-B (planned):** Job posting link extraction, company web research with real URLs only, extracted-field review/edit UI.

**004E-B research expectation:** Before implementation, apply the [Research-Assisted Development Rule](#research-assisted-development-rule) — review official docs and reputable open-source examples for job-posting parsers, HTML extraction, company-profile capture, and source-citation patterns. Document chosen approach and rejected alternatives in `project_review/`.

**Status:** Documented requirement and task list only — **do not implement until explicitly instructed.**

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
- [ ] Roadmap includes 004F as planned major phase after 004E-A commit

---

## Iteration 004F — Global Job Search Agent and Location-Aware Search Page (PLANNED)

**Status:** Documented requirement only — **do not implement until 004E-A is committed and explicitly instructed.**

**Gate:** 004E-A stabilization committed. Apply [Research-Assisted Development Rule](#research-assisted-development-rule) before provider implementation.

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

The Job Search page must support a rigorous web job search experience. The user searches any job role and optionally specifies location, job type, work mode, date posted, and whether to expand worldwide.

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

**Backend exposes:** `total_fetched`, `total_after_deduplication`, `providers_searched`, `provider_statuses`, `has_more`, `next_cursor`, `warnings`, `coverage_note`. Never fake searching the entire internet.

### 5. Location-aware search rule

- Provided city/country → search first; rank closer jobs higher when coordinates exist; expand only if worldwide enabled.
- No location → geolocation with permission, else profile/saved location, else compliant IP/country hint if already available — else warn or require worldwide.
- Do not silently track location.

### 6. Job type and odd/gig job support

Support standard roles (Software Engineer, Nurse, …), part-time/hourly (Barista, Tutor, …), and safe odd/gig jobs (Dog Walker, Event Staff, Handyman, Freelance Creative, …).

**Query expansion** for odd jobs → safe categories (cleaning, event staff, dog walking, gardening, moving help, etc.).

**Block unsafe categories:** weapons, illegal drugs, adult services, gambling, dangerous stunts, illegal hacking, scams, extremist activity.

### 7. Multi-agent search architecture

Suggested module: `backend/app/agents/job_search/web_search/`

| Agent | Responsibility |
|-------|----------------|
| `SearchIntentParserAgent` | Build `JobSearchIntent` (role, job type, location, remote mode, date posted, worldwide flag, odd-job intent, unsafe exclusions) |
| `LocationResolverAgent` | Resolve city/country, coordinates, country codes, distance fields — graceful fallback without requiring permission |
| `QueryExpansionAgent` | Provider-specific query strings |
| `ProviderSearchAgent` | Call configured providers (Adzuna, SerpApi Google Jobs if keyed, USAJOBS if keyed, remote provider, **mock provider for tests**) |
| `PaginationCrawlerAgent` | Page until exhausted/limited; track pages, tokens, errors |
| `JobNormalizerAgent` | `NormalizedJobResult` schema (title, company, location, remote_mode, job_type, salary, descriptions, posted_at, source_provider, original_url, apply_url, scores, …) |
| `DeduplicationAgent` | By title, company, location, URL, provider ID, text similarity |
| `RankingAgent` | Role match, proximity, freshness, job type, source confidence, filters; local dominance when worldwide off |
| `ResultActionAgent` | Use this job → Job Intelligence Profile fields; Open original link |
| `SearchAuditAgent` | Provider statuses, pages, warnings, rate limits, worldwide flag |

**Provider rules:** official APIs only; no scraping where disallowed; API keys via env; tests use mocks.

### 8. Provider research notes (pre-implementation)

Apply Research-Assisted Development Rule. Document sources in `project_review/` when they influence design.

- **Adzuna** — keywords, location, pagination, contract type, redirect URL
- **USAJOBS** — keyword, location, schedule, page, radius
- **SerpApi Google Jobs** — location param, `next_page_token` pagination (page-limited)
- Browser geolocation — permission-gated nearest-first only

### 9. Backend API requirement

Suggested endpoints (adapt to existing `/api/v1/job-search` conventions):

```text
POST /api/v1/job-search/web/search
GET  /api/v1/job-search/web/search/{search_id}
POST /api/v1/job-search/web/search/{search_id}/load-more
POST /api/v1/job-search/web/use-job
```

**Request (`WebJobSearchRequest`):** `query`, `city`, `country`, `job_type`, `work_mode`, `date_posted`, `search_worldwide=False`, `user_latitude`, `user_longitude`, `max_pages_per_provider`, `include_remote=True`

**Response (`WebJobSearchResponse`):** `results`, `total_fetched`, `total_after_deduplication`, `providers_searched`, `provider_statuses`, `has_more`, `next_cursor`, `warnings`, `coverage_note`

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

### 13. Tests (when implemented)

Under `backend/app/agents/job_search/tests/`:

- `test_web_job_search_intent.py`
- `test_web_job_search_providers.py`
- `test_web_job_search_ranking.py`
- `test_web_job_search_use_job.py`

Verify: intent parsing, job types, odd-job safe expansion, unsafe blocking, location/worldwide rules, pagination, dedup, ranking, Use this job → intelligence profile, real URLs only, mock providers, no API keys in default tests, existing suite still passes.

Frontend: city/country fields, job type selector, worldwide checkbox default unchecked, required action buttons visible.

### 14. Samples and review output (when implemented)

`project_review/samples/iteration_004f_global_job_search_agent/`:

- `iteration_004f_summary.md`, `metrics.json`
- Sample JSON: data analyst (no location / worldwide false & true), barista city filter, part-time odd jobs, social media creator country filter
- `sample_use_this_job_to_intelligence_profile.md`

Summary metrics table columns: Scenario, Query, City, Country, Job Type, Search Worldwide, Providers Searched, Pages Fetched, Results Fetched, Deduplicated, Has More, Warnings, Unsafe Blocked, Fake URLs.

### 15. Remaining after 004F (next phases)

- Job posting detail extraction from selected job link (004E-B overlap)
- Company profile web research with real captured URLs
- Persistent saved jobs and search history

### Acceptance criteria (004F planning)

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
