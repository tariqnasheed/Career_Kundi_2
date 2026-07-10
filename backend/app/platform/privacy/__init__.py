"""
CareerKundi privacy domain (0050-PF9-S1).

Public exports are refs and kind enums/parsers.
"""

from app.platform.privacy.kinds import (
    ConsentStatus,
    DataClassification,
    ProcessingPurpose,
    RetentionCategory,
    VisibilityScope,
    parse_consent_status,
    parse_data_classification,
    parse_processing_purpose,
    parse_retention_category,
    parse_visibility_scope,
)
from app.platform.privacy.refs import (
    ConsentRecordRef,
    PrivacyPolicyRef,
    PrivacyRefError,
    RetentionPolicyRef,
)

__all__ = [
    "ConsentRecordRef",
    "ConsentStatus",
    "DataClassification",
    "PrivacyPolicyRef",
    "PrivacyRefError",
    "ProcessingPurpose",
    "RetentionCategory",
    "RetentionPolicyRef",
    "VisibilityScope",
    "parse_consent_status",
    "parse_data_classification",
    "parse_processing_purpose",
    "parse_retention_category",
    "parse_visibility_scope",
]
