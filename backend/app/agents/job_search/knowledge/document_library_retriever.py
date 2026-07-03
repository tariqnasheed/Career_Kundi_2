"""Deterministic retrieval of saved role-pack study material from documents/interview_packs/."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.agents.job_search.knowledge.normalize import title_case_skill
from app.agents.job_search.quality.blocked_phrase_guard import (
    GENERIC_SNIPPET_PHRASES,
    INTERMEDIATE_QUALITY_CHECKS,
    STRUCTURED_VERIFICATION,
)
from app.agents.job_search.quality.surface_text_normalize import normalize_surface_text, truncate_at_word
from app.core.config import settings
from app.services.role_pack_library import find_role_pack, normalize_role_slug

StudySourceStatus = Literal["used", "available_not_used", "not_configured", "failed"]

_GENERIC_SKILLS = frozenset({"technical", "general", "n/a", "behavioral", "hr", "daily routine", "motivation"})

# Vocabulary/meta skills — may appear secondary but must not alone justify `used`.
_GENERIC_VOCABULARY_SKILLS = frozenset({"core terminology", "domain vocabulary", "operating principles"})

_HR_LIKE_CATEGORIES = frozenset({"hr", "behavioral", "role_specific"})
_TECHNICAL_CATEGORIES = frozenset({
    "technical",
    "scenario",
    "practical",
    "case",
    "case_study",
    "tool",
    "tools",
    "standards",
    "calculation",
    "domain_vocabulary",
    "system_design",
})

_STOPWORDS = frozenset(
    {
        "about", "after", "also", "and", "are", "been", "being", "both", "describe",
        "explain", "from", "have", "how", "into", "more", "most", "other", "role",
        "that", "their", "them", "then", "there", "these", "this", "through", "what",
        "when", "where", "which", "while", "with", "would", "your", "tell", "give",
        "want", "why", "you", "the", "for", "this", "does", "work", "day", "one",
    }
)

_ROLE_SPECIFIC_PLACEHOLDER_RE = re.compile(r"\brole specific\b", re.I)

_CORE_TERMINOLOGY_SNIPPET_RE = re.compile(
    r"core terminology for (?:core terminology|[\w /-]+)\s*[-—].*(?:precise definitions required|interviews)",
    re.I,
)

_SKILL_FOCUS_HINTS: dict[str, tuple[str, ...]] = {
    "aws": ("deployment reliability", "infrastructure automation", "monitoring signals", "rollback planning"),
    "ci/cd": ("pipeline automation", "release gating", "deployment reliability", "rollback planning"),
    "docker": ("container packaging", "image security scanning", "runtime isolation", "registry hygiene"),
    "kubernetes": ("orchestration controls", "health checks", "rolling updates", "cluster observability"),
    "monitoring": ("alert coverage", "SLO tracking", "incident signals", "post-release verification"),
    "cable sizing": ("load assumptions", "protective-device coordination", "voltage-drop checks", "compliance verification"),
    "electrical installation": ("installation safety", "testing procedures", "standards compliance", "commissioning checks"),
    "load calculations": ("demand assumptions", "diversity factors", "protective-device coordination", "design verification"),
    "commissioning": ("test evidence", "handover documentation", "safety verification", "sign-off controls"),
    "pharmacology": ("dose rationale", "interaction review", "contraindication checks", "clinical escalation"),
    "medication review": ("medicine optimisation", "interaction review", "documentation", "patient safety"),
    "patient counselling": ("shared decision-making", "adherence planning", "risk communication", "documentation"),
    "clinical governance": ("governance controls", "escalation pathways", "audit evidence", "risk management"),
    "coffee preparation": ("espresso consistency", "grind and dose control", "extraction timing", "quality checks"),
    "haccp": ("hygiene controls", "allergen handling", "temperature monitoring", "contamination prevention"),
    "customer service": ("queue management", "order accuracy", "complaint handling", "rush-period workflow"),
    "stock control": ("stock rotation", "wastage control", "ordering discipline", "hygiene during handling"),
}

_MIN_SNIPPET_CHARS = 80
_MAX_SNIPPETS = 2
_MAX_SNIPPET_CHARS = 220


@dataclass
class DocumentLibraryRetrievalResult:
    status: StudySourceStatus
    relevance_score: float = 0.0
    document_path: str | None = None
    source_label: str = "Document library"
    matched_skills: list[str] = field(default_factory=list)
    supporting_focus: list[str] = field(default_factory=list)
    snippets: list[str] = field(default_factory=list)
    note: str = ""
    matched_question_id: str | None = None
    pack_exists: bool = False

    @property
    def matched(self) -> bool:
        return self.status == "used"


@dataclass
class _MatchEvidence:
    strong_skill_tag_match: bool = False
    skill_overlap_count: int = 0
    question_token_overlap: int = 0
    material_token_overlap: int = 0
    matched_skills: list[str] = field(default_factory=list)
    score: float = 0.0


def _documents_root() -> Path:
    return Path(settings.resolved_documents_root)


def _relative_library_path(path: str | Path) -> str:
    root = _documents_root()
    p = Path(path)
    try:
        rel = p.relative_to(root.parent)
    except ValueError:
        rel = p
    return str(rel).replace("\\", "/")


def _tokenize(text: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-z0-9][a-z0-9_/-]{2,}", (text or "").lower())
        if tok not in _STOPWORDS and not tok.isdigit()
    }


def _normalize_skill(skill: str) -> str:
    return re.sub(r"\s+", " ", (skill or "").strip().lower())


def _is_meaningful_skill(skill: str) -> bool:
    normalized = _normalize_skill(skill)
    return bool(normalized) and normalized not in _GENERIC_SKILLS and len(normalized) > 2


def _substantive_matched_skills(matched_skills: list[str]) -> list[str]:
    """Matched skills excluding generic vocabulary/meta labels like Core Terminology."""
    return [
        s
        for s in matched_skills
        if _normalize_skill(s) not in _GENERIC_VOCABULARY_SKILLS
    ]


def _is_core_terminology_only_match(matched_skills: list[str]) -> bool:
    return bool(matched_skills) and not _substantive_matched_skills(matched_skills)


def _is_core_terminology_snippet(text: str) -> bool:
    lowered = (text or "").lower().strip()
    if not lowered:
        return True
    if _CORE_TERMINOLOGY_SNIPPET_RE.search(lowered):
        return True
    if lowered.startswith("core terminology for ") and "interviews" in lowered:
        return True
    if lowered.startswith("operating principles for ") and "how work is executed to standard" in lowered:
        return True
    if re.fullmatch(r"core terminology for [a-z0-9 /_-]+", lowered):
        return True
    return False


def _format_matched_skill_label(skill: str) -> str:
    return title_case_skill((skill or "").strip())


def _is_role_specific_placeholder_snippet(text: str) -> bool:
    lowered = (text or "").lower().strip()
    if not lowered:
        return True
    if _ROLE_SPECIFIC_PLACEHOLDER_RE.search(lowered):
        return True
    return False


def _snippet_mentions_substantive_skill(snippet: str, matched_skills: list[str]) -> bool:
    """Snippet must reference at least one substantive matched skill or known technical term."""
    lowered = (snippet or "").lower()
    substantive = _substantive_matched_skills(matched_skills)
    if not substantive:
        return False
    for skill in substantive:
        normalized = _normalize_skill(skill)
        display = title_case_skill(skill).lower()
        if display in lowered or normalized in lowered:
            return True
        for token in re.split(r"[\s/]+", normalized):
            if len(token) >= 4 and token in lowered:
                return True
    return False


def _query_skills(question: dict[str, Any]) -> set[str]:
    skills: set[str] = set()
    if question.get("skill_tag"):
        skills.add(_normalize_skill(str(question["skill_tag"])))
    for item in question.get("related_skills") or []:
        skills.add(_normalize_skill(str(item)))
    return {s for s in skills if _is_meaningful_skill(s)}


def _saved_question_skills(saved: dict[str, Any]) -> set[str]:
    """Skills declared on a saved pack question only — never inflate with job-level skills."""
    skills: set[str] = set()
    if saved.get("skill_tag"):
        skills.add(_normalize_skill(str(saved["skill_tag"])))
    for item in saved.get("related_skills") or []:
        skills.add(_normalize_skill(str(item)))
    return {s for s in skills if _is_meaningful_skill(s)}


def _study_material_text(study: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "overview",
        "beginner_explanation",
        "what_this_question_tests",
        "worked_example",
        "practical_example",
    ):
        value = study.get(key)
        if isinstance(value, str):
            parts.append(value)
    for key in ("step_by_step_breakdown", "common_mistakes", "explanations", "skill_explanations"):
        value = study.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(str(item.get("explanation") or item.get("definition") or ""))
    return " ".join(parts)


def _is_generic_phrase(text: str, *, min_len: int | None = None) -> bool:
    lowered = (text or "").lower().strip()
    if not lowered:
        return True
    if min_len is not None and len(lowered) < min_len:
        return True
    if lowered in _GENERIC_SKILLS:
        return True
    for phrase in GENERIC_SNIPPET_PHRASES:
        if phrase in lowered:
            return True
    return False


def _is_generic_snippet(text: str) -> bool:
    lowered = (text or "").lower().strip()
    if not lowered:
        return True
    if len(lowered) < _MIN_SNIPPET_CHARS:
        return True
    if lowered in _GENERIC_SKILLS:
        return True
    if re.fullmatch(r"[a-z0-9][a-z0-9 /_-]{0,40}", lowered) and " " not in lowered.strip():
        return True
    if re.fullmatch(r"[a-z][a-z /_-]{0,30}", lowered) and len(lowered.split()) <= 2:
        if not any(ch.isdigit() for ch in lowered):
            return True
    if _is_core_terminology_snippet(lowered):
        return True
    if _is_role_specific_placeholder_snippet(lowered):
        return True
    return _is_generic_phrase(lowered)


def _is_generic_snippet_for_match(text: str, matched_skills: list[str]) -> bool:
    if _is_generic_snippet(text):
        return True
    if matched_skills and not _snippet_mentions_substantive_skill(text, matched_skills):
        return True
    return False


def _normalize_snippet(text: str) -> str:
    return truncate_at_word(normalize_surface_text(text.strip()), _MAX_SNIPPET_CHARS)


def _extract_snippets(study: dict[str, Any], *, matched_skills: list[str] | None = None) -> list[str]:
    skills = matched_skills or []
    candidates: list[str] = []
    for key in (
        "step_by_step_breakdown",
        "common_mistakes",
        "practical_example",
        "worked_example",
        "overview",
        "beginner_explanation",
        "what_this_question_tests",
    ):
        value = study.get(key)
        if isinstance(value, str) and value.strip():
            parts = re.split(r"[\n\r]+", value.strip())
            for part in parts:
                cleaned = re.sub(r"^\s*[•\-\d]+[\.\)]\s*", "", part).strip()
                if cleaned:
                    candidates.append(cleaned)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    candidates.append(item.strip())

    snippets: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        snippet = _normalize_snippet(raw)
        key = snippet.lower()
        if _is_generic_snippet_for_match(snippet, skills) or key in seen:
            continue
        seen.add(key)
        snippets.append(snippet)
        if len(snippets) >= _MAX_SNIPPETS:
            break
    return snippets


def _snippet_quality_score(snippets: list[str]) -> int:
    if not snippets:
        return -1
    score = len(snippets)
    for snippet in snippets:
        lowered = snippet.lower()
        if "i applied" in lowered or "stabilize" in lowered:
            score += 10
        if "deployment" in lowered or "pipeline" in lowered:
            score += 4
        if "medication" in lowered or "prescribing" in lowered:
            score += 4
        if "espresso" in lowered or "allergen" in lowered:
            score += 4
        if "qps to db" in lowered or "quantitative problem" in lowered:
            score -= 6
        if _is_role_specific_placeholder_snippet(snippet):
            score -= 25
        if _is_core_terminology_snippet(snippet):
            score -= 20
        if INTERMEDIATE_QUALITY_CHECKS in lowered or STRUCTURED_VERIFICATION in lowered:
            score -= 12
    return score


def _resolve_snippet_source(
    matched: dict[str, Any],
    matched_skills: list[str],
    saved_questions: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Prefer a saved question with substantive overlap that yields quality snippets."""
    substantive = {_normalize_skill(s) for s in _substantive_matched_skills(matched_skills)}
    candidates: list[dict[str, Any]] = [matched]
    for saved in saved_questions:
        if saved is matched:
            continue
        if substantive & _saved_question_skills(saved):
            candidates.append(saved)

    best_saved = matched
    best_snippets: list[str] = []
    best_score = -1
    for saved in candidates:
        snippets = _extract_snippets(saved.get("study_material") or {}, matched_skills=matched_skills)
        quality = _snippet_quality_score(snippets)
        if quality > best_score:
            best_saved = saved
            best_snippets = snippets
            best_score = quality
    return best_saved, best_snippets


