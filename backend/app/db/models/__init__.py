"""
db/models/__init__.py
========================
Re-exports every ORM model so Alembic's autogenerate (see
db/migrations/env.py) sees the full schema by importing this one module,
and so application code can `from app.db.models import User, Profile, ...`.
"""

from app.db.models.apply import JobApplication
from app.db.models.assets import GeneratedAsset
from app.db.models.audit import AuditLog, FeedbackRecord, TokenUsageRecord
from app.db.models.badges import BadgeDefinition, UserBadge
from app.db.models.career_subject import CareerSubject
from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.claim import ClaimRecord
from app.db.models.cv import GeneratedCV
from app.db.models.geo import (
    GeoArea,
    JurisdictionArea,
    LocaleProfile,
    WorkAuthorizationArea,
)
from app.db.models.job import SavedJob
from app.db.models.lifecycle import (
    CareerAttempt,
    CareerFeedback,
    CareerGoal,
    CareerOutcome,
    CareerRecommendation,
)
from app.db.models.memory import AgentMemory
from app.db.models.privacy import ConsentRecord, PrivacyPolicy, RetentionPolicy
from app.db.models.profile import (
    Award,
    Certification,
    CustomSection,
    CustomSectionEntry,
    Education,
    Language,
    Profile,
    Project,
    Publication,
    Reference,
    Skill,
    Volunteer,
    WorkExperience,
)
from app.db.models.provenance import SourceRecord, SourceSnapshot
from app.db.models.queue import GenerationJob
from app.db.models.roadmap import Roadmap, RoadmapMilestone, RoadmapSkill
from app.db.models.user import User
from app.db.models.passport import CareerPassport, PassportTarget

__all__ = [
    "User",
    "Profile",
    "Education",
    "WorkExperience",
    "Project",
    "Certification",
    "Publication",
    "Language",
    "Volunteer",
    "Award",
    "Reference",
    "Skill",
    "CustomSection",
    "CustomSectionEntry",
    "SavedJob",
    "GeneratedCV",
    "Roadmap",
    "RoadmapMilestone",
    "RoadmapSkill",
    "ChatSession",
    "ChatMessage",
    "AgentMemory",
    "AuditLog",
    "TokenUsageRecord",
    "FeedbackRecord",
    "GenerationJob",
    "GeneratedAsset",
    "BadgeDefinition",
    "UserBadge",
    "JobApplication",
    "CareerSubject",
    "ClaimRecord",
    "SourceRecord",
    "SourceSnapshot",
    "GeoArea",
    "JurisdictionArea",
    "LocaleProfile",
    "WorkAuthorizationArea",
    "CareerGoal",
    "CareerRecommendation",
    "CareerAttempt",
    "CareerOutcome",
    "CareerFeedback",
    "PrivacyPolicy",
    "ConsentRecord",
    "RetentionPolicy",
    "CareerPassport",
    "PassportTarget",
]
