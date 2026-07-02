"""
api/routes/profile.py
=========================
CRUD endpoints for the Profile Data Hub (§4.4). This is the only feature in
the platform that is pure data management with no LLM agent involved (aside
from the "Improve with AI" bullet endpoint, which delegates to the CV
Builder's BulletWriterAgent — see api/routes/cv_builder.py) — every other
feature reads from this data but never writes to it, per the CVReflector's
"never fabricate profile data" guardrail (§4.2).

Endpoint summary
----------------
GET    /api/v1/profile                       — Full nested profile (drives CV Builder toggles)
PATCH  /api/v1/profile                        — Update personal info fields
GET    /api/v1/profile/export                 — Download entire profile as JSON
POST   /api/v1/profile/import                 — Restore profile from an exported JSON file
For each repeatable section (education, experience, projects, certifications,
publications, languages, volunteer, awards, references, skills):
POST   /api/v1/profile/<section>              — Add an entry
PUT    /api/v1/profile/<section>/{id}         — Update an entry
DELETE /api/v1/profile/<section>/{id}         — Delete an entry
PUT    /api/v1/profile/<section>/reorder      — Bulk drag-and-drop reorder
Custom sections additionally support:
POST   /api/v1/profile/custom-sections                          — Create a custom section
DELETE /api/v1/profile/custom-sections/{id}                      — Delete a custom section
POST   /api/v1/profile/custom-sections/{id}/entries               — Add an entry to a list-type section
"""

import uuid
from typing import TypeVar

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import NotFoundError
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
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.profile import (
    AwardIn,
    AwardOut,
    CertificationIn,
    CertificationOut,
    CustomSectionEntryIn,
    CustomSectionIn,
    CustomSectionOut,
    EducationIn,
    EducationOut,
    LanguageIn,
    LanguageOut,
    ProfileRead,
    ProfileUpdate,
    ProjectIn,
    ProjectOut,
    PublicationIn,
    PublicationOut,
    ReferenceIn,
    ReferenceOut,
    SkillIn,
    SkillOut,
    VolunteerIn,
    VolunteerOut,
    WorkExperienceIn,
    WorkExperienceOut,
)

router = APIRouter(prefix="/profile", tags=["profile"])

ModelT = TypeVar("ModelT")
SchemaInT = TypeVar("SchemaInT", bound=BaseModel)