def _focus_phrase_from_step(step: str) -> str | None:
    text = normalize_surface_text(step.strip())
    if not text or _is_generic_phrase(text, min_len=_MIN_SNIPPET_CHARS):
        return None
    text = re.sub(r"^(clarify|apply|validate|record|review)\s+", "", text, flags=re.I)
    text = re.sub(r"\.$", "", text)
    if len(text) > 72:
        text = truncate_at_word(text, 72)
    if len(text) < 12 or _is_generic_phrase(text):
        return None
    return text.lower()


def _focus_hints_for_skill(skill: str) -> list[str]:
    normalized = _normalize_skill(skill)
    if normalized in _GENERIC_VOCABULARY_SKILLS:
        return []
    for key, hints in _SKILL_FOCUS_HINTS.items():
        if key in normalized or normalized in key:
            return list(hints)
    words = normalized.split()
    if len(words) >= 2:
        return [f"{words[0]} {words[1]} checks", f"{words[0]} verification", f"{normalized} workflow"]
    return [f"{normalized} checks", f"{normalized} verification", f"{normalized} workflow"]


def _build_supporting_focus(
    question: dict[str, Any],
    matched_skills: list[str],
    study: dict[str, Any],
    query_tokens: set[str],
) -> list[str]:
    phrases: list[str] = []
    seen: set[str] = set()

    def _add(phrase: str) -> None:
        cleaned = normalize_surface_text(phrase.strip().lower())
        if not cleaned or cleaned in seen or _is_generic_phrase(cleaned):
            return
        if len(cleaned) < 8:
            return
        seen.add(cleaned)
        phrases.append(cleaned)

    for skill in matched_skills[:3]:
        if _normalize_skill(skill) in _GENERIC_VOCABULARY_SKILLS:
            continue
        for hint in _focus_hints_for_skill(skill)[:2]:
            _add(hint)

    for step in study.get("step_by_step_breakdown") or []:
        phrase = _focus_phrase_from_step(str(step))
        if phrase:
            _add(phrase)
        if len(phrases) >= 4:
            break

    material_tokens = _tokenize(_study_material_text(study))
    for token in sorted(query_tokens & material_tokens):
        if len(token) >= 5:
            _add(f"{token} checks")
        if len(phrases) >= 4:
            break

    for mistake in study.get("common_mistakes") or []:
        text = normalize_surface_text(str(mistake))
        if text and not _is_generic_phrase(text, min_len=_MIN_SNIPPET_CHARS):
            short = truncate_at_word(text, 60).lower()
            if 12 <= len(short) <= 60:
                _add(short)
        if len(phrases) >= 4:
            break

    if not phrases:
        substantive = _substantive_matched_skills(matched_skills)
        for skill in substantive[:4]:
            for hint in _focus_hints_for_skill(skill):
                _add(hint)
                if len(phrases) >= 4:
                    break

    return phrases[:4]


