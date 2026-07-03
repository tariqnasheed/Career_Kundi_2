# Final Cleanup Plan

Cleanup happens **after** project completion, not during active feature development unless generated cache files pollute git status.

**Important:** Final cleanup (step 13) must **not** run until **Final Content Library Regeneration** (step 12) completes successfully.

**Gate before regeneration:** Iteration **004E — Job Posting Intelligence and Interview Pack Source Ladder** must be complete, along with interview Q&A quality, interview study material, roadmap generator, and roadmap study material corrections (see `01_job_search_and_interview_pack.md`).

---

## Final Content Library Regeneration (required before cleanup)

**Status:** Documented requirement only — **no deletions or regeneration performed yet**.

### When to run

After all corrections are completed for:

- **004E — Job Posting Intelligence and Interview Pack Source Ladder**
- Interview Pack Generator (job intelligence, coverage audit, source ladder)
- Interview Question and Answer quality
- Interview Study Material (per-question, profile-connected)
- Roadmap Generator
- Roadmap Study Material

### Required generated final outputs

1. Interview question-and-answer PDFs
2. Interview study-material PDFs
3. Full interview-pack PDFs
4. Roadmap PDFs
5. Roadmap study-material PDFs
6. Matching Markdown/JSON structured files where the backend uses them for fallback or indexing

### Required behavior

- Remove outdated previously generated PDFs **only after** new final PDFs are successfully generated, saved, indexed, and verified
- Do **not** delete source templates, code, seed data, or `.env.example`
- Rebuild `documents/indexes/` (`role_index.json`, `skill_index.json`, `document_index.json`) after regeneration
- Ensure database/document-library metadata points to the latest regenerated files
- Ensure fallback retrieval uses the latest generated material, not stale PDFs
- Ensure frontend download buttons download the latest final PDFs (interview + roadmap)
- Add verification commands and sample output notes to `project_review/samples/final_content_library_regeneration/`
- Record verification that old PDFs are not referenced by indexes or API responses

### Planned regeneration commands

```bash
# Interview packs — full regeneration (JSON + Markdown + PDFs + indexes)
make seed-role-packs-force

# Interview packs — PDF-only from final structured JSON
make seed-role-packs-pdf-force

# Skill/role knowledge rebuild when catalog or knowledge engine changed
make build-skill-knowledge

# Backend regression
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run pytest -q

# Library/index sanity check
cd backend && uv run python -c "from app.services.role_pack_library import list_library_roles; print(len(list_library_roles()))"
ls -la documents/indexes/
```

Roadmap regeneration commands will be added when the roadmap export pipeline is finalized (see `project_review/04_roadmap_page.md`).

### Verification artifacts to capture

Save under `project_review/samples/final_content_library_regeneration/` (create during the phase):

- Regeneration run summary (roles processed, PDF success/fail counts, timestamp)
- Spot-check notes for frontend download buttons (interview + roadmap exports)
- Index freshness check (`role_index.json`, `skill_index.json`, `document_index.json`)
- Short before/after file inventory for `documents/interview_packs/` and roadmap export paths

### What not to delete during regeneration

| Preserve | May replace after successful regen |
|----------|-------------------------------------|
| Source templates | Outdated role-pack PDFs in `documents/interview_packs/` |
| Application code | Stale export copies not referenced by indexes |
| Seed data / catalog JSON | Temporary ad-hoc PDFs in repo root |
| `.env.example` | Archived exports superseded by new final PDFs |
| `structured_content.json` sources of truth | — (update in place, do not remove library folders) |

---

## Final cleanup checklist

- [ ] **Confirm 004E and dependent interview/roadmap corrections completed**
- [ ] **Confirm Final Content Library Regeneration completed** (step 12 gate)
- [ ] Remove `__pycache__/`
- [ ] Remove `*.pyc`
- [ ] Remove `.pytest_cache/`
- [ ] Remove `.DS_Store`
- [ ] Remove temporary Vite timestamp files:
  - `frontend/vite.config.ts.timestamp-*.mjs`
- [ ] Review whether `frontend/dist/` should be committed
- [ ] Remove temporary PDFs not intended for final repo (only **after** final library regen verified)
- [ ] Remove temporary Markdown samples not intended for final repo
- [ ] Keep `.env.example`
- [ ] Do **not** commit real `.env`
- [ ] Check for exposed secrets
- [ ] Check duplicate reports
- [ ] Check unused temporary scripts
- [ ] Run final tests
- [ ] Run final `git status`
- [ ] Confirm working tree clean

---

## `.gitignore` rules to verify

Ensure `.gitignore` ignores:

| Pattern | Status in repo `.gitignore` |
|---------|----------------------------|
| `__pycache__/` | ✅ present |
| `*.pyc` | ✅ covered by `*.py[cod]` |
| `.pytest_cache/` | ✅ present |
| `.DS_Store` | ✅ present |
| `frontend/vite.config.ts.timestamp-*.mjs` | ✅ covered by `*.timestamp-*.mjs` |

**Do not ignore `project_review/`** — review artifacts should be committed when ready for external review.

### Optional additions (only if gaps appear later)

```gitignore
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
frontend/vite.config.ts.timestamp-*.mjs
```

---

## Pre-cleanup commands

```bash
# From repo root — inspect only; run removal during final cleanup iteration
find . -type d -name __pycache__ | head
find . -name '*.pyc' | head
find . -type d -name .pytest_cache | head
find . -name .DS_Store | head
find frontend -name 'vite.config.ts.timestamp-*.mjs' 2>/dev/null | head
```

---

## Final test commands

```bash
cd backend && uv run pytest app/agents/job_search/tests -q
cd backend && uv run pytest -q
cd frontend && npm run test:e2e   # if applicable at project end
```

---

## Artifacts to keep vs remove

| Keep | Remove (unless explicitly intended) |
|------|-------------------------------------|
| `project_review/` curated samples | Ad-hoc `*.pdf` in repo root |
| `documents/` role packs (after final regen) | `__pycache__/`, `.pytest_cache/` |
| `.env.example` | Real `.env` files |
| Committed review screenshots in `project_review/screenshots_or_export_notes/` | Temp Vite timestamp files |
| Final regenerated PDFs under `documents/interview_packs/` | Outdated PDFs superseded by final regen |

---

## Notes

- `*.pdf` is currently gitignored globally — intentional samples for review should live under `project_review/samples/` and may need a `.gitkeep` + documented exception or renamed extension if they must be committed.
- Revisit `project_review/samples/` git policy during Iteration 002 when baseline captures begin.
- **Do not remove stale PDFs or temporary exports during active development** — defer to the Final Content Library Regeneration phase, then final cleanup.
