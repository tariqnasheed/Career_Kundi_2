"""
db/models/profile.py
========================
The Profile data hub — every model backing §4.4 of the product spec
("User Profile Page — The Complete CV Data Hub"). This is the single source
of truth that the CV Builder feature reads from exclusively; the CV agent
team is guardrailed to NEVER fabricate data that isn't present here.

Design choice — relational tables vs JSON columns:
  Repeatable, orderable, structured entries (Education, WorkExperience,
  Project, etc.) get their own table with a `profile_id` foreign key and an
  `order_index` (via OrderableMixin) so drag-and-drop reordering is a simple
  `UPDATE ... SET order_index = ...` rather than rewriting a JSON blob.
  Free-form / variable-shape data (custom section entry fields, rich-text
  bullet lists) is stored as JSON columns since its shape is user-defined
  and doesn't need to be queried relationally.
"""

import uuid
from datetime import date

from sqlalchemy import JSON, Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import OrderableMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Profile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Personal information + top-level profile fields (§4.4 "Personal Information").

    Everything else in this file (Education, WorkExperience, ...) hangs off
    this row via a `profile_id` foreign key.
    """

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Personal information
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    twitter_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Dynamic list of {"label": str, "url": str} — user can add arbitrarily many.
    other_social_links: Mapped[list] = mapped_column(JSON, default=list)

    address_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address_state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address_country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    professional_headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # max 1000 chars, enforced in schema

    declaration_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    references_available_on_request: Mapped[bool] = mapped_column(Boolean, default=False)

    interests: Mapped[list] = mapped_column(JSON, default=list)  # tag list of strings

    # --- Relationships (all cascade-deleted with the profile / GDPR-friendly) ---
    user: Mapped["User"] = relationship(back_populates="profile")  # noqa: F821
    educations: Mapped[list["Education"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Education.order_index"
    )
    work_experiences: Mapped[list["WorkExperience"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="WorkExperience.order_index"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Project.order_index"
    )
    certifications: Mapped[list["Certification"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Certification.order_index"
    )
    publications: Mapped[list["Publication"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Publication.order_index"
    )
    languages: Mapped[list["Language"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Language.order_index"
    )
    volunteer_entries: Mapped[list["Volunteer"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Volunteer.order_index"
    )
    awards: Mapped[list["Award"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Award.order_index"
    )
    references: Mapped[list["Reference"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Reference.order_index"
    )
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Skill.order_index"
    )
    custom_sections: Mapped[list["CustomSection"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="CustomSection.order_index"
    )

    def completeness_score(self) -> float:
        """
        Compute the "Profile Strength Meter" (§4.4 Profile Management).

        A simple weighted heuristic: each populated section contributes a
        fixed weight, summed to a 0-100 score. Intentionally simple and
        deterministic (no LLM call) since this runs on every profile page
        load and must be instant.
        """
        weights = {
            "headline": 10 if self.professional_headline else 0,
            "bio": 10 if self.bio_summary else 0,
            "education": 15 if self.educations else 0,
            "experience": 20 if self.work_experiences else 0,
            "skills": 15 if self.skills else 0,
            "projects": 10 if self.projects else 0,
            "certifications": 5 if self.certifications else 0,
            "links": 5 if (self.linkedin_url or self.github_url or self.portfolio_url) else 0,
            "languages": 5 if self.languages else 0,
            "custom": 5 if self.custom_sections else 0,
        }
        return float(sum(weights.values()))


class Education(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    __tablename__ = "educations"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    degree: Mapped[str] = mapped_column(String(255))
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description_bullets: Mapped[list] = mapped_column(JSON, default=list)  # list[str]
    relevant_coursework: Mapped[list] = mapped_column(JSON, default=list)  # list[str] tags
    profile: Mapped["Profile"] = relationship(back_populates="educations")


class WorkExperience(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    __tablename__ = "work_experiences"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    job_title: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str] = mapped_column(String(255))
    company_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    description_bullets: Mapped[list] = mapped_column(JSON, default=list)  # list[str], AI-enhanceable
    profile: Mapped["Profile"] = relationship(back_populates="work_experiences")


class Project(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    __tablename__ = "projects"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[list] = mapped_column(JSON, default=list)  # list[str] tags
    project_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    key_achievements: Mapped[list] = mapped_column(JSON, default=list)  # list[str]
    profile: Mapped["Profile"] = relationship(back_populates="projects")


class Certification(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    __tablename__ = "certifications"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    issuing_organization: Mapped[str] = mapped_column(String(255))
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    credential_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    profile: Mapped["Profile"] = relationship(back_populates="certifications")


class Publication(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    __tablename__ = "publications"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(512))
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    co_authors: Mapped[list] = mapped_column(JSON, default=list)  # list[str]
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile: Mapped["Profile"] = relationship(back_populates="publications")


class Language(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    __tablename__ = "languages"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    proficiency: Mapped[str] = mapped_column(String(50))  # Native|Fluent|Professional|Intermediate|Basic
    profile: Mapped["Profile"] = relationship(back_populates="languages")


class Volunteer(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    __tablename__ = "volunteer_entries"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(255))
    organization: Mapped[str] = mapped_column(String(255))
    cause_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description_bullets: Mapped[list] = mapped_column(JSON, default=list)
    profile: Mapped["Profile"] = relationship(back_populates="volunteer_entries")


class Award(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    __tablename__ = "awards"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    issuing_organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_received: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile: Mapped["Profile"] = relationship(back_populates="awards")


class Reference(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    __tablename__ = "references_"  # trailing underscore: "references" can clash with reserved words in some dialects
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    relationship_to_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile: Mapped["Profile"] = relationship(back_populates="references")


class Skill(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    """
    A single skill entry. `category` distinguishes technical vs soft skills
    and custom groupings (e.g. "Programming Languages", "DevOps Tools") that
    the user defines, per §4.4 "Skill Categories".
    """

    __tablename__ = "skills"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    skill_type: Mapped[str] = mapped_column(String(20), default="technical")  # technical | soft
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)  # custom group label
    proficiency: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Beginner..Expert
    profile: Mapped["Profile"] = relationship(back_populates="skills")


class CustomSection(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    """
    A user-defined CV section (§4.4 "Custom Sections — User-Defined"), e.g.
    "Open Source Contributions" or "Patents". `section_type` determines how
    the frontend renders its entries and how the CV agent formats them.
    """

    __tablename__ = "custom_sections"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    section_type: Mapped[str] = mapped_column(String(20), default="list")  # list | free_text | tags
    free_text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)  # used when section_type == "tags"
    profile: Mapped["Profile"] = relationship(back_populates="custom_sections")
    entries: Mapped[list["CustomSectionEntry"]] = relationship(
        back_populates="section", cascade="all, delete-orphan", order_by="CustomSectionEntry.order_index"
    )


class CustomSectionEntry(UUIDPrimaryKeyMixin, OrderableMixin, Base):
    """One entry within a `section_type == "list"` CustomSection."""

    __tablename__ = "custom_section_entries"
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("custom_sections.id", ondelete="CASCADE")
    )
    entry_title: Mapped[str] = mapped_column(String(255))
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description_bullets: Mapped[list] = mapped_column(JSON, default=list)
    section: Mapped["CustomSection"] = relationship(back_populates="entries")