def _hr_unmatched_note() -> str:
    return (
        "Saved role-pack material exists, but no question-specific document-library match "
        "was strong enough for this HR/behavioral prompt."
    )


def _weak_match_note(score: float) -> str:
    return (
        "Saved role pack exists but no meaningful skill/question overlap was found "
        f"for this prompt (best score {score:.1f})."
    )


def _core_terminology_only_note() -> str:
    return (
        "Saved role-pack material exists, but only generic core-terminology overlap was found, "
        "so it was not used as question-specific support."
    )


def _is_strong_match(category: str, evidence: _MatchEvidence) -> bool:
    cat = (category or "").lower()
    if cat in _HR_LIKE_CATEGORIES:
        return evidence.question_token_overlap >= 4
    if cat == "daily_routine":
        return (
            evidence.strong_skill_tag_match
            or evidence.skill_overlap_count >= 2
            or (evidence.skill_overlap_count >= 1 and evidence.question_token_overlap >= 2)
        )
    if cat not in _TECHNICAL_CATEGORIES and cat != "daily_routine":
        return (
            evidence.strong_skill_tag_match
            or evidence.skill_overlap_count >= 2
            or evidence.question_token_overlap >= 4
        )
    if evidence.strong_skill_tag_match:
        return True
    if evidence.skill_overlap_count >= 2:
        return True
    if evidence.skill_overlap_count >= 1 and evidence.question_token_overlap >= 2:
        return True
    if evidence.question_token_overlap >= 3:
        return True
    if evidence.material_token_overlap >= 3 and evidence.skill_overlap_count >= 1:
        return True
    return False


