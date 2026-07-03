# Study Material

## Current goal

Upgrade study material into comprehensive, question-specific, multi-source learning modules.

---

## Desired source ladder

Priority order for content retrieval and synthesis:

1. **Web research** — reputable educational, official, documentation, academic, or professional sources
2. **LLM/model knowledge**
3. **Saved PDFs/Markdown/JSON** role material from the project document library
4. **Local deterministic fallback**

---

## Desired fallback behavior

| Web | Model | Action |
|-----|-------|--------|
| success | success | Synthesize both with source tracking |
| fail | success | Model knowledge + saved role/skill material |
| success | fail | Web knowledge + saved role/skill material |
| fail | fail | Saved PDFs/Markdown/JSON for role or skill |
| fail | fail (no saved material) | Clearly marked local fallback; report source limitations |

---

## Desired multi-agent architecture

| Agent | Responsibility |
|-------|----------------|
| `StudyMaterialOrchestrator` | Coordinates pipeline, selects source ladder step |
| `RoleSkillMapperAgent` | Maps question → role family, skills, standards |
| `WebResearchAgent` | Fetches and normalizes external sources |
| `ModelKnowledgeAgent` | Generates structured draft from model knowledge |
| `PDFLibraryRetrieverAgent` | Loads role/skill packs from `documents/` library |
| `SourceVerifierAgent` | Validates citations, rejects fake sources |
| `StudySynthesisAgent` | Merges sources into one question-specific module |
| `StudyQualityAuditorAgent` | Runs deterministic quality gates |
| `ExportFormatterAgent` | Renders Markdown/PDF study blocks |
| `PersistenceAgent` | Saves modules and audit metadata |

---

## Required output structure per interview question

Each question must have its own study module containing:

- core idea
- technical skills covered
- definitions
- principles
- formulas where relevant
- diagrams or visual explanation placeholders where possible
- practical examples
- common mistakes
- tools/software
- standards/regulations where relevant
- beginner explanation
- intermediate explanation
- advanced explanation
- interview application
- source/fallback status

### Markdown export structure (current target)

```markdown
### Study material

**Core idea:**
…

**How to apply it:**
…

**Common mistakes:**
…

**Interview tip:**
…

**Standards / safety / compliance note:** _(when evidence-backed)_
…
```

---

## Quality rules

- No generic output
- No disconnected broad notes
- No placeholder text
- No repeated boilerplate across unrelated roles
- No fake sources
- No fake standards
- No shallow one-paragraph modules
- Must be linked to the exact interview question
- Must include all important skills mentioned in the question
- Must be exportable in Markdown and PDF

### Current automated checks

- `study_material_quality_audit.py` — components, specificity, banned phrases, duplicates
- `study_depth_audit.py` — structured depth gates
- Export audit — visible learning structure in Markdown

---

## Baseline sample (Iteration 002)

| Role | Study-only export | Notes |
|------|-------------------|-------|
| Data Analyst | [data_analyst_study_only.md](../samples/iteration_002_baseline/data_analyst_study_only.md) | 29 modules, all with visible sections |
| Electrical Engineer | [electrical_engineer_study_only.md](../samples/iteration_002_baseline/electrical_engineer_study_only.md) | 28 modules |
| Clinical Pharmacist | [clinical_pharmacist_study_only.md](../samples/iteration_002_baseline/clinical_pharmacist_study_only.md) | 28 modules |
| Barista | [barista_study_only.md](../samples/iteration_002_baseline/barista_study_only.md) | 24 modules |
| DevOps Engineer | [devops_engineer_study_only.md](../samples/iteration_002_baseline/devops_engineer_study_only.md) | 32 modules |

Full analysis: [baseline_summary.md](../samples/iteration_002_baseline/baseline_summary.md)

**Exported section pattern (technical questions):** `Core idea` → `How to apply it` → `Common mistakes` → `Interview tip` (+ standards note when evidence exists).

---

