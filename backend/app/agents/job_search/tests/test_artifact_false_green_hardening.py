"""Artifact-level false-green root-cause hardening regressions (004E-E2.3 final).

Every test in this file reproduces a defect confirmed in the REAL regenerated
Markdown artifacts under
``project_review/samples/iteration_004e_f_final_regression`` — content that
was exported while the canonical gate reported ``all_clean = true``.

Classes:
  A — cross-domain scenario contamination (Delivery Driver / Warehouse Picker
      receiving the Barista drink-quality scenario)
  B — prose fragments promoted into professional terminology
  C — synthetic modifier suffix saturation reintroduced after overload repair
  D — cross-skill answer contamination (Python/Excel/Dashboarding answers
      closing as SQL analysis)
  E — title-only packs claiming captured posting facts
  F — generic template saturation across unrelated roles/skills
  G — generic standard placeholders satisfying explicit standard obligations
"""

from __future__ import annotations

import pytest

from app.agents.job_search.knowledge.coverage_planner import build_case_study_questions
from app.agents.job_search.knowledge.core_technical_content import (
    get_role_terminology_question,
    get_terminology_pack,
)
from app.agents.job_search.knowledge.expert_content_library import resolve_expert_content
from app.agents.job_search.knowledge.question_obligations import (
    extract_question_obligations,
    mark_synthetic_question,
)
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.claim_integrity import audit_pack_claim_integrity
from app.agents.job_search.quality.cross_domain_guard import audit_cross_domain_contamination
from app.agents.job_search.quality.key_term_quality_audit import is_valid_key_term
from app.agents.job_search.quality.question_obligation_coverage_audit import (
    audit_synthetic_overload,
    evaluate_answer_obligation_coverage,
    evaluate_study_obligation_coverage,
    is_synthetic_overload_failure,
)


# ---------------------------------------------------------------------------
# Shared fixtures / jobs
# ---------------------------------------------------------------------------

DELIVERY_DRIVER_JOB = {
    "title": "Delivery Driver",
    "description_raw": "Last-mile delivery and customer handoffs.",
    "responsibilities": ["Route planning", "Safe driving", "Proof of delivery"],
    "requirements": ["Driving licence", "Customer service"],
    "extracted_skills": [{"skill": "Route Planning"}, {"skill": "Customer Service"}],
}

WAREHOUSE_PICKER_JOB = {
    "title": "Warehouse Picker",
    "description_raw": "Pick and pack orders accurately during peak shifts.",
    "responsibilities": ["Order picking", "Stock rotation", "Packing accuracy"],
    "requirements": ["Order picking", "Attention to detail"],
    "extracted_skills": [{"skill": "Order Picking"}, {"skill": "Stock Control"}],
}

BARISTA_JOB = {
    "title": "Barista",
    "company_name": "Harbour Cafe",
    "description_raw": "Espresso preparation and rush-hour service.",
    "responsibilities": ["Espresso preparation", "HACCP hygiene controls"],
    "requirements": ["Coffee preparation", "Customer service"],
    "extracted_skills": [{"skill": "Coffee Preparation"}, {"skill": "HACCP"}],
}

# Artifact-exact job (FIXED_CROSS_SECTOR_CASES "Data Analyst").
DATA_ANALYST_JOB = {
    "title": "Data Analyst",
    "company_name": "Acme Analytics",
    "description_raw": "SQL dashboards, KPI reporting, and stakeholder communication.",
    "responsibilities": ["SQL dashboard creation", "Data quality checks"],
    "requirements": ["SQL", "Excel", "Stakeholder communication"],
    "extracted_skills": [{"skill": "SQL"}, {"skill": "Excel"}, {"skill": "Dashboarding"}],
}

# Same role with Python present — used for cross-skill answer alignment (Class D).
DATA_ANALYST_JOB_WITH_PYTHON = {
    **DATA_ANALYST_JOB,
    "extracted_skills": [
        {"skill": "SQL"},
        {"skill": "Python"},
        {"skill": "Excel"},
        {"skill": "Dashboarding"},
    ],
}