def find_role_study_documents(role_title: str) -> dict[str, Any] | None:
    """Locate saved role-pack documents for a role title."""
    pack = find_role_pack(role_title)
    if not pack:
        return None
    folder = Path(pack["folder"])
    structured_path = folder / "structured_content.json"
    markdown_candidates = sorted(folder.glob("*_study_material.md"))
    return {
        "role_name": pack.get("role_name", role_title),
        "role_slug": pack.get("role_slug") or normalize_role_slug(role_title),
        "category": pack.get("category"),
        "folder": str(folder),
        "structured_path": str(structured_path) if structured_path.exists() else None,
        "markdown_path": str(markdown_candidates[0]) if markdown_candidates else None,
        "questions": pack.get("questions") or [],
        "role_overview": pack.get("role_overview") or {},
        "metadata": pack.get("metadata") or {},
    }


def _load_saved_questions(documents: dict[str, Any]) -> list[dict[str, Any]]:
    structured_path = documents.get("structured_path")
    if structured_path and Path(structured_path).exists():
        try:
            payload = json.loads(Path(structured_path).read_text(encoding="utf-8"))
            questions = payload.get("questions") or []
            if questions:
                return questions
        except (OSError, json.JSONDecodeError):
            pass
    markdown_path = documents.get("markdown_path")
    if markdown_path and Path(markdown_path).exists():
        return documents.get("questions") or []
    return documents.get("questions") or []


