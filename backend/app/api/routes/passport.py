"""
Authenticated Passport API routes (0052-F3).

Aggregate GET lazy-creates. Section mutations write Profile-backed rows or
Passport targets. Every successful mutation returns the full aggregate.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.career_passport.application import service as passport_service
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.passport import (
    PassportCredentialCreate,
    PassportCredentialPatch,
    PassportEducationCreate,
    PassportEducationPatch,
    PassportEnvelope,
    PassportExperienceCreate,
    PassportExperiencePatch,
    PassportPatch,
    PassportProfilePatch,
    PassportProjectCreate,
    PassportProjectPatch,
    PassportReorder,
    PassportSkillCreate,
    PassportSkillPatch,
    PassportTargetCreate,
    PassportTargetPatch,
)

router = APIRouter(prefix="/passport", tags=["passport"])


@router.get("", response_model=PassportEnvelope)
async def get_passport(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.get_passport_aggregate(db, user)


@router.patch("", response_model=PassportEnvelope)
async def patch_passport(
    payload: PassportPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.patch_passport_aggregate(db, user, payload)


@router.patch("/profile", response_model=PassportEnvelope)
async def patch_passport_profile(
    payload: PassportProfilePatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.patch_passport_profile(db, user, payload)


# ---------------------------------------------------------------------------
# Experiences
# ---------------------------------------------------------------------------


@router.post(
    "/experiences",
    response_model=PassportEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_experience(
    payload: PassportExperienceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.create_profile_section_entry(
        db,
        user,
        "experiences",
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.put("/experiences/reorder", response_model=PassportEnvelope)
async def reorder_experiences(
    payload: PassportReorder,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.reorder_profile_section(db, user, "experiences", payload)


@router.patch("/experiences/{entry_id}", response_model=PassportEnvelope)
async def patch_experience(
    entry_id: UUID,
    payload: PassportExperiencePatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.patch_profile_section_entry(
        db,
        user,
        "experiences",
        entry_id,
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.delete("/experiences/{entry_id}", response_model=PassportEnvelope)
async def delete_experience(
    entry_id: UUID,
    expected_version: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.delete_profile_section_entry(
        db, user, "experiences", entry_id, expected_version
    )


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------


@router.post(
    "/education",
    response_model=PassportEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_education(
    payload: PassportEducationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.create_profile_section_entry(
        db,
        user,
        "education",
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.put("/education/reorder", response_model=PassportEnvelope)
async def reorder_education(
    payload: PassportReorder,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.reorder_profile_section(db, user, "education", payload)


@router.patch("/education/{entry_id}", response_model=PassportEnvelope)
async def patch_education(
    entry_id: UUID,
    payload: PassportEducationPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.patch_profile_section_entry(
        db,
        user,
        "education",
        entry_id,
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.delete("/education/{entry_id}", response_model=PassportEnvelope)
async def delete_education(
    entry_id: UUID,
    expected_version: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.delete_profile_section_entry(
        db, user, "education", entry_id, expected_version
    )


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@router.post(
    "/projects",
    response_model=PassportEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    payload: PassportProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.create_profile_section_entry(
        db,
        user,
        "projects",
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.put("/projects/reorder", response_model=PassportEnvelope)
async def reorder_projects(
    payload: PassportReorder,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.reorder_profile_section(db, user, "projects", payload)


@router.patch("/projects/{entry_id}", response_model=PassportEnvelope)
async def patch_project(
    entry_id: UUID,
    payload: PassportProjectPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.patch_profile_section_entry(
        db,
        user,
        "projects",
        entry_id,
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.delete("/projects/{entry_id}", response_model=PassportEnvelope)
async def delete_project(
    entry_id: UUID,
    expected_version: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.delete_profile_section_entry(
        db, user, "projects", entry_id, expected_version
    )


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@router.post(
    "/skills",
    response_model=PassportEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_skill(
    payload: PassportSkillCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.create_profile_section_entry(
        db,
        user,
        "skills",
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.put("/skills/reorder", response_model=PassportEnvelope)
async def reorder_skills(
    payload: PassportReorder,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.reorder_profile_section(db, user, "skills", payload)


@router.patch("/skills/{entry_id}", response_model=PassportEnvelope)
async def patch_skill(
    entry_id: UUID,
    payload: PassportSkillPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.patch_profile_section_entry(
        db,
        user,
        "skills",
        entry_id,
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.delete("/skills/{entry_id}", response_model=PassportEnvelope)
async def delete_skill(
    entry_id: UUID,
    expected_version: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.delete_profile_section_entry(
        db, user, "skills", entry_id, expected_version
    )


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


@router.post(
    "/credentials",
    response_model=PassportEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_credential(
    payload: PassportCredentialCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.create_profile_section_entry(
        db,
        user,
        "credentials",
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.put("/credentials/reorder", response_model=PassportEnvelope)
async def reorder_credentials(
    payload: PassportReorder,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.reorder_profile_section(db, user, "credentials", payload)


@router.patch("/credentials/{entry_id}", response_model=PassportEnvelope)
async def patch_credential(
    entry_id: UUID,
    payload: PassportCredentialPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.patch_profile_section_entry(
        db,
        user,
        "credentials",
        entry_id,
        payload.model_dump(exclude={"expected_version"}),
        payload.model_fields_set,
        payload.expected_version,
    )


@router.delete("/credentials/{entry_id}", response_model=PassportEnvelope)
async def delete_credential(
    entry_id: UUID,
    expected_version: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.delete_profile_section_entry(
        db, user, "credentials", entry_id, expected_version
    )


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


@router.post(
    "/targets",
    response_model=PassportEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_target(
    payload: PassportTargetCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.create_target(db, user, payload)


@router.put("/targets/reorder", response_model=PassportEnvelope)
async def reorder_targets(
    payload: PassportReorder,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.reorder_targets(db, user, payload)


@router.patch("/targets/{entry_id}", response_model=PassportEnvelope)
async def patch_target(
    entry_id: UUID,
    payload: PassportTargetPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.patch_target(db, user, entry_id, payload)


@router.delete("/targets/{entry_id}", response_model=PassportEnvelope)
async def delete_target(
    entry_id: UUID,
    expected_version: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PassportEnvelope:
    return await passport_service.delete_target(db, user, entry_id, expected_version)
