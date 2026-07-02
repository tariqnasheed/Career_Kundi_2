from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.answer_builders import (
    MAX_COMPLIANCE_WORKFLOW_SIMILARITY,
    compliance_workflow_overlap_ratio,
)
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.broken_template_audit import (
    broken_template_count,
    contains_broken_pattern,
)
from app.agents.job_search.quality.compiler_boilerplate_audit import (
    contains_universal_boilerplate,
    universal_boilerplate_count,
)
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.generic_phrase_audit import generic_phrase_count
from app.agents.job_search.quality.question_intent_alignment_audit import audit_question_intent_alignment
from app.agents.job_search.quality.study_material_phrase_audit import study_banned_phrase_count
from app.agents.job_search.quality.study_material_quality_audit import audit_study_material
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

PLACEHOLDER_PATTERNS = [
    r"\bTBD\b",
    r"\bTODO\b",
    r"\bLorem ipsum\b",
    r"\[insert\b",
    r"\{\{",
    r"\?\?\?",
    r"<placeholder>",
]

BANNED_SPOKEN_LABELS = (
    "Key terms are",
    "My practical workflow is:",
    "For compliance, I check",
    "I also apply safety checks such as",
)

MIN_STUDY_CHARS = 120
MIN_SECTION_CHARS = 40
EXPORT_SCORE_FLOOR = 85.0
STUDY_STRUCTURE_MARKERS = (
    "**Core idea:**",
    "**How to apply it:**",
    "**Common mistakes:**",
    "**Interview tip:**",
)