LAB_TECH_JOB = {
    "title": "Lab Technician",
    "description_raw": "Process lab samples and maintain safety records.",
    "responsibilities": ["Sample processing", "Equipment calibration", "Lab safety checks"],
    "requirements": ["Lab safety", "Sample handling"],
    "extracted_skills": [{"skill": "Sample Processing"}, {"skill": "Lab Safety"}],
}

MEP_JOB = {
    "title": "MEP Site Engineer",
    "description_raw": "Coordinate mechanical, electrical, and plumbing packages on site.",
    "responsibilities": ["MEP coordination", "Site supervision", "Snagging and handover"],
    "requirements": ["MEP systems", "Site coordination"],
    "extracted_skills": [{"skill": "MEP Coordination"}, {"skill": "Site Supervision"}],
}

GRAPHIC_DESIGNER_JOB = {
    "title": "Graphic Designer",
    "description_raw": "Brand assets, social creatives, and campaign visuals.",
    "responsibilities": ["Brand design", "Campaign visuals", "Client revisions"],
    "requirements": ["Adobe Creative Suite", "Brand design"],
    "extracted_skills": [{"skill": "Brand Design"}, {"skill": "Adobe Creative Suite"}],
}


_PACK_CACHE: dict = {}


def _generate(job, focus, difficulty: str = "mid"):
    """Generate a pack once per unique job (generation is expensive, ~10s).

    The cross-role fingerprint registry is cleared before each fresh generation
    so every cached pack is produced from a deterministic, isolated state —
    exactly how a single-pack production request behaves.
    """
    from app.agents.job_search import mock_data

    key = (job.get("title"), tuple(focus), difficulty)
    if key not in _PACK_CACHE:
        mock_data._GLOBAL_QUESTION_FINGERPRINTS.clear()
        qs = mock_generate_questions(dict(job), focus_areas=list(focus), difficulty=difficulty)
        mock_data._GLOBAL_QUESTION_FINGERPRINTS.clear()
        _PACK_CACHE[key] = [
            q for q in qs if q.get("model_answer") and not q.get("export_blocked")
        ]
    return _PACK_CACHE[key]


# ---------------------------------------------------------------------------
# Class A — cross-domain scenario contamination
# ---------------------------------------------------------------------------


