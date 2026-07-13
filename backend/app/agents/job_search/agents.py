"""
agents/job_search/agents.py
================================
Concrete Guardrail / Planner / Executor / CrossVerifier / Reflector agents
for the two pipelines in this feature package (§4.1 Job Search & Discovery,
§4.2 Interview Pack Generation).

Both Executors follow the same live/mock split used throughout the
platform: in live mode they call `get_llm()` with a JSON schema derived
from the Pydantic response models in `app/schemas/job_search.py`; in mock
mode they call the content-aware builders in `mock_data.py`. Either way,
RAG retrieval, GraphRAG graph growth, citation construction, cross-source
verification, and Reflector quality checks are ALL real code paths — only
the LLM/search API calls themselves are swapped.
"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.documents import Document

from app.agents.common.base import BaseAgent
from app.agents.common.cost_monitor import CostMonitor
from app.agents.common.guardrail import BaseGuardrailAgent
from app.agents.common.prompts import build_system_prompt
from app.agents.common.reflector import BaseReflectorAgent
from app.agents.job_search.knowledge.evidence_packs import get_evidence_pack, resolve_role_family
from app.core.config import settings
from app.schemas.job_search import InterviewQuestion, JobEnrichmentResult
from app.tools.graph_rag import ensure_role_node
from app.tools.llm import PromptSpec, get_llm
from app.tools.rag import add_documents, citations_from_documents, format_context_for_prompt, retrieve
from app.tools.search import verify_claim

from . import mock_data

# --- Job enrichment pipeline ----------------------------------------------------------

_JOB_PARSER_ROLE = """
You are the Job Enrichment agent for Careerkundi, an AI career platform. You
are given the raw text of a job posting (already scraped or pasted by the
user). Extract structured fields EXACTLY as they appear in the posting:
title, company name, location, employment type, remote status, salary
range if stated, responsibilities, requirements, and benefits. Then,
using the numbered skill-taxonomy context provided, identify the specific
technical/soft skills this role requires and tag each with an importance
level based on how the posting itself emphasizes it (a skill in a
"requirements" section is more critical than one mentioned only in
passing).
""".strip()

_JOB_FIELDS_SCHEMA = JobEnrichmentResult.model_json_schema()


class JobSearchGuardrailAgent(BaseGuardrailAgent):
    """Vets the resolved job text (scraping/URL resolution already happened before the graph runs — see graph.py)."""

    name = "JobSearchGuardrailAgent"
    input_field = "raw_input"

    async def extra_checks(self, state: dict[str, Any], sanitized_input: Any) -> list[str]:
        if not isinstance(sanitized_input, str) or len(sanitized_input.strip()) < 50:
            return ["Job text is too short to extract meaningful structured fields (minimum 50 characters)."]
        return []


class JobPlannerAgent(BaseAgent):
    """Decides model tier and RAG retrieval breadth based on how much text there is to work with."""

    name = "JobPlannerAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        job_text = state["raw_input"]
        tier = self.cost_monitor.recommend_tier(input_length_chars=len(job_text))
        plan = {"tier": tier, "retrieval_k": 8, "retrieval_category": "skill_taxonomy"}
        return {"plan": plan, "job_text": job_text}


class JobEnricherExecutorAgent(BaseAgent):
    """Extracts structured job fields, grounded in RAG skill-taxonomy context, and grows RAG/GraphRAG with the new posting."""

    name = "JobEnricherAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        job_text = state["job_text"]
        plan = state["plan"]
        revision_issues = state.get("reflection_issues") or []

        retrieved = retrieve(job_text, k=plan["retrieval_k"], category=plan["retrieval_category"])
        context = format_context_for_prompt(retrieved)
        citations = citations_from_documents(retrieved)
        tier = plan["tier"]

        if settings.llm_mode == "mock":
            parsed = mock_data.mock_parse_job(job_text)
            parsed["company_profile"] = mock_data.mock_company_profile(parsed.get("company_name"))
        else:
            llm = get_llm(tier)
            user_prompt = f"Numbered skill-taxonomy context:\n{context}\n\nJob posting text:\n{job_text}"
            if revision_issues:
                user_prompt += "\n\nThe previous extraction had these issues — fix them:\n" + "\n".join(
                    f"- {issue}" for issue in revision_issues
                )
            spec = PromptSpec(
                system_prompt=build_system_prompt(_JOB_PARSER_ROLE),
                user_prompt=user_prompt,
                json_schema=_JOB_FIELDS_SCHEMA,
                temperature=0.2,
            )
            response = await llm.generate(spec)
            self.cost_monitor.record(response, tier=tier)
            parsed = response.parsed_json or {}

        # Grow the knowledge graph with this (possibly novel) role + its skills,
        # and ingest the posting text into the RAG store (deduplicated) so future
        # retrievals benefit from real, accumulated job-market content — this is
        # the "continuously ingest" behavior promised in tools/rag.py and
        # tools/graph_rag.py, exercised on every successful enrichment.
        skill_names = [s["skill"] if isinstance(s, dict) else s for s in parsed.get("extracted_skills", [])]
        if parsed.get("title"):
            ensure_role_node(parsed["title"], skills=skill_names)
        add_documents(
            [
                Document(
                    page_content=job_text,
                    metadata={
                        "doc_id": f"job-{hash(job_text) & 0xFFFFFFFF:x}",
                        "category": "job_posting",
                        "source": parsed.get("company_name") or "user-submitted posting",
                        "title": parsed.get("title", "Untitled posting"),
                    },
                )
            ]
        )

        return {
            "draft_output": parsed,
            "citations": citations,
            "retrieved_context": context,
            "model_tier_used": tier,
        }


class CrossVerifierAgent(BaseAgent):
    """
    Independently re-checks the extracted company name against Google
    Search grounding (§4.1 "Cross-Source Verification"). In mock mode this
    always yields `verified=False` results (see tools/search.py) — exactly
    the honest behavior we want: the platform should never claim a job
    posting is "verified" without a real, independent source actually
    confirming it.
    """

    name = "CrossVerifierAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("draft_output") or {}
        company = draft.get("company_name")
        if not company:
            return {"verification_status": "unverified", "verification_sources": [], "search_grounded": False}

        is_grounded, results = await verify_claim(f"{company} company official site")
        sources = [
            {"url": r.url, "matched_fields": ["company_name"] if r.verified else [], "verified": r.verified}
            for r in results
        ]
        status = "verified" if is_grounded else ("partial" if sources else "unverified")
        return {"verification_status": status, "verification_sources": sources, "search_grounded": is_grounded}


class JobReflectorAgent(BaseReflectorAgent):
    """Quality gate for extracted job fields, beyond the generic citation/boilerplate checks."""

    name = "JobReflectorAgent"
    output_field = "draft_output"
    max_revisions = 2

    def render_for_review(self, draft: Any) -> str:
        if not isinstance(draft, dict):
            return super().render_for_review(draft)
        parts = [draft.get("title", ""), *draft.get("responsibilities", []), *draft.get("requirements", [])]
        return " ".join(str(p) for p in parts)

    async def domain_checks(self, state: dict[str, Any], draft: Any) -> list[str]:
        issues = []
        if not draft or not draft.get("title"):
            issues.append("Extraction is missing a job title.")
        if draft and not draft.get("responsibilities") and not draft.get("requirements"):
            issues.append("No responsibilities or requirements were extracted — the input text may be too thin.")
        return issues


# --- Interview pack pipeline ----------------------------------------------------------------

_INTERVIEW_ROLE = """
You are a patient PhD-level scholar and master teacher generating interview preparation
packs for Careerkundi. You have deep expertise across professions and explain concepts
with real definitions, established principles, advanced theory, and concrete examples.