## Iteration 003 note (2026-07-03)

**Source ladder:** Still **not implemented** — study modules remain local/deterministic/compiler-backed.

**New categories:** HR, daily-routine, seniority, case-study, practical-task, tools, and standards questions all receive study modules via `_coverage_question_study`, `_hr_study`, `_daily_routine_study`, and existing behavioral/compiler paths.

**Quality gates:** Existing `study_material_quality_audit` and export audits still pass with expanded packs (54 backend tests).

**Comparison samples:** [iteration_003a_interview_pack_stabilization](../samples/iteration_003a_interview_pack_stabilization/) · [iteration_003b_interview_pack_surface_cleanup](../samples/iteration_003b_interview_pack_surface_cleanup/)

New HR/daily-routine/seniority/case-study categories still receive study modules via deterministic paths. Source ladder remains deferred.

**Iteration 003B (2026-07-03):** No study-material architecture changes. Surface normalization now repairs `operationaldata` and related compound joins; review summaries use word-boundary ellipsis truncation.

---

## Iteration 004A — Study source metadata foundation (2026-07-03)

**Goal:** Introduce a stable source metadata model and honest source/fallback export without live web/model/PDF retrieval.

### Source metadata structure

Each question now carries `study_sources`:

```json
{
  "used_source_types": ["local_fallback"],
  "sources": [
    {"source_type": "web", "label": "Web research", "status": "not_configured", "note": "..."},
    {"source_type": "model", "label": "Model knowledge", "status": "not_configured", "note": "..."},
    {"source_type": "document_library", "label": "Document library", "status": "not_configured|available_not_used", "document_path": "...", "note": "..."},
    {"source_type": "local_fallback", "label": "Local deterministic study material", "status": "used", "note": "..."}
  ],
  "summary": "Generated from local deterministic study material. Web/model/document-library source ladder is not fully enabled yet."
}
```

### Source ladder status (004A)

| Step | Status |
|------|--------|
| Web research | `not_configured` — no live browsing |
| Model knowledge | `not_configured` in deterministic mode |
| Document library | `available_not_used` when `find_role_pack()` finds saved material; otherwise `not_configured` |
| Local fallback | **`used`** — current compiler/template study modules |

### Example source/fallback status block (Markdown export)

```markdown
### Source / fallback status

- **Used:** Local deterministic study material
- **Web research:** Not configured in this iteration — Web research retrieval is not configured in this iteration.
- **Model knowledge:** Not configured in this iteration — Model knowledge retrieval is not enabled in deterministic mode.
- **Document library:** Not configured in this iteration — No saved role pack found in the document library for this role.

_Generated from local deterministic study material. Web, model, and document-library source ladder is not fully enabled yet._
```

**Samples:** [iteration_004a_summary.md](../samples/iteration_004a_study_source_metadata/iteration_004a_summary.md)

**004A-S (2026-07-03):** Fixed source-status wording (`deterministic mode`); added normalization for joined source-status artifacts; regenerated samples with 003B snapshot parity and coverage confirmation.

### Next implementation notes (Iteration 004B) — completed in 004B

- [x] Consume document-library content for matching role/skill questions
- [x] **004C:** deterministic study synthesis layer, Role Specific label cleanup, saved-material insight integration
- [ ] Add web-research stub with real URL capture only
- [x] Persist `study_sources` through saved role packs (via full question JSON on save)

---

## Iteration 004B — Document-library retrieval (2026-07-03)

**Goal:** Use saved `documents/interview_packs/` material as a real supporting source for generated study modules.

### Retrieval design

- **Module:** `document_library_retriever.py`
- **Lookup:** `find_role_pack()` + `structured_content.json` (Markdown fallback metadata only)
- **Matching:** question `skill_tag` / `related_skills` overlap with saved pack questions; category and token overlap as secondary signals
- **Threshold:** minimum score with question-level skills required; generic skills filtered
- **Output:** compact `document_library_support` block on `study_material` + updated `study_sources`

