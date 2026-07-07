"""Claim integrity tests (Iteration 004E-E2.2)."""

from __future__ import annotations

from app.agents.job_search.quality.claim_integrity import (
    audit_claim_integrity,
    audit_pack_claim_integrity,
    classify_claim_support,
    collect_user_claim_context,
    detect_unsupported_numeric_claims,
    detect_unsupported_personal_claims,
    rewrite_or_flag_unsupported_claims,
)


def test_explicit_user_claim_usable_without_evidence() -> None:
    job = {
        "title": "Electrical Engineer",
        "responsibilities": ["Supervised electrical installations"],
        "extracted_skills": [{"skill": "AutoCAD"}],
        "profile_summary": "Worked as an Electrical Engineer using AutoCAD on installation projects.",
    }
    text = (
        "In my electrical engineering work I supervised installation activities and used AutoCAD "
        "to coordinate cable routes."
    )
    assert classify_claim_support(job) in {"claimed", "profile_supported"}
    assert detect_unsupported_personal_claims(text, job) == []


def test_no_information_is_unknown_not_false() -> None:
    job = {"title": "Cloud Engineer"}
    ctx = collect_user_claim_context(job)
    assert ctx["has_explicit_experience"] is False
    assert classify_claim_support(job) == "unknown"


def test_role_requirement_is_not_user_biography() -> None:
    job = {
        "title": "Team Lead",
        "requirements": ["Must manage teams of 25 people"],
    }
    text = "I managed 25 people across three regions and improved delivery by 31%."
    assert detect_unsupported_personal_claims(text, job)
    assert detect_unsupported_numeric_claims(text, job)


def test_uploaded_evidence_is_not_automatically_verified() -> None:
    job = {
        "title": "Analyst",
        "evidence_items": [{"label": "Experience letter"}],
    }
    assert classify_claim_support(job) == "evidence_backed"
    assert classify_claim_support(job) != "verified"


def test_explicit_user_metric_allowed() -> None:
    job = {
        "title": "Operations Analyst",
        "achievements": ["Reduced turnaround time by 20%"],
    }
    text = "I reduced turnaround time by 20% after redesigning the handoff checklist."
    assert detect_unsupported_numeric_claims(text, job) == []


def test_invented_metric_blocked() -> None:
    job = {"title": "Mystery Role"}
    text = "I improved quality by 31% and managed 25 employees."
    rewritten, meta = rewrite_or_flag_unsupported_claims(text, job)
    assert meta["unsupported_numeric_claim_count"] >= 1 or "31%" not in rewritten


def test_title_only_unsupported_biography_rewritten() -> None:
    job = {"title": "Mystery Role"}
    text = "In a previous Mystery Role assignment, we delivered on time and measurable outcomes improved."
    rewritten, meta = rewrite_or_flag_unsupported_claims(text, job)
    assert "previous Mystery Role assignment" not in rewritten
    assert meta["rewritten_for_claim_integrity"] is True


def test_audit_counts_unsupported_biography() -> None:
    job = {"title": "HR Assistant"}
    audit = audit_claim_integrity("In a previous HR Assistant assignment I led a team.", job)
    assert audit["unsupported_personal_claim_count"] >= 1


# --- Provenance: opportunity/job data must never establish personal biography ---


def test_posting_description_and_responsibilities_do_not_create_claimed() -> None:
    job = {
        "title": "Data Analyst",
        "description_raw": "Build dashboards and KPI reporting.",
        "responsibilities": ["SQL dashboard creation", "Daily data quality checks"],
    }
    ctx = collect_user_claim_context(job)
    assert ctx["has_explicit_experience"] is False
    assert classify_claim_support(job) == "unknown"


def test_two_responsibilities_do_not_create_profile_supported() -> None:
    job = {
        "title": "Data Analyst",
        "responsibilities": ["SQL dashboards", "Stakeholder reporting"],
    }
    assert classify_claim_support(job) not in {"claimed", "profile_supported"}


