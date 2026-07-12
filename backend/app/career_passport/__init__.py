"""
Career & Education Passport — contract boundary (0052-F1).

Pure, deterministic domain contracts only.
No database, no FastAPI, no LLM, no evidence verification, no feature integration.
"""

from __future__ import annotations

from app.career_passport.contracts import (
    CareerPassportContract,
    PassportContractModel,
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

__all__ = [
    "CareerPassportContract",
    "PassportContractModel",
    "PassportCredentialRef",
    "PassportCredentialType",
    "PassportEducation",
    "PassportExperience",
    "PassportProfile",
    "PassportProject",
    "PassportRecordMeta",
    "PassportSectionKey",
    "PassportSectionPreference",
    "PassportSkill",
    "PassportSourceStatus",
    "PassportTarget",
    "PassportTaxonomyKind",
    "PassportTaxonomyReference",
    "PassportVisibility",
    "default_section_preferences",
]