### Source metadata behavior (004B)

| Step | Status |
|------|--------|
| Web research | `not_configured` |
| Model knowledge | `not_configured` in deterministic mode |
| Document library | **`used`** when strong skill/question overlap and quality snippets exist; `available_not_used` when pack exists but no match; `not_configured` when no pack |
| Local fallback | **`used`** (compiler content remains primary) |

### Example source/fallback block

```markdown
### Source / fallback status
- **Used:** Document-library role material; Local deterministic study material
- **Web research:** Not configured in this iteration
- **Model knowledge:** Not configured in deterministic mode
- **Document library:** Used — matched saved role-pack material from `documents/interview_packs/technology/devops_engineer/structured_content.json`
```

**Samples:** [iteration_004b_summary.md](../samples/iteration_004b_document_library_retrieval/iteration_004b_summary.md)

### Limitations

- No PDF parsing, web calls, or LLM retrieval
- Snippets are short supporting excerpts, not full pack rewrites
- Data Analyst lacks a saved pack in the library
- HR/generic prompts usually do not match saved technical questions

### Next step (Iteration 004C)

- Model-knowledge study synthesis behind a feature flag (recommended)
- Optional later: web-research stub with real URL capture only

---

## Iteration 004B-S — Document-library stabilization (2026-07-03)

**Goal:** Fix overly broad document-library matching and weak support snippets introduced in 004B.

### Stabilization changes

- **Matching tightened:** saved-question skills only (no job-level skill inflation); requires skill-tag match, two or more meaningful skill overlaps, or meaningful question-text overlap
- **HR/generic handling:** `hr`, `behavioral`, and `role_specific` categories always remain `available_not_used` unless future exact-prompt matching is added
- **Snippet filtering:** minimum 80 characters; heading-only, skill-name-only, and generic process boilerplate removed
- **Supporting focus:** skill-linked phrases (e.g. deployment reliability, rollback planning) instead of random principle sentences

### 004B-S sample metrics

| Role | Doc library used | Available not used |
|------|----------------:|-------------------:|
| Data Analyst | 0/35 | 0 (`not_configured`) |
| Electrical Engineer | 1/37 | 36 |
| Clinical Pharmacist | 26/36 | 10 |
| Barista | 25/34 | 9 |
| DevOps Engineer | 29/37 | 8 |

### Limitations (post–004B-S)

- Saved pack skill tags may not align with generated interview-pack skills (Electrical Engineer is the clearest example)
- Legacy saved study material can still produce templated snippets above the quality threshold
- No PDF parsing, web calls, or LLM retrieval

### Next step (Iteration 004C)

- Model-knowledge study synthesis behind a feature flag (recommended)

---

## Iteration 004B-F — Core Terminology polish (2026-07-03)

**Goal:** Stop generic vocabulary-only matches from marking document library as `used`.

### Changes

- **`Core Terminology` alone** → `available_not_used` with note: only generic core-terminology overlap was found
- **Secondary use allowed:** Core Terminology may appear alongside substantive skills but is excluded from supporting-focus generation
- **Snippet filters:** reject `Core terminology for Core Terminology`, `precise definitions required for … interviews`, operating-principles boilerplate
- **Snippet source selection:** quality-ranked fallback across saved questions with the same substantive skill overlap

### 004B-F sample metrics

| Role | Doc library used | Available not used |
|------|----------------:|-------------------:|
| Data Analyst | 0/35 | 0 (`not_configured`) |
| Electrical Engineer | 0/36 | 36 |
| Clinical Pharmacist | 26/36 | 10 |
| Barista | 23/32 | 9 |
| DevOps Engineer | 29/37 | 8 |

Document-library retrieval is now more conservative and useful; Electrical Engineer remains low because saved pack skills rarely align with generated question skills.

### Next step (Iteration 004C)

- Model-knowledge study synthesis behind a feature flag (recommended)

---

