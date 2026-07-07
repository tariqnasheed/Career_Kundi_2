"""Question-skill alignment tests (004E-E2.3 §5, §10, §15).

These assert *positive obligations* on generated answers:
  - the primary skill's own mechanism/workflow is present, and
  - a role-family / adjacent skill does not silently replace it.

Each obligation is also proven *discriminating* against a synthetic blob that
represents the exact failure mode (SQL-dominant "Python", installation-only
"Load Calculations", technical workflow for a motivation question). This avoids
exact-string overfitting while still failing the defective behaviour.
"""

from __future__ import annotations

from app.agents.job_search.knowledge.content_engine import _question_archetype, build_model_answer
from app.agents.job_search.knowledge.study_material_budget import (
    build_role_fit_apply_steps,
    build_role_fit_interview_application,
    classify_study_material_depth,
    is_question_study_alignment_failure,
    motivation_study_application_blob,
)
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.knowledge.core_technical_content import (
    build_technical_questions_for_skill,
)
from app.agents.job_search.knowledge.skill_cards import build_skill_card

PYTHON_NATIVE_MARKERS = (
    "python",
    "pandas",
    "dataframe",
    "script",
    "function",
    "list comprehension",
    "import ",
    "def ",
    "library",
    "module",
)
# SQL-specific *workflow* markers (not a bare "sql" mention, which is legitimate
# adjacency when Python analytics reads from a database).
SQL_WORKFLOW_MARKERS = (
    "join key",
    "execution plan",
    "covering index",
    "select only",
    "logical reads",
    "query plan",
    "bookmark lookup",
)

LOADCALC_NATIVE_MARKERS = (
    "connected load",
    "demand",
    "diversity",
    "power factor",
    "design current",
    "voltage drop",
    "protective device",
    "phase",
    "capacity",
    "future allowance",
)
INSTALLATION_ONLY_MARKERS = (
    "safe isolation",
    "insulation resistance",
    "continuity test",
    "earthing test",
    "cable termination",
)


def _job(role: str, skill: str, resp: str) -> dict:
    return {
        "title": role,
        "responsibilities": [resp],
        "requirements": [skill],
        "extracted_skills": [{"skill": skill}],
    }


def _answers_by_intent(role: str, skill: str, resp: str) -> dict[str, str]:
    """Build model answers for the intents that render deterministically without
    extra scenario/calculation payload (explain / terminology / principles)."""
    job = _job(role, skill, resp)
    questions = build_technical_questions_for_skill(skill, role, resp)
    out: dict[str, str] = {}
    for q in questions:
        qt = q.get("question_type")
        if qt not in {"explain", "terminology", "principles"}:
            continue
        card = build_skill_card(skill, job)
        enriched = {
            **q,
            "mapped_skill": skill,
            "role_family": card.get("role_family"),
            "skill_card": card,
        }
        if qt == "terminology":
            enriched["terminology_terms"] = q.get("terminology_terms")
        answer = build_model_answer(enriched, job)
        if answer:
            out[qt] = answer
    return out


def _python_native_and_not_sql_dominant(answer: str) -> bool:
    low = answer.lower()
    has_python = any(m in low for m in PYTHON_NATIVE_MARKERS)
    sql_workflow_hits = sum(1 for m in SQL_WORKFLOW_MARKERS if m in low)
    return has_python and sql_workflow_hits < 2


def _loadcalc_native(answer: str) -> bool:
    low = answer.lower()
    return sum(1 for m in LOADCALC_NATIVE_MARKERS if m in low) >= 2


# --- §5: Data Analyst + Python ---------------------------------------------


def test_data_analyst_python_is_python_native_not_sql() -> None:
    answers = _answers_by_intent(
        "Data Analyst", "Python", "Python data analysis and automation"
    )
    assert answers, "expected Python explain/terminology/principles answers"
    for intent, answer in answers.items():
        assert _python_native_and_not_sql_dominant(answer), (
            f"Python {intent} answer is not Python-native or is SQL-dominant: {answer[:200]}"
        )


def test_python_obligation_is_discriminating() -> None:
    """The obligation must FAIL SQL-dominant content where Python is only a label."""
    sql_dominant = (
        "For a Data Analyst, Python means writing queries. I would start by choosing the join key, "
        "then read the execution plan, add a covering index, select only needed columns, and check "
        "logical reads to reduce the query plan cost."
    )
    assert not _python_native_and_not_sql_dominant(sql_dominant)


