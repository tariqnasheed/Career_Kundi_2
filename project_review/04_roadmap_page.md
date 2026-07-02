# Roadmap Page

## Current goal

Rebuild the roadmap page, fix roadmap generation, expand role coverage, and add comprehensive roadmap study material.

---

## Required role search/dropdown

Should support:

- global roles
- fields
- streams
- departments
- technical careers
- healthcare careers
- engineering careers
- business careers
- education careers
- public service careers
- creative/media careers
- creator careers
- sports careers
- unique/trending careers
- direct custom role input

### Example unique/trending roles

- YouTuber
- social media personality
- Instagram creator
- TikTok creator
- podcaster
- cricketer
- footballer
- journalist
- content strategist
- esports player
- streamer
- influencer marketing specialist

---

## Technical role roadmap requirements

Roadmaps for technical roles should include:

- foundations
- core skills
- tools/software
- projects
- practice tasks
- certifications if relevant
- portfolio plan
- interview preparation
- job application plan
- advanced specialization

---

## Non-technical and creator roadmap requirements

Roadmaps for non-technical or creator roles should include:

- niche/content selection
- platform setup
- audience research
- content planning
- publishing schedule
- branding
- marketing strategy
- monetization strategy
- analytics
- collaboration strategy
- realistic earning ranges or scenarios
- legal/safety/platform policy basics

> **Important:** Do not promise guaranteed earnings. Use realistic ranges, assumptions, and scenarios.

---

## Study material requirements

Each roadmap should include study material for all important skills and milestones.

Study material should include:

- comprehensive skill modules
- basic to advanced explanations
- principles
- formulas where relevant
- examples
- diagrams or visual explanation placeholders where possible
- projects/practice tasks
- source ladder same as interview packs
- downloadable Markdown/PDF

---

## Fallback strategy

Use the same source ladder as interview-pack study material:

1. web research
2. LLM/model knowledge
3. saved PDFs/Markdown/JSON
4. local deterministic fallback

---

## Baseline issues placeholder

_Document roadmap page and generation issues found during review._

| ID | Area | Issue | Severity | Status |
|----|------|-------|----------|--------|
| RM-001 | Coverage | Role catalog breadth vs creator/trending roles TBD | TBD | open |
| RM-002 | Generation | Roadmap generation reliability TBD | TBD | open |
| RM-003 | Study material | Per-milestone study modules not yet comprehensive | TBD | open |
| RM-004 | Monetization | Earnings content must use ranges/scenarios only | TBD | policy |

---

## Next implementation notes placeholder

_Next Cursor task: Roadmap page rebuild (Implementation order step 8)._

- [ ] Expand role search taxonomy (fields, streams, creator careers)
- [ ] Rebuild roadmap UI and generation flow
- [ ] Add per-milestone study material with source ladder
- [ ] Add Markdown/PDF export for roadmaps
- [ ] Capture sample roadmaps in `project_review/samples/`

---

## Final Content Library Regeneration (pre-cleanup gate)

**Status:** Documented only — not executed yet.

Before final cleanup, after roadmap generator and roadmap study-material corrections are complete, regenerate and persist all final roadmap exports alongside interview-pack content.

### Required roadmap outputs

4. Roadmap PDFs
5. Roadmap study-material PDFs
6. Matching Markdown/JSON structured files used for fallback, indexing, or download

### Required behavior

- Remove outdated roadmap PDFs only after new final PDFs are successfully generated
- Do **not** delete source templates, code, seed data, or `.env.example`
- Rebuild document indexes after regeneration so roadmap entries appear in `documents/indexes/`
- Ensure database/document-library metadata references the latest roadmap files
- Ensure fallback retrieval and frontend download buttons use the latest regenerated roadmap PDFs

### Planned verification (to document in `project_review/`)

- Roadmap export smoke test per representative role category (technical, healthcare, creator)
- Download-button check for roadmap PDF and roadmap study-material PDF
- Index/metadata spot-check after regeneration
- Sample notes under `project_review/samples/final_content_library_regeneration/` (created during the phase)

Roadmap-specific regeneration commands will be added when the export pipeline is finalized. Interview-pack regeneration commands are documented in `project_review/00_iteration_log.md` and `project_review/02_study_material.md`.

**This phase must complete before final cleanup** (`project_review/05_cleanup_plan.md`).