Given a job's structured fields (title, responsibilities, requirements, extracted skills)
and numbered interview-methodology context, generate a COMPLETE interview preparation
pack for a candidate with ZERO prior knowledge.

TEACHING STANDARDS (mandatory):
- Write as the world's foremost expert IN THE ROOM — first person, direct, substantive.
- model_answer must be the ACTUAL spoken answer (300–800 words) — NOT coaching ("you should",
  "interviewers look for", "I'd start by asking what they know").
- study_material teaches SUBJECT MATTER ONLY — definitions, how things work, standards, facts,
  worked examples. NO "how to answer better" or interview technique sections.
- answer_explanation summarises key facts/concepts covered — NOT why the answer structure works.
- Never use placeholders like [specific problem] or generic "deliver reliable outcomes" text.

For EVERY question provide: comprehensive model_answer, rich study_material,
evaluation_criteria, common_mistakes, follow_up_questions, difficulty,
estimated_answer_time_minutes.

QUESTION-SPECIFICITY (mandatory — this is what makes the pack useful):
- common_mistakes must be SPECIFIC TO THIS QUESTION's topic and skill. Do NOT reuse the
  same generic role-level mistakes across questions. Two different questions must not share
  an identical common_mistakes list. If a question is about JavaScript closures, its mistakes
  are about closures — not "deploy without a rollback plan".