def test_python_sql_adjacency_negative_control() -> None:
    """Legitimate adjacency: a Python analytics answer MAY mention SQL once when SQL
    supports the Python workflow; that must NOT be rejected."""
    legit = (
        "In Python I load the data with pandas, using a small SQL query to pull the source table, "
        "then clean it in a dataframe, write a reusable function, and validate the output with asserts."
    )
    assert _python_native_and_not_sql_dominant(legit)


# --- §5: Electrical Engineer + Load Calculations ---------------------------


def test_electrical_load_calculations_is_load_calc_native() -> None:
    answers = _answers_by_intent(
        "Electrical Engineer",
        "Load Calculations",
        "LV distribution design and load calculations",
    )
    assert answers, "expected Load Calculations explain/terminology/principles answers"
    for intent, answer in answers.items():
        assert _loadcalc_native(answer), (
            f"Load Calculations {intent} answer lacks load-calculation reasoning: {answer[:200]}"
        )


def test_load_calc_obligation_is_discriminating() -> None:
    """The obligation must FAIL a module that contains only installation/testing."""
    installation_only = (
        "I would begin with safe isolation, then carry out continuity testing, insulation resistance "
        "testing, an earthing test, and inspect the cable termination before energising."
    )
    assert not _loadcalc_native(installation_only)
    # Sanity: the installation-only text is indeed installation-flavoured.
    assert any(m in installation_only.lower() for m in INSTALLATION_ONLY_MARKERS)


# --- §10: role-specific motivation / company fit ---------------------------


def _motivation_job() -> dict:
    return {
        "title": "Data Analyst",
        "company_name": "Northline",
        "responsibilities": ["SQL dashboard creation"],
        "requirements": ["SQL"],
        "extracted_skills": [{"skill": "SQL"}, {"skill": "Excel"}],
    }


def _is_motivation_answer(answer: str) -> bool:
    low = answer.lower()
    motivation_signal = any(
        t in low
        for t in ("interested in this", "motivated", "i am applying", "i bring", "keen to")
    )
    sql_workflow = any(t in low for t in SQL_WORKFLOW_MARKERS) or "for a data analyst, sql means" in low
    return motivation_signal and not sql_workflow


def test_role_motivation_gets_motivation_answer() -> None:
    job = _motivation_job()
    card = build_skill_card("SQL", job)
    for qtext in (
        "How would your experience help Northline deliver KPI dashboards effectively?",
        "What makes you a good fit for this Data Analyst role?",
        "Why do you want to work as a Data Analyst at Northline?",
    ):
        q = {
            "question": qtext,
            "category": "company_specific",
            "skill_tag": "SQL",
            "mapped_skill": "SQL",
            "role_family": card.get("role_family"),
            "skill_card": card,
        }
        answer = build_model_answer(q, job)
        assert _is_motivation_answer(answer), f"expected motivation answer for {qtext!r}: {answer[:200]}"


def test_technical_role_fit_question_stays_technical() -> None:
    """§10 negative control: a genuinely technical question keeps its technical answer."""
    job = _motivation_job()
    card = build_skill_card("SQL", job)
    q = {
        "question": "How would you use SQL to build a KPI dashboard and validate the numbers?",
        "category": "technical",
        "question_type": "tool_usage",
        "skill_tag": "SQL",
        "mapped_skill": "SQL",
        "role_family": card.get("role_family"),
        "skill_card": card,
    }
    answer = build_model_answer(q, job)
    assert not _is_motivation_answer(answer)
    assert q.get("answer_source") != "legacy_template" or "sql" in answer.lower()


def _electrical_job() -> dict:
    return {
        "title": "Electrical Engineer",
        "responsibilities": ["Load calculations"],
        "requirements": ["Cable Sizing", "Load Calculations"],
        "extracted_skills": [
            {"skill": "Cable Sizing"},
            {"skill": "Load Calculations"},
            {"skill": "Commissioning"},
        ],
    }


_TECH_PROCEDURE_IN_APPLY = (
    "checks you would run",
    "interpret calculation",
    "confirm safe isolation",
    "demand factor",
    "state the goal, your method",
)


def _motivation_apply_blob(study: dict) -> str:
    return motivation_study_application_blob(study)


def _apply_is_motivation_focused(study: dict) -> bool:
    blob = _motivation_apply_blob(study)
    motivation_signal = any(
        t in blob
        for t in (
            "interested",
            "posting attracts",
            "genuinely interests",
            "hope to contribute",
            "development goals",
        )
    )
    procedure_signal = any(marker in blob for marker in _TECH_PROCEDURE_IN_APPLY)
    return motivation_signal and not procedure_signal


_ELECTRICAL_EXCITES_QUESTION = (
    "What excites you specifically about this Electrical Engineer position, "
    "based on what you've read? In this role-specific case, address: "
    "Electrical Engineer context: Load calculations."
)


