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

## Current issues found (baseline inspection)

| ID | Area | Issue | Severity | Status |
|----|------|-------|----------|--------|
| SM-001 | Architecture | Multi-source ladder not implemented (compiler/fallback only) | high | open |
| SM-002 | Depth | Behavioral/motivation modules are STAR-framed but thin vs technical modules | medium | open |
| SM-003 | Sources | No `source/fallback status` field in study modules | high | open |
| SM-004 | Export | Beginner/intermediate/advanced fields exist in structured data but export compresses visual depth | medium | open |
| SM-005 | Learning | No cited web/PDF/library sources — not yet real research-backed study material | high | open |
| SM-006 | Skills | Secondary skills get study modules but less technical depth than primary focus skill | medium | open |

---

## Next implementation notes

**Next Cursor task:** After Job Search workflow fixes (step 3), proceed to step 4 — Study Material multi-source architecture.

- [ ] Add `source/fallback status` to every study module
- [ ] Implement `StudyMaterialOrchestrator` skeleton with web/model/library/fallback ladder
- [ ] Preserve existing `study_material_quality_audit` as hard gate
- [ ] Re-capture Iteration 003 samples after architecture lands