## Iteration 004B-G — Role Specific snippet filter + skill labels (2026-07-03)

**Goal:** Remove generic Role Specific placeholder snippets and fix technical abbreviation casing in document-library support exports.

### Changes

- **Snippet filters:** reject `Apply/applied Role Specific`, `intermediate quality checks`, `structured verification`, and snippets that do not mention a substantive matched skill
- **Skill labels:** use shared `title_case_skill()` so `aws` → `AWS`, `ci/cd` → `CI/CD`, `haccp` → `HACCP`
- **Conservative behavior:** if only generic snippets remain, status stays `available_not_used` and no support snippets are exported
- **Showcase:** summary example uses Barista/Clinical Pharmacist blocks with substantive skill terms (not Role Specific placeholders)

### 004B-G sample metrics

| Role | Doc library used | Available not used |
|------|----------------:|-------------------:|
| Data Analyst | 0/35 | 0 (`not_configured`) |
| Electrical Engineer | 0/35 | 35 |
| Clinical Pharmacist | 26/36 | 10 |
| Barista | 23/32 | 9 |
| DevOps Engineer | 0/36 | 36 |

Document-library retrieval is conservative and source-transparent; DevOps/Electrical saved packs currently lack non-generic snippets under the quality filters.

### Next step (Iteration 004C)

- Study-material synthesis quality layer (deterministic enrichment — **completed in 004C**)

---

## Iteration 004C — Study synthesis quality layer (2026-07-03)

**Goal:** Improve study-material synthesis using local deterministic content, document-library support, and role/skill context — without LLM or web retrieval.

### Design

New module: `backend/app/agents/job_search/knowledge/study_synthesis.py`

Pipeline hook: after `attach_study_source_metadata()` in `_finalize_question()`.

Functions:

- `synthesize_study_module()` — orchestrates post-processing
- `build_user_facing_related_skills()` / `clean_user_facing_study_labels()` — replace internal `Role Specific` with contextual labels
- `scrub_generic_phrasing()` — role-family replacements for blocked compiler boilerplate
- `build_skill_learning_path()` — beginner / intermediate / advanced explanations + `technical_skills_covered`
- `merge_document_support_into_study_material()` — concise **Saved material insight** when document library is `used`

Export: `document_export.py` renders learning-path sections and saved-material insight; document-library support block remains transparent.

### Fixes

- User-facing `Related skills: … Role Specific` removed (replaced with Role Motivation, Daily Workflow, real skills)
- Blocked generic phrases scrubbed from model answers and study modules (role-family specific replacements)
- Expert fallback facts no longer emit traceability/risk boilerplate that tripped key-term audits
- `_boost_specificity()` skipped when export is blocked (prevents thin addendum resurrection)

### 004C sample metrics

| Role | Questions | Study Material | Source Status | Role Specific Labels | Generic Phrase Hits | Saved Material Insights | Answers Over 500 |
|------|----------:|---------------:|--------------:|---------------------:|--------------------:|------------------------:|-----------------:|
| Data Analyst | 35 | 35 | 35 | 0 | 0 | 0 | 0 |
| Electrical Engineer | 37 | 37 | 37 | 0 | 0 | 0 | 0 |
| Clinical Pharmacist | 35 | 35 | 35 | 0 | 0 | 25 | 0 |
| Barista | 34 | 34 | 34 | 0 | 0 | 25 | 0 |
| DevOps Engineer | 37 | 37 | 37 | 0 | 0 | 0 | 0 |

Samples: `project_review/samples/iteration_004c_study_synthesis_quality/`

### Next step (Iteration 004D) — completed

- **Completed in 004D:** model-knowledge study synthesis behind a feature flag.
- **Next (004E):** Job Posting Intelligence and Interview Pack Source Ladder — see `01_job_search_and_interview_pack.md`.

---

## Iteration 004C-S — Verification cleanup (2026-07-03)

**Goal:** Keep blocked-phrase filter behavior active without contiguous bad-phrase literals in guard source (grep-clean verification).

