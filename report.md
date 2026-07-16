# CareerKundi — Repair Report

> **LLM provider (current):** Local Ollama 8B at `http://127.0.0.1:11434`. No Gemini API required. Use `LLM_PROVIDER=mock` for deterministic tests. Historical Gemini mentions in this report are legacy/deprecated.

## CORE-VALUE-R1 (2026-07-16)

Visible product loop repair before 0053-F1:

- **Roadmap:** empty Ollama JSON (`overview: ""`) no longer accepted; normalize to useful study/practice; FE empty states + refresh errors.
- **CV Builder:** `generation_mode=quick_intake` from name/role/level without mutating Profile/Passport; Generate & Export PDF; honest placeholders only.

Evidence: `~/Desktop/CareerKundi_CORE_VALUE_R1_CV_Roadmap_Repair_Evidence.txt`

## JOB-INT-R1 + ROADMAP-RICH-CONTENT + POST-CLAUDE-R2 (2026-07-16)

Pushed after CORE-VALUE-R1 and verified in POST-CLAUDE-R2:

- **JOB-INT-R1 (`8ac8793a`):** first-person interview answers; prompt contract; no unsupported candidate claims.
- **ROADMAP-RICH-CONTENT (`893a4812`):** Bloom-aligned study + flashcards/quizzes/projects/reflection.
- **POST-CLAUDE-R2:** integration audit / readiness gate before 0053-F1.

Evidence: `~/Desktop/CareerKundi_POST_CLAUDE_R2_Integration_Audit_Evidence.txt`

## 0053-F1 Claim Service Contract Boundary (2026-07-16)

Locks claim create-time contracts before evidence/verification:

- Create verification: `unverified` only
- Create support: `not_provided` / `profile_supported` / `source_linked` only
- Source/snapshot = provenance, not verification; no silent upgrades
- Safe display labels (`display.py`); no public claim routes; no EvidenceRecord yet

Evidence: `~/Desktop/CareerKundi_0053_F1_Claim_Service_Contract_Boundary_Evidence.txt`

## 0053-F2 Evidence Domain Skeleton (2026-07-16)

Private evidence metadata + claim-evidence links only:

- Tables: `evidence_records`, `claim_evidence_links` via `f0009_evidence_foundation`
- Link does **not** mutate claim support/verification axes
- No upload/download, no HTTP routes, no frontend, no verification workflow

Evidence: `~/Desktop/CareerKundi_0053_F2_Evidence_Domain_Skeleton_Evidence.txt`

## 0053-F3 Private Evidence Service/API Boundary (2026-07-16)

Private authenticated metadata API:

- `/api/v1/evidence` create/list/get/subject list
- `/api/v1/evidence/links` + claim link list
- Current-user ownership; cross-user 404; no upload/download; no claim axis mutation

Evidence: `~/Desktop/CareerKundi_0053_F3_Private_Evidence_API_Boundary_Evidence.txt`

## 0053-F4 Private Evidence Library UI (2026-07-16)

Private `/evidence` page for metadata create/list:

- Safe wording; no file upload/download; no verification/share controls
- Attachment storage deferred to F5 (`careerkundi_0053_f4_attachment_storage_decision.md`)

Evidence: `~/Desktop/CareerKundi_0053_F4_Private_Evidence_Library_UI_Evidence.txt`

## 0053-F5 Attachment Storage Backend (2026-07-16)

Private local evidence file storage + owner-only attachment APIs:

- `POST/GET /api/v1/evidence/{evidence_id}/attachment`
- Size/MIME/SHA-256 guards; no public URL; upload ≠ verified
- Frontend upload UI still disabled until F6

Evidence: `~/Desktop/CareerKundi_0053_F5_Attachment_Storage_Backend_Evidence.txt`

## 0053-F6 Evidence Upload UI (2026-07-16)

Private attach/download controls on `/evidence`:

- “Attach private file” / “Download private attachment”
- Client 5 MB + MIME guards; authenticated blob download; no public URL
- Upload does not verify evidence or claims; no OCR/Passport/CV/Roadmap/Jobs integrations

Evidence: `~/Desktop/CareerKundi_0053_F6_Evidence_Upload_UI_Evidence.txt`

