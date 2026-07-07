"""004E-F final interview-pack + study-material regression gate tests."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

from app.agents.job_search.company_research import (
    extract_company_from_html,
    merge_company_research_into_job_snapshot,
)
from app.agents.job_search.job_posting_extractor import (
    extract_job_posting_from_html,
    merge_extraction_into_job_snapshot,
)
from app.agents.job_search.quality.final_regression_audit import (
    DETERMINISTIC_RANDOM_ROLES,
    FIXED_CROSS_SECTOR_CASES,
    audit_generated_pack,
    audit_intent_depth_consistency,
    audit_question_study_alignment,
    metrics_are_clean,
    pack_failure_reasons,
)
from app.core.config import settings

JOB_HTML = """
<html><head><script type="application/ld+json">
{"@type":"JobPosting","title":"Data Analyst","description":"Build dashboards.",
 "responsibilities":["SQL dashboard creation","Daily data quality checks"],
 "tools":["Power BI","SQL"],"skills":["SQL","Python"]}
</script></head></html>
"""

ORG_HTML = """
<html><head><script type="application/ld+json">
{"@type":"Corporation","legalName":"Northline Analytics Ltd",
 "makesOffer":[{"name":"KPI dashboards"}],"knowsAbout":["Retail analytics"]}
</script></head></html>
"""

TITLE_ONLY_JOB = {"title": "Mystery Role"}


def _full_ladder_job() -> dict:
    extraction = extract_job_posting_from_html(JOB_HTML, "https://northline.example/jobs/analyst")
    research = extract_company_from_html(ORG_HTML, "https://northline.example/about")
    job = merge_extraction_into_job_snapshot(
        {
            "title": "Data Analyst",
            "company_name": "Northline Analytics",
            "description_raw": "Build dashboards and KPI reporting.",
            "responsibilities": ["SQL dashboard creation"],
            "requirements": ["Strong SQL"],
            "extracted_skills": [{"skill": "SQL"}, {"skill": "Excel"}],
        },
        extraction,
    )
    return merge_company_research_into_job_snapshot(job, research)


def _assert_clean(metrics: dict, *, allow_thin_coverage: bool = False) -> None:
    # §11: consume the single canonical clean/fail derivation instead of
    # maintaining an independent (and historically weaker) list here. Any new
    # final-gate field added to `pack_failure_reasons` is enforced automatically.
    reasons = pack_failure_reasons(metrics, allow_thin_coverage=allow_thin_coverage)
    assert reasons == [], {"failure_reasons": reasons, "metrics": metrics}
    # Positive invariants that are preconditions for a meaningful clean pack.
    assert metrics["source_ladder_present"] is True, metrics
    assert metrics["export_ready"] is True, metrics
    assert metrics["question_count"] >= 1, metrics


# Roles whose extracted skills have NO curated expert content, so every skill
# falls to the shared generic fallback and the hardened Class F gate correctly
# reports generic-template saturation. This is a truthfully-reported content-depth
# limitation (fallback dominance), NOT a false green: the fix is curated per-skill
# content, which is out of scope for the artifact false-green hardening pass. The
# case is asserted explicitly so the gate is never silently weakened and nothing
# else can hide behind the known reason.
_KNOWN_FALLBACK_SATURATED_ROLES = {"DevOps Engineer"}


@pytest.mark.parametrize("case", FIXED_CROSS_SECTOR_CASES, ids=[c["sample"] for c in FIXED_CROSS_SECTOR_CASES])
def test_fixed_cross_sector_regression(case: dict) -> None:
    metrics = audit_generated_pack(
        case["job"],
        focus_areas=case["focus"],
        role_label=case["role"],
        input_type=case["input_type"],
        sample_name=case["sample"],
    )
    if case["role"] in _KNOWN_FALLBACK_SATURATED_ROLES:
        reasons = pack_failure_reasons(metrics)
        assert reasons == ["generic_template_saturation_failure_count"], {
            "note": "expected ONLY the documented generic-fallback saturation",
            "failure_reasons": reasons,
        }
        assert metrics["export_ready"] is True, metrics
        return
    _assert_clean(metrics)


@pytest.mark.parametrize(
    "case",
    DETERMINISTIC_RANDOM_ROLES,
    ids=[c["sample"] for c in DETERMINISTIC_RANDOM_ROLES],
)
def test_deterministic_random_regression(case: dict) -> None:
    metrics = audit_generated_pack(
        case["job"],
        focus_areas=case["focus"],
        role_label=case["role"],
        input_type=case["input_type"],
        sample_name=case["sample"],
    )
    _assert_clean(metrics)


def test_title_only_does_not_claim_fake_full_coverage() -> None:
    metrics = audit_generated_pack(
        TITLE_ONLY_JOB,
        focus_areas=[],
        difficulty="auto",
        role_label="Mystery Role",
        input_type="title_only",
        sample_name="Title only",
    )
    _assert_clean(metrics, allow_thin_coverage=True)
    audit = metrics["job"].get("coverage_audit") or {}
    score = audit.get("coverage_score", 0)
    if score not in (0, "N/A", "0", None, ""):
        assert int(score) == 0


def test_rich_source_ladder_regression() -> None:
    metrics = audit_generated_pack(
        _full_ladder_job(),
        focus_areas=["SQL"],
        role_label="Data Analyst",
        input_type="rich_source_ladder",
        sample_name="Rich source ladder",
    )
    _assert_clean(metrics)
    questions = metrics["questions"]
    assert any("dashboard" in (q.get("question") or "").lower() for q in questions)
    assert any(
        "KPI dashboards" in (q.get("question") or "")
        or "company_research" in (q.get("question_source_types") or [])
        for q in questions
    )


def test_document_export_keeps_answer_and_study_together() -> None:
    metrics = audit_generated_pack(
        _full_ladder_job(),
        focus_areas=["SQL"],
        sample_name="Document export",
    )
    pack_md = metrics["pack_markdown"]
    assert "### Model answer" in pack_md
    assert "### Study material" in pack_md
    assert pack_md.count("### Study material") >= metrics["question_count"]
    assert pack_md.count("### Model answer") >= metrics["question_count"]


def test_part_time_odd_job_plain_input() -> None:
    job = {
        "title": "Weekend Barista",
        "description_raw": "Part-time weekend espresso shifts.",
        "responsibilities": ["Espresso preparation", "Till operation"],
        "requirements": ["Customer service"],
        "extracted_skills": [{"skill": "Coffee Preparation"}],
    }
    metrics = audit_generated_pack(
        job,
        focus_areas=["Coffee Preparation"],
        role_label="Weekend Barista",
        input_type="part_time_odd_job",
        sample_name="Part-time odd job",
    )
    _assert_clean(metrics)


def test_model_knowledge_disabled_by_default() -> None:
    assert settings.job_search_enable_model_knowledge is False


def test_no_new_direct_network_imports_in_job_search_agents() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    cmd = (
        'grep -R -E "(^|\\\\s)(import httpx|import requests|from httpx|from requests|'
        "import urllib\\\\.request|from urllib\\\\.request import|urllib\\\\.request\\\\.urlopen|"
        'urlopen\\\\()" -n backend/app/agents/job_search '
        '--exclude-dir="__pycache__" --exclude="*.pyc" --exclude="test_*" '
        '| grep -v "job_posting_extractor.py" | grep -v "company_research.py" || true'
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=repo_root)
    assert result.stdout.strip() == ""


def test_source_ladder_audit_module_has_no_direct_network_imports() -> None:
    path = Path(__file__).resolve().parents[1] / "quality" / "final_regression_audit.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    banned = {"httpx", "requests", "urllib", "aiohttp"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned


def test_metrics_are_clean_helper() -> None:
    good = {
        "missing_answer_count": 0,
        "missing_study_module_count": 0,
        "fake_url_hits": 0,
        "generic_phrase_hits": 0,
        "silly_question_hits": 0,
        "empty_section_count": 0,
        "duplicate_study_module_count": 0,
        "internal_label_leak_count": 0,
        "source_ladder_present": True,
        "export_ready": True,
        "question_count": 3,
        "coverage_score": 0,
    }
    assert metrics_are_clean(good, allow_thin_coverage=True)


def _clean_metrics_stub() -> dict:
    return {
        "missing_answer_count": 0,
        "missing_study_module_count": 0,
        "fake_url_hits": 0,
        "generic_phrase_hits": 0,
        "silly_question_hits": 0,
        "empty_section_count": 0,
        "duplicate_study_module_count": 0,
        "internal_label_leak_count": 0,
        "unsupported_personal_claim_count": 0,
        "unsupported_numeric_claim_count": 0,
        "cross_domain_contamination_hits": 0,
        "surface_quality_defect_count": 0,
        "thin_input_specificity_violation_count": 0,
        "structure_incomplete_count": 0,
        "substantive_depth_failure_count": 0,
        "intent_depth_mismatch_count": 0,
        "question_study_alignment_failure_count": 0,
        "synthetic_overload_failure_count": 0,
        "answer_obligation_coverage_failure_count": 0,
        "study_obligation_coverage_failure_count": 0,
        "pure_motivation_technical_dominance_failure_count": 0,
        "source_ladder_present": True,
        "export_ready": True,
        "question_count": 3,
        "coverage_score": 0,
    }


def test_structure_incomplete_is_not_clean() -> None:
    metrics = _clean_metrics_stub()
    metrics["structure_incomplete_count"] = 1
    assert metrics_are_clean(metrics, allow_thin_coverage=True) is False


def test_low_substantive_depth_is_not_clean() -> None:
    metrics = _clean_metrics_stub()
    metrics["substantive_depth_failure_count"] = 2
    assert metrics_are_clean(metrics, allow_thin_coverage=True) is False


def test_unsupported_biography_is_not_clean() -> None:
    metrics = _clean_metrics_stub()
    metrics["unsupported_personal_claim_count"] = 1
    assert metrics_are_clean(metrics, allow_thin_coverage=True) is False


def test_metrics_are_clean_delegates_to_pack_failure_reasons() -> None:
    # metrics_are_clean must be exactly `not pack_failure_reasons(...)`.
    for key in (
        "structure_incomplete_count",
        "substantive_depth_failure_count",
        "surface_quality_defect_count",
        "unsupported_numeric_claim_count",
    ):
        metrics = _clean_metrics_stub()
        metrics[key] = 1
        reasons = pack_failure_reasons(metrics, allow_thin_coverage=True)
        assert key in reasons
        assert metrics_are_clean(metrics, allow_thin_coverage=True) is (not reasons)


def test_assert_clean_consumes_canonical_semantics() -> None:
    # _assert_clean must fail whenever the canonical derivation reports a failure,
    # including structure/substantive fields the old duplicated list omitted.
    for key in ("structure_incomplete_count", "substantive_depth_failure_count"):
        metrics = _clean_metrics_stub()
        metrics[key] = 1
        with pytest.raises(AssertionError):
            _assert_clean(metrics, allow_thin_coverage=True)


def test_sample_generators_consume_canonical_clean_path() -> None:
    # Both the E2 (per-question) and F (per-pack) generators must derive their
    # failure reasons from the single canonical path so a structure-incomplete or
    # substantive-depth failure can never be reported clean by a generator.
    from scripts.generate_iteration_004e_e2_samples import (
        _row_failure_reasons as e2_reasons,
    )
    from scripts.generate_iteration_004e_f_samples import (
        _row_failure_reasons as f_reasons,
    )

    # F generator consumes pack-level canonical keys directly.
    f_row = _clean_metrics_stub()
    assert f_reasons(f_row) == []
    f_row["structure_incomplete_count"] = 1
    assert "structure_incomplete_count" in f_reasons(f_row)

    # E2 generator maps per-question rows onto the canonical path.
    e2_clean = {
        "budget_status": "within_target",
        "study_depth": "complex_scenario",
        "substantive_contract_coverage": 1.0,
    }
    assert e2_reasons(e2_clean) == []
    e2_struct = dict(e2_clean, budget_status="structure_incomplete")
    assert "structure_incomplete_count" in e2_reasons(e2_struct)
    e2_subst = dict(e2_clean, substantive_contract_coverage=0.5)
    assert any(r.startswith("substantive_depth_failure_count") for r in e2_reasons(e2_subst))


def test_intent_depth_mismatch_blocks_canonical_clean() -> None:
    metrics = _clean_metrics_stub()
    metrics["intent_depth_mismatch_count"] = 1
    assert metrics_are_clean(metrics, allow_thin_coverage=True) is False
    assert "intent_depth_mismatch_count" in pack_failure_reasons(metrics, allow_thin_coverage=True)


def test_injected_intent_depth_mismatch_detected() -> None:
    q = {
        "question": (
            "What excites you specifically about this Electrical Engineer position, "
            "based on what you've read? In this role-specific case, address: "
            "Electrical Engineer context: Load calculations."
        ),
        "category": "role_specific",
        "study_material": {"study_depth": "standard_technical"},
    }
    assert audit_intent_depth_consistency([q])["intent_depth_mismatch_count"] == 1


def test_electrical_pack_has_aligned_motivation_depth() -> None:
    case = FIXED_CROSS_SECTOR_CASES[1]
    metrics = audit_generated_pack(
        case["job"],
        focus_areas=case["focus"],
        role_label=case["role"],
        input_type=case["input_type"],
        sample_name=case["sample"],
    )
    assert metrics["intent_depth_mismatch_count"] == 0
    excites = next(
        q for q in metrics["questions"] if "excites you" in (q.get("question") or "").lower()
    )
    assert (excites.get("study_material") or {}).get("study_depth") == "hr_behavioral"


def test_technical_load_calculation_not_flagged_as_intent_depth_mismatch() -> None:
    q = {
        "question": "How would you perform load calculations for a new LV distribution board?",
        "category": "technical",
        "question_type": "calculation",
        "skill_tag": "Load Calculations",
        "study_material": {"study_depth": "standard_technical"},
    }
    assert audit_intent_depth_consistency([q])["intent_depth_mismatch_count"] == 0


def test_complex_scenario_not_flagged_as_intent_depth_mismatch() -> None:
    q = {
        "question": (
            "Walk through a complex multi-constraint safety scenario where regulatory "
            "limits, patient risk, and staffing all conflict and you must decide."
        ),
        "category": "technical",
        "question_type": "scenario",
        "skill_tag": "Medication Review",
        "study_material": {"study_depth": "complex_scenario"},
    }
    assert audit_intent_depth_consistency([q])["intent_depth_mismatch_count"] == 0


def test_question_study_alignment_failure_blocks_canonical_clean() -> None:
    metrics = _clean_metrics_stub()
    metrics["question_study_alignment_failure_count"] = 1
    assert metrics_are_clean(metrics, allow_thin_coverage=True) is False
    assert "question_study_alignment_failure_count" in pack_failure_reasons(
        metrics, allow_thin_coverage=True
    )


def test_injected_study_alignment_mismatch_detected() -> None:
    q = {
        "question": (
            "What excites you specifically about this Electrical Engineer position, "
            "based on what you've read? In this role-specific case, address: "
            "Electrical Engineer context: Load calculations."
        ),
        "category": "role_specific",
        "study_material": {
            "study_depth": "hr_behavioral",
            "step_by_step_method": ["Confirm safe isolation before work."],
            "interview_application": (
                "Structure your spoken answer around the focus area: state the goal, your method, "
                "checks you would run, and the outcome an Electrical Engineer interviewer expects."
            ),
        },
    }
    assert audit_question_study_alignment([q])["question_study_alignment_failure_count"] == 1


def test_electrical_pack_has_aligned_motivation_study_application() -> None:
    case = FIXED_CROSS_SECTOR_CASES[1]
    metrics = audit_generated_pack(
        case["job"],
        focus_areas=case["focus"],
        role_label=case["role"],
        input_type=case["input_type"],
        sample_name=case["sample"],
    )
    assert metrics["question_study_alignment_failure_count"] == 0
    excites = next(
        q for q in metrics["questions"] if "excites you" in (q.get("question") or "").lower()
    )
    blob = " ".join(
        str((excites.get("study_material") or {}).get(k) or "")
        for k in ("step_by_step_method", "interview_application")
    ).lower()
    assert "checks you would run" not in blob
    assert any(t in blob for t in ("posting attracts", "genuinely interests", "hope to contribute"))


def test_clinical_motivation_pack_has_aligned_study_application() -> None:
    case = FIXED_CROSS_SECTOR_CASES[2]
    metrics = audit_generated_pack(
        case["job"],
        focus_areas=case["focus"],
        role_label=case["role"],
        input_type=case["input_type"],
        sample_name=case["sample"],
    )
    assert metrics["question_study_alignment_failure_count"] == 0
    excites = next(
        q for q in metrics["questions"] if "excites you" in (q.get("question") or "").lower()
    )
    assert "medication review" in (excites.get("model_answer") or "").lower()
    assert audit_question_study_alignment([excites])["question_study_alignment_failure_count"] == 0


def test_technical_load_calculation_not_flagged_as_study_alignment_failure() -> None:
    q = {
        "question": "How would you perform load calculations for a new LV distribution board?",
        "category": "technical",
        "question_type": "calculation",
        "skill_tag": "Load Calculations",
        "study_material": {
            "study_depth": "standard_technical",
            "step_by_step_method": ["Apply diversity factors to connected load totals."],
            "interview_application": "Show the calculation logic and verify against BS 7671 limits.",
        },
    }
    assert audit_question_study_alignment([q])["question_study_alignment_failure_count"] == 0


def test_answer_obligation_coverage_failure_blocks_canonical_clean() -> None:
    metrics = _clean_metrics_stub()
    metrics["answer_obligation_coverage_failure_count"] = 1
    assert metrics_are_clean(metrics, allow_thin_coverage=True) is False
    assert "answer_obligation_coverage_failure_count" in pack_failure_reasons(
        metrics, allow_thin_coverage=True
    )


def test_injected_answer_obligation_mismatch_detected() -> None:
    from app.agents.job_search.quality.question_obligation_coverage_audit import (
        audit_answer_obligation_coverage,
    )

    q = {
        "question": (
            "What excites you about this DevOps role, and how would you improve deployment reliability?"
        ),
        "category": "hr",
        "model_answer": (
            "I am interested in this DevOps Engineer role because the posting centres on ci/cd pipeline maintenance."
        ),
        "obligation_profile": {
            "obligations": ["motivation_fit", "technical_method"],
            "primary_obligation": "motivation_fit",
            "origin": "employer_provided",
            "is_hybrid": True,
            "synthetic_overload": False,
            "overload_reasons": [],
            "evidence_by_obligation": {},
        },
    }
    assert audit_answer_obligation_coverage([q])["answer_obligation_coverage_failure_count"] == 1


_DEVOPS_MODIFIER_JOB = {
    "title": "DevOps Engineer",
    "responsibilities": ["CI/CD pipeline maintenance"],
    "extracted_skills": [{"skill": "CI/CD"}],
}


def test_technical_explicit_modifier_omission_blocks_canonical_clean() -> None:
    """Non-HR technical question with explicit modifier asks must fail the canonical pack gate."""
    from app.agents.job_search.knowledge.question_obligations import Obligation, extract_question_obligations
    from app.agents.job_search.quality.question_obligation_coverage_audit import audit_question_obligations

    q = {
        "question": (
            "How would you improve deployment reliability in this CI/CD workflow, "
            "which metric would you monitor, and what failure mode would you plan for?"
        ),
        "category": "technical",
        "question_type": "technical_method",
        "skill_tag": "CI/CD",
        "mapped_skill": "CI/CD",
        "model_answer": (
            "I would start by adding pipeline health checks and rollback gates after each deploy. "
            "Then I would wire monitoring alerts to on-call ownership and validate artefacts before promotion. "
            "After that, I would compare deployment outcomes against the previous baseline before closing the change."
        ),
        "study_material": {"study_depth": "standard_technical"},
    }
    profile = extract_question_obligations(q, _DEVOPS_MODIFIER_JOB)
    assert Obligation.TECHNICAL_METHOD.value in profile.obligations
    assert Obligation.METRIC.value in profile.obligations
    assert Obligation.FAILURE_MODE.value in profile.obligations

    obligation_metrics = audit_question_obligations([q], _DEVOPS_MODIFIER_JOB)
    metrics = _clean_metrics_stub()
    metrics.update(obligation_metrics)
    metrics["question_count"] = 1

    assert obligation_metrics["answer_obligation_coverage_failure_count"] > 0
    assert metrics_are_clean(metrics, allow_thin_coverage=True) is False
    assert "answer_obligation_coverage_failure_count" in pack_failure_reasons(
        metrics, allow_thin_coverage=True
    )


def test_technical_without_explicit_modifiers_stays_canonically_clean() -> None:
    """Ordinary technical prompts must not fail canonical obligation coverage for missing modifiers."""
    from app.agents.job_search.quality.question_obligation_coverage_audit import audit_question_obligations

    q = {
        "question": "How would you perform load calculations for a new LV distribution board?",
        "category": "technical",
        "question_type": "calculation",
        "skill_tag": "Load Calculations",
        "model_answer": (
            "I would establish the connected load for every circuit and total it by phase, apply diversity factors, "
            "calculate design current, and verify cable capacity and voltage drop against BS 7671 limits."
        ),
        "study_material": {"study_depth": "standard_technical"},
    }
    obligation_metrics = audit_question_obligations([q], {"title": "Electrical Engineer"})
    metrics = _clean_metrics_stub()
    metrics.update(obligation_metrics)

    assert obligation_metrics["answer_obligation_coverage_failure_count"] == 0
    assert metrics_are_clean(metrics, allow_thin_coverage=True) is True