class TestClassAScenarioDomainContamination:
    def test_delivery_driver_case_study_is_not_barista_scenario(self):
        """Exact artifact reproduction: DELIVERY-DRIVER-ROUTE-PLANNI-026."""
        qs = build_case_study_questions(dict(DELIVERY_DRIVER_JOB), ["Route Planning"])
        blob = " ".join(q["question"].lower() for q in qs)
        assert "drink quality" not in blob
        # The scenario must stay compatible with delivery work.
        assert any(
            tok in blob for tok in ("deliver", "route", "customer", "stop", "late", "complaint")
        )

    def test_warehouse_picker_case_study_is_not_barista_scenario(self):
        """Exact artifact reproduction: WAREHOUSE-PICKER-ORDER-PICKIN-025."""
        qs = build_case_study_questions(dict(WAREHOUSE_PICKER_JOB), ["Order Picking"])
        blob = " ".join(q["question"].lower() for q in qs)
        assert "drink quality" not in blob
        assert any(tok in blob for tok in ("pick", "stock", "pack", "order", "accuracy"))

    def test_barista_drink_quality_scenario_remains_valid(self):
        """Negative control: the hospitality scenario stays for hospitality roles."""
        qs = build_case_study_questions(dict(BARISTA_JOB), ["Coffee Preparation"])
        blob = " ".join(q["question"].lower() for q in qs)
        assert "drink quality" in blob
        audit = audit_cross_domain_contamination(
            blob, role="Barista", skill="Coffee Preparation", job=dict(BARISTA_JOB)
        )
        assert audit["cross_domain_contamination_hits"] == 0

    def test_delivery_driver_valid_route_scenario_stays_clean(self):
        text = (
            "During a peak delivery window as a Delivery Driver, several stops are running late "
            "and customers are calling about missed time slots. Walk me through how you re-plan "
            "the route, communicate delays, and protect proof-of-delivery accuracy."
        )
        audit = audit_cross_domain_contamination(
            text, role="Delivery Driver", skill="Route Planning", job=dict(DELIVERY_DRIVER_JOB)
        )
        assert audit["cross_domain_contamination_hits"] == 0

    def test_warehouse_picker_valid_picking_scenario_stays_clean(self):
        text = (
            "During a peak shift as a Warehouse Picker, pick accuracy drops and mis-picks rise. "
            "Walk me through how you diagnose the issue using Order Picking practices, protect "
            "stock rotation, and restore packing accuracy."
        )
        audit = audit_cross_domain_contamination(
            text, role="Warehouse Picker", skill="Order Picking", job=dict(WAREHOUSE_PICKER_JOB)
        )
        assert audit["cross_domain_contamination_hits"] == 0

    def test_injected_foreign_domain_scenario_is_detected(self):
        """The audit must independently catch a foreign-domain scenario anchor."""
        contaminated = (
            "During a busy rush as a Delivery Driver, drink quality drops and customer "
            "complaints rise. Walk me through how you diagnose and fix the issue using "
            "Route Planning practices."
        )
        audit = audit_cross_domain_contamination(
            contaminated,
            role="Delivery Driver",
            skill="Route Planning",
            job=dict(DELIVERY_DRIVER_JOB),
        )
        assert audit["cross_domain_contamination_hits"] > 0

    def test_injected_foreign_scenario_blocks_canonical_clean(self):
        from app.agents.job_search.quality.final_regression_audit import (
            metrics_are_clean,
            pack_failure_reasons,
        )

        metrics = {"cross_domain_contamination_hits": 1}
        assert not metrics_are_clean(metrics)
        assert "cross_domain_contamination_hits" in pack_failure_reasons(metrics)

    def test_generated_delivery_driver_pack_has_no_drink_quality(self):
        exportable = _generate(DELIVERY_DRIVER_JOB, ["Route Planning", "Customer Service"])
        blob = " ".join((q.get("question") or "") for q in exportable).lower()
        assert "drink quality" not in blob


# ---------------------------------------------------------------------------
# Class B — prose promoted into terminology
# ---------------------------------------------------------------------------

_MALFORMED_TERM_PREFIXES = (
    "clear scope and verification steps keep",
    "handover notes and revision records keep",
)


def _terms_from_pack(skill: str, role: str, resp: str) -> list[str]:
    pack = get_terminology_pack(skill, role, resp)
    return [str(t.get("term") or "").strip() for t in pack["terms"]]