## 0053-F7 Evidence-to-Claim Linking UI (2026-07-16)

Private claim linking on `/evidence`:

- `GET /api/v1/evidence/linkable-claims` (current-user only; no `/api/v1/claims`)
- “Link evidence to claim” with supports/contests/context
- Linking does not verify claims or mutate support/verification axes
- No Passport evidence panel yet

Evidence: `~/Desktop/CareerKundi_0053_F7_Evidence_To_Claim_Linking_UI_Evidence.txt`

---

This document explains, in plain language, everything that was broken in the
project and exactly how it was fixed. It is written so that a non-coder can
follow along. Technical terms are explained the first time they appear.

---

## Simple summary (read this first)

CareerKundi has two halves that must talk to each other:

- **Backend** — the Python "engine" (FastAPI + AI agents + Gemini) that does the real work.
- **Frontend** — the React website you see in the browser.

The audit found **three showstoppers** and several smaller problems:

1. The **backend could not even start** — one missing line of code crashed it on boot.
2. Two AI features (**"Import job from URL"** and **"Auto-Apply / cover letter"**) crashed every time they ran, because their code was written for an older version of the AI helper that no longer exists.
3. The **frontend was calling the wrong web addresses**, so most buttons (job list, CV builder, interview packs, "Save Job") silently failed.

All three are now fixed, plus a real safety bug, a wasted-money bug in the AI
cost path, and some tidy-up. The frontend now type-checks and builds cleanly,
and the backend now compiles, lints clean, and its configuration and data
models load correctly.

**Status: Fixed** (one setup caveat remains — running the full server needs a real environment; see *Remaining items* at the end).

---

## Errors found

| # | Severity | Where | What was wrong |
|---|----------|-------|----------------|
| 1 | 🔴 Critical | `backend/app/main.py` | Used `AsyncGenerator` without importing it → backend crashes on startup |
| 2 | 🔴 Critical | `backend/app/agents/job_extractor/agents.py`, `auto_apply/agents.py` | Called a non-existent setting `USE_MOCK_LLM` and an old AI-helper signature → every run crashes |
| 3 | 🔴 Critical | `frontend/src/lib/api.ts` | Called wrong API paths (`/jobs`, `/cv`) that don't exist on the backend (`/job-search`, `/cv-builder`) |
| 4 | 🟠 High | `frontend` ↔ `backend` | The **"Save Job"** button had no matching backend endpoint at all |
| 5 | 🟠 High (safety) | 4 backend files | `.lstrip("www.")` mangled website names, letting blocked job sites slip past the safety check |
| 6 | 🟡 Medium (cost) | `backend/app/tools/rag.py` | Every stored document was sent to the AI embedding model **twice** — wasted money |
| 7 | 🟢 Low | several files | Unused imports / dead variables / a stale comment |
| 8 | 🟠 High | `frontend` ↔ `backend` | Keyword job-search and the application-status tracker had no backend route, and `SavedJob` had no `status` column |

---

## Files changed

**Backend (Python)**

- `app/main.py` — added the missing import (Fix 1) + removed 1 unused import
- `app/agents/job_extractor/agents.py` — rewired to the correct AI helper (Fix 2) + safety fix (Fix 5)
- `app/agents/auto_apply/agents.py` — rewired to the correct AI helper (Fix 2) + safety fix (Fix 5)
- `app/agents/job_extractor/mock_data.py` — safety fix (Fix 5) + removed dead variable + fixed stale comment
- `app/agents/auto_apply/mock_data.py` — safety fix (Fix 5)
- `app/agents/job_search/mock_data.py` — removed an unused loop counter
- `app/tools/rag.py` — removed the duplicate embedding call (Fix 6) + removed unused imports
- `app/schemas/job_search.py` — added `SavedJobCreate` for "Save Job" (Fix 4); added `JobStatusUpdate` and a `status` field on `SavedJobRead` (Fix 8)
- `app/api/routes/job_search.py` — added `POST /job-search/` save (Fix 4); added `GET /job-search/search` and `PATCH /job-search/{id}/status` (Fix 8)
- `app/db/models/job.py` — added the `status` tracking column to `SavedJob` (Fix 8)
- `app/services/badges.py`, `app/api/routes/apply.py`, `app/api/routes/profile.py`, `app/db/models/queue.py`, `app/db/models/user.py`, `app/agents/job_extractor/graph.py` — unused imports auto-removed (Fix 7)