### Changes

- Centralized runtime-built guard strings in `blocked_phrase_guard.py` (`_p("structured", " verification")` pattern)
- Updated synthesis, document-library retriever, phrase audits, and tests to consume guard constants
- Fixed learning-path skill label so internal `role_specific` category does not appear in exported study text
- Regenerated 004C samples; interview packs remain free of blocked phrases and internal label leaks

### Verification

- Generated interview packs: no blocked generic phrases; no user-facing internal category labels
- Backend tests: **157 passed**

---

## Iteration 004C-R — Skill knowledge source sanitization (2026-07-03)

**Goal:** Stop stale generic boilerplate in `skill_knowledge.json` from reaching exported answers/study material.

### Design

- **`source_sanitizer.py`:** recursive sanitizer for skill/role knowledge dicts; applies joined-word fixes then role-family generic phrase scrubbing
- **Runtime hook:** `_load_knowledge()` sanitizes the full payload on read (covers `_expert()`, `get_skill_knowledge()`, `get_role_context()`)
- **Build hook:** `build_skill_knowledge.py` sanitizes entries before writing JSON

### Source JSON decision

**Regenerated** `skill_knowledge.json` via `build_skill_knowledge.py` (version 2.1). The build script now uses the fixed `resolve_expert_content()` path plus sanitizer, so on-disk blocked-phrase grep hits dropped to **0**. Runtime sanitization remains as a safety net for any future stale writes.

### 004C-R sample status

- Generated benchmark packs: **0** blocked generic phrase hits
- On-disk `skill_knowledge.json`: **0** blocked phrase grep hits after regeneration
- Full document-library/index regeneration still deferred to pre-cleanup gate

## Iteration 004C-P — Saved material insight sentence polish (2026-07-03)

**Goal:** Clean sentence boundaries in Saved material insight (no `flow Pay` joins; natural skill joining).

### Fix

- `build_saved_material_insight()` splits reinforce / revise / focus into three sentences
- Matched skills join naturally (`Coffee Preparation and Customer Service`)
- `_polish_saved_material_insight()` catches residual join artifacts

### 004C-P sample status

- Barista benchmark insight example is clean in `iteration_004c_summary.md`
- Verification grep on generated samples: no blocked phrases or join artifacts

**Test result:** `158 passed`

## Iteration 004D — Model-knowledge feature flag (2026-07-03)

**Goal:** Safe model-knowledge synthesis layer behind a feature flag; random validation sampling from this iteration onward.

### Feature flag design

| Setting | Default | Purpose |
|---|---|---|
| `JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE` | `false` | Master switch — no model calls when off |
| `JOB_SEARCH_MODEL_KNOWLEDGE_PROVIDER` | `disabled` | `deterministic_test` for tests/samples; `gemini` reserved |

### Behavior

- **Disabled (default):** source block shows `Model knowledge: Disabled — … feature flag`; local deterministic + document-library material unchanged
- **Enabled + deterministic_test:** role-family insight added as `### Model knowledge insight`; marked `used` only when non-empty sanitized insight exists
- **Failed provider:** `Failed fallback` status; generation continues with local/document-library material
- **Web research:** remains `not_configured` in 004D
- **No fake URLs or citations** in model insight path

### Sample generation (004D)

- **Fixed benchmark (5):** Data Analyst, Electrical Engineer, Clinical Pharmacist, Barista, DevOps Engineer → `fixed/`
- **Random validation (5, seed 42):** Primary School Teacher, Solicitor, Mechanical Engineer, Journalist, Social Media Creator → `random_validation/`
- Samples at `project_review/samples/iteration_004d_model_knowledge_flag/`

**Test result:** `172 passed` — no API keys required for default tests.

## Iteration 004D-S — Random validation coverage stabilization (2026-07-03)

**Problem:** Random validation exposed weak packs for creative/trending roles (Journalist 17, Social Media Creator 14).