def match_document_material_to_question(
    question: dict[str, Any],
    saved_questions: list[dict[str, Any]],
    *,
    role_overview: dict[str, Any] | None = None,
    job: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, float, list[str], _MatchEvidence | None]:
    """Score saved pack questions against the generated question."""
    _ = job  # retained for API compatibility; job-level skills are not used for matching
    query_skills = _query_skills(question)
    query_tokens = _tokenize(question.get("question", ""))
    query_category = (question.get("category") or "").lower()

    overview_skills = {
        _normalize_skill(s)
        for s in (role_overview or {}).get("required_skills") or []
        if _is_meaningful_skill(str(s))
    }

    best: dict[str, Any] | None = None
    best_evidence: _MatchEvidence | None = None

    for saved in saved_questions:
        saved_skills = _saved_question_skills(saved)
        overlap = query_skills & saved_skills
        meaningful_overlap = sorted({s for s in overlap if _is_meaningful_skill(s)}, key=str.lower)
        score = float(len(meaningful_overlap) * 2.0)

        saved_skill_tag = _normalize_skill(str(saved.get("skill_tag", "")))
        query_skill_tag = _normalize_skill(str(question.get("skill_tag", "")))
        strong_tag = bool(
            saved_skill_tag
            and query_skill_tag
            and saved_skill_tag == query_skill_tag
            and _is_meaningful_skill(saved_skill_tag)
        )
        if strong_tag:
            score += 2.5

        saved_category = (saved.get("category") or "").lower()
        if query_category and query_category == saved_category and query_category in _TECHNICAL_CATEGORIES:
            score += 0.75

        saved_q_tokens = _tokenize(saved.get("question", ""))
        question_token_overlap = len(query_tokens & saved_q_tokens)
        score += min(question_token_overlap * 0.5, 2.0)

        study = saved.get("study_material") or {}
        material_tokens = _tokenize(_study_material_text(study))
        material_token_overlap = len(query_tokens & material_tokens)
        score += min(material_token_overlap * 0.35, 1.5)

        if overview_skills and overlap & overview_skills:
            score += 0.5

        evidence = _MatchEvidence(
            strong_skill_tag_match=strong_tag,
            skill_overlap_count=len(meaningful_overlap),
            question_token_overlap=question_token_overlap,
            material_token_overlap=material_token_overlap,
            matched_skills=meaningful_overlap,
            score=score,
        )

        if best_evidence is None or score > best_evidence.score:
            best = saved
            best_evidence = evidence

    if best_evidence is None:
        return None, 0.0, [], None
    return best, best_evidence.score, best_evidence.matched_skills, best_evidence


def summarize_document_library_retrieval(result: DocumentLibraryRetrievalResult) -> str:
    if result.status == "used":
        skills = ", ".join(result.matched_skills[:6])
        return (
            f"Matched saved role-pack material for {result.source_label}"
            + (f" using skill overlap: {skills}." if skills else ".")
        )
    if result.status == "available_not_used":
        return result.note or "Saved role pack exists but no useful match was found for this question."
    if result.status == "not_configured":
        return result.note or "No saved role pack found in the document library for this role."
    return result.note or "Document-library retrieval did not return usable material."