**Frontend (TypeScript/React)**

- `src/lib/api.ts` — corrected every job, CV, and profile API address (Fix 3) + wired "Save Job", CV download, and URL-import to the real backend routes

**New file**

- `report.md` — this document

---

## The fixes, explained

### Fix 1: The backend now starts

**Problem.** The whole backend refused to start. The very first thing it does
when booting is define a "startup/shutdown" helper, and that line referenced a
type name called `AsyncGenerator` that had never been imported.

**Why it happened.** In Python, a type "hint" like `-> AsyncGenerator[None, None]`
is actually run when the file loads. Because nothing imported that name, Python
threw a `NameError` and stopped — before a single web page could load.

**What was changed.** One line added to the top of `app/main.py`:

```python
from collections.abc import AsyncGenerator
```

**Why this fix works.** Now the name exists when Python reads that line, so the
startup helper is defined normally and the server boots.

**How it was verified.** A tiny standalone script defined the same startup
helper after adding the import and confirmed it no longer raises `NameError`.

---

### Fix 2: "Import from URL" and "Auto-Apply" no longer crash

**Problem.** Two AI features crashed the instant they ran:
the **job-URL extractor** (used by "Import job from URL") and the
**auto-apply / cover-letter** agent.

**Why it happened.** These two files were written against an **older, deleted
version** of the shared AI helper. Three things no longer matched reality:

- They checked a setting called `settings.USE_MOCK_LLM`, which **does not exist**
  (the project uses `settings.llm_mode`, which is `"mock"` or `"live"`). Reading a
  setting that doesn't exist crashes immediately — even in offline/mock mode.
- They built the AI request with the wrong field names
  (`system_role`, `system_body`, `user_body`, `model_tier`, `response_schema`)
  instead of the real ones (`system_prompt`, `user_prompt`, `json_schema`, `temperature`).
- They called the AI like `await get_llm(spec, cost_monitor)`, but `get_llm()`
  actually takes a difficulty tier and returns a helper object you then call
  `.generate()` on.

The project's other four agent teams (job search, CV builder, roadmap, chatbot)
already use the **correct** pattern — these two were simply never updated.

**What was changed.** Both files were rewired to copy the exact pattern the
working agents use:

```python
if settings.llm_mode == "mock":
    result = mock_data.<realistic offline result>
else:
    llm = get_llm("flash")
    spec = PromptSpec(system_prompt=..., user_prompt=..., json_schema=..., temperature=...)
    response = await llm.generate(spec)
    self.cost_monitor.record(response, tier="flash")   # tracks token cost
    result = response.parsed_json      # (or response.text for the cover letter)
```

**Why this fix works.** The code now uses names and calls that actually exist,
so both the offline (mock) path and the live-Gemini path run without crashing,
and every AI call is cost-tracked like the rest of the system.

**How it was verified.** Both files compile; a project-wide search confirms
**no** remaining references to `USE_MOCK_LLM` or the old field names; and the
shared AI helper's real function signatures were read directly to match them.

---

### Fix 3: The frontend can now reach the backend

**Problem.** Most of the site quietly did nothing: the jobs list, CV list, CV
generation, interview packs, and profile screen all failed with "not found"
errors behind the scenes.

**Why it happened.** The frontend's address book (`src/lib/api.ts`) pointed at
paths that don't exist on the backend:

| Frontend was calling | Backend actually serves |
|---|---|
| `/jobs/...` | `/job-search/...` |
| `/cv/...` | `/cv-builder/...` |
| `/cv/{id}/pdf` | `/cv-builder/{id}/export?format=pdf` |
| `/profile/` (trailing slash) | `/profile` (no slash) |

**What was changed.** Every job, CV, and profile address in `api.ts` was
corrected to the real backend route. The CV "download" call now uses the real
`export` route (which supports PDF, DOCX, and Markdown). The URL-import call now
points at the real `/job-search/parse` endpoint. The genuine `/apply/jobs/...`
addresses were left untouched.

**Why this fix works.** The browser now knocks on doors that actually exist, so
the backend answers instead of returning "not found."

**How it was verified.** The frontend **type-check passed** (`tsc --noEmit`,
0 errors) and a **production build succeeded** (`vite build`, 2122 modules). A
search confirmed no stale `/jobs` or `/cv/` paths remain (only the correct
`/apply/jobs/...` one).

---

### Fix 4: The "Save Job" button now works

**Problem.** After importing a job from a URL and reviewing it, clicking
**"Save Job"** did nothing useful — the frontend sent the job to `POST /jobs/`,
an address the backend never had.

**Why it happened.** The backend could *parse-and-save* a job from a raw URL
(`POST /job-search/parse`), but it had **no endpoint to save a job the user had
already reviewed and possibly hand-edited**. That endpoint was simply missing.

**What was changed.** Two small, self-contained additions to the backend:

- A new data shape `SavedJobCreate` (in `app/schemas/job_search.py`) that
  accepts the exact fields the review form sends (title, company, location,
  salary, etc.). It safely turns blank form values into "empty" so, for example,
  an empty salary box doesn't crash the save.
- A new endpoint `POST /job-search/` (in `app/api/routes/job_search.py`) that
  saves that reviewed job straight to the database **without** re-scraping — so
  the user's manual edits are kept. The frontend "Save Job" call now points here.

**Why this fix works.** The button's request now lands on a real endpoint whose
input shape exactly matches what the page sends, and the job is stored under the
signed-in user.

**How it was verified.** With the lightweight `pydantic` library installed, the
new `SavedJobCreate` shape was fed the **exact payload the page sends** —
including a blank salary field and an unexpected extra field — and it validated
correctly (blank salary → empty, `"120000"` → number `120000.0`, extra field
ignored, missing title → "Untitled Role"). The route file compiles cleanly.

---

### Fix 5: Blocked job sites are correctly detected again (safety)

**Problem.** The safety check that blocks auto-applying to sites which forbid it
(LinkedIn, Workday, Wellfound, etc.) could be **fooled**. A web address like
`www.wellfound.com` was being turned into `ellfound.com`, so it no longer
matched the blocked list — and the block was skipped.

**Why it happened.** The code used `.lstrip("www.")` to remove a leading
`www.`. But `lstrip` does **not** remove the text `"www."` — it removes any of
the individual characters `w`, `.` from the start. So `www.wellfound.com` lost
its `w`,`w`,`w`,`.` **and the next `w`**, leaving `ellfound.com`.

**What was changed.** In all four places, `.lstrip("www.")` became
`.removeprefix("www.")`, which removes the exact prefix `"www."` and nothing
else. (Files: `job_extractor/agents.py`, `job_extractor/mock_data.py`,
`auto_apply/agents.py`, `auto_apply/mock_data.py`.)

**Why this fix works.** `removeprefix` strips the literal `"www."` only, so the
real domain survives intact and matches the blocked list correctly.

**How it was verified.** A short script compared old vs. new on real domains and
proved the security impact directly:

```
www.wellfound.com   old(lstrip)=ellfound.com    new(removeprefix)=wellfound.com
BEFORE fix blocks www.wellfound.com?  False   ← bug: block was skipped
AFTER  fix blocks www.wellfound.com?  True    ← fixed
```

---

### Fix 6: Stop paying the AI twice per document (cost)

**Problem.** When the app saved new text into its "memory" (the vector store
used for retrieval), it sent every document to the AI **embedding** model twice.

**Why it happened.** The code computed `query_vec = ...embed_query(doc)` and then
never used it — the very next line already did the similarity search, which
embeds the text again internally. The first call was pure waste (it cost money
in live mode and slowed things down).

**What was changed.** In `app/tools/rag.py`, the unused embedding call (and a
now-unused helper variable) were removed, with a comment explaining why.

**Why this fix works.** The duplicate work is gone; the deduplication logic still
runs exactly as before, just once instead of twice per document.

**How it was verified.** The file compiles and the linter confirms the leftover
unused variables are gone; the surrounding dedup logic was left unchanged.

---

### Fix 7: Tidy-up (unused imports, dead code, a stale comment)

Small, low-risk clean-ups that remove confusion and let the linter pass:
unused imports across seven files were auto-removed; two dead variables and one
unused loop counter were deleted; and one comment that mentioned the old
`USE_MOCK_LLM` setting was corrected to `llm_mode`.

---

### Fix 8: Job keyword-search and the application-status tracker are now live

**Problem.** Two frontend helpers had nothing to talk to: `jobApi.search(...)`
(a keyword/filter search over jobs) and `jobApi.updateStatus(...)` (moving a
saved job through saved → applied → interviewing → offered → rejected). The
backend had neither endpoint, and the saved-job record had no `status` field at
all — even though the frontend's type already expected one.

**Why it happened.** These endpoints were simply never built on the backend, and
the tracking `status` column was never added to the database model.

**What was changed.**

- Added a `status` column to the `SavedJob` model (`app/db/models/job.py`),
  defaulting to `"saved"`, with a database-level default so existing rows stay valid.
- Added `status` to the `SavedJobRead` output shape, so every job now reports it.
- Added `PATCH /job-search/{id}/status` (with a `JobStatusUpdate` body that only
  accepts the five valid values) to change it.
- Added `GET /job-search/search`, which filters the user's saved jobs by keyword
  (`q` over title / company / description), `location`, `employment_type`, and
  `remote` — newest-first and paginated.

**Why this fix works.** The two frontend helpers now hit real endpoints whose
inputs and outputs match exactly what the frontend already sends and expects. The
`/search` route is deliberately declared **before** `/{job_id}` so the word
"search" isn't mistaken for a job ID.

Note on search scope: CareerKundi imports jobs by URL/paste rather than crawling
outside job boards, so "search" filters the jobs the user has **already saved** —
the honest, working behavior given the data the app actually has.

**How it was verified.** All 101 backend files compile; the full real-bug linter
pass is clean; `JobStatusUpdate` accepts valid values and rejects invalid ones;
`SavedJobRead` defaults `status` to `"saved"`; and the route order was checked so
`/search` resolves before `/{job_id}`.

**One setup note (important).** This adds a database column. The project keeps its
`migrations/versions/` folder empty and builds the schema from the models (the way
every table here is created), so the new column is picked up automatically when
migrations are generated/applied — e.g. `make migrate-auto name=add_job_status`
then `make migrate` (the Docker image already runs `alembic upgrade head` on boot).
If you point the app at a database that already has a `saved_jobs` table, apply
that one migration so the column gets added.

---

## Round 3 — README §36 "Known Limitations" fixes

Eight of the twelve documented limitations were fixed; the other four are large
features or intentional (listed at the end).

**§36.1 — Fresh databases now get tables.** Added a baseline Alembic migration
(`backend/app/db/migrations/versions/0001_initial.py`) that builds the whole
schema from the ORM models, so `alembic upgrade head` on a new database creates
every table instead of doing nothing.

**§36.2 — `make seed` now creates real demo data.** Rewrote
`backend/scripts/seed.py` to create a demo login (`demo@careerkundi.com` /
`demo1234`), a profile with skills, and two sample jobs. It's idempotent
(re-running when the demo user exists does nothing).

**§36.4 — CV export button works.** The CV Builder's export button now downloads
the real file from `GET /cv-builder/{id}/export` instead of showing a
placeholder toast (`frontend/src/pages/CVBuilderPage.tsx`).

**§36.5 — Profile Match Rating is computed.** New
`backend/app/services/matching.py` scores 0–100 fit from a job's skills vs. the
user's profile skills (weighted by importance), stored on every job saved or
parsed. It was always `null` before.

**§36.8 — `backend/.env.example` fixed.** Rewritten so every variable matches a
real `Settings` field; the non-existent `SECRET_KEY` / `LLM_MODE` /
`GEMINI_MODEL` / `SEARCH_MODE` / `ACCESS_TOKEN_EXPIRE_MINUTES` names are gone.

**§36.9 — Readiness probe added.** New `GET /health/deep`
(`backend/app/api/routes/health.py`) pings the database and Redis and returns
HTTP 503 if either is down; `GET /health` stays a fast liveness probe.