class TestClassBTerminologyIntegrity:
    def test_data_analyst_terminology_question_has_no_prose_terms(self):
        """Exact artifact reproduction: DATA-ANALYST-CORE-TERMINO-TERM-016."""
        q = get_role_terminology_question(dict(DATA_ANALYST_JOB))
        assert q is not None
        lowered = q["question"].lower()
        for prefix in _MALFORMED_TERM_PREFIXES:
            assert prefix not in lowered
        for term in q["terminology_terms"]:
            assert is_valid_key_term(term["term"]), term["term"]

    def test_lab_technician_terminology_has_no_prose_terms(self):
        terms = _terms_from_pack("Sample Processing", "Lab Technician", "Sample processing")
        for term in terms:
            assert is_valid_key_term(term), term

    def test_mep_terminology_has_no_prose_terms(self):
        terms = _terms_from_pack("MEP Coordination", "MEP Site Engineer", "MEP coordination")
        for term in terms:
            assert is_valid_key_term(term), term

    def test_malformed_terms_do_not_duplicate_across_aggregation(self):
        """Duplicate malformed-term aggregation: the same clipped prose fragment
        must not appear (once per skill) in the consolidated terminology question."""
        q = get_role_terminology_question(dict(DATA_ANALYST_JOB))
        assert q is not None
        names = [t["term"].strip().lower() for t in q["terminology_terms"]]
        assert len(names) == len(set(names))
        for prefix in _MALFORMED_TERM_PREFIXES:
            assert not any(n.startswith(prefix) for n in names)

    def test_legitimate_multiword_terminology_preserved(self):
        for term in (
            "root cause analysis",
            "continuous integration",
            "data quality",
            "route planning",
            "medication reconciliation",
            "load calculation",
        ):
            assert is_valid_key_term(term), term

    def test_prose_fragments_rejected_structurally(self):
        """Structural rejection — clipped clauses, not a phrase blacklist."""
        for fragment in (
            "Clear scope and verification steps keep",
            "Handover notes and revision records keep",
            "Dashboarding work must stay auditable so",
            "Quality improves when checks are explicit",
            "records keep teams aligned across shifts",
        ):
            assert not is_valid_key_term(fragment), fragment

    def test_terminology_defect_blocks_canonical_clean(self):
        from app.agents.job_search.quality.final_regression_audit import (
            CANONICAL_FAILURE_METRIC_KEYS,
            metrics_are_clean,
        )

        assert "terminology_integrity_failure_count" in CANONICAL_FAILURE_METRIC_KEYS
        assert not metrics_are_clean({"terminology_integrity_failure_count": 1})

    def test_terminology_integrity_audit_flags_malformed_final_question(self):
        from app.agents.job_search.quality.terminology_integrity_audit import (
            audit_terminology_integrity,
        )

        bad_question = {
            "question_type": "terminology",
            "category": "technical",
            "question": (
                "As a Data Analyst, define and explain these core professional terms: SQL, "
                "Excel, Clear scope and verification steps keep, Handover notes and revision "
                "records keep."
            ),
            "terminology_terms": [
                {"term": "SQL", "definition": "Structured Query Language"},
                {
                    "term": "Clear scope and verification steps keep",
                    "definition": "Clear scope and verification steps keep work predictable.",
                },
            ],
            "study_material": {},
        }
        metrics = audit_terminology_integrity([bad_question])
        assert metrics["terminology_integrity_failure_count"] > 0

        good_question = {
            "question_type": "terminology",
            "category": "technical",
            "question": (
                "As a Data Analyst, define and explain these core professional terms: SQL, "
                "Excel, data quality, root cause analysis."
            ),
            "terminology_terms": [
                {"term": "SQL", "definition": "Structured Query Language"},
                {"term": "data quality", "definition": "Fitness of data for its intended use."},
            ],
            "study_material": {},
        }
        metrics = audit_terminology_integrity([good_question])
        assert metrics["terminology_integrity_failure_count"] == 0


# ---------------------------------------------------------------------------
# Class C — synthetic modifier suffix saturation
# ---------------------------------------------------------------------------