**Fix:**

- Archetype coverage packs for creative/media, creator/trending, and sports careers
- Evidence packs + legacy answer paths to reduce export blocking
- Coverage floor (`28+` exportable questions) for archetype roles only
- Journalist **17 → 31**; Social Media Creator **14 → 30** in regenerated 004D samples

**Test result:** `186 passed`

### Next step (Iteration 004E)

**Planned — not implemented:** [004E — Job Posting Intelligence and Interview Pack Source Ladder](../01_job_search_and_interview_pack.md#iteration-004e--job-posting-intelligence-and-interview-pack-source-ladder-planned)

Key study-material implications for 004E:

- Per-question study modules must connect to the **Job Intelligence Profile** (company, responsibility, skill, tool context) — not role-title-only generics.
- Source ladder extends to pack generation: user posting → link extraction → web (real URLs) → model (flagged) → document library → local fallback.
- Coverage audit must verify study material exists for every exportable question and reflects extracted posting items.
- Final Content Library Regeneration remains blocked until 004E + roadmap corrections complete.

**Test result (latest):** `186 passed`

---

Before final cleanup, after interview-pack and study-material corrections are complete (and again after roadmap study-material corrections), the system must regenerate all final downloadable content and persist it to project storage/database.

### Required outputs (interview study material scope)

1. Interview question-and-answer PDFs
2. Interview study-material PDFs
3. Full interview-pack PDFs
4. Matching Markdown/JSON structured files (`structured_content.json`, study/Q&A Markdown mirrors, indexes)

Roadmap PDFs and roadmap study-material PDFs are covered in `project_review/04_roadmap_page.md`.

### Required behavior

- Delete outdated PDFs only after new final PDFs succeed
- Preserve source templates, code, seed data, and `.env.example`
- Rebuild `documents/indexes/` after regeneration
- Point document-library metadata and fallback retrieval at the latest files
- Ensure frontend downloads serve regenerated PDFs
- Capture verification notes under `project_review/samples/final_content_library_regeneration/` during the phase

### Planned commands

```bash
make seed-role-packs-force          # full library regen
make seed-role-packs-pdf-force      # PDF-only from final JSON
make build-skill-knowledge          # skill index refresh if needed
cd backend && uv run pytest app/agents/job_search/tests -q
```

See also: `project_review/05_cleanup_plan.md` (this phase runs **before** cleanup).

---

## Current issues found (post–Iteration 003)

| ID | Area | Issue | Severity | Status |
|----|------|-------|----------|--------|
| SM-001 | Architecture | Multi-source ladder not implemented | high | open |
| SM-002 | Depth | HR/daily-routine modules improved but not research-backed | medium | open |
| SM-003 | Sources | No `source/fallback status` field | high | **fixed (004A)** |
| SM-004 | Export | Beginner/intermediate/advanced compression in export | medium | open |
| SM-005 | Learning | No cited web/PDF/library sources | high | **improved (004B local library)** |
| SM-006 | Skills | Secondary skill depth uneven | medium | open → **004E** profile-driven |
| SM-007 | Coverage | New categories have study blocks | medium | **fixed** |
| SM-008 | Architecture | Study material not tied to Job Intelligence Profile | high | open → **004E** |

---

## Next implementation notes

**Next major phase:** Iteration 004E — Job Posting Intelligence and Interview Pack Source Ladder (see `01_job_search_and_interview_pack.md`).

- [x] `source/fallback status` on every module (004A metadata + export)
- [x] Wire document-library retrieval to `documents/interview_packs/` (004B)
- [x] Model-knowledge feature flag (004D) — disabled by default
- [x] Random validation coverage floor for creative/trending roles (004D-S)
- [ ] **004E:** Job Intelligence Profile + coverage audit + full source ladder for pack generation
- [ ] **004E:** Per-question study material tied to extracted job profile items
- [ ] **Final content library regeneration** (pre-cleanup gate — after 004E + roadmap corrections)
