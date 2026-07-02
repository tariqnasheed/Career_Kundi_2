from __future__ import annotations

from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.study_material_phrase_audit import study_banned_phrase_count
from app.agents.job_search.quality.study_material_quality_audit import audit_study_material
from app.agents.job_search.tests.regression_metrics import load_golden_cases

AVERAGE_SCORE_FLOOR = 85.0
MAX_WARNINGS_PER_ROLE = 1


def _job_for_case(case: dict) -> dict:
    return {
        "title": case["role"],
        "responsibilities": [f"Deliver {case['skill']} work safely and accurately"],
        "requirements": [case["skill"]],
        "extracted_skills": [{"skill": case["skill"]}],
    }


def _study_blob(study: dict) -> str:
    return " ".join(
        str(study.get(key, ""))
        for key in (
            "what_this_question_tests",
            "beginner_explanation",
            "step_by_step_method",
            "worked_example",
            "overview",
        )
    )


def test_study_material_quality() -> None:
    cases = load_golden_cases()
    assert len(cases) >= 15

    all_audits: list[dict] = []
    all_blobs: list[str] = []
    role_warnings: dict[str, int] = {}

    for case in cases:
        job = _job_for_case(case)
        questions = mock_generate_questions(job, focus_areas=[case["skill"]], difficulty="medium")
        role_warning_count = 0
        role_blobs = [_study_blob(q.get("study_material") or {}) for q in questions if q.get("study_material")]

        for question in questions:
            if question.get("export_blocked"):
                continue
            study = question.get("study_material") or {}
            if not study:
                skill = question.get("mapped_skill") or question.get("skill_tag") or "General"
                raise AssertionError(
                    f'{case["role"]} / {skill}: study material for '
                    f'"{(question.get("question") or "")[:90]}" is missing (expected structured module, actual none)'
                )

            peers = [blob for blob in all_blobs + role_blobs if blob and blob != _study_blob(study)]
            audit = audit_study_material(study, question, role=case["role"], peer_studies=peers)
            all_audits.append(audit)
            all_blobs.append(_study_blob(study))
            role_warning_count += len(audit["warnings"])

            banned = study_banned_phrase_count(" ".join(str(v) for v in study.values() if isinstance(v, str)))
            assert banned == 0, (
                f'{case["role"]} / {question.get("mapped_skill") or "General"}: study material for '
                f'"{(question.get("question") or "")[:90]}" contains banned generic phrases '
                f"(expected 0, actual {banned})"
            )

            assert audit["passed"], (
                f'{case["role"]} / {question.get("mapped_skill") or "General"}: '
                f'{audit["errors"][0] if audit["errors"] else "study quality failed"} '
                f"(score={audit['score']}, components={audit['component_count']})"
            )

        role_warnings[case["role"]] = role_warning_count

    average_score = round(sum(a["score"] for a in all_audits) / len(all_audits), 1)
    print(f"Study-material quality: {len(all_audits)} modules checked, average score {average_score}")

    assert average_score >= AVERAGE_SCORE_FLOOR, (
        f"Average study-material quality score too low (expected >= {AVERAGE_SCORE_FLOOR}, actual {average_score})"
    )
    for role, warning_count in role_warnings.items():
        assert warning_count <= MAX_WARNINGS_PER_ROLE, (
            f"{role}: too many study-material warnings (expected <= {MAX_WARNINGS_PER_ROLE}, actual {warning_count})"
        )