class TestClassCModifierSuffixSaturation:
    def test_atomic_synthetic_hr_remains_atomic(self):
        exportable = _generate(GRAPHIC_DESIGNER_JOB, ["Brand Design"])
        hr = [q for q in exportable if (q.get("question_type") or "").startswith("hr_")]
        assert hr
        for q in hr:
            assert "include one concrete" not in q["question"].lower(), q["question"]

    def test_behavioral_questions_not_forced_into_triple_modifier(self):
        """Exact artifact reproduction: Graphic Designer behavioral questions carried
        'Include one concrete ... metric, one governing standard/protocol, and one
        failure mode' purely as a uniqueness device."""
        exportable = _generate(GRAPHIC_DESIGNER_JOB, ["Brand Design"])
        behavioral = [q for q in exportable if q.get("category") == "behavioral"]
        assert behavioral
        for q in behavioral:
            assert "include one concrete" not in q["question"].lower(), q["question"]

    def test_daily_routine_not_forced_into_triple_modifier(self):
        exportable = _generate(GRAPHIC_DESIGNER_JOB, ["Brand Design"])
        daily = [q for q in exportable if q.get("category") == "daily_routine"]
        for q in daily:
            assert "include one concrete" not in q["question"].lower(), q["question"]

    def test_uniqueness_pass_does_not_collide_with_itself(self):
        """Re-finalisation of the same pack must not append suffixes to every
        question via self-collision in the global fingerprint registry."""
        exportable = _generate(GRAPHIC_DESIGNER_JOB, ["Brand Design"])
        suffixed = [
            q for q in exportable if "include one concrete" in (q.get("question") or "").lower()
        ]
        assert not suffixed, [q["question"][:90] for q in suffixed[:3]]

    def test_genuine_technical_question_may_retain_modifiers(self):
        """Negative control: an authored technical question with explicit modifier
        demands keeps them (extraction sees them; no stripping)."""
        q = mark_synthetic_question(
            {
                "category": "technical",
                "question_type": "technical_method",
                "question": (
                    "How would you size a distribution cable for a new machine feed? "
                    "Include one concrete Cable Sizing metric, one governing standard/protocol, "
                    "and one failure mode you would guard against."
                ),
                "skill_tag": "Cable Sizing",
            }
        )
        profile = extract_question_obligations(q, {})
        assert "metric" in profile.obligations
        assert "standard_or_protocol" in profile.obligations
        assert "failure_mode" in profile.obligations
        assert not profile.synthetic_overload

    def test_employer_provided_hybrid_preserves_required_modifiers(self):
        q = {
            "category": "technical",
            "question_type": "technical_method",
            "question_origin": "employer_provided",
            "question": (
                "Why do you want this role, and how would you improve our reporting? "
                "Include one concrete KPI metric and one governing standard you would follow."
            ),
        }
        profile = extract_question_obligations(q, {})
        assert "metric" in profile.obligations
        assert not profile.synthetic_overload

    def test_late_stage_modifier_reintroduction_is_caught(self):
        """The FINAL exported question text is audited: a synthetic behavioral
        question that acquired the forced triple modifier late must register as
        synthetic overload."""
        q = mark_synthetic_question(
            {
                "category": "behavioral",
                "question_type": "behavioral",
                "question": (
                    "Describe one complex assignment in Graphic Designer work where your "
                    "planning prevented failure. In this role-specific case, address: Graphic "
                    "Designer context: Brand design. Include one concrete core competency "
                    "metric, one governing standard/protocol, and one failure mode relevant to "
                    "Graphic Designer context: Brand design."
                ),
                "skill_tag": None,
            }
        )
        assert is_synthetic_overload_failure(q, dict(GRAPHIC_DESIGNER_JOB))
        metrics = audit_synthetic_overload([q], dict(GRAPHIC_DESIGNER_JOB))
        assert metrics["synthetic_overload_failure_count"] == 1

    def test_final_exported_pack_is_overload_free(self):
        exportable = _generate(GRAPHIC_DESIGNER_JOB, ["Brand Design"])
        metrics = audit_synthetic_overload(exportable, dict(GRAPHIC_DESIGNER_JOB))
        assert metrics["synthetic_overload_failure_count"] == 0


# ---------------------------------------------------------------------------
# Class D — cross-skill answer contamination
# ---------------------------------------------------------------------------


