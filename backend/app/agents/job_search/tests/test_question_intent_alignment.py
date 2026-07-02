from __future__ import annotations

from app.agents.job_search.knowledge.content_engine import build_model_answer
from app.agents.job_search.knowledge.core_technical_content import build_technical_questions_for_skill
from app.agents.job_search.knowledge.skill_cards import build_skill_card
from app.agents.job_search.quality.question_intent_alignment_audit import audit_question_intent_alignment


def _job(role: str, skill: str) -> dict:
    return {
        "title": role,
        "responsibilities": [f"Deliver {skill} work safely and accurately"],
        "requirements": [skill],
        "extracted_skills": [{"skill": skill}],
    }


def _answer_for_question(
    role: str,
    skill: str,
    question_type: str,
    matcher: str | None = None,
) -> tuple[str, dict]:
    job = _job(role, skill)
    questions = build_technical_questions_for_skill(skill, role, job["responsibilities"][0])
    candidates = [q for q in questions if q.get("question_type") == question_type]
    if matcher:
        preferred = [q for q in candidates if matcher.lower() in (q.get("question") or "").lower()]
        if preferred:
            candidates = preferred
    if not candidates:
        raise AssertionError(f"No {question_type} question found for {role}")

    question = candidates[0]
    card = build_skill_card(skill, job)
    enriched = {
        **question,
        "mapped_skill": skill,
        "role_family": card.get("role_family"),
        "skill_card": card,
    }
    if question_type == "terminology":
        enriched["terminology_terms"] = question.get("terminology_terms")
    if question_type == "calculation":
        enriched["calculation"] = question.get("calculation")
    answer = build_model_answer(enriched, job)
    assert answer, f"No answer generated for {role} / {question_type}"
    return answer, enriched


def test_question_intent_alignment_representative_cases() -> None:
    cases = [
        ("Data Analyst", "SQL", "calculation", "10 million"),
        ("Barista", "Coffee Preparation", "terminology", None),
        ("Solicitor", "Legal Research", "terminology", None),
        ("DevOps Engineer", "AWS", "explain", "junior engineer"),
        ("Clinical Pharmacist", "Pharmacology", "scenario", "high-risk"),
        ("Operations Manager", "Process Improvement", "scenario", "complex problem"),
    ]

    audits = []
    for role, skill, question_type, matcher in cases:
        answer, question = _answer_for_question(role, skill, question_type, matcher)
        audit = audit_question_intent_alignment(answer, question)
        audits.append(audit)
        assert audit["passed"], (
            f"{role} intent alignment failed for intent={audit['intent']}: {audit['errors']}"
        )

    sql_answer, sql_question = _answer_for_question("Data Analyst", "SQL", "calculation", "10 million")
    sql_lower = sql_answer.lower()
    assert any(tok in sql_lower for tok in ("select only", "needed columns", "covering index"))
    assert any(tok in sql_lower for tok in ("execution plan", "logical reads", "i/o", "bookmark"))

    devops_answer, _ = _answer_for_question("DevOps Engineer", "AWS", "explain", "junior engineer")
    devops_lower = devops_answer.lower()
    assert any(tok in devops_lower for tok in ("trade-off", "trade off", "versus", "balance"))
    assert any(tok in devops_lower for tok in ("mttr", "failure rate", "alarm", "rollback", "metric"))

    barista_answer, barista_q = _answer_for_question("Barista", "Coffee Preparation", "terminology")
    assert barista_answer.count("**") >= 8
    assert "means" in barista_answer.lower()
    barista_audit = audit_question_intent_alignment(barista_answer, barista_q)
    assert barista_audit["intent"] == "terminology_definition"

    scenario_answer, scenario_q = _answer_for_question("Clinical Pharmacist", "Pharmacology", "scenario", "high-risk")
    scenario_lower = scenario_answer.lower()
    assert any(tok in scenario_lower for tok in ("case", "patient", "document", "escalat", "risk"))
    assert "for compliance" in scenario_lower or "i would evidence" in scenario_lower

    avg_score = round(sum(a["score"] for a in audits) / len(audits), 1)
    assert avg_score >= 85.0, f"Average intent alignment score too low: {avg_score}"