def test_electrical_excites_routes_to_motivation_not_calculation() -> None:
    """E2.3 micro-fix: 'Load calculations' context must not steal motivation routing."""
    job = _electrical_job()
    q = {"question": _ELECTRICAL_EXCITES_QUESTION, "category": "role_specific", "skill_tag": None}
    assert _question_archetype(q["question"], q["category"], q) == "motivation"
    assert classify_study_material_depth(q, job) == "hr_behavioral"
    answer = build_model_answer(q, job)
    assert _is_motivation_answer(answer), f"expected motivation answer: {answer[:200]}"
    installation_only = (
        "For an Electrical Engineer, General means installing and testing electrical work so it is safe, "
        "compliant, and ready for inspection. You could start by confirming safe isolation before work."
    )
    assert not _is_motivation_answer(installation_only)


def test_electrical_excites_finalized_study_depth_is_hr_behavioral() -> None:
    """Motivation intent, answer route, and study depth must align end-to-end."""
    job = _electrical_job()
    questions = mock_generate_questions(job, focus_areas=["Cable Sizing", "Load Calculations"], difficulty="mid")
    excites = next(q for q in questions if "excites you" in (q.get("question") or "").lower())
    study = excites.get("study_material") or {}
    assert excites.get("answer_source") == "legacy_template"
    assert _is_motivation_answer(excites.get("model_answer", ""))
    assert study.get("study_depth") == "hr_behavioral"
    assert study.get("study_depth_label") == "HR / behavioral"
    assert "load calculations" in (excites.get("model_answer") or "").lower()
    assert _apply_is_motivation_focused(study), f"apply blob: {_motivation_apply_blob(study)[:250]}"
    assert not is_question_study_alignment_failure(excites)


def test_electrical_load_calculation_question_stays_technical() -> None:
    """Negative control: genuine load-calculation questions remain technical."""
    job = _electrical_job()
    card = build_skill_card("Load Calculations", job)
    q = {
        "question": "How would you perform load calculations for a new LV distribution board?",
        "category": "technical",
        "question_type": "calculation",
        "skill_tag": "Load Calculations",
        "mapped_skill": "Load Calculations",
        "role_family": card.get("role_family"),
        "skill_card": card,
    }
    answer = build_model_answer(q, job)
    assert not _is_motivation_answer(answer)
    assert _loadcalc_native(answer) or "calculation" in answer.lower()
    assert classify_study_material_depth(q, job) != "hr_behavioral"


def test_clinical_pharmacist_excites_stays_motivation() -> None:
    """Regression guard: healthcare motivation routing unchanged."""
    job = {
        "title": "Clinical Pharmacist",
        "responsibilities": ["Medication review"],
        "requirements": ["Pharmacology"],
        "extracted_skills": [
            {"skill": "Pharmacology"},
            {"skill": "Medication Review"},
            {"skill": "Clinical Governance"},
        ],
    }
    qtext = (
        "What excites you specifically about this Clinical Pharmacist position, "
        "based on what you've read? In this role-specific case, address: "
        "Clinical Pharmacist context: Medication review."
    )
    q = {"question": qtext, "category": "role_specific", "skill_tag": None}
    assert _question_archetype(q["question"], q["category"], q) == "motivation"
    assert classify_study_material_depth(q, job) == "hr_behavioral"
    answer = build_model_answer(q, job)
    assert _is_motivation_answer(answer), f"expected motivation answer: {answer[:200]}"
    questions = mock_generate_questions(job, focus_areas=["Medication Review", "Pharmacology"], difficulty="mid")
    excites = next(item for item in questions if "excites you" in (item.get("question") or "").lower())
    study = excites.get("study_material") or {}
    assert _apply_is_motivation_focused(study), f"apply blob: {_motivation_apply_blob(study)[:250]}"
    assert "medication review" in (excites.get("model_answer") or "").lower()
    assert not is_question_study_alignment_failure(excites)


def test_electrical_load_calculation_study_not_flagged_as_alignment_failure() -> None:
    job = _electrical_job()
    card = build_skill_card("Load Calculations", job)
    q = {
        "question": "How would you perform load calculations for a new LV distribution board?",
        "category": "technical",
        "question_type": "calculation",
        "skill_tag": "Load Calculations",
        "mapped_skill": "Load Calculations",
        "role_family": card.get("role_family"),
        "skill_card": card,
        "study_material": {
            "study_depth": "standard_technical",
            "step_by_step_method": ["Establish connected load by phase before applying diversity."],
            "interview_application": "Show the calculation logic and verify against BS 7671 limits.",
        },
    }
    assert not is_question_study_alignment_failure(q)