def test_requirements_do_not_create_personal_experience() -> None:
    job = {"title": "Cloud Engineer", "requirements": ["5 years AWS", "Kubernetes"]}
    assert collect_user_claim_context(job)["has_explicit_experience"] is False
    assert classify_claim_support(job) == "unknown"


def test_company_research_does_not_create_personal_experience() -> None:
    job = {
        "title": "Data Analyst",
        "company_research": {"legal_name": "Northline Analytics Ltd"},
    }
    assert collect_user_claim_context(job)["has_explicit_experience"] is False
    assert classify_claim_support(job) == "unknown"


def test_url_extracted_responsibilities_do_not_create_personal_experience() -> None:
    job = {
        "title": "Data Analyst",
        "job_posting_extraction": {"source_url": "https://example.com/jobs/1"},
        "responsibilities": ["SQL dashboard creation"],
    }
    assert collect_user_claim_context(job)["has_explicit_experience"] is False
    assert classify_claim_support(job) == "unknown"


def test_profile_summary_creates_claimed_support() -> None:
    job = {"title": "Data Analyst", "profile_summary": "Worked as a Data Analyst using SQL."}
    assert classify_claim_support(job) in {"claimed", "profile_supported"}


def test_work_history_and_profile_create_profile_supported() -> None:
    job = {
        "title": "Data Analyst",
        "profile_summary": "Data Analyst with dashboard experience.",
        "work_experiences": [{"title": "Data Analyst", "company": "Acme"}],
    }
    assert classify_claim_support(job) == "profile_supported"


# --- Broadened biography detection (many first-person event verbs) ---


def test_various_first_person_events_detected_when_unsupported() -> None:
    job = {"title": "Mystery Role"}
    for verb in ("reviewed", "adjusted", "diagnosed", "configured", "deployed", "tested", "rebuilt"):
        text = f"I {verb} the system during the last release."
        assert detect_unsupported_personal_claims(text, job), verb


def test_collective_team_event_detected() -> None:
    job = {"title": "Mystery Role"}
    assert detect_unsupported_personal_claims("The team delivered the migration ahead of schedule.", job)


def test_team_hit_faced_encountered_detected() -> None:
    """§18: team-event framing beyond 'delivered' must be caught."""
    job = {"title": "Mystery Role"}
    for text in (
        "The team hit its target three weeks early.",
        "The team faced a major outage last quarter.",
        "The team encountered a critical defect in production.",
    ):
        assert detect_unsupported_personal_claims(text, job), text


def test_assignment_and_release_framing_detected() -> None:
    """§18: assignment/release event framing without a first-person 'I' start."""
    job = {"title": "Mystery Role"}
    for text in (
        "On an assignment last year I led the rollout.",
        "During a release we shipped the hotfix overnight.",
        "During a project the scope changed and we re-planned delivery.",
    ):
        assert detect_unsupported_personal_claims(text, job), text


def test_second_person_historical_framing_detected() -> None:
    """§18: 'You specifically ...' historical framing must not be treated as generic."""
    job = {"title": "Mystery Role"}
    assert detect_unsupported_personal_claims(
        "You specifically avoided the deadlock by reordering writes.", job
    )


def test_legitimate_hypothetical_example_not_flagged() -> None:
    """§18 negative control: a clearly hypothetical example is safe."""
    job = {"title": "Mystery Role"}
    text = (
        "Hypothetical example: imagine a service that could reduce latency to 180 ms with caching."
    )
    assert detect_unsupported_personal_claims(text, job) == []
    assert detect_unsupported_numeric_claims(text, job) == []


def test_mixed_factual_and_hypothetical_clause_scope() -> None:
    """§6/§18: a trailing hypothetical clause must not sanitize a leading unsupported claim."""
    job = {"title": "Mystery Role"}
    text = "We reduced latency to 180 ms. Hypothetical example: another team could test caching."
    assert detect_unsupported_numeric_claims(text, job)
    rewritten, meta = rewrite_or_flag_unsupported_claims(text, job)
    assert meta["rewritten_for_claim_integrity"] is True
    assert "reduced latency to 180 ms" not in rewritten.lower()
    assert "hypothetical" in rewritten.lower()


# --- Numeric achievement detection (broadened) ---


def test_before_after_seconds_flagged() -> None:
    job = {"title": "Data Analyst"}
    assert detect_unsupported_numeric_claims("Cut query runtime from 48 seconds to 6 seconds.", job)


def test_percentage_transition_flagged() -> None:
    job = {"title": "Teaching Assistant"}
    assert detect_unsupported_numeric_claims("Attainment improved from 58% to 76%.", job)


def test_percentile_latency_flagged() -> None:
    job = {"title": "DevOps Engineer"}
    assert detect_unsupported_numeric_claims("P95 dropped to 180 ms after the change.", job)


def test_signed_percentage_delta_flagged() -> None:
    job = {"title": "Data Analyst"}
    assert detect_unsupported_numeric_claims("Storage cost +4% after the redesign.", job)


def test_headcount_with_event_flagged() -> None:
    job = {"title": "Team Lead"}
    assert detect_unsupported_numeric_claims("I managed 25 engineers across three regions.", job)


def test_calculation_question_spec_not_flagged() -> None:
    """Neutral calculation/question-spec numbers must NOT be treated as claims."""
    job = {"title": "DevOps Engineer"}
    assert detect_unsupported_numeric_claims(
        "Service must handle 2000 requests in 50 ms during peak.", job
    ) == []


def test_standard_version_number_not_flagged() -> None:
    job = {"title": "Data Analyst"}
    assert detect_unsupported_numeric_claims("Normalise the table to 3NF before loading.", job) == []


def test_returned_below_percentage_flagged() -> None:
    """§7/§18: operational result phrasing like 'returned below 0.2%'."""
    job = {"title": "Site Reliability Engineer"}
    assert detect_unsupported_numeric_claims("Error rate returned below 0.2% after the fix.", job)


def test_down_to_latency_flagged() -> None:
    """§7/§18: 'came down to 180 ms' operational latency claim."""
    job = {"title": "Backend Engineer"}
    assert detect_unsupported_numeric_claims("Latency came down to 180 ms.", job)


def test_throughput_and_transactions_flagged() -> None:
    """§7/§18: throughput/QPS/transaction-scale operational claims."""
    job = {"title": "Platform Engineer"}
    assert detect_unsupported_numeric_claims("Throughput rose to 5000 QPS during peak.", job)
    assert detect_unsupported_numeric_claims("We handled 12000 transactions per second.", job)


# --- Coaching rewrite grammar (no malformed conjugations) ---


def test_coaching_rewrite_has_no_malformed_conjugations() -> None:
    job = {"title": "Data Analyst"}
    text = (
        "I would start by checking the data. I will build a validation step. "
        "I can deploy the change. I fixed the join and cut runtime from 48 seconds to 6 seconds."
    )
    rewritten, meta = rewrite_or_flag_unsupported_claims(text, job)
    low = rewritten.lower()
    for bad in ("you could would", "you could fixed", "you could can", "the team could delivered"):
        assert bad not in low
    assert meta["rewritten_for_claim_integrity"] is True


# --- Recursive audit reaches nested lists/dicts ---


def test_recursive_audit_detects_nested_unsupported_claim() -> None:
    job = {"title": "Financial Analyst"}
    question = {
        "question": "Explain your approach.",
        "model_answer": "A strong answer explains the method.",
        "study_material": {
            "common_mistakes": [
                "Rushing verification.",
                "In a previous Financial Analyst assignment I rebuilt the model and improved accuracy by 30%.",
            ],
            "advanced_extension": {
                "notes": ["We delivered the forecast two weeks early."]
            },
        },
    }
    audit = audit_pack_claim_integrity([question], job)
    assert audit["unsupported_personal_claim_count"] >= 1