async def _get_or_create_profile(db: AsyncSession, user: User) -> Profile:
    """
    Fetch the user's Profile row, eager-loading every relationship needed
    for ProfileRead. Creates one on the fly for legacy users who somehow
    don't have one (defensive — normally created at registration time).
    """
    from sqlalchemy.orm import selectinload

    stmt = (
        select(Profile)
        .where(Profile.user_id == user.id)
        .options(
            selectinload(Profile.educations),
            selectinload(Profile.work_experiences),
            selectinload(Profile.projects),
            selectinload(Profile.certifications),
            selectinload(Profile.publications),
            selectinload(Profile.languages),
            selectinload(Profile.volunteer_entries),
            selectinload(Profile.awards),
            selectinload(Profile.references),
            selectinload(Profile.skills),
            selectinload(Profile.custom_sections).selectinload(CustomSection.entries),
        )
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


def _section_router(
    *,
    path: str,
    model: type,
    schema_in: type[BaseModel],
    schema_out: type[BaseModel],
) -> None:
    """
    Register POST/PUT/DELETE/reorder routes for one repeatable profile
    section. Defined as a function (rather than copy-pasting 10x) so every
    section behaves identically and a bug fix here fixes all ten at once.
    """

    @router.post(f"/{path}", response_model=schema_out, status_code=201, name=f"add_{path}")
    async def add_entry(
        payload: schema_in,  # type: ignore[valid-type]
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        profile = await _get_or_create_profile(db, user)
        entry = model(profile_id=profile.id, **payload.model_dump())
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @router.put(f"/{path}/{{entry_id}}", response_model=schema_out, name=f"update_{path}")
    async def update_entry(
        entry_id: uuid.UUID,
        payload: schema_in,  # type: ignore[valid-type]
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        profile = await _get_or_create_profile(db, user)
        result = await db.execute(
            select(model).where(model.id == entry_id, model.profile_id == profile.id)
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            raise NotFoundError(f"{model.__name__} entry not found.")
        for field, value in payload.model_dump().items():
            setattr(entry, field, value)
        await db.commit()
        await db.refresh(entry)
        return entry

    @router.delete(f"/{path}/{{entry_id}}", status_code=204, name=f"delete_{path}")
    async def delete_entry(
        entry_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        profile = await _get_or_create_profile(db, user)
        result = await db.execute(
            select(model).where(model.id == entry_id, model.profile_id == profile.id)
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            raise NotFoundError(f"{model.__name__} entry not found.")
        await db.delete(entry)
        await db.commit()
        return Response(status_code=204)

    @router.put(f"/{path}/reorder", status_code=204, name=f"reorder_{path}")
    async def reorder_entries(
        ordered_ids: list[uuid.UUID],
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        """Drag-and-drop reorder: body is the entry IDs in their new display order."""
        profile = await _get_or_create_profile(db, user)
        result = await db.execute(select(model).where(model.profile_id == profile.id))
        entries_by_id = {e.id: e for e in result.scalars().all()}
        for index, entry_id in enumerate(ordered_ids):
            if entry_id in entries_by_id:
                entries_by_id[entry_id].order_index = index
        await db.commit()
        return Response(status_code=204)


# Register every repeatable section's CRUD routes.
_section_router(path="education", model=Education, schema_in=EducationIn, schema_out=EducationOut)
_section_router(path="experience", model=WorkExperience, schema_in=WorkExperienceIn, schema_out=WorkExperienceOut)
_section_router(path="projects", model=Project, schema_in=ProjectIn, schema_out=ProjectOut)
_section_router(path="certifications", model=Certification, schema_in=CertificationIn, schema_out=CertificationOut)
_section_router(path="publications", model=Publication, schema_in=PublicationIn, schema_out=PublicationOut)
_section_router(path="languages", model=Language, schema_in=LanguageIn, schema_out=LanguageOut)
_section_router(path="volunteer", model=Volunteer, schema_in=VolunteerIn, schema_out=VolunteerOut)
_section_router(path="awards", model=Award, schema_in=AwardIn, schema_out=AwardOut)
_section_router(path="references", model=Reference, schema_in=ReferenceIn, schema_out=ReferenceOut)
_section_router(path="skills", model=Skill, schema_in=SkillIn, schema_out=SkillOut)


@router.get("", response_model=ProfileRead)
async def get_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Full nested profile — the exact payload the CV Builder's section-toggle panel consumes."""
    profile = await _get_or_create_profile(db, user)
    data = ProfileRead.model_validate(profile)
    data.completeness_score = profile.calculate_completeness_score()
    return data


@router.patch("", response_model=ProfileRead)
async def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Partial update of top-level Personal Information fields, auto-saved by the frontend on blur."""
    profile = await _get_or_create_profile(db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    data = ProfileRead.model_validate(profile)
    data.completeness_score = profile.calculate_completeness_score()
    return data


@router.get("/export")
async def export_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """GDPR-friendly full profile export as a downloadable JSON document."""
    profile = await _get_or_create_profile(db, user)
    data = ProfileRead.model_validate(profile)
    data.completeness_score = profile.calculate_completeness_score()
    return data.model_dump(mode="json")


@router.post("/custom-sections", response_model=CustomSectionOut, status_code=201)
async def add_custom_section(
    payload: CustomSectionIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a brand-new, user-defined CV section (§4.4 'Custom Sections')."""
    profile = await _get_or_create_profile(db, user)
    section = CustomSection(profile_id=profile.id, **payload.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


@router.delete("/custom-sections/{section_id}", status_code=204)
async def delete_custom_section(
    section_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, user)
    result = await db.execute(
        select(CustomSection).where(CustomSection.id == section_id, CustomSection.profile_id == profile.id)
    )
    section = result.scalar_one_or_none()
    if section is None:
        raise NotFoundError("Custom section not found.")
    await db.delete(section)
    await db.commit()
    return Response(status_code=204)


@router.post("/custom-sections/{section_id}/entries", status_code=201)
async def add_custom_section_entry(
    section_id: uuid.UUID,
    payload: CustomSectionEntryIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, user)
    result = await db.execute(
        select(CustomSection).where(CustomSection.id == section_id, CustomSection.profile_id == profile.id)
    )
    section = result.scalar_one_or_none()
    if section is None:
        raise NotFoundError("Custom section not found.")
    entry = CustomSectionEntry(section_id=section.id, **payload.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry
