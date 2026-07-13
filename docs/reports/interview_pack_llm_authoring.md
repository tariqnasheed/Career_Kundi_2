# Interview Pack: LLM-Authored Content Redesign

**Date:** 2026-07-13
**Area:** `backend/app/agents/job_search` (Interview Pack Generation, §4.2)
**Status:** Implemented, tested (mock suite green; live path validated with a stubbed provider)

---

## 1. Problem

Every question in a generated interview pack showed the **same** "Common Mistakes"
and **near-identical** model answers. For a *Software Engineer* pack, every
question — regardless of topic — displayed:

> - Deploying without a rollback plan
> - Using overly broad IAM permissions
> - Ignoring failed health checks after release

and every model answer opened with *"For a Software Engineer, JavaScript means
building and operating cloud services in a way that is secure, observable,
repeatable, and recoverable."*

This made the pack read as generic boilerplate and defeated the purpose of paying
for live Gemini generation.

## 2. Root cause

The answers were **not** authored per-question by the LLM. Even in **live** mode
(`settings.llm_mode == "live"`), the pipeline ran the returned questions through a
deterministic content engine that overwrote the LLM's prose with content pulled
from a **role-FAMILY-keyed evidence pack**. Because the pack is selected by role
family only (not by the individual question), every question in a role collapsed
to the same text.

The chain:

| Step | Location | Effect |
|------|----------|--------|
| Role → family | `knowledge/evidence_packs/__init__.py:48` `resolve_role_family` | "Software Engineer" → `technology` → one `TECHNOLOGY_PACK` for the whole pack |
| Mistakes from family pack | `knowledge/evidence_slot_builder.py:502` | `family_pack["common_mistakes"]` taken first → identical 3-item list everywhere |
| Fixed mistake list | `knowledge/evidence_packs/technology.py:28` | The exact three strings above |
| Always template #0 | `knowledge/evidence_packs/__init__.py:214` `select_role_family_opening` | Every answer opens with the same family sentence |
| Overwrite of LLM output | `mock_data.py` `_finalize_question` (`build_model_answer`, `common_mistakes = study.get(...)`) | LLM prose replaced by template regardless of mode |

## 3. Redesign principle

**Gemini is the author; the deterministic engine is a validator + fallback,
never a silent rewriter.**

- Evidence packs move from **outputs** (text shipped to users) to **inputs**
  (domain vocabulary + a validation rubric fed into the prompt).
- The template engine authors content **only** when the LLM produced nothing
  usable, or when running offline (mock) — and it says so via provenance.
- Quality problems (thin/generic/duplicate) trigger **regeneration** by the LLM
  through the existing Reflector revision loop, not template substitution.

## 4. Changes

### 4.1 Provenance field (visibility)
`app/schemas/job_search.py` — added `content_source` to `InterviewQuestion`:
`"gemini"` | `"gemini_partial"` | `"deterministic_fallback"` | `"deterministic_mock"`.
Lets anyone confirm whether a pack was genuinely LLM-authored or fell back.

### 4.2 Inversion #2 — stop overwriting LLM output (`mock_data.py::_finalize_question`)
At the top of the function we capture the model's original `model_answer`,
`common_mistakes`, and `evaluation_criteria` and compute preserve-flags:

```python
_llm_authoring = settings.llm_mode == "live"
_preserve_answer   = _llm_authoring and bool(orig_answer) and not is_generic_content(orig_answer)
_preserve_mistakes = _llm_authoring and bool(orig_mistakes)
_preserve_eval     = _llm_authoring and bool(orig_evaluation)
```

Every deterministic authoring/substitution step is then guarded by
`not _preserve_*`:
- compiler-only regeneration neutralised for preserved answers,
- `polish_spoken_answer` skipped,
- `build_model_answer` "generic upgrade", role-anchor rewrite, and
  low-domain-density rebuild skipped,
- `common_mistakes` / `evaluation_criteria` kept from the LLM instead of the
  family study material, and re-asserted after study-module synthesis.

**Key property:** in **mock** mode `_llm_authoring` is `False`, so every guard is a
no-op and behaviour (plus the entire mock test suite) is unchanged. Live-mode
questions the LLM never authored (coverage-plan fillers) have empty content, so
they are still authored deterministically and tagged `deterministic_fallback`.

### 4.3 Inversion #1 — evidence pack as prompt grounding (`agents.py`)
New `_evidence_grounding_block(job)` builds a `DOMAIN GROUNDING` section from the
role-family pack's `domain_terms` + `verification_checks` and appends it to the
interview user-prompt. The `_INTERVIEW_ROLE` system prompt now explicitly requires
**question-specific** `common_mistakes` and forbids reusing one role-level list.
The pack is used as vocabulary/checklist, not copied verbatim. Returns `""` for the
generic `default` family so we never over-constrain uncurated roles.

### 4.4 Inversions #3 + #4 — cross-question uniqueness gate (`agents.py::InterviewPackReflectorAgent`)
`domain_checks` already flagged generic model answers. Added
`_cross_question_issues`, which flags:
- **near-duplicate model answers** (Jaccard word-overlap ≥ 0.85), and
- **reused `common_mistakes` lists** (identical normalised tuple across questions).

These issues feed back through the existing revision loop (`reflection_issues` →
executor re-prompts Gemini). **Live-only:** the gate is skipped in mock mode, where
duplicates are expected and the mock generator cannot regenerate — flagging there
would only spin the revision loop.

### 4.5 Incidental fix
`graph.py:23` had a merge-mangled line (`import uuidfrom typing import Any`) that
was a hard `SyntaxError` blocking import of the whole job-search API. Split into two
lines.

## 5. New logical flow

```
PLAN → GROUND (RAG + evidence pack INTO the prompt) → GENERATE (one structured
Gemini call for the whole pack) → VALIDATE (per-question generic + cross-question
duplicate predicates, no rewriting) → REPAIR (failing questions only, re-prompted
via reflection_issues) → PERSIST (content_source per question)
                                   └─ FALLBACK (labeled): live call empty after
                                      retries, or mock mode → deterministic engine
```

## 6. Behaviour matrix

| Mode | Question has LLM content? | Result | `content_source` |
|------|---------------------------|--------|------------------|
| live | yes, non-generic | LLM prose + mistakes preserved | `gemini` / `gemini_partial` |
| live | no (coverage filler) | authored by template engine | `deterministic_fallback` |
| mock | n/a | authored by template engine (unchanged) | `deterministic_mock` |

## 7. Testing

New: `app/agents/job_search/tests/test_llm_authored_preservation.py` (6 tests)
- live mode preserves distinct answers + mistakes; family template does **not** win;
- live filler questions still authored (`deterministic_fallback`);
- mock mode unchanged (`deterministic_mock`);
- Reflector flags identical mistakes + near-duplicate answers in live;
- Reflector silent on duplicates in mock;
- Reflector does **not** false-flag genuinely distinct questions.

Regression: full `app/agents/job_search/tests/` suite (runs in live mode in this
environment). Results recorded below.

**Results (2026-07-13, live mode — real `GEMINI_API_KEY` present):**

- New `test_llm_authored_preservation.py`: **6/6 passed.**
- Standalone end-to-end check through `finalize_questions_list`: two distinct
  Gemini answers preserved (`content_source=gemini`), the family template mistake
  ("Deploying without a rollback plan") did **not** leak, and the two questions
  produced **different** `common_mistakes`.
- Curated regression batch (10 directly-affected files incl. final-regression,
  study-material finalization, surface stability, export readiness, answer-length,
  study-material quality): **105 passed, 1 failed** in 5m12s.
- The single failure — `test_interview_pack_surface_stability.py::test_hr_questions_contain_role_keywords`
  (`Data Analyst HR missing keyword: kpi`) — is **pre-existing and unrelated**.
  It exercises `_hr_motivation_question` in `knowledge/coverage_planner.py`, a file
  this change never touches, on a path that involves no LLM content, no
  `_finalize_question`, no reflector, and no schema. **Verified**: reverting all
  three behavioral files (`schemas/job_search.py`, `mock_data.py`, `agents.py`) to
  baseline reproduces the identical failure, so it exists independently of this work.
  (The `kpi` keyword simply isn't in the deterministic HR-motivation question the
  planner generates for a Data Analyst.)

## 8. How to verify against real Gemini

1. Ensure `GEMINI_API_KEY` is set (it is → `settings.llm_mode == "live"`).
2. Regenerate a pack for a role and inspect the questions:
   - `content_source` should be `gemini` for most questions;
   - `common_mistakes` should differ across questions;
   - no two `model_answer`s should be near-duplicates.
3. If you see `deterministic_fallback` everywhere, the live call is failing — check
   logs for `interview_pack_llm_failed` and the API key/quota.

## 8b. Live-environment verification (2026-07-13) — why the UI still showed templates

After the code change, the UI still showed identical template answers. Live diagnosis
against the running Docker backend found the real blocker was NOT the code — the live
Gemini call was failing and silently falling back to the deterministic engine
(`content_source=deterministic_fallback`, which the new provenance field correctly
reported). A cascade of config issues, fixed in order:

1. **API key blocked** — original key 401'd with `API_KEY_SERVICE_BLOCKED` (Generative
   Language API not enabled/allowed on its project). Replaced with a working key.
2. **Model IDs 404** — `gemini-2.5-flash` / `gemini-2.5-pro` return "no longer available
   to new users" for new keys. Switched to `gemini-flash-latest` / `gemini-pro-latest`
   in `.env` and [config.py](../../backend/app/core/config.py). (`gemini-flash-latest`
   resolves to `gemini-3.5-flash`.)
3. **Embedding model 404** — `text-embedding-004` is gone; available models are
   `gemini-embedding-001` / `gemini-embedding-2`. NOT changed yet: swapping it may not
   match the existing FAISS store's vector dimensions. RAG retrieval failing is
   non-fatal (the evidence-pack grounding block still feeds the prompt).
4. **Container env reload** — `docker compose restart` keeps the old baked env; env
   changes need `docker compose up -d --force-recreate`. That recreate hit a pre-existing
   DB migration crash-loop (`NONEMPTY_UNOWNED`), worked around non-destructively via
   [docker-compose.nomigrate.yml](../../docker-compose.nomigrate.yml). See
   [[careerkundi-backend-ops]].
5. **Free-tier quota** — after the above, the structured call reaches the model and fails
   ONLY with `429 RESOURCE_EXHAUSTED` (free-tier limit 20 req/day for gemini-3.5-flash),
   exhausted by diagnostic test runs. Auth + model + code are confirmed working up to the
   quota wall. **Requires billing enabled (or a quota reset) to produce live packs.**
   Note each pack generation costs ~1 + up to 2 reflector-revision calls, so the 20/day
   free tier is impractical for real use.

## 8c. Local Ollama provider (free, no-quota testing) — 2026-07-13

To test the live-authoring flow without Gemini quota, added a local Ollama backend:

- **`OllamaProvider`** in [tools/llm.py](../../backend/app/tools/llm.py) — talks to a local
  Ollama server over `/api/chat` via httpx (no new dependency). Structured output uses
  Ollama's `format` field. `_hoist_defs_to_root()` moves Pydantic's nested `$defs` to the
  schema root (Ollama 400s otherwise: "$defs not in {root}").
- **Provider selection** in [config.py](../../backend/app/core/config.py): `LLM_PROVIDER`
  (`auto` | `gemini` | `ollama` | `mock`), `OLLAMA_BASE_URL`, `OLLAMA_MODEL`. `llm_mode`
  is now derived from `resolved_llm_provider`, so Ollama counts as a "live" path and the
  preservation logic applies to it too.
- **Required content fields**: `_InterviewPackQuestionList.json_schema()` now marks
  `question`/`why_asked`/`model_answer`/`common_mistakes` **required** (+ `minItems:2` on
  mistakes). Pydantic left them optional, so a small model emitted minimal JSON with empty
  answers → fell back to templates. Requiring them makes both Gemini and Ollama fill them.
- **Run setup**: Ollama runs **natively on the host** (Metal GPU; Docker on macOS can't use
  the GPU) bound to `0.0.0.0:11434`; the container reaches it via `host.docker.internal`
  (`extra_hosts` in [docker-compose.nomigrate.yml](../../docker-compose.nomigrate.yml)).
  Root `.env` sets `LLM_PROVIDER=ollama`. Switch back to Gemini with `LLM_PROVIDER=auto`.

**Verified end-to-end (container → host Ollama, llama3.1:8b):** a Cybersecurity Analyst pack
produced 20 questions — 11 `content_source=gemini` (LLM-authored, preserved) + 9
`deterministic_fallback` (coverage fillers), 0 LLM failures. LLM-authored questions had
distinct answers AND question-specific `common_mistakes` (e.g. SIEM-config vs incident-response
vs vulnerability-management mistakes) — the original identical-template symptom is gone.
Note: `content_source` still reads "gemini" for any live provider (it means "LLM-authored");
it is internal provenance, not shown in the UI.

## 9. Follow-ups (not in this change)

- Deep-preserve nested `study_material` sub-fields (definitions, worked examples)
  the same way, not just top-level `common_mistakes`/`model_answer`.
- Consider a similarity threshold config knob for the cross-question gate.
- Optionally surface `content_source` in the UI so users/QA can see provenance.