class TestClassDCrossSkillAnswerContamination:
    def _pack(self):
        return _generate(DATA_ANALYST_JOB_WITH_PYTHON, ["Python", "Excel", "Dashboarding"])

    def test_python_answer_does_not_close_as_sql_analysis(self):
        exportable = self._pack()
        python_qs = [
            q
            for q in exportable
            if (q.get("skill_tag") or "").lower() == "python"
            and "sql" not in (q.get("question") or "").lower()
        ]
        assert python_qs
        for q in python_qs:
            closing = (q.get("model_answer") or "").strip().lower()[-220:]
            assert "reliable sql analysis" not in closing, q["question"][:90]

    def test_excel_answer_not_sql_dominant(self):
        exportable = self._pack()
        excel_qs = [
            q
            for q in exportable
            if (q.get("skill_tag") or "").lower() == "excel"
            and "sql" not in (q.get("question") or "").lower()
        ]
        assert excel_qs
        for q in excel_qs:
            closing = (q.get("model_answer") or "").strip().lower()[-220:]
            assert "reliable sql analysis" not in closing, q["question"][:90]

    def test_dashboarding_answer_not_silently_rewritten_as_sql(self):
        exportable = self._pack()
        dash_qs = [
            q
            for q in exportable
            if "dashboard" in (q.get("skill_tag") or "").lower()
            and "sql" not in (q.get("question") or "").lower()
        ]
        assert dash_qs
        for q in dash_qs:
            closing = (q.get("model_answer") or "").strip().lower()[-220:]
            assert "reliable sql analysis" not in closing, q["question"][:90]

    def test_sql_question_keeps_sql_closing(self):
        """Negative control: SQL-primary questions may keep the SQL closing."""
        exportable = self._pack()
        sql_qs = [q for q in exportable if (q.get("skill_tag") or "").lower() == "sql"]
        assert sql_qs  # SQL closing remains legitimate for SQL questions.

    def test_explicit_cross_skill_question_may_discuss_both(self):
        from app.agents.job_search.quality.cross_skill_alignment_audit import (
            is_cross_skill_answer_contamination,
        )

        q = {
            "skill_tag": "Python",
            "question": (
                "How would you combine SQL extraction with Python post-processing for a "
                "weekly report, and how do you validate the handoff between the two?"
            ),
            "model_answer": (
                "I would extract with SQL, validate row counts, then post-process in Python "
                "with tested transforms. In an interview, I would show that I can build "
                "reliable SQL analysis with sound joins alongside tested Python transforms."
            ),
        }
        assert not is_cross_skill_answer_contamination(q, dict(DATA_ANALYST_JOB_WITH_PYTHON))

    def test_injected_cross_skill_contamination_blocks_canonical_clean(self):
        from app.agents.job_search.quality.cross_skill_alignment_audit import (
            audit_cross_skill_answer_alignment,
        )
        from app.agents.job_search.quality.final_regression_audit import (
            CANONICAL_FAILURE_METRIC_KEYS,
            metrics_are_clean,
        )

        contaminated = {
            "skill_tag": "Python",
            "question": "Explain how you structure a Python data-cleaning script for reuse.",
            "model_answer": (
                "I would modularise the cleaning steps and add unit tests. In an interview, "
                "I would show that I can build reliable SQL analysis with sound joins, data "
                "quality controls, and performance awareness."
            ),
        }
        metrics = audit_cross_skill_answer_alignment([contaminated], dict(DATA_ANALYST_JOB_WITH_PYTHON))
        assert metrics["cross_skill_answer_contamination_failure_count"] == 1
        assert "cross_skill_answer_contamination_failure_count" in CANONICAL_FAILURE_METRIC_KEYS
        assert not metrics_are_clean({"cross_skill_answer_contamination_failure_count": 1})


# ---------------------------------------------------------------------------
# Class E — title-only unsupported posting claims
# ---------------------------------------------------------------------------

_CAPTURED_FACT_CLAIMS = (
    "skills listed",
    "listed responsibilities",
    "responsibilities listed",
    "duties listed",
    "listed duties",
    "posting centres on",
    "posting centers on",
    "based on what you've read",
    "what you have read",
)


class TestClassETitleOnlyClaimIntegrity:
    def test_mystery_role_title_only_makes_no_captured_posting_claims(self):
        """Exact artifact reproduction: Mystery Role, coverage_score = 0."""
        exportable = _generate({"title": "Mystery Role"}, [])
        assert exportable
        for q in exportable:
            blob = " ".join(
                [
                    q.get("question") or "",
                    q.get("model_answer") or "",
                    q.get("answer_explanation") or "",
                ]
            ).lower()
            for marker in _CAPTURED_FACT_CLAIMS:
                assert marker not in blob, (marker, (q.get("question") or "")[:90])

    def test_title_only_motivation_answer_has_honest_framing(self):
        exportable = _generate({"title": "Mystery Role"}, [])
        motivation = [
            q
            for q in exportable
            if (q.get("question_type") or "") in {"hr_motivation"}
            or "interested" in (q.get("question") or "").lower()
            or "excites" in (q.get("question") or "").lower()
        ]
        assert motivation
        for q in motivation:
            answer = (q.get("model_answer") or "").lower()
            assert "responsibilities listed" not in answer
            assert "skills listed" not in answer

    def test_title_only_claim_violation_is_counted(self):
        job = {"title": "Mystery Role"}
        contaminated = [
            {
                "question": "Why are you interested in this Mystery Role?",
                "question_type": "hr_motivation",
                "category": "hr",
                "model_answer": (
                    "I am interested because the posting centres on core duties and the skills "
                    "listed — I can deliver on the responsibilities listed."
                ),
                "study_material": {},
            }
        ]
        metrics = audit_pack_claim_integrity(contaminated, job)
        assert metrics["thin_input_specificity_violation_count"] > 0

    def test_rich_posting_may_reference_captured_duties(self):
        """Negative control: a rich posting genuinely has listed responsibilities."""
        job = dict(DATA_ANALYST_JOB)
        questions = [
            {
                "question": "Why are you interested in this Data Analyst role?",
                "question_type": "hr_motivation",
                "category": "hr",
                "model_answer": (
                    "I am interested because the posting centres on sql dashboard creation and "
                    "the skills listed — especially SQL and Excel."
                ),
                "study_material": {},
            }
        ]
        metrics = audit_pack_claim_integrity(questions, job)
        assert metrics["thin_input_specificity_violation_count"] == 0

    def test_thin_input_claim_violation_blocks_canonical_clean(self):
        from app.agents.job_search.quality.final_regression_audit import metrics_are_clean

        assert not metrics_are_clean({"thin_input_specificity_violation_count": 1})


