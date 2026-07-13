"""
Passport application service (0052-F3).

Deterministic database operations for authenticated Passport aggregate reads
and Profile-wrapper / target mutations. No FastAPI, LLM, or HTTP clients.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import null as sa_null
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.career_passport.contracts import (
    PassportCredentialRef,
    PassportCredentialType,
    PassportEducation,
    PassportExperience,
    PassportProfile,
    PassportProject,
    PassportRecordMeta,
    PassportSectionPreference,
    PassportSkill,
    PassportTarget as PassportTargetContract,
    PassportTaxonomyReference,
)
from app.core.errors import ConflictError, NotFoundError, ValidationFailedError
from app.db.models.passport import CareerPassport, PassportTarget
from app.db.models.profile import (
    Certification,
    Education,
    Profile,
    Project,
    Skill,
    WorkExperience,
)
from app.db.models.user import User
from app.platform.identity.service import ensure_owned_subject
from app.schemas.passport import (
    PassportCredentialCreate,
    PassportCredentialPatch,
    PassportCredentialRead,
    PassportEducationCreate,
    PassportEducationPatch,
    PassportEducationRead,
    PassportEnvelope,
    PassportExperienceCreate,
    PassportExperiencePatch,
    PassportExperienceRead,
    PassportPatch,
    PassportProfilePatch,
    PassportProfileRead,
    PassportProjectCreate,
    PassportProjectPatch,
    PassportProjectRead,
    PassportRead,
    PassportRecordMetaRead,
    PassportReorder,
    PassportSkillCreate,
    PassportSkillPatch,
    PassportSkillRead,
    PassportTargetCreate,
    PassportTargetPatch,
    PassportTargetRead,
)

_PROFILE_BACKED_META = {
    "source_status": "user_asserted",
    "support_status": "profile_supported",
    "verification_status": "unverified",
}

_NATIVE_META = {
    "source_status": "user_asserted",
    "support_status": "not_provided",
    "verification_status": "unverified",
}

_PROFILE_FIELDS = (
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
)

# Fixed collection mapping — never selected from client input.
_COLLECTION_MAP: dict[str, dict[str, Any]] = {
    "experiences": {
        "model": WorkExperience,
        "relationship": "work_experiences",
        "legacy_fields": (
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
        ),
        "taxonomy_field": "passport_role_taxonomy",
        "taxonomy_contract_field": "role_taxonomy",
        "taxonomy_is_list": False,
        "validator": PassportExperience,
        "not_found": "Experience entry not found.",
    },
    "education": {
        "model": Education,
        "relationship": "educations",
        "legacy_fields": (
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
        ),
        "taxonomy_field": None,
        "taxonomy_contract_field": None,
        "taxonomy_is_list": False,
        "validator": PassportEducation,
        "not_found": "Education entry not found.",
    },
    "projects": {
        "model": Project,
        "relationship": "projects",
        "legacy_fields": (
            "title",
            "description",
            "technologies",
            "project_url",
            "start_date",
            "end_date",
            "role",
            "key_achievements",
            "order_index",
        ),
        "taxonomy_field": "passport_skill_taxonomy",
        "taxonomy_contract_field": "skill_taxonomy",
        "taxonomy_is_list": True,
        "validator": PassportProject,
        "not_found": "Project entry not found.",
    },
    "skills": {
        "model": Skill,
        "relationship": "skills",
        "legacy_fields": (
            "name",
            "skill_type",
            "category",
            "proficiency",
            "order_index",
        ),
        "taxonomy_field": "passport_taxonomy",
        "taxonomy_contract_field": "taxonomy",
        "taxonomy_is_list": False,
        "validator": PassportSkill,
        "not_found": "Skill entry not found.",
    },
    "credentials": {
        "model": Certification,
        "relationship": "certifications",
        "legacy_fields": (
            "name",
            "issuing_organization",
            "issue_date",
            "expiry_date",
            "credential_id",
            "credential_url",
            "order_index",
        ),
        "taxonomy_field": None,
        "taxonomy_contract_field": None,
        "taxonomy_is_list": False,
        "credential_type_field": "passport_credential_type",
        "validator": PassportCredentialRef,
        "not_found": "Credential entry not found.",
    },
}


def _safe_validation_details(exc: ValidationError) -> dict[str, Any]:
    """JSON-serializable validation summary without request payloads or PII."""
    errors: list[dict[str, Any]] = []
    for err in exc.errors():
        errors.append(
            {
                "loc": [str(part) for part in err.get("loc", ())],
                "msg": str(err.get("msg", "validation error")),
                "type": str(err.get("type", "value_error")),
            }
        )
    return {"errors": errors}


def _validate_contract(model_cls: type, data: dict[str, Any]) -> Any:
    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        raise ValidationFailedError(
            "Passport domain validation failed.",
            details=_safe_validation_details(exc),
        ) from exc


def _dump_taxonomy(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, list):
        return [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in value]
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _enum_value(value: Any) -> Any:
    if value is None:
        return None
    return getattr(value, "value", value)


_MIN_DT = datetime.min.replace(tzinfo=timezone.utc)


def _sorted_entries(entries: list[Any]) -> list[Any]:
    return sorted(
        entries,
        key=lambda e: (
            getattr(e, "order_index", 0),
            getattr(e, "created_at", None) or _MIN_DT,
            str(getattr(e, "id", "")),
        ),
    )


def _row_timestamps(entry: Any, passport: CareerPassport) -> tuple[datetime, datetime]:
    """Profile-backed rows have no TimestampMixin; use Passport timestamps."""
    created = getattr(entry, "created_at", None) or passport.created_at
    updated = getattr(entry, "updated_at", None) or passport.updated_at
    return created, updated


def _meta_read(raw: dict[str, Any] | None) -> PassportRecordMetaRead:
    validated = PassportRecordMeta.model_validate(raw or _PROFILE_BACKED_META)
    return PassportRecordMetaRead(
        source_status=validated.source_status.value,
        support_status=validated.support_status.value,
        verification_status=validated.verification_status.value,
    )


def _parse_taxonomy_obj(raw: Any) -> PassportTaxonomyReference | None:
    if raw is None:
        return None
    return PassportTaxonomyReference.model_validate(raw)


def _parse_taxonomy_list(raw: Any) -> list[PassportTaxonomyReference]:
    if not raw:
        return []
    return [PassportTaxonomyReference.model_validate(item) for item in raw]


def _passport_load_options(*, for_update: bool = False, populate_existing: bool = False):
    stmt = (
        select(CareerPassport)
        .options(
            selectinload(CareerPassport.owner),
            selectinload(CareerPassport.profile).selectinload(Profile.work_experiences),
            selectinload(CareerPassport.profile).selectinload(Profile.educations),
            selectinload(CareerPassport.profile).selectinload(Profile.projects),
            selectinload(CareerPassport.profile).selectinload(Profile.skills),
            selectinload(CareerPassport.profile).selectinload(Profile.certifications),
            selectinload(CareerPassport.targets),
        )
    )
    if for_update:
        stmt = stmt.with_for_update(of=CareerPassport)
    if populate_existing:
        stmt = stmt.execution_options(populate_existing=True)
    return stmt


async def _load_owned_passport(
    db: AsyncSession,
    user_id: UUID,
    *,
    for_update: bool = False,
    populate_existing: bool = False,
) -> CareerPassport | None:
    stmt = _passport_load_options(
        for_update=for_update,
        populate_existing=populate_existing,
    ).where(CareerPassport.owner_user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _load_passport_by_id(
    db: AsyncSession,
    passport_id: UUID,
) -> CareerPassport:
    stmt = _passport_load_options(populate_existing=True).where(
        CareerPassport.id == passport_id
    )
    result = await db.execute(stmt)
    passport = result.scalar_one_or_none()
    if passport is None:
        raise NotFoundError("Passport not found.")
    return passport


async def _ensure_profile(db: AsyncSession, user: User) -> Profile:
    result = await db.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is not None:
        return profile
    profile = Profile(user_id=user.id)
    db.add(profile)
    try:
        async with db.begin_nested():
            await db.flush()
    except IntegrityError:
        result = await db.execute(select(Profile).where(Profile.user_id == user.id))
        profile = result.scalar_one()
    return profile


async def get_or_create_passport_for_user(
    db: AsyncSession,
    user: User,
) -> tuple[CareerPassport, bool]:
    """
    Lazily create one Passport wrapping the user's Profile.

    Returns (passport, created). Commits only when creation is necessary.
    """
    existing = await _load_owned_passport(db, user.id, for_update=False)
    if existing is not None:
        return existing, False

    profile = await _ensure_profile(db, user)
    passport = CareerPassport(
        owner_user_id=user.id,
        profile_id=profile.id,
    )
    db.add(passport)
    created = True
    try:
        async with db.begin_nested():
            await db.flush()
    except IntegrityError:
        created = False

    await db.commit()

    loaded = await _load_owned_passport(
        db, user.id, for_update=False, populate_existing=True
    )
    if loaded is None:
        raise NotFoundError("Passport not found.")
    return loaded, created


async def _lock_passport_for_mutation(
    db: AsyncSession,
    user: User,
    expected_version: int,
) -> CareerPassport:
    passport = await _load_owned_passport(db, user.id, for_update=True)
    if passport is None:
        # Lazy-create then re-lock
        await get_or_create_passport_for_user(db, user)
        passport = await _load_owned_passport(db, user.id, for_update=True)
    if passport is None:
        raise NotFoundError("Passport not found.")
    if passport.owner_user_id != user.id:
        raise NotFoundError("Passport not found.")
    if passport.version != expected_version:
        raise ConflictError(
            "Passport version conflict.",
            details={
                "expected_version": expected_version,
                "current_version": passport.version,
            },
        )
    return passport


async def _commit_versioned(
    db: AsyncSession,
    passport: CareerPassport,
) -> CareerPassport:
    passport.version = passport.version + 1
    await db.commit()
    return await _load_passport_by_id(db, passport.id)


def to_passport_read(passport: CareerPassport) -> PassportRead:
    profile = passport.profile
    owner = passport.owner

    try:
        section_prefs = [
            PassportSectionPreference.model_validate(item)
            for item in (passport.section_preferences or [])
        ]
    except ValidationError as exc:
        raise ValidationFailedError(
            "Stored section_preferences failed validation.",
            details=_safe_validation_details(exc),
        ) from exc

    profile_payload = {field: getattr(profile, field) for field in _PROFILE_FIELDS}
    profile_payload["record_meta"] = passport.profile_record_meta or _PROFILE_BACKED_META
    validated_profile = _validate_contract(PassportProfile, profile_payload)

    experiences = [
        _map_experience(entry, passport)
        for entry in _sorted_entries(list(profile.work_experiences or []))
    ]
    education = [
        _map_education(entry, passport)
        for entry in _sorted_entries(list(profile.educations or []))
    ]
    projects = [
        _map_project(entry, passport)
        for entry in _sorted_entries(list(profile.projects or []))
    ]
    skills = [
        _map_skill(entry, passport) for entry in _sorted_entries(list(profile.skills or []))
    ]
    credentials = [
        _map_credential(entry, passport)
        for entry in _sorted_entries(list(profile.certifications or []))
    ]
    targets = [
        _map_target(entry) for entry in _sorted_entries(list(passport.targets or []))
    ]

    return PassportRead(
        id=passport.id,
        subject_id=passport.subject_id,
        display_name=owner.full_name if owner else None,
        headline=profile.professional_headline,
        summary=profile.bio_summary,
        visibility=passport.visibility,
        version=passport.version,
        section_preferences=section_prefs,
        profile=PassportProfileRead(
            **validated_profile.model_dump(exclude={"record_meta"}),
            record_meta=_meta_read(passport.profile_record_meta),
        ),
        experiences=experiences,
        education=education,
        projects=projects,
        skills=skills,
        credentials=credentials,
        targets=targets,
        created_at=passport.created_at,
        updated_at=passport.updated_at,
    )


def _map_experience(entry: WorkExperience, passport: CareerPassport) -> PassportExperienceRead:
    payload = {
        "job_title": entry.job_title,
        "company_name": entry.company_name,
        "company_url": entry.company_url,
        "location": entry.location,
        "employment_type": entry.employment_type,
        "start_date": entry.start_date,
        "end_date": entry.end_date,
        "is_current": entry.is_current,
        "description_bullets": entry.description_bullets or [],
        "order_index": entry.order_index,
        "role_taxonomy": entry.passport_role_taxonomy,
        "record_meta": entry.passport_record_meta or _PROFILE_BACKED_META,
    }
    validated = _validate_contract(PassportExperience, payload)
    created_at, updated_at = _row_timestamps(entry, passport)
    return PassportExperienceRead(
        id=entry.id,
        created_at=created_at,
        updated_at=updated_at,
        **validated.model_dump(exclude={"record_meta"}),
        record_meta=_meta_read(entry.passport_record_meta),
    )


def _map_education(entry: Education, passport: CareerPassport) -> PassportEducationRead:
    payload = {
        "degree": entry.degree,
        "field_of_study": entry.field_of_study,
        "institution": entry.institution,
        "location": entry.location,
        "start_date": entry.start_date,
        "end_date": entry.end_date,
        "is_current": entry.is_current,
        "grade": entry.grade,
        "description_bullets": entry.description_bullets or [],
        "relevant_coursework": entry.relevant_coursework or [],
        "order_index": entry.order_index,
        "record_meta": entry.passport_record_meta or _PROFILE_BACKED_META,
    }
    validated = _validate_contract(PassportEducation, payload)
    created_at, updated_at = _row_timestamps(entry, passport)
    return PassportEducationRead(
        id=entry.id,
        created_at=created_at,
        updated_at=updated_at,
        **validated.model_dump(exclude={"record_meta"}),
        record_meta=_meta_read(entry.passport_record_meta),
    )


def _map_project(entry: Project, passport: CareerPassport) -> PassportProjectRead:
    payload = {
        "title": entry.title,
        "description": entry.description,
        "technologies": entry.technologies or [],
        "project_url": entry.project_url,
        "start_date": entry.start_date,
        "end_date": entry.end_date,
        "role": entry.role,
        "key_achievements": entry.key_achievements or [],
        "order_index": entry.order_index,
        "skill_taxonomy": entry.passport_skill_taxonomy or [],
        "record_meta": entry.passport_record_meta or _PROFILE_BACKED_META,
    }
    validated = _validate_contract(PassportProject, payload)
    created_at, updated_at = _row_timestamps(entry, passport)
    return PassportProjectRead(
        id=entry.id,
        created_at=created_at,
        updated_at=updated_at,
        **validated.model_dump(exclude={"record_meta"}),
        record_meta=_meta_read(entry.passport_record_meta),
    )


def _map_skill(entry: Skill, passport: CareerPassport) -> PassportSkillRead:
    payload = {
        "name": entry.name,
        "skill_type": entry.skill_type,
        "category": entry.category,
        "proficiency": entry.proficiency,
        "order_index": entry.order_index,
        "taxonomy": entry.passport_taxonomy,
        "record_meta": entry.passport_record_meta or _PROFILE_BACKED_META,
    }
    validated = _validate_contract(PassportSkill, payload)
    created_at, updated_at = _row_timestamps(entry, passport)
    return PassportSkillRead(
        id=entry.id,
        created_at=created_at,
        updated_at=updated_at,
        **validated.model_dump(exclude={"record_meta"}),
        record_meta=_meta_read(entry.passport_record_meta),
    )


def _map_credential(entry: Certification, passport: CareerPassport) -> PassportCredentialRead:
    payload = {
        "credential_type": entry.passport_credential_type or PassportCredentialType.CERTIFICATION.value,
        "name": entry.name,
        "issuing_organization": entry.issuing_organization,
        "issue_date": entry.issue_date,
        "expiry_date": entry.expiry_date,
        "credential_id": entry.credential_id,
        "credential_url": entry.credential_url,
        "order_index": entry.order_index,
        "record_meta": entry.passport_record_meta or _PROFILE_BACKED_META,
    }
    validated = _validate_contract(PassportCredentialRef, payload)
    created_at, updated_at = _row_timestamps(entry, passport)
    return PassportCredentialRead(
        id=entry.id,
        created_at=created_at,
        updated_at=updated_at,
        **validated.model_dump(exclude={"record_meta"}),
        record_meta=_meta_read(entry.passport_record_meta),
    )


def _map_target(entry: PassportTarget) -> PassportTargetRead:
    payload = {
        "target_role_text": entry.target_role_text,
        "role_taxonomy": entry.role_taxonomy,
        "pathway_type": entry.pathway_type,
        "target_country": entry.target_country,
        "target_region": entry.target_region,
        "target_industry": entry.target_industry,
        "target_seniority": entry.target_seniority,
        "time_horizon": entry.time_horizon,
        "priority": entry.priority,
        "order_index": entry.order_index,
        "record_meta": entry.passport_record_meta or _NATIVE_META,
    }
    validated = _validate_contract(PassportTargetContract, payload)
    return PassportTargetRead(
        id=entry.id,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        **validated.model_dump(exclude={"record_meta"}),
        record_meta=_meta_read(entry.passport_record_meta),
    )


def envelope_for(passport: CareerPassport) -> PassportEnvelope:
    return PassportEnvelope(data=to_passport_read(passport))


async def get_passport_aggregate(db: AsyncSession, user: User) -> PassportEnvelope:
    passport, _created = await get_or_create_passport_for_user(db, user)
    return envelope_for(passport)


async def patch_passport_aggregate(
    db: AsyncSession,
    user: User,
    payload: PassportPatch,
) -> PassportEnvelope:
    passport = await _lock_passport_for_mutation(db, user, payload.expected_version)

    if "subject_id" in payload.model_fields_set:
        if payload.subject_id is None:
            passport.subject_id = None
        else:
            subject = await ensure_owned_subject(db, payload.subject_id, user.id)
            if subject is None:
                raise NotFoundError("Career subject not found.")
            passport.subject_id = subject.id

    if payload.section_preferences is not None:
        passport.section_preferences = [
            pref.model_dump(mode="json") for pref in payload.section_preferences
        ]

    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)


async def patch_passport_profile(
    db: AsyncSession,
    user: User,
    payload: PassportProfilePatch,
) -> PassportEnvelope:
    passport = await _lock_passport_for_mutation(db, user, payload.expected_version)
    profile = passport.profile

    merged: dict[str, Any] = {field: getattr(profile, field) for field in _PROFILE_FIELDS}
    for field in _PROFILE_FIELDS:
        if field in payload.model_fields_set:
            merged[field] = getattr(payload, field)
    merged["record_meta"] = passport.profile_record_meta or _PROFILE_BACKED_META
    validated = _validate_contract(PassportProfile, merged)

    for field in _PROFILE_FIELDS:
        if field in payload.model_fields_set:
            setattr(profile, field, getattr(validated, field))

    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)


def _collection_cfg(collection: str) -> dict[str, Any]:
    if collection not in _COLLECTION_MAP:
        raise ValidationFailedError(f"Unknown Passport collection: {collection}")
    return _COLLECTION_MAP[collection]


async def create_profile_section_entry(
    db: AsyncSession,
    user: User,
    collection: str,
    data: dict[str, Any],
    fields_set: set[str],
    expected_version: int,
) -> PassportEnvelope:
    cfg = _collection_cfg(collection)
    passport = await _lock_passport_for_mutation(db, user, expected_version)

    contract_data = {k: v for k, v in data.items() if k != "expected_version"}
    # Fill defaults for create validation
    if cfg.get("taxonomy_is_list") and cfg["taxonomy_contract_field"] not in contract_data:
        contract_data[cfg["taxonomy_contract_field"]] = []
    if collection == "credentials" and "credential_type" not in contract_data:
        contract_data["credential_type"] = PassportCredentialType.CERTIFICATION
    contract_data["record_meta"] = _PROFILE_BACKED_META
    validated = _validate_contract(cfg["validator"], contract_data)

    model_cls = cfg["model"]
    kwargs: dict[str, Any] = {"profile_id": passport.profile_id}
    for field in cfg["legacy_fields"]:
        kwargs[field] = getattr(validated, field)

    tax_field = cfg.get("taxonomy_field")
    tax_contract = cfg.get("taxonomy_contract_field")
    if tax_field and tax_contract:
        raw = getattr(validated, tax_contract)
        if cfg.get("taxonomy_is_list"):
            kwargs[tax_field] = _dump_taxonomy(raw) or []
        else:
            dumped = _dump_taxonomy(raw)
            if dumped is not None:
                kwargs[tax_field] = dumped
            # omit key when None so DB stores SQL NULL (not JSON null)

    if cfg.get("credential_type_field"):
        kwargs[cfg["credential_type_field"]] = _enum_value(validated.credential_type)

    kwargs["passport_record_meta"] = dict(_PROFILE_BACKED_META)

    entry = model_cls(**kwargs)
    db.add(entry)
    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)


async def patch_profile_section_entry(
    db: AsyncSession,
    user: User,
    collection: str,
    entry_id: UUID,
    data: dict[str, Any],
    fields_set: set[str],
    expected_version: int,
) -> PassportEnvelope:
    cfg = _collection_cfg(collection)
    passport = await _lock_passport_for_mutation(db, user, expected_version)
    model_cls = cfg["model"]

    result = await db.execute(
        select(model_cls).where(
            model_cls.id == entry_id,
            model_cls.profile_id == passport.profile_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotFoundError(cfg["not_found"])

    merged: dict[str, Any] = {}
    for field in cfg["legacy_fields"]:
        merged[field] = getattr(entry, field)

    tax_field = cfg.get("taxonomy_field")
    tax_contract = cfg.get("taxonomy_contract_field")
    if tax_field and tax_contract:
        if cfg.get("taxonomy_is_list"):
            merged[tax_contract] = _parse_taxonomy_list(getattr(entry, tax_field))
        else:
            merged[tax_contract] = _parse_taxonomy_obj(getattr(entry, tax_field))

    if cfg.get("credential_type_field"):
        merged["credential_type"] = getattr(entry, cfg["credential_type_field"])

    mutable = fields_set - {"expected_version"}
    for field in mutable:
        merged[field] = data[field]

    merged["record_meta"] = getattr(entry, "passport_record_meta", None) or _PROFILE_BACKED_META
    validated = _validate_contract(cfg["validator"], merged)

    for field in cfg["legacy_fields"]:
        if field in mutable:
            setattr(entry, field, getattr(validated, field))

    if tax_field and tax_contract and tax_contract in mutable:
        raw = getattr(validated, tax_contract)
        if cfg.get("taxonomy_is_list"):
            setattr(entry, tax_field, _dump_taxonomy(raw) or [])
        else:
            dumped = _dump_taxonomy(raw)
            # SQL NULL (not JSON null) required by jsonb object check constraints
            setattr(entry, tax_field, dumped if dumped is not None else sa_null())

    if cfg.get("credential_type_field") and "credential_type" in mutable:
        setattr(entry, cfg["credential_type_field"], _enum_value(validated.credential_type))

    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)


async def delete_profile_section_entry(
    db: AsyncSession,
    user: User,
    collection: str,
    entry_id: UUID,
    expected_version: int,
) -> PassportEnvelope:
    cfg = _collection_cfg(collection)
    passport = await _lock_passport_for_mutation(db, user, expected_version)
    model_cls = cfg["model"]

    result = await db.execute(
        select(model_cls).where(
            model_cls.id == entry_id,
            model_cls.profile_id == passport.profile_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotFoundError(cfg["not_found"])

    await db.delete(entry)
    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)


async def reorder_profile_section(
    db: AsyncSession,
    user: User,
    collection: str,
    payload: PassportReorder,
) -> PassportEnvelope:
    cfg = _collection_cfg(collection)
    passport = await _lock_passport_for_mutation(db, user, payload.expected_version)
    model_cls = cfg["model"]

    result = await db.execute(
        select(model_cls).where(model_cls.profile_id == passport.profile_id)
    )
    entries = list(result.scalars().all())
    owned_ids = {e.id for e in entries}
    supplied = set(payload.ordered_ids)

    if supplied != owned_ids:
        raise ValidationFailedError(
            "ordered_ids must be the exact set of owned entries for this collection.",
            details={
                "owned_count": len(owned_ids),
                "supplied_count": len(supplied),
            },
        )

    by_id = {e.id: e for e in entries}
    for index, entry_id in enumerate(payload.ordered_ids):
        by_id[entry_id].order_index = index

    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)


# ---------------------------------------------------------------------------
# Targets (Passport-owned)
# ---------------------------------------------------------------------------


async def create_target(
    db: AsyncSession,
    user: User,
    payload: PassportTargetCreate,
) -> PassportEnvelope:
    passport = await _lock_passport_for_mutation(db, user, payload.expected_version)
    contract_data = payload.model_dump(exclude={"expected_version"})
    contract_data["record_meta"] = _NATIVE_META
    validated = _validate_contract(PassportTargetContract, contract_data)

    target_kwargs: dict[str, Any] = {
        "passport_id": passport.id,
        "target_role_text": validated.target_role_text,
        "pathway_type": _enum_value(validated.pathway_type),
        "target_country": validated.target_country,
        "target_region": validated.target_region,
        "target_industry": validated.target_industry,
        "target_seniority": _enum_value(validated.target_seniority),
        "time_horizon": validated.time_horizon,
        "priority": validated.priority,
        "order_index": validated.order_index,
        "passport_record_meta": dict(_NATIVE_META),
    }
    if validated.role_taxonomy is not None:
        target_kwargs["role_taxonomy"] = _dump_taxonomy(validated.role_taxonomy)
    target = PassportTarget(**target_kwargs)
    db.add(target)
    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)


async def patch_target(
    db: AsyncSession,
    user: User,
    entry_id: UUID,
    payload: PassportTargetPatch,
) -> PassportEnvelope:
    passport = await _lock_passport_for_mutation(db, user, payload.expected_version)
    result = await db.execute(
        select(PassportTarget).where(
            PassportTarget.id == entry_id,
            PassportTarget.passport_id == passport.id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError("Target entry not found.")

    merged = {
        "target_role_text": target.target_role_text,
        "role_taxonomy": _parse_taxonomy_obj(target.role_taxonomy),
        "pathway_type": target.pathway_type,
        "target_country": target.target_country,
        "target_region": target.target_region,
        "target_industry": target.target_industry,
        "target_seniority": target.target_seniority,
        "time_horizon": target.time_horizon,
        "priority": target.priority,
        "order_index": target.order_index,
        "record_meta": target.passport_record_meta or _NATIVE_META,
    }
    mutable = payload.model_fields_set - {"expected_version"}
    data = payload.model_dump(exclude={"expected_version"})
    for field in mutable:
        merged[field] = data[field]

    validated = _validate_contract(PassportTargetContract, merged)

    field_map = {
        "target_role_text": "target_role_text",
        "target_country": "target_country",
        "target_region": "target_region",
        "target_industry": "target_industry",
        "time_horizon": "time_horizon",
        "priority": "priority",
        "order_index": "order_index",
    }
    for src, dest in field_map.items():
        if src in mutable:
            setattr(target, dest, getattr(validated, src))
    if "role_taxonomy" in mutable:
        dumped = _dump_taxonomy(validated.role_taxonomy)
        target.role_taxonomy = dumped if dumped is not None else sa_null()
    if "pathway_type" in mutable:
        target.pathway_type = _enum_value(validated.pathway_type)
    if "target_seniority" in mutable:
        target.target_seniority = _enum_value(validated.target_seniority)

    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)


async def delete_target(
    db: AsyncSession,
    user: User,
    entry_id: UUID,
    expected_version: int,
) -> PassportEnvelope:
    passport = await _lock_passport_for_mutation(db, user, expected_version)
    result = await db.execute(
        select(PassportTarget).where(
            PassportTarget.id == entry_id,
            PassportTarget.passport_id == passport.id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError("Target entry not found.")
    await db.delete(target)
    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)


async def reorder_targets(
    db: AsyncSession,
    user: User,
    payload: PassportReorder,
) -> PassportEnvelope:
    passport = await _lock_passport_for_mutation(db, user, payload.expected_version)
    result = await db.execute(
        select(PassportTarget).where(PassportTarget.passport_id == passport.id)
    )
    entries = list(result.scalars().all())
    owned_ids = {e.id for e in entries}
    supplied = set(payload.ordered_ids)
    if supplied != owned_ids:
        raise ValidationFailedError(
            "ordered_ids must be the exact set of owned entries for this collection.",
            details={
                "owned_count": len(owned_ids),
                "supplied_count": len(supplied),
            },
        )
    by_id = {e.id: e for e in entries}
    for index, entry_id in enumerate(payload.ordered_ids):
        by_id[entry_id].order_index = index
    passport = await _commit_versioned(db, passport)
    return envelope_for(passport)