def prepare_interview_pack_export(
    job: dict[str, Any],
    *,
    focus_skill: str | None = None,
    difficulty: str = "medium",
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Build Markdown + structured context the same way API/library export does."""
    skill = focus_skill or (job.get("extracted_skills") or [{}])[0].get("skill") or (job.get("requirements") or ["General"])[0]
    questions = mock_generate_questions(job, focus_areas=[skill], difficulty=difficulty)
    role_overview = build_role_overview(job.get("title") or "Professional", job)
    markdown = build_interview_pack_markdown(
        job_title=job.get("title") or "Professional",
        company_name=job.get("company_name"),
        questions=questions,
        role_overview=role_overview,
    )
    return markdown, questions, role_overview


def _split_question_sections(markdown: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    pattern = re.compile(r"^## ([^:\n]+): (.+)$", re.M)
    skip_headers = {"role overview", "employer expectations", "skill map"}
    matches = [
        match
        for match in pattern.finditer(markdown)
        if match.group(1).strip().lower() not in skip_headers
    ]
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        sections.append(
            {
                "qid": match.group(1).strip(),
                "question": match.group(2).strip(),
                "body": body,
            }
        )
    return sections


def _extract_study_block(body: str) -> str:
    match = re.search(
        r"### (?:Study material|Dedicated study material)[^\n]*\n(.*?)(?=\n### |\n\*\*What interviewers|\n---|$)",
        body,
        re.S,
    )
    return (match.group(1).strip() if match else "")


def _skill_for_question(question_text: str, questions: list[dict[str, Any]] | None) -> str:
    for question in questions or []:
        if (question.get("question") or "").strip() == question_text.strip():
            return str(question.get("mapped_skill") or question.get("skill_tag") or "")
    return ""


def _extract_block(body: str, heading: str) -> str:
    pattern = rf"{re.escape(heading)}\s*\n(.*?)(?=\n### |\n\*\*|$)"
    match = re.search(pattern, body, re.S)
    return (match.group(1).strip() if match else "")


def _duplicate_paragraph_count(text: str) -> int:
    paras = [p.strip().lower() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paras) < 2:
        return 0
    dupes = 0
    for i in range(1, len(paras)):
        if paras[i] == paras[i - 1] and len(paras[i]) > 40:
            dupes += 1
    return dupes


def _empty_heading_count(markdown: str) -> int:
    return len(re.findall(r"^#{1,6}\s*$", markdown, re.M))


def _study_is_question_specific(question_text: str, study_text: str, skill: str = "") -> bool:
    blob = study_text.lower()
    q_lower = question_text.lower()
    if skill and skill.lower() in blob:
        return True
    tokens = [t for t in q_lower.split() if len(t) > 4]
    return any(token in blob for token in tokens[:6])


def _study_is_question_specific_structured(question: dict[str, Any], study: dict[str, Any]) -> bool:
    skill = (question.get("mapped_skill") or question.get("skill_tag") or "").lower()
    question_text = (question.get("question") or "").lower()
    blob = " ".join(
        str(study.get(key, ""))
        for key in (
            "what_this_question_tests",
            "overview",
            "beginner_explanation",
            "mini_practice_task",
            "worked_example",
        )
    ).lower()
    if skill and skill in blob:
        return True
    tokens = [t for t in question_text.split() if len(t) > 4]
    return any(token in blob for token in tokens[:6])


def _question_for_section(question_text: str, questions: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    for question in questions or []:
        if (question.get("question") or "").strip() == question_text.strip():
            return question
    return None


def _is_strict_compiler_question(question: dict[str, Any] | None) -> bool:
    if not question or question.get("export_blocked"):
        return False
    return (
        question.get("category") == "technical"
        and question.get("answer_source") == "contract_compiler"
        and bool(question.get("skill_card"))
    )


def _compiler_answer_texts(parsed_sections: list[dict[str, str]], questions: list[dict[str, Any]] | None) -> list[str]:
    texts: list[str] = []
    for section in parsed_sections:
        matched = _question_for_section(section["question"], questions)
        if not _is_strict_compiler_question(matched):
            continue
        texts.append(_extract_block(section["body"], "### Model answer"))
    return texts


def _format_issue(role: str, section: str, reason: str, *, question: str = "") -> str:
    qbit = f' for question "{question[:90]}"' if question else ""
    return f"{role} / {section}{qbit}: {reason}"


def audit_export_markdown(
    markdown: str,
    *,
    role: str,
    questions: list[dict[str, Any]] | None = None,
    role_overview: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    md = markdown or ""
    exportable = [q for q in (questions or []) if not q.get("export_blocked")]

    if not md.strip():
        errors.append(_format_issue(role, "markdown", "exported Markdown is empty"))

    if "## Role overview" not in md:
        errors.append(_format_issue(role, "role introduction", "missing '## Role overview' section in Markdown"))

    if "## Employer expectations" not in md:
        errors.append(_format_issue(role, "employer expectations", "missing '## Employer expectations' section in Markdown"))
    elif len(re.findall(r"^-\s+\S", md.split("## Employer expectations", 1)[-1].split("\n##", 1)[0], re.M)) < 1:
        errors.append(_format_issue(role, "employer expectations", "section has no bullet items (expected >= 1, actual 0)"))

    if "## Skill map" not in md:
        errors.append(_format_issue(role, "skill map", "missing '## Skill map' section in Markdown"))
    elif len(re.findall(r"^-\s+\S", md.split("## Skill map", 1)[-1].split("\n##", 1)[0], re.M)) < 1:
        errors.append(_format_issue(role, "skill map", "section has no bullet items (expected >= 1, actual 0)"))

    parsed_sections = _split_question_sections(md)
    if not parsed_sections:
        errors.append(_format_issue(role, "questions", "no question sections found in Markdown (expected >= 1, actual 0)"))

    answer_count = 0
    study_module_count = 0
    intent_alignment_fail_count = 0
    answers_over_500_count = 0
    study_quality_scores: list[float] = []
    peer_study_blobs = [
        " ".join(
            str((q.get("study_material") or {}).get(key, ""))
            for key in (
                "what_this_question_tests",
                "beginner_explanation",
                "step_by_step_method",
                "worked_example",
                "overview",
            )
        )
        for q in exportable
        if q.get("study_material")
    ]

    for section in parsed_sections:
        qtext = section["question"]
        body = section["body"]
        matched_question = _question_for_section(qtext, questions)
        structured_study = (matched_question or {}).get("study_material") or {}

        if "### Study material" not in body and "Dedicated study material" not in body:
            errors.append(_format_issue(role, "study material", "missing dedicated study module", question=qtext))
        else:
            study_text = _extract_study_block(body)
            skill = _skill_for_question(qtext, questions)
            study_specific = False
            if matched_question and structured_study:
                study_specific = _study_is_question_specific_structured(matched_question, structured_study)
            if not study_specific:
                study_specific = _study_is_question_specific(qtext, study_text, skill)
            visible_structure = sum(1 for marker in STUDY_STRUCTURE_MARKERS if marker in body)
            if visible_structure < 2:
                errors.append(
                    _format_issue(
                        role,
                        "study material",
                        f"study module lacks visible learning structure "
                        f"(expected >= 2 markers, actual {visible_structure})",
                        question=qtext,
                    )
                )
            if len(study_text) < MIN_STUDY_CHARS and not structured_study:
                errors.append(
                    _format_issue(
                        role,
                        "study material",
                        f"study module too short (expected >= {MIN_STUDY_CHARS} chars, actual {len(study_text)})",
                        question=qtext,
                    )
                )
            elif not study_specific:
                errors.append(
                    _format_issue(role, "study material", "study module is not question-specific", question=qtext)
                )
            else:
                study_module_count += 1

            if matched_question and structured_study:
                peers = [
                    blob
                    for blob in peer_study_blobs
                    if blob
                    and blob
                    != " ".join(
                        str(structured_study.get(key, ""))
                        for key in (
                            "what_this_question_tests",
                            "beginner_explanation",
                            "step_by_step_method",
                            "worked_example",
                            "overview",
                        )
                    )
                ]
                study_audit = audit_study_material(
                    structured_study,
                    matched_question,
                    role=role,
                    peer_studies=peers,
                )
                study_quality_scores.append(study_audit["score"])
                if not study_audit["passed"]:
                    errors.extend(study_audit["errors"][:2])
            study_phrase_count = study_banned_phrase_count(study_text)
            if study_phrase_count:
                errors.append(
                    _format_issue(
                        role,
                        "study material",
                        f"banned generic study phrases found (expected 0, actual {study_phrase_count})",
                        question=qtext,
                    )
                )

        if "### Model answer" not in body:
            errors.append(_format_issue(role, "model answer", "missing model answer section", question=qtext))
        else:
            answer_text = _extract_block(body, "### Model answer")
            word_count = len(answer_text.split())
            is_strict = _is_strict_compiler_question(matched_question)
            if not answer_text.strip():
                errors.append(_format_issue(role, "model answer", "answer section is empty", question=qtext))
            else:
                answer_count += 1
                if word_count > ABSOLUTE_MAX_WORDS:
                    answers_over_500_count += 1
                    errors.append(
                        _format_issue(
                            role,
                            "model answer",
                            f"answer exceeds flexible maximum (expected <= {ABSOLUTE_MAX_WORDS} words, actual {word_count})",
                            question=qtext,
                        )
                    )
                if matched_question:
                    intent_audit = audit_question_intent_alignment(answer_text, matched_question)
                    if not intent_audit["passed"]:
                        intent_alignment_fail_count += 1
                        errors.append(
                            _format_issue(
                                role,
                                "model answer",
                                f"answer intent misaligned ({intent_audit['intent']}): {intent_audit['errors'][0]}",
                                question=qtext,
                            )
                        )
            if is_strict:
                if "Key terms are" in answer_text:
                    errors.append(_format_issue(role, "model answer", 'contains banned label "Key terms are"', question=qtext))
                for label in BANNED_SPOKEN_LABELS[1:]:
                    if label in answer_text:
                        errors.append(_format_issue(role, "model answer", f'contains banned label "{label}"', question=qtext))
                if contains_broken_pattern(answer_text):
                    errors.append(_format_issue(role, "model answer", "contains broken template marker", question=qtext))
                if contains_universal_boilerplate(answer_text):
                    errors.append(_format_issue(role, "model answer", "contains universal boilerplate", question=qtext))
                overlap = compliance_workflow_overlap_ratio(answer_text)
                if overlap > MAX_COMPLIANCE_WORKFLOW_SIMILARITY:
                    warnings.append(
                        _format_issue(
                            role,
                            "model answer",
                            f"high compliance/workflow overlap ({overlap:.2f})",
                            question=qtext,
                        )
                    )
                if not any(
                    tok in answer_text.lower() for tok in ("for compliance", "i would evidence", "i would also")
                ):
                    warnings.append(
                        _format_issue(
                            role,
                            "model answer",
                            "technical answer missing compliance/evidence/safety phrasing",
                            question=qtext,
                        )
                    )

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, md, re.I):
            errors.append(_format_issue(role, "placeholder", f"placeholder pattern matched: {pattern}"))

    empty_section_count = _empty_heading_count(md)
    if empty_section_count:
        errors.append(
            _format_issue(
                role,
                "headings",
                f"empty headings found (expected 0, actual {empty_section_count})",
            )
        )

    duplicate_paragraph_count = _duplicate_paragraph_count(md)
    if duplicate_paragraph_count:
        warnings.append(
            _format_issue(
                role,
                "duplicates",
                f"duplicate consecutive paragraphs (count={duplicate_paragraph_count})",
            )
        )

    role_intro = md.split("## Employer expectations", 1)[0]
    compiler_answers_blob = "\n\n".join(_compiler_answer_texts(parsed_sections, questions))
    study_blob = "\n\n".join(_extract_study_block(section["body"]) for section in parsed_sections)
    generic_phrase_total = generic_phrase_count(f"{role_intro}\n{compiler_answers_blob}") + study_banned_phrase_count(
        study_blob
    )
    if generic_phrase_total:
        errors.append(
            _format_issue(
                role,
                "generic phrases",
                f"banned generic phrases found (expected 0, actual {generic_phrase_total})",
            )
        )

    if parsed_sections:
        strict_answers = _compiler_answer_texts(parsed_sections, questions)
        boilerplate_answers = sum(1 for answer in strict_answers if contains_universal_boilerplate(answer))
        if strict_answers and boilerplate_answers / len(strict_answers) > 0.5:
            errors.append(
                _format_issue(
                    role,
                    "boilerplate",
                    f"export is mostly boilerplate answers "
                    f"(expected <= 50%, actual {round(100 * boilerplate_answers / len(strict_answers), 1)}%)",
                )
            )

    if exportable:
        compiler_count = sum(1 for q in exportable if _is_strict_compiler_question(q))
        strict_answer_count = len(_compiler_answer_texts(parsed_sections, questions))
        if compiler_count and strict_answer_count < compiler_count:
            errors.append(
                _format_issue(
                    role,
                    "answers",
                    f"compiler answer sections missing in Markdown "
                    f"(expected >= {compiler_count}, actual {strict_answer_count})",
                )
            )

    if role_overview and not role_overview.get("summary"):
        warnings.append(_format_issue(role, "role introduction", "role overview summary missing in structured context"))

    question_count = len(parsed_sections)
    passed = not errors
    penalty = (len(errors) * 12) + (len(warnings) * 3) + min(generic_phrase_total * 5, 20) + min(broken_template_count(md) * 5, 20)
    score = max(0.0, round(100.0 - penalty, 1))

    study_quality_score = round(sum(study_quality_scores) / len(study_quality_scores), 1) if study_quality_scores else 0.0

    return {
        "passed": passed,
        "score": score,
        "errors": errors,
        "warnings": warnings,
        "role": role,
        "question_count": question_count,
        "answer_count": answer_count,
        "study_module_count": study_module_count,
        "generic_phrase_count": generic_phrase_total,
        "empty_section_count": empty_section_count,
        "duplicate_paragraph_count": duplicate_paragraph_count,
        "intent_alignment_fail_count": intent_alignment_fail_count,
        "answers_over_500_count": answers_over_500_count,
        "study_quality_score": study_quality_score,
    }
