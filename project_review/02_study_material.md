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

## Baseline sample placeholder

_Paste or link study-module samples after Iteration 002._

**Sample paths (to be filled):**

| Role | Question topic | File |
|------|----------------|------|
| _e.g. Electrician_ | Electrical Installation | `samples/study_material/electrician_installation.md` |
| _e.g. Data Analyst_ | SQL diagnostic | |

**Sample module (template):**

```markdown
**Core idea:** Whether you can answer this [skill] interview question for [role]: …

**How to apply it:**
1. …

**Common mistakes:**
- …

**Interview tip:**
- …

**Source/fallback status:** web+model | model+library | library-only | local-fallback
```

---

## Current issues placeholder

_Document study-material weaknesses found during review._

| ID | Area | Issue | Severity | Status |
|----|------|-------|----------|--------|
| SM-001 | Architecture | Multi-source ladder not yet implemented (deterministic compiler path only) | high | open |
| SM-002 | Export | Some behavioral answers remain visually short in export | low | known |
| SM-003 | Sources | No web-research or source-verification agents yet | high | open |

---

## Next implementation notes placeholder

_Next Cursor task: Study Material multi-source architecture (Implementation order step 4)._

- [ ] Implement `StudyMaterialOrchestrator` skeleton
- [ ] Wire `PDFLibraryRetrieverAgent` to `documents/interview_packs/`
- [ ] Add `source/fallback status` field to every study module
- [ ] Preserve existing quality audits as hard gates
- [ ] Save iteration samples to `project_review/samples/`