- model_answer must be distinct per question — never a boilerplate opener reused verbatim.
- If a DOMAIN GROUNDING block is supplied below, use it as VOCABULARY and a checklist to make
  answers concrete (reference the relevant terms/checks), NOT as text to copy. Only pull in the
  terms that actually apply to the specific question.

Include behavioral (STAR), technical (one question per extracted skill), system-design
if warranted, and role/company-specific closing questions. Generate as many questions
as the input genuinely supports.
""".strip()


class _InterviewPackQuestionList:
    """Tiny wrapper so we can hand `with_structured_output` a `{"questions": [...]}` shaped schema built from the single-question Pydantic model."""

    @staticmethod
    def json_schema() -> dict:
        item_schema = InterviewQuestion.model_json_schema()
        # Force the fields we actually consume to be REQUIRED in the structured
        # output. Pydantic marks model_answer/common_mistakes optional (they have
        # defaults), so a model — especially a smaller local one — will happily
        # emit minimal JSON that leaves them empty, which then falls back to the
        # deterministic template engine (the very bug we're fixing). Requiring
        # them makes both Gemini and Ollama actually produce per-question content.
        required = list(item_schema.get("required") or [])
        for field in ("question", "why_asked", "model_answer", "common_mistakes"):
            if field not in required:
                required.append(field)
        item_schema["required"] = required
        # Nudge the model to produce a real, non-trivial mistakes list.
        props = item_schema.get("properties") or {}
        if isinstance(props.get("common_mistakes"), dict):
            props["common_mistakes"]["minItems"] = 2
        return {
            "title": "InterviewPackQuestions",
            "type": "object",
            "properties": {"questions": {"type": "array", "items": item_schema}},
            "required": ["questions"],
        }


class InterviewPackGuardrailAgent(BaseGuardrailAgent):
    name = "InterviewPackGuardrailAgent"
    input_field = "raw_input"

    async def extra_checks(self, state: dict[str, Any], sanitized_input: Any) -> list[str]:
        job_snapshot = state.get("job_snapshot") or {}
        if not job_snapshot.get("title"):
            return ["No job title found on the saved job — cannot generate a tailored interview pack."]
        return []


class InterviewPackPlannerAgent(BaseAgent):
    name = "InterviewPackPlannerAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        job_snapshot = state["job_snapshot"]
        description_len = len(job_snapshot.get("description_raw") or "") or 500
        tier = self.cost_monitor.recommend_tier(input_length_chars=description_len, force_pro=bool(state.get("focus_areas")))
        plan = {"tier": tier, "retrieval_k": 5, "retrieval_category": "interview_pattern"}
        return {"plan": plan}


def _evidence_grounding_block(job: dict[str, Any]) -> str:
    """
    Build a DOMAIN GROUNDING block for the interview prompt from the role-family
    evidence pack.

    This is inversion #1 of the "Gemini authors, templates ground & validate"
    redesign: the evidence pack's vocabulary and checks are handed to the model
    as *grounding hints* (terms to reference, checks to consider) instead of
    being concatenated into the output afterwards. The model still writes its
    own question-specific prose — it is just anchored in real domain vocabulary,
    which preserves the zero-hallucination grounding without producing identical
    template text across questions. Returns "" for the generic default pack so
    we never over-constrain roles we have no curated vocabulary for.
    """
    role_family = resolve_role_family(job.get("title") or "", job.get("role_family"))
    if role_family == "default":
        return ""
    pack = get_evidence_pack(role_family)
    terms = [str(t) for t in (pack.get("domain_terms") or []) if str(t).strip()]
    checks = [str(c) for c in (pack.get("verification_checks") or []) if str(c).strip()]
    if not terms and not checks:
        return ""
    lines = ["\n\nDOMAIN GROUNDING (vocabulary + checklist — reference where relevant, do NOT copy verbatim):"]
    if terms:
        lines.append(f"- Domain terms: {', '.join(terms)}")
    if checks:
        lines.append(f"- Verification checks a strong answer may reference: {'; '.join(checks)}")
    lines.append(
        "- Use ONLY the items relevant to each specific question. Different questions should "
        "reference different subsets, and each question's common_mistakes must be about THAT "
        "question's topic — not a shared role-level list."
    )
    return "\n".join(lines)


class InterviewPackExecutorAgent(BaseAgent):
    name = "InterviewPackAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        job = state["job_snapshot"]
        plan = state["plan"]
        revision_issues = state.get("reflection_issues") or []

        retrieved = retrieve(
            f"{job.get('title', '')} interview questions", k=plan["retrieval_k"], category=plan["retrieval_category"]
        )
        context = format_context_for_prompt(retrieved)
        citations = citations_from_documents(retrieved)
        tier = plan["tier"]

        if settings.llm_mode == "mock":
            questions = mock_data.mock_generate_questions(
                job, focus_areas=state.get("focus_areas", []), difficulty=state.get("difficulty", "auto")
            )
            # Attach the genuine, real-sourced interview-methodology citations to
            # every behavioral/system-design question — these citations are NOT
            # fabricated even though the LLM call is mocked: they come straight
            # out of the real RAG retrieval call two lines above.
            for q in questions:
                if q["category"] in ("behavioral", "system_design"):
                    q["citations"] = citations
        else:
            llm = get_llm(tier)
            grounding = _evidence_grounding_block(job)
            user_prompt = (
                f"Numbered interview-methodology context:\n{context}\n\n"
                f"Job fields:\n{job}\n\nFocus areas requested: {state.get('focus_areas') or 'none specified'}\n"
                f"Difficulty: {state.get('difficulty', 'auto')}\n"
                f"Include study material for zero-prior-knowledge candidates: {state.get('include_study_material', True)}"
                f"{grounding}"
            )
            if revision_issues:
                user_prompt += "\n\nThe previous pack had these issues — fix them:\n" + "\n".join(
                    f"- {issue}" for issue in revision_issues
                )
            spec = PromptSpec(
                system_prompt=build_system_prompt(_INTERVIEW_ROLE),
                user_prompt=user_prompt,
                json_schema=_InterviewPackQuestionList.json_schema(),
                temperature=0.5,
                max_output_tokens=8192,  # interview packs can be long — no artificial truncation
            )
            try:
                response = await llm.generate(spec)
                self.cost_monitor.record(response, tier=tier)
                questions = (response.parsed_json or {}).get("questions", [])
            except Exception as exc:  # noqa: BLE001 — fall back to deterministic mock pack
                self.logger.warning("interview_pack_llm_failed", error=str(exc))
                questions = []
            if not questions:
                questions = mock_data.mock_generate_questions(
                    job, focus_areas=state.get("focus_areas", []), difficulty=state.get("difficulty", "auto")
                )
            else:
                questions = mock_data.finalize_questions_list(
                    questions, job, state.get("difficulty", "auto")
                )

        return {
            "draft_output": {"questions": questions},
            "citations": citations,
            "retrieved_context": context,
            "model_tier_used": tier,
        }


class InterviewPackReflectorAgent(BaseReflectorAgent):
    name = "InterviewPackReflectorAgent"
    output_field = "draft_output"
    max_revisions = 2

    def render_for_review(self, draft: Any) -> str:
        if not isinstance(draft, dict):
            return super().render_for_review(draft)
        questions = draft.get("questions", [])
        return " ".join(f"{q.get('question', '')} {q.get('why_asked', '')}" for q in questions)

    async def domain_checks(self, state: dict[str, Any], draft: Any) -> list[str]:
        issues = []
        questions = (draft or {}).get("questions", [])
        if not questions:
            issues.append("No interview questions were generated.")

        seen: set[str] = set()
        for q in questions:
            text = (q.get("question") or "").strip().lower()
            if not text:
                issues.append("A generated question has empty text.")
                continue
            if text in seen:
                issues.append(f"Duplicate/near-duplicate question detected: '{q.get('question')[:80]}'")
            seen.add(text)
            if not q.get("why_asked"):
                issues.append(f"Question missing 'why_asked' rationale: '{q.get('question', '')[:80]}'")
            if not (q.get("model_answer") or "").strip():
                issues.append(f"Question missing comprehensive model_answer: '{q.get('question', '')[:80]}'")
            study = q.get("study_material") or {}
            if not (study.get("overview") or "").strip():
                issues.append(f"Question missing study_material overview: '{q.get('question', '')[:80]}'")
            if q.get("category") == "technical" and not study.get("definitions"):
                issues.append(f"Technical question missing study_material definitions: '{q.get('question', '')[:80]}'")
            from app.agents.job_search.knowledge.content_engine import is_generic_content

            model = (q.get("model_answer") or "").strip()
            if model and is_generic_content(model):
                issues.append(f"Model answer appears generic/template — needs real definitions and examples: '{q.get('question', '')[:60]}'")
            overview = (study.get("overview") or "").strip()
            if overview and is_generic_content(overview):
                issues.append(f"Study material appears generic — needs PhD-level teaching content: '{q.get('question', '')[:60]}'")

        # Cross-question uniqueness (inversion #4). The deterministic template
        # engine produced identical common_mistakes and near-identical model
        # answers across a whole role; flag repeats so the executor regenerates
        # the offenders (fed back via reflection_issues) instead of shipping
        # duplicates. LIVE-ONLY: in mock mode duplicates are expected (templates
        # are deterministic) and the mock generator cannot regenerate them, so
        # flagging there would only spin the revision loop for no benefit.
        if settings.llm_mode == "live":
            issues.extend(self._cross_question_issues(questions))

        return issues

    @staticmethod
    def _cross_question_issues(questions: list[dict[str, Any]]) -> list[str]:
        """Detect near-duplicate model answers and reused common_mistakes lists across questions."""

        def _norm(text: str) -> str:
            return re.sub(r"\s+", " ", (text or "").strip().lower())

        def _tokens(text: str) -> set[str]:
            return set(re.findall(r"[a-z0-9]+", (text or "").lower()))

        def _jaccard(a: str, b: str) -> float:
            ta, tb = _tokens(a), _tokens(b)
            if not ta or not tb:
                return 0.0
            return len(ta & tb) / len(ta | tb)

        issues: list[str] = []

        # Near-duplicate model answers (O(n^2), fine for a single pack's size).
        answered = [q for q in questions if (q.get("model_answer") or "").strip()]
        for i in range(len(answered)):
            for j in range(i + 1, len(answered)):
                sim = _jaccard(answered[i].get("model_answer", ""), answered[j].get("model_answer", ""))
                if sim >= 0.85:
                    issues.append(
                        f"Two model answers are near-duplicates ({int(sim * 100)}% word overlap) — "
                        f"make each answer specific to its own question: "
                        f"'{(answered[i].get('question') or '')[:50]}' vs '{(answered[j].get('question') or '')[:50]}'"
                    )
                    break  # one report per outer question keeps the feedback actionable

        # Reused common_mistakes lists (the exact symptom that started this work).
        mistakes_seen: dict[tuple[str, ...], str] = {}
        for q in questions:
            mistakes = tuple(_norm(m) for m in (q.get("common_mistakes") or []) if _norm(m))
            if not mistakes:
                continue
            if mistakes in mistakes_seen:
                issues.append(
                    f"Identical common_mistakes reused across questions "
                    f"('{(q.get('question') or '')[:50]}' repeats those of "
                    f"'{mistakes_seen[mistakes][:50]}') — write mistakes specific to each question's topic."
                )
            else:
                mistakes_seen[mistakes] = q.get("question") or ""

        return issues
