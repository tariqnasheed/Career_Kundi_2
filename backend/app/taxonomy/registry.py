"""
In-memory taxonomy registry MVP (0051-F2).

Deterministic lookup over the tiny internal seed catalog.
No database, FastAPI, HTTP, or LLM dependencies.
"""

from __future__ import annotations

from app.taxonomy.catalog import TaxonomySeedCatalog, get_seed_catalog
from app.taxonomy.contracts import (
    CanonicalRole,
    ConfidenceLevel,
    PathwayType,
    Skill,
    SourceType,
    TaxonomyMatch,
)
from app.taxonomy.normalization import build_taxonomy_match, normalize_taxonomy_text


class TaxonomyRegistry:
    """Seed-backed in-memory indexes for roles, skills, and pathway types."""

    def __init__(self, catalog: TaxonomySeedCatalog) -> None:
        self._catalog = catalog
        self._roles_by_id: dict[str, CanonicalRole] = {
            role.id: role for role in catalog.canonical_roles
        }
        self._skills_by_id: dict[str, Skill] = {skill.id: skill for skill in catalog.skills}

        self._role_text_index: dict[str, str] = {}
        for role in catalog.canonical_roles:
            self._index_role_text(role.id, role.id)
            self._index_role_text(role.title, role.id)
            for alias in role.aliases:
                self._index_role_text(alias, role.id)
        for role_alias in catalog.role_aliases:
            self._index_role_text(role_alias.alias, role_alias.canonical_role_id)

        self._skill_text_index: dict[str, str] = {}
        for skill in catalog.skills:
            self._index_skill_text(skill.id, skill.id)
            self._index_skill_text(skill.label, skill.id)
            for alias in skill.aliases:
                self._index_skill_text(alias, skill.id)

    @classmethod
    def from_seed_catalog(cls) -> TaxonomyRegistry:
        return cls(get_seed_catalog())

    def _index_role_text(self, text: str, role_id: str) -> None:
        key = normalize_taxonomy_text(text)
        if not key:
            return
        # First writer wins — keep indexing deterministic and non-hallucinating.
        self._role_text_index.setdefault(key, role_id)

    def _index_skill_text(self, text: str, skill_id: str) -> None:
        key = normalize_taxonomy_text(text)
        if not key:
            return
        self._skill_text_index.setdefault(key, skill_id)

    def get_role(self, role_id: str) -> CanonicalRole | None:
        return self._roles_by_id.get((role_id or "").strip())

    def get_skill(self, skill_id: str) -> Skill | None:
        return self._skills_by_id.get((skill_id or "").strip())

    def match_role(
        self,
        text: str,
        *,
        source: SourceType = SourceType.MODEL_INFERRED,
        confidence: ConfidenceLevel = ConfidenceLevel.INFERRED,
    ) -> TaxonomyMatch:
        normalized = normalize_taxonomy_text(text)
        if not normalized:
            return build_taxonomy_match(
                input_text=text,
                matched_role_id=None,
                source=SourceType.UNKNOWN,
                confidence=ConfidenceLevel.UNKNOWN,
                explanation="no deterministic seed match found",
            )

        role_id = self._role_text_index.get(normalized)
        if role_id is None:
            return build_taxonomy_match(
                input_text=text,
                matched_role_id=None,
                source=SourceType.UNKNOWN,
                confidence=ConfidenceLevel.UNKNOWN,
                explanation="no deterministic seed match found",
            )

        role = self._roles_by_id[role_id]
        if normalized == normalize_taxonomy_text(role.id):
            how = "canonical id"
        elif normalized == normalize_taxonomy_text(role.title):
            how = "title"
        else:
            how = "alias"
        return build_taxonomy_match(
            input_text=text,
            matched_role_id=role_id,
            source=source,
            confidence=confidence,
            explanation=f"matched seed role by {how}",
        )

    def match_skill(
        self,
        text: str,
        *,
        source: SourceType = SourceType.MODEL_INFERRED,
        confidence: ConfidenceLevel = ConfidenceLevel.INFERRED,
    ) -> TaxonomyMatch:
        normalized = normalize_taxonomy_text(text)
        if not normalized:
            return build_taxonomy_match(
                input_text=text,
                matched_role_id=None,
                matched_skill_id=None,
                source=SourceType.UNKNOWN,
                confidence=ConfidenceLevel.UNKNOWN,
                explanation="no deterministic seed match found",
            )

        skill_id = self._skill_text_index.get(normalized)
        if skill_id is None:
            return build_taxonomy_match(
                input_text=text,
                matched_role_id=None,
                matched_skill_id=None,
                source=SourceType.UNKNOWN,
                confidence=ConfidenceLevel.UNKNOWN,
                explanation="no deterministic seed match found",
            )

        skill = self._skills_by_id[skill_id]
        if normalized == normalize_taxonomy_text(skill.id):
            how = "canonical id"
        elif normalized == normalize_taxonomy_text(skill.label):
            how = "label"
        else:
            how = "alias"
        return build_taxonomy_match(
            input_text=text,
            matched_role_id=None,
            matched_skill_id=skill_id,
            source=source,
            confidence=confidence,
            explanation=f"matched seed skill by {how}",
        )

    def list_pathway_types(self) -> list[PathwayType]:
        return list(PathwayType)

    def validate_pathway_type(self, value: str | PathwayType) -> PathwayType:
        if isinstance(value, PathwayType):
            return value
        cleaned = (value or "").strip()
        try:
            return PathwayType(cleaned)
        except ValueError as exc:
            raise ValueError(f"invalid pathway type: {value!r}") from exc

    def skills_for_role(self, role_id: str) -> list[Skill]:
        role = self.get_role(role_id)
        if role is None:
            return []
        out: list[Skill] = []
        seen: set[str] = set()
        for skill_ref in role.common_skills:
            skill = self.get_skill(skill_ref) or self._resolve_skill_by_text(skill_ref)
            if skill is None or skill.id in seen:
                continue
            seen.add(skill.id)
            out.append(skill)
        return out

    def related_roles(self, role_id: str) -> list[CanonicalRole]:
        role = self.get_role(role_id)
        if role is None:
            return []
        out: list[CanonicalRole] = []
        seen: set[str] = set()
        for related_id in role.related_roles:
            related = self.get_role(related_id)
            if related is None or related.id in seen:
                continue
            seen.add(related.id)
            out.append(related)
        return out

    def _resolve_skill_by_text(self, text: str) -> Skill | None:
        skill_id = self._skill_text_index.get(normalize_taxonomy_text(text))
        if skill_id is None:
            return None
        return self._skills_by_id.get(skill_id)