**§36.7 — Real tests added.** Backend `tests/unit/` (match scorer, job schemas,
CV Markdown export) = 12 tests; frontend `tests/unit/api.test.ts` (client
surface) = 2 tests. All pass, so CI now runs real tests. Also made
`src/test-setup.ts` safe to load outside a DOM.

**Deferred (large features or intentional):** §36.3 (real background queue +
storage) and §36.6 (real auto-apply submission) are large build-outs — and
auto-submitting real job applications is deliberately kept out of scope for
safety. §36.10 (CV-viewer true PDF render), §36.11 (real deploy workflow), and
§36.12 (Playwright e2e) are infra/design items that need real targets or a
running stack. All four remain documented in README §36.

---

## Verification — what was actually run

| Check | Command | Result |
|---|---|---|
| Frontend types | `tsc --noEmit` | ✅ Passed (0 errors) |
| Frontend build | `vite build` | ✅ Passed (2122 modules bundled) |
| Backend syntax/compile | `py_compile` on all 101 files | ✅ Passed |
| Backend lint (real bugs) | `ruff check --select F,B,E9` | ✅ Clean¹ |
| Backend config loads | import `app.core.config` | ✅ Loads (mode=`live`, model=`gemini-2.5-flash`) |
| Backend data shapes load | import all 6 `app.schemas.*` | ✅ All import |
| New "Save Job" shape | validate real page payload | ✅ Passed |
| New status + search routes | compile + full lint + schema tests + route-order check | ✅ Passed |
| §36 fixes (backend) | `pytest tests/unit` — 12 tests | ✅ Passed |
| §36 fixes (frontend) | `vitest run` — 2 tests | ✅ Passed |
| §36 fixes (types/build) | `tsc --noEmit` + `vite build` after CV-export wiring | ✅ Passed |
| Safety fix (domains) | before/after comparison script | ✅ Proven fixed |
| Startup fix | annotation-resolves script | ✅ Proven fixed |

¹ The only remaining linter notices are 114 `B008` warnings. These are **not
bugs** — they are FastAPI's normal, recommended way of declaring endpoint inputs
(`= Depends(...)`, `= Query(...)`). They were intentionally left as-is.

---

## Remaining items & manual steps (honest notes)

**1. The full backend was not booted end-to-end in this environment.**
Running the live server needs Python 3.11+ (this sandbox had 3.10) and heavy AI
libraries (LangGraph, FAISS, sentence-transformers, Playwright, WeasyPrint).
Those were not installable here, so verification used compilation, linting,
targeted logic review, and focused import/validation tests instead. **Next step
on your own machine:** `make docker-up` (or `cd backend && uv sync` then
`uvicorn app.main:app --reload`) and open http://localhost/api/docs to click
through the endpoints.

**2. (Resolved) The two previously-missing job routes are now implemented** —
see *Fix 8*. `jobApi.search(...)` → `GET /job-search/search` and
`jobApi.updateStatus(...)` → `PATCH /job-search/{id}/status` are live and match
the frontend. The only setup step is applying the one database migration that
adds the new `status` column (see the setup note under Fix 8).

---

## API keys, environment & AI notes

- **Gemini key handling is correct and safe.** The key is read **only** from an
  environment variable (`GEMINI_API_KEY`); there are **no hardcoded keys** anywhere
  in the source. If the key is blank, the whole platform automatically runs in
  free offline **"mock" mode**.
- **A real Gemini key is present** in `backend/.env` on this machine, so the app
  will run in **live** mode. That file is correctly listed in `.gitignore`, so it
  won't be committed — keep it private and don't share it. (Its value was never
  printed during this audit.)
- **Model names are valid:** `gemini-2.5-flash` (routine tasks) and
  `gemini-2.5-pro` (complex generation), with `text-embedding-004` for retrieval.
- **Multi-agent workflows:** the two repaired agents (job extractor, auto-apply)
  now correctly flow through the shared guardrail → generate → cost-tracking
  pattern used by the other agent teams.
- **Cost optimization:** the duplicate embedding call (Fix 6) was removed, and
  the repaired live-mode AI calls now record token usage via `CostMonitor` like
  every other call, so per-feature cost tracking is consistent.
- **PDF / CV export** and the **badge** system were reviewed and found correct;
  the CV "download" button was simply pointed at the real export route (Fix 3).
