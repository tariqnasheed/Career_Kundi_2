# Final Cleanup Plan

Cleanup happens **after** project completion, not during active feature development unless generated cache files pollute git status.

**Important:** Final cleanup (step 14) must **not** run until **Final Content Library Regeneration** (step 13) completes successfully.

**Do not run final cleanup or Final Content Library Regeneration yet** unless explicitly instructed. Complete the Interview Pack + Study Material system first (004E-B through 004E-F).

**Gate before regeneration:** **004E-B through 004E-F** must be complete, along with interview Q&A quality, interview study material, roadmap generator, and roadmap study material corrections (see `01_job_search_and_interview_pack.md`).

> **004F Global Job Search Agent is intentionally deferred until Interview Pack Generator and Interview Study Material are fully completed.**

---

## Research-Assisted Development Rule

**Applies to every future major implementation iteration** (effective 004E-A-S, 2026-07-03). Full rule: `project_review/00_iteration_log.md`.

Major iterations may use web research to improve design, reliability, and UX — especially for PDF/export generation, document-library storage/indexing, final content library regeneration, source ladders, and testing strategy.

**Rules (summary):** prefer official documentation and reputable open-source examples; no proprietary copying; justify risky dependencies; no fake citations or URLs; do not claim research was used unless it was; keep tests deterministic; document influential ideas in `project_review/`.

**004E-B onward:** research job-posting extraction and company-profile capture patterns before implementation so final regeneration and cleanup phases inherit sound storage, indexing, and citation practices.

**004E-B–004E-F (active):** Complete interview pack link extraction, company research, source ladder, study material finalization, and regression gate before any Job Search work.

**004F (DEFERRED):** Global Job Search Agent — requirements preserved in `01_job_search_and_interview_pack.md` § Iteration 004F. **Do not implement** until 004E-F gate passes. When eventually started, apply research-assisted development before job provider integration (Adzuna, USAJOBS, SerpApi, etc.). 004F does not change the final cleanup gate.

**Job Search page roadmap (004F — deferred):**

- City and country filters; full-time, part-time, contract, internship, freelance, and odd/gig job types
- `Search around the world` checkbox (default **unchecked**); default search deeply targets selected/nearest location
- Worldwide expansion only when user enables the checkbox
- Exhaustive configured-provider search — not falsely unlimited global coverage
- Nearest-first requires user location permission or profile location
- **Use this job** and **Open original link** must remain on every result card
- Tests must use mock providers; default tests must not require API keys

---

## Final Content Library Regeneration (required before cleanup)

**Status:** Documented requirement only — **no deletions or regeneration performed yet**. **Do not run unless explicitly instructed.**

### When to run

After all corrections are completed for:

- **004E-B through 004E-F** — Interview Pack + Study Material completion track
- Interview Pack Generator (job intelligence, link extraction, company research, coverage audit, full source ladder)
- Interview Question and Answer quality
- Interview Study Material (per-question, profile-connected — 004E-E)
- Roadmap Generator
- Roadmap Study Material

**Not a substitute for 004E-F:** The regression gate (004E-F) validates samples and metrics before Job Search. Full library regeneration runs later, after roadmap work is also complete.

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

- [ ] **Confirm 004E-B through 004E-F and dependent interview/roadmap corrections completed**
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