def retrieve_study_material_snippets(
    question: dict[str, Any],
    job: dict[str, Any],
) -> DocumentLibraryRetrievalResult:
    """Retrieve and score document-library material for one generated question."""
    role_title = job.get("title") or "this role"
    query_category = (question.get("category") or "").lower()
    query_tokens = _tokenize(question.get("question", ""))

    documents = find_role_study_documents(role_title)
    if not documents:
        return DocumentLibraryRetrievalResult(
            status="not_configured",
            note="No saved role pack found in the document library for this role.",
            pack_exists=False,
        )

    structured_rel = (
        _relative_library_path(documents["structured_path"])
        if documents.get("structured_path")
        else _relative_library_path(documents["folder"])
    )
    saved_questions = _load_saved_questions(documents)
    if not saved_questions:
        return DocumentLibraryRetrievalResult(
            status="available_not_used",
            document_path=structured_rel,
            source_label=documents.get("role_name", role_title),
            note="Saved role pack exists but contains no structured questions to match.",
            pack_exists=True,
        )

    if query_category in _HR_LIKE_CATEGORIES:
        return DocumentLibraryRetrievalResult(
            status="available_not_used",
            document_path=structured_rel,
            source_label=documents.get("role_name", role_title),
            note=_hr_unmatched_note(),
            pack_exists=True,
        )

    matched, score, matched_skills, evidence = match_document_material_to_question(
        question,
        saved_questions,
        role_overview=documents.get("role_overview"),
        job=job,
    )

    if not matched or not evidence or not matched_skills:
        return DocumentLibraryRetrievalResult(
            status="available_not_used",
            relevance_score=score,
            document_path=structured_rel,
            source_label=documents.get("role_name", role_title),
            note=_weak_match_note(score),
            pack_exists=True,
        )

    if not _is_strong_match(query_category, evidence):
        return DocumentLibraryRetrievalResult(
            status="available_not_used",
            relevance_score=score,
            document_path=structured_rel,
            source_label=documents.get("role_name", role_title),
            note=_weak_match_note(score),
            pack_exists=True,
        )

    if _is_core_terminology_only_match(matched_skills):
        return DocumentLibraryRetrievalResult(
            status="available_not_used",
            relevance_score=score,
            document_path=structured_rel,
            source_label=documents.get("role_name", role_title),
            matched_skills=[_format_matched_skill_label(s) for s in matched_skills],
            note=_core_terminology_only_note(),
            pack_exists=True,
        )

    substantive_skills = _substantive_matched_skills(matched_skills)
    snippet_source, snippets = _resolve_snippet_source(matched, matched_skills, saved_questions)
    study = snippet_source.get("study_material") or {}
    supporting_focus = _build_supporting_focus(question, substantive_skills, study, query_tokens)

    if not snippets or not supporting_focus:
        return DocumentLibraryRetrievalResult(
            status="available_not_used",
            relevance_score=score,
            document_path=structured_rel,
            source_label=documents.get("role_name", role_title),
            matched_skills=[_format_matched_skill_label(s) for s in matched_skills],
            note=(
                "Saved role pack exists and partial overlap was detected, but no high-quality "
                "document-library snippets were available for this question."
            ),
            pack_exists=True,
        )

    display_skills = [_format_matched_skill_label(s) for s in substantive_skills] or [
        _format_matched_skill_label(s) for s in matched_skills
    ]

    result = DocumentLibraryRetrievalResult(
        status="used",
        relevance_score=score,
        document_path=structured_rel,
        source_label=documents.get("role_name", role_title),
        matched_skills=display_skills,
        supporting_focus=supporting_focus,
        snippets=snippets,
        matched_question_id=snippet_source.get("question_id") or matched.get("question_id"),
        pack_exists=True,
    )
    result.note = summarize_document_library_retrieval(result)
    return result


def apply_document_library_support(question: dict[str, Any], job: dict[str, Any]) -> DocumentLibraryRetrievalResult:
    """Attach compact document-library support metadata to a question study module."""
    result = retrieve_study_material_snippets(question, job)
    if not result.matched:
        return result

    study = dict(question.get("study_material") or {})
    study["document_library_support"] = {
        "summary": "Saved project material matched this question through role/skill overlap.",
        "source_path": result.document_path,
        "matched_skills": result.matched_skills,
        "supporting_focus": result.supporting_focus,
        "snippets": result.snippets,
        "matched_question_id": result.matched_question_id,
        "relevance_score": result.relevance_score,
    }
    question["study_material"] = study
    return result