# ---------------------------------------------------------------------------
# Class F — generic template saturation
# ---------------------------------------------------------------------------


class TestClassFTemplateSaturation:
    def test_saturated_template_skeleton_is_flagged(self):
        from app.agents.job_search.quality.template_saturation_audit import (
            audit_template_saturation,
        )

        questions = []
        for skill in ("SQL", "Excel", "Dashboarding", "Python", "Reporting", "Modelling"):
            questions.append(
                {
                    "skill_tag": skill,
                    "question": f"Explain {skill} for a Data Analyst.",
                    "study_material": {
                        "principles": [
                            f"Clear scope and verification steps keep {skill} work predictable in Data Analyst settings.",
                            "Handover notes and revision records keep teams aligned across shifts and trades.",
                        ],
                        "overview": f"Overview of {skill}.",
                    },
                }
            )
        metrics = audit_template_saturation(
            questions, role="Data Analyst", skills=[s for s in ("SQL", "Excel", "Dashboarding", "Python", "Reporting", "Modelling")]
        )
        assert metrics["generic_template_saturation_failure_count"] > 0

    def test_single_occurrence_is_not_a_defect(self):
        from app.agents.job_search.quality.template_saturation_audit import (
            audit_template_saturation,
        )

        questions = [
            {
                "skill_tag": "SQL",
                "question": "Explain SQL.",
                "study_material": {
                    "principles": [
                        "Clear scope and verification steps keep SQL work predictable in Data Analyst settings.",
                    ],
                    "overview": "Overview of SQL.",
                },
            },
            {
                "skill_tag": "Excel",
                "question": "Explain Excel.",
                "study_material": {
                    "principles": [
                        "Reconcile lookup ranges against control totals before publishing.",
                    ],
                    "overview": "Overview of Excel.",
                },
            },
        ]
        metrics = audit_template_saturation(questions, role="Data Analyst", skills=["SQL", "Excel"])
        assert metrics["generic_template_saturation_failure_count"] == 0

    def test_fallback_facts_are_not_verbatim_skeletons_across_skills(self):
        """Producer-level: two unrelated fallback skills must not share the exact
        generic fact skeleton (role/skill token substitution only)."""
        import re

        def _skeleton(text: str, skill: str, role: str) -> str:
            out = text.lower()
            for token in (skill.lower(), role.lower()):
                out = out.replace(token, "@")
            return re.sub(r"\s+", " ", out).strip()

        exp_a = resolve_expert_content("MEP Coordination", "MEP Site Engineer", "MEP coordination")
        exp_b = resolve_expert_content("Sample Processing", "Lab Technician", "Sample processing")
        facts_a = {
            _skeleton(f, "MEP Coordination", "MEP Site Engineer") for f in exp_a.get("key_facts") or []
        }
        facts_b = {
            _skeleton(f, "Sample Processing", "Lab Technician") for f in exp_b.get("key_facts") or []
        }
        shared = facts_a & facts_b
        assert not shared, shared

    def test_template_saturation_blocks_canonical_clean(self):
        from app.agents.job_search.quality.final_regression_audit import (
            CANONICAL_FAILURE_METRIC_KEYS,
            metrics_are_clean,
        )

        assert "generic_template_saturation_failure_count" in CANONICAL_FAILURE_METRIC_KEYS
        assert not metrics_are_clean({"generic_template_saturation_failure_count": 1})


# ---------------------------------------------------------------------------
# Class G — weak standard/protocol satisfaction
# ---------------------------------------------------------------------------


def _explicit_standard_question():
    return mark_synthetic_question(
        {
            "category": "technical",
            "question_type": "standards",
            "question": (
                "Which governing standard applies to sample handling in this Lab Technician "
                "role, and how do you verify compliance during Sample Processing?"
            ),
            "skill_tag": "Sample Processing",
        }
    )


class TestClassGStandardPlaceholderSatisfaction:
    def test_applicable_standards_fails_explicit_standard_obligation(self):
        q = _explicit_standard_question()
        q["model_answer"] = (
            "I would process samples carefully and check records. For compliance, I would "
            "rely on applicable standards. I would evidence the work through records and "
            "escalation where needed."
        )
        result = evaluate_answer_obligation_coverage(q, dict(LAB_TECH_JOB))
        assert "missing_standard_or_protocol" in result["failures"]

    def test_named_standard_passes_explicit_standard_obligation(self):
        q = _explicit_standard_question()
        q["model_answer"] = (
            "I would anchor verification to ISO 15189 and the laboratory's documented SOP for "
            "chain of custody. Calibration records and QC sign-off evidence the work, and any "
            "deviation is escalated with a documented corrective action."
        )
        result = evaluate_answer_obligation_coverage(q, dict(LAB_TECH_JOB))
        assert "missing_standard_or_protocol" not in result["failures"]

    def test_evidence_unavailable_path_stays_honest(self):
        """When no named standard is available, the renderer must not claim
        reliance on unnamed 'applicable standards' — it makes the gap explicit."""
        from app.agents.job_search.knowledge.answer_builders import render_compliance_naturally

        text = render_compliance_naturally(["Default standards"], [], role_family="default")
        lowered = text.lower()
        assert "rely on default standards" not in lowered
        assert "rely on applicable standards" not in lowered
        # Honest-gap framing instead of a fake satisfied obligation.
        assert "confirm" in lowered or "no specific" in lowered or "not specified" in lowered

    def test_honest_gap_satisfies_explicit_obligation_without_hallucination(self):
        q = _explicit_standard_question()
        q["model_answer"] = (
            "No single published standard was specified for this work in the posting; I would "
            "confirm which standard or local SOP governs sample handling before starting, and "
            "follow the documented procedure with calibration and chain-of-custody checks."
        )
        result = evaluate_answer_obligation_coverage(q, dict(LAB_TECH_JOB))
        assert "missing_standard_or_protocol" not in result["failures"]

    def test_incidental_standard_context_creates_no_false_requirement(self):
        """Negative control: incidental mention of working 'under GDPR' does not
        turn a behavioral question into a standard-obligated question."""
        q = mark_synthetic_question(
            {
                "category": "behavioral",
                "question_type": "behavioral",
                "question": (
                    "Tell me about a time you delivered a reporting project under GDPR "
                    "constraints with a tight deadline."
                ),
                "skill_tag": None,
            }
        )
        profile = extract_question_obligations(q, {})
        assert "standard_or_protocol" not in profile.obligations

    def test_study_material_also_checked_for_standard_placeholder(self):
        q = _explicit_standard_question()
        q["model_answer"] = "See study."
        q["study_material"] = {
            "core_idea": "Standards matter.",
            "step_by_step_method": ["Check the applicable standards", "Record results"],
            "interview_application": "For compliance, I would rely on applicable standards.",
        }
        result = evaluate_study_obligation_coverage(q, dict(LAB_TECH_JOB))
        assert "missing_study_standard_or_protocol" in result["failures"]
