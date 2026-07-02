# Final Cleanup Plan

Cleanup happens **after** project completion, not during active feature development unless generated cache files pollute git status.

---

## Final cleanup checklist

- [ ] Remove `__pycache__/`
- [ ] Remove `*.pyc`
- [ ] Remove `.pytest_cache/`
- [ ] Remove `.DS_Store`
- [ ] Remove temporary Vite timestamp files:
  - `frontend/vite.config.ts.timestamp-*.mjs`
- [ ] Review whether `frontend/dist/` should be committed
- [ ] Remove temporary PDFs not intended for final repo
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
| `documents/` role packs | `__pycache__/`, `.pytest_cache/` |
| `.env.example` | Real `.env` files |
| Committed review screenshots in `project_review/screenshots_or_export_notes/` | Temp Vite timestamp files |

---

## Notes

- `*.pdf` is currently gitignored globally — intentional samples for review should live under `project_review/samples/` and may need a `.gitkeep` + documented exception or renamed extension if they must be committed.
- Revisit `project_review/samples/` git policy during Iteration 002 when baseline captures begin.
