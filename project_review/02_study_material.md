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

### Remaining limitations

- No web URLs or external citations are fabricated
- Document library packs are detected but not merged into study modules
- Model-knowledge and web-research agents not wired

### Next implementation notes (Iteration 004B)

- [ ] Consume document-library content for matching role/skill questions
- [ ] Add model-knowledge draft step behind feature flag
- [ ] Add web-research stub with real URL capture only
- [ ] Persist `study_sources` in saved role packs and API responses

---

## Current issues found (post–Iteration 003)

| ID | Area | Issue | Severity | Status |
|----|------|-------|----------|--------|
| SM-001 | Architecture | Multi-source ladder not implemented | high | open |
| SM-002 | Depth | HR/daily-routine modules improved but not research-backed | medium | open |
| SM-003 | Sources | No `source/fallback status` field | high | **fixed (004A)** |
| SM-004 | Export | Beginner/intermediate/advanced compression in export | medium | open |
| SM-005 | Learning | No cited web/PDF/library sources | high | open |
| SM-006 | Skills | Secondary skill depth uneven | medium | open |
| SM-007 | Coverage | New categories have study blocks | medium | **fixed** |

---

## Next implementation notes

**Next Cursor task:** Iteration 004B — document-library retrieval + model draft behind feature flags.

- [ ] `StudyMaterialOrchestrator` skeleton
- [x] `source/fallback status` on every module (004A metadata + export)
- [ ] Wire `PDFLibraryRetrieverAgent` to `documents/interview_packs/`
- [ ] Re-capture Iteration 004B samples after library retrieval lands
