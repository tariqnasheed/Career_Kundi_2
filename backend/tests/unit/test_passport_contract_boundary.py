"""
0052-F1 — Passport contract boundary unit tests.

Covers enums, defaults, record-status axes, taxonomy references,
Profile field compatibility, validation, serialization, and import hygiene.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.career_passport import (
    CareerPassportContract,
    PassportCredentialRef,
    PassportCredentialType,
    PassportEducation,
    PassportExperience,
    PassportProfile,
    PassportProject,
    PassportRecordMeta,
    PassportSectionKey,
    PassportSectionPreference,
    PassportSkill,
    PassportSourceStatus,
    PassportTarget,
    PassportTaxonomyKind,
    PassportTaxonomyReference,
    PassportVisibility,
    default_section_preferences,
)
from app.platform.claims.status import SupportStatus, VerificationStatus
from app.schemas.profile import (
    CertificationIn,
    EducationIn,
    ProfileUpdate,
    ProjectIn,
    SkillIn,
    WorkExperienceIn,
)
from app.taxonomy.contracts import ConfidenceLevel, PathwayType, SeniorityLevel, SourceType


PASSPORT_ROOT = Path(__file__).resolve().parents[2] / "app" / "career_passport"


# ---------------------------------------------------------------------------
# Enums and defaults
# ---------------------------------------------------------------------------


def test_passport_visibility_values():
    assert {m.value for m in PassportVisibility} == {"private"}


def test_section_key_values():
    assert {m.value for m in PassportSectionKey} == {
        "profile",
        "experience",
        "education",
        "projects",
        "skills",
        "credentials",
        "targets",
    }


def test_source_status_values():
    assert {m.value for m in PassportSourceStatus} == {
        "user_asserted",
        "suggested_accepted",
        "unknown",
        "not_provided",
    }


def test_taxonomy_kind_values():
    assert {m.value for m in PassportTaxonomyKind} == {"role", "skill"}


def test_credential_type_values():
    assert {m.value for m in PassportCredentialType} == {
        "certification",
        "license",
        "course_certificate",
        "education_award",
        "professional_membership",
        "other",
    }


def test_aggregate_defaults_private_subject_none_version_one():
    passport = CareerPassportContract()
    assert passport.visibility == PassportVisibility.PRIVATE
    assert passport.subject_id is None
    assert passport.version == 1


def test_default_section_order_is_deterministic():
    prefs = default_section_preferences()
    assert [p.section.value for p in prefs] == [
        "profile",
        "experience",
        "education",
        "projects",
        "skills",
        "credentials",
        "targets",
    ]
    assert [p.order_index for p in prefs] == list(range(7))
    assert all(p.enabled for p in prefs)


# ---------------------------------------------------------------------------
# Strict boundary
# ---------------------------------------------------------------------------


def test_unknown_extra_fields_rejected():
    with pytest.raises(ValidationError):
        CareerPassportContract(owner_user_id="x")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        PassportProfile(summary="frontend-only")  # type: ignore[call-arg]


def test_aggregate_has_no_owner_or_public_share_fields():
    fields = set(CareerPassportContract.model_fields)
    assert "owner_user_id" not in fields
    assert "public_url" not in fields
    assert "organization_id" not in fields
    assert "sharing" not in fields
    assert "claims" not in fields
    assert "evidence" not in fields


def test_empty_passport_is_valid():
    passport = CareerPassportContract()
    assert passport.experiences == []
    assert passport.education == []
    assert passport.projects == []
    assert passport.skills == []
    assert passport.credentials == []
    assert passport.targets == []


def test_optional_sections_not_required():
    passport = CareerPassportContract(targets=[PassportTarget(target_role_text="PM")])
    assert len(passport.targets) == 1
    assert passport.experiences == []


# ---------------------------------------------------------------------------
# Record status
# ---------------------------------------------------------------------------


def test_record_meta_defaults():
    meta = PassportRecordMeta()
    assert meta.source_status == PassportSourceStatus.USER_ASSERTED
    assert meta.support_status == SupportStatus.NOT_PROVIDED
    assert meta.verification_status == VerificationStatus.UNVERIFIED


@pytest.mark.parametrize(
    "status",
    [
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.CONFLICTING,
        VerificationStatus.UNKNOWN,
    ],
)
def test_verification_status_rejected(status: VerificationStatus):
    with pytest.raises(ValidationError):
        PassportRecordMeta(verification_status=status)


@pytest.mark.parametrize(
    "status",
    [
        SupportStatus.SOURCE_LINKED,
        SupportStatus.EVIDENCE_BACKED,
        SupportStatus.ASSESSMENT_DEMONSTRATED,
        SupportStatus.UNKNOWN,
    ],
)
def test_forbidden_support_status_rejected(status: SupportStatus):
    with pytest.raises(ValidationError):
        PassportRecordMeta(support_status=status)


def test_suggested_accepted_cannot_carry_profile_supported():
    with pytest.raises(ValidationError):
        PassportRecordMeta(
            source_status=PassportSourceStatus.SUGGESTED_ACCEPTED,
            support_status=SupportStatus.PROFILE_SUPPORTED,
        )


def test_unknown_and_not_provided_cannot_carry_profile_supported():
    with pytest.raises(ValidationError):
        PassportRecordMeta(
            source_status=PassportSourceStatus.UNKNOWN,
            support_status=SupportStatus.PROFILE_SUPPORTED,
        )
    with pytest.raises(ValidationError):
        PassportRecordMeta(
            source_status=PassportSourceStatus.NOT_PROVIDED,
            support_status=SupportStatus.PROFILE_SUPPORTED,
        )


def test_axes_do_not_silently_upgrade():
    meta = PassportRecordMeta(
        source_status=PassportSourceStatus.USER_ASSERTED,
        support_status=SupportStatus.PROFILE_SUPPORTED,
        verification_status=VerificationStatus.UNVERIFIED,
    )
    assert meta.verification_status == VerificationStatus.UNVERIFIED
    with pytest.raises(ValidationError):
        PassportRecordMeta(
            source_status=PassportSourceStatus.USER_ASSERTED,
            support_status=SupportStatus.PROFILE_SUPPORTED,
            verification_status=VerificationStatus.VERIFIED,
        )


# ---------------------------------------------------------------------------
# Taxonomy reference
# ---------------------------------------------------------------------------


def test_taxonomy_reference_normalizes_input_text():
    ref = PassportTaxonomyReference(
        kind=PassportTaxonomyKind.ROLE,
        input_text="  Electrical   Engineer ",
        taxonomy_id="electrical_engineer",
        source=SourceType.USER_PROVIDED,
        confidence=ConfidenceLevel.SUGGESTED,
        accepted_by_user=True,
    )
    assert ref.normalized_text == "electrical engineer"
    assert ref.input_text == "Electrical   Engineer" or ref.input_text == "Electrical Engineer"
    # str_strip_whitespace may collapse differently — ensure casefold match
    assert "electrical" in ref.normalized_text


def test_valid_role_and_skill_references_accepted():
    role = PassportTaxonomyReference(
        kind=PassportTaxonomyKind.ROLE,
        input_text="Software Engineer",
        taxonomy_id="software_engineer",
        source=SourceType.USER_PROVIDED,
        confidence=ConfidenceLevel.SUGGESTED,
        accepted_by_user=True,
    )
    skill = PassportTaxonomyReference(
        kind=PassportTaxonomyKind.SKILL,
        input_text="Python",
        taxonomy_id="python",
        source=SourceType.USER_PROVIDED,
        confidence=ConfidenceLevel.SUGGESTED,
        accepted_by_user=True,
    )
    assert role.kind == PassportTaxonomyKind.ROLE
    assert skill.kind == PassportTaxonomyKind.SKILL


def test_unknown_reference_requires_unknown_unknown():
    ref = PassportTaxonomyReference(
        kind=PassportTaxonomyKind.ROLE,
        input_text="Galactic Tea Router",
    )
    assert ref.taxonomy_id is None
    assert ref.source == SourceType.UNKNOWN
    assert ref.confidence == ConfidenceLevel.UNKNOWN
    assert ref.accepted_by_user is False
    with pytest.raises(ValidationError):
        PassportTaxonomyReference(
            kind=PassportTaxonomyKind.ROLE,
            input_text="Galactic Tea Router",
            source=SourceType.USER_PROVIDED,
            confidence=ConfidenceLevel.SUGGESTED,
        )


def test_taxonomy_id_absent_with_accepted_flag_rejected():
    with pytest.raises(ValidationError):
        PassportTaxonomyReference(
            kind=PassportTaxonomyKind.ROLE,
            input_text="Software Engineer",
            accepted_by_user=True,
        )


def test_invalid_taxonomy_id_rejected():
    with pytest.raises(ValidationError):
        PassportTaxonomyReference(
            kind=PassportTaxonomyKind.ROLE,
            input_text="X",
            taxonomy_id="Not Valid!",
            source=SourceType.USER_PROVIDED,
            confidence=ConfidenceLevel.SUGGESTED,
        )


def test_invalid_source_confidence_pair_rejected():
    with pytest.raises(ValidationError):
        PassportTaxonomyReference(
            kind=PassportTaxonomyKind.ROLE,
            input_text="Software Engineer",
            taxonomy_id="software_engineer",
            source=SourceType.UNKNOWN,
            confidence=ConfidenceLevel.SUGGESTED,
        )


def test_model_inferred_verified_rejected():
    with pytest.raises(ValidationError):
        PassportTaxonomyReference(
            kind=PassportTaxonomyKind.ROLE,
            input_text="Software Engineer",
            taxonomy_id="software_engineer",
            source=SourceType.MODEL_INFERRED,
            confidence=ConfidenceLevel.VERIFIED,
            accepted_by_user=True,
        )


def test_role_ref_rejected_in_skill_field():
    role_ref = PassportTaxonomyReference(
        kind=PassportTaxonomyKind.ROLE,
        input_text="Software Engineer",
        taxonomy_id="software_engineer",
        source=SourceType.USER_PROVIDED,
        confidence=ConfidenceLevel.SUGGESTED,
        accepted_by_user=True,
    )
    with pytest.raises(ValidationError):
        PassportSkill(name="Python", taxonomy=role_ref)


def test_skill_ref_rejected_in_role_field():
    skill_ref = PassportTaxonomyReference(
        kind=PassportTaxonomyKind.SKILL,
        input_text="Python",
        taxonomy_id="python",
        source=SourceType.USER_PROVIDED,
        confidence=ConfidenceLevel.SUGGESTED,
        accepted_by_user=True,
    )
    with pytest.raises(ValidationError):
        PassportExperience(
            job_title="Engineer",
            company_name="Acme",
            role_taxonomy=skill_ref,
        )
    with pytest.raises(ValidationError):
        PassportTarget(target_role_text="Engineer", role_taxonomy=skill_ref)


def test_freeform_target_and_skill_without_taxonomy():
    target = PassportTarget(target_role_text="Electrical Engineer")
    skill = PassportSkill(name="Circuit Design")
    assert target.role_taxonomy is None
    assert skill.taxonomy is None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_blank_required_fields_rejected():
    with pytest.raises(ValidationError):
        PassportExperience(job_title=" ", company_name="Acme")
    with pytest.raises(ValidationError):
        PassportEducation(degree=" ", institution="Uni")
    with pytest.raises(ValidationError):
        PassportProject(title="")
    with pytest.raises(ValidationError):
        PassportSkill(name="  ")
    with pytest.raises(ValidationError):
        PassportCredentialRef(name="", issuing_organization="Org")
    with pytest.raises(ValidationError):
        PassportTarget(target_role_text=" ")


def test_blank_optional_values_normalize_to_none():
    exp = PassportExperience(
        job_title="Engineer",
        company_name="Acme",
        company_url="  ",
        location="",
    )
    assert exp.company_url is None
    assert exp.location is None


def test_current_experience_rejects_end_date():
    with pytest.raises(ValidationError):
        PassportExperience(
            job_title="Engineer",
            company_name="Acme",
            is_current=True,
            end_date=date(2024, 1, 1),
        )


def test_experience_end_before_start_rejected():
    with pytest.raises(ValidationError):
        PassportExperience(
            job_title="Engineer",
            company_name="Acme",
            start_date=date(2024, 1, 1),
            end_date=date(2023, 1, 1),
        )


def test_current_education_rejects_end_date():
    with pytest.raises(ValidationError):
        PassportEducation(
            degree="BSc",
            institution="Uni",
            is_current=True,
            end_date=date(2024, 1, 1),
        )


def test_education_end_before_start_rejected():
    with pytest.raises(ValidationError):
        PassportEducation(
            degree="BSc",
            institution="Uni",
            start_date=date(2024, 1, 1),
            end_date=date(2023, 1, 1),
        )


def test_project_end_before_start_rejected():
    with pytest.raises(ValidationError):
        PassportProject(
            title="App",
            start_date=date(2024, 1, 1),
            end_date=date(2023, 1, 1),
        )


def test_credential_expiry_before_issue_rejected():
    with pytest.raises(ValidationError):
        PassportCredentialRef(
            name="Cert",
            issuing_organization="Org",
            issue_date=date(2024, 1, 1),
            expiry_date=date(2023, 1, 1),
        )


@pytest.mark.parametrize("priority", [0, 6, -1])
def test_priority_out_of_range_rejected(priority: int):
    with pytest.raises(ValidationError):
        PassportTarget(target_role_text="Role", priority=priority)


def test_negative_order_indexes_rejected():
    with pytest.raises(ValidationError):
        PassportSectionPreference(section=PassportSectionKey.PROFILE, order_index=-1)
    with pytest.raises(ValidationError):
        PassportSkill(name="Python", order_index=-1)


def test_duplicate_section_preferences_rejected():
    with pytest.raises(ValidationError):
        CareerPassportContract(
            section_preferences=[
                PassportSectionPreference(section=PassportSectionKey.PROFILE, order_index=0),
                PassportSectionPreference(section=PassportSectionKey.PROFILE, order_index=1),
            ]
        )


def test_blank_bullets_removed_and_deduplicated():
    exp = PassportExperience(
        job_title="Engineer",
        company_name="Acme",
        description_bullets=["Built APIs", "  ", "built apis", "Led team", "Built APIs"],
    )
    assert exp.description_bullets == ["Built APIs", "Led team"]


def test_interests_deduplicated_case_insensitively():
    profile = PassportProfile(interests=["Python", "python", "  Rust ", ""])
    assert profile.interests == ["Python", "Rust"]


# ---------------------------------------------------------------------------
# Profile compatibility
# ---------------------------------------------------------------------------


def _model_field_names(model) -> set[str]:
    return set(model.model_fields)


def test_profile_compatible_field_set():
    expected = {
        "phone",
        "date_of_birth",
        "nationality",
        "linkedin_url",
        "github_url",
        "portfolio_url",
        "twitter_url",
        "other_social_links",
        "address_city",
        "address_state",
        "address_country",
        "photo_url",
        "professional_headline",
        "bio_summary",
        "declaration_text",
        "references_available_on_request",
        "interests",
    }
    assert expected <= _model_field_names(PassportProfile)
    assert expected <= _model_field_names(ProfileUpdate)


def test_experience_compatible_field_set():
    expected = {
        "job_title",
        "company_name",
        "company_url",
        "location",
        "employment_type",
        "start_date",
        "end_date",
        "is_current",
        "description_bullets",
        "order_index",
    }
    assert expected <= _model_field_names(PassportExperience)
    assert expected <= _model_field_names(WorkExperienceIn)


def test_education_compatible_field_set():
    expected = {
        "degree",
        "field_of_study",
        "institution",
        "location",
        "start_date",
        "end_date",
        "is_current",
        "grade",
        "description_bullets",
        "relevant_coursework",
        "order_index",
    }
    assert expected <= _model_field_names(PassportEducation)
    assert expected <= _model_field_names(EducationIn)


def test_project_compatible_field_set():
    expected = {
        "title",
        "description",
        "technologies",
        "project_url",
        "start_date",
        "end_date",
        "role",
        "key_achievements",
        "order_index",
    }
    assert expected <= _model_field_names(PassportProject)
    assert expected <= _model_field_names(ProjectIn)


def test_skill_compatible_field_set():
    expected = {"name", "skill_type", "category", "proficiency", "order_index"}
    assert expected <= _model_field_names(PassportSkill)
    assert expected <= _model_field_names(SkillIn)


def test_credential_compatible_field_set():
    expected = {
        "name",
        "issuing_organization",
        "issue_date",
        "expiry_date",
        "credential_id",
        "credential_url",
        "order_index",
    }
    assert expected <= _model_field_names(PassportCredentialRef)
    assert expected <= _model_field_names(CertificationIn)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def test_aggregate_model_dump_round_trip():
    passport = CareerPassportContract(
        display_name="Ada",
        headline="Engineer",
        experiences=[
            PassportExperience(job_title="EE", company_name="Acme", is_current=True)
        ],
        targets=[
            PassportTarget(
                target_role_text="Electrical Engineer",
                pathway_type=PathwayType.SKILL_GAP,
                target_seniority=SeniorityLevel.MID,
            )
        ],
        credentials=[
            PassportCredentialRef(name="PMP", issuing_organization="PMI")
        ],
    )
    dumped = passport.model_dump(mode="python")
    restored = CareerPassportContract.model_validate(dumped)
    assert restored.display_name == "Ada"
    assert restored.targets[0].target_role_text == "Electrical Engineer"
    assert restored.experiences[0].company_name == "Acme"
    assert restored.credentials[0].name == "PMP"


def test_enum_values_serialize_predictably():
    passport = CareerPassportContract()
    data = passport.model_dump(mode="json")
    assert data["visibility"] == "private"
    assert data["section_preferences"][0]["section"] == "profile"


def test_nested_metadata_remains_unverified():
    passport = CareerPassportContract(
        profile=PassportProfile(),
        skills=[PassportSkill(name="Python")],
    )
    assert passport.profile.record_meta.verification_status == VerificationStatus.UNVERIFIED
    assert passport.skills[0].record_meta.verification_status == VerificationStatus.UNVERIFIED
    data = passport.model_dump(mode="json")
    assert "evidence" not in data
    assert "verified" not in data["profile"]["record_meta"].values()


def test_other_social_links_rejects_non_dict():
    with pytest.raises(ValidationError):
        PassportProfile(other_social_links=["https://x.com"])  # type: ignore[list-item]


def test_pathway_and_seniority_reuse_existing_enums():
    target = PassportTarget(
        target_role_text="PM",
        pathway_type=PathwayType.CAREER_SWITCH,
        target_seniority=SeniorityLevel.SENIOR,
        priority=1,
    )
    assert target.pathway_type == PathwayType.CAREER_SWITCH
    assert target.target_seniority == SeniorityLevel.SENIOR


# ---------------------------------------------------------------------------
# Import boundary
# ---------------------------------------------------------------------------


def test_passport_package_import_boundary():
    forbidden_import_snippets = (
        "from fastapi",
        "import fastapi",
        "from sqlalchemy",
        "import sqlalchemy",
        "app.db",
        "app.api",
        "app.schemas",
        "APIRouter",
        "Session(",
        "openai",
        "anthropic",
        "google.generativeai",
        "langchain",
        "ChatOpenAI",
        "ChatGoogle",
    )
    # Allowlisted CareerKundi imports (substring check is for forbidden only)
    py_files = sorted(PASSPORT_ROOT.glob("*.py"))
    assert py_files, "expected career_passport package files"
    for path in py_files:
        source = path.read_text(encoding="utf-8")
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Only inspect import lines and from-import lines
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            lowered = stripped.lower()
            for snippet in forbidden_import_snippets:
                assert snippet.lower() not in lowered, (
                    f"{path.name} import line contains forbidden marker {snippet!r}: {stripped}"
                )
        # Also ensure no Profile schema imports
        assert "app.schemas.profile" not in source
        assert "from app.db" not in source
        assert "import app.db" not in source


def test_package_only_allows_known_internal_imports():
    allowed_prefixes = (
        "from __future__",
        "from datetime",
        "from enum",
        "from typing",
        "from uuid",
        "from pydantic",
        "from app.platform.claims.status",
        "from app.taxonomy.contracts",
        "from app.taxonomy.normalization",
        "from app.career_passport.contracts",
        "import",  # stdlib bare imports checked via prefixes above when from
    )
    contracts = (PASSPORT_ROOT / "contracts.py").read_text(encoding="utf-8")
    for line in contracts.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("from ") or stripped.startswith("import ")):
            continue
        if stripped.startswith("import "):
            # Only stdlib / pydantic expected — reject app.* except via from
            assert not stripped.startswith("import app."), stripped
            continue
        assert any(stripped.startswith(prefix) for prefix in allowed_prefixes), stripped
