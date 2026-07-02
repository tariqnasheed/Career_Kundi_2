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
- [ ] Add model-knowledge draft step behind feature flag (004C)
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

- Model-knowledge study synthesis behind a feature flag (recommended)

---

**Status:** Documented only — not executed yet.

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
| SM-006 | Skills | Secondary skill depth uneven | medium | open |
| SM-007 | Coverage | New categories have study blocks | medium | **fixed** |

---

## Next implementation notes

**Next Cursor task:** Iteration 004C — model-knowledge study synthesis behind a feature flag.

- [ ] `StudyMaterialOrchestrator` skeleton
- [x] `source/fallback status` on every module (004A metadata + export)
- [x] Wire document-library retrieval to `documents/interview_packs/` (004B)
- [x] Re-capture Iteration 004B samples after library retrieval lands
- [x] **004B-F:** filter Core Terminology-only matches and generic vocabulary snippets
- [x] **004B-G:** filter Role Specific/generic procedure snippets; normalize skill label casing
- [ ] **Final content library regeneration** (pre-cleanup gate — regenerate interview PDFs/JSON/indexes before cleanup)
- [ ] **Final content library regeneration** (pre-cleanup gate — regenerate all interview PDFs/JSON/indexes before cleanup)
