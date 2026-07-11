"""
Tiny internal seed catalog for taxonomy contract tests (0051-F1).

Illustrative only — not an external taxonomy ingestion (O*NET/ESCO/NIST).
Not wired into CV Builder, Roadmap, Job Search, or role packs in F1.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.taxonomy.contracts import (
    CanonicalRole,
    CareerDomain,
    ConfidenceLevel,
    PathwayGoal,
    PathwayType,
    RoleAlias,
    RoleFamily,
    SeniorityLevel,
    Skill,
    SkillCluster,
    SourceType,
)


@dataclass(frozen=True, slots=True)
class TaxonomySeedCatalog:
    domains: tuple[CareerDomain, ...]
    role_families: tuple[RoleFamily, ...]
    canonical_roles: tuple[CanonicalRole, ...]
    role_aliases: tuple[RoleAlias, ...]
    skill_clusters: tuple[SkillCluster, ...]
    skills: tuple[Skill, ...]
    pathway_goals: tuple[PathwayGoal, ...]


def _build_seed_catalog() -> TaxonomySeedCatalog:
    domains = (
        CareerDomain(
            id="technology",
            label="Technology",
            description="Software and digital product roles",
            aliases=["tech", "IT"],
        ),
        CareerDomain(
            id="engineering",
            label="Engineering",
            description="Engineering disciplines outside pure software",
            aliases=["eng"],
        ),
        CareerDomain(
            id="healthcare",
            label="Healthcare",
            description="Clinical and care delivery roles",
            aliases=["health", "clinical"],
        ),
        CareerDomain(
            id="business_operations",
            label="Business Operations",
            description="Delivery, coordination, and operations roles",
            aliases=["ops", "business ops"],
        ),
    )

    role_families = (
        RoleFamily(
            id="software_engineering",
            domain_id="technology",
            label="Software Engineering",
            aliases=["swe", "software eng"],
            example_roles=["software_engineer", "backend_engineer"],
        ),
        RoleFamily(
            id="electrical_engineering",
            domain_id="engineering",
            label="Electrical Engineering",
            aliases=["EE"],
            example_roles=["electrical_engineer"],
        ),
        RoleFamily(
            id="clinical_healthcare",
            domain_id="healthcare",
            label="Clinical Healthcare",
            aliases=["clinical"],
            example_roles=["clinical_pharmacist"],
        ),
        RoleFamily(
            id="project_management",
            domain_id="business_operations",
            label="Project Management",
            aliases=["PM"],
            example_roles=["project_manager"],
        ),
    )

    canonical_roles = (
        CanonicalRole(
            id="software_engineer",
            role_family_id="software_engineering",
            title="Software Engineer",
            aliases=["Software Developer", "SWE"],
            description="Builds and maintains software systems",
            seniority_range=[SeniorityLevel.JUNIOR, SeniorityLevel.MID, SeniorityLevel.SENIOR],
            common_skills=["python", "system_design"],
            related_roles=["project_manager"],
        ),
        CanonicalRole(
            id="electrical_engineer",
            role_family_id="electrical_engineering",
            title="Electrical Engineer",
            aliases=["EE"],
            description="Designs electrical systems and components",
            seniority_range=[SeniorityLevel.ENTRY, SeniorityLevel.MID, SeniorityLevel.SENIOR],
            common_skills=["load_calculations"],
            related_roles=[],
        ),
        CanonicalRole(
            id="clinical_pharmacist",
            role_family_id="clinical_healthcare",
            title="Clinical Pharmacist",
            aliases=["Hospital Pharmacist"],
            description="Supports safe medication use in clinical settings",
            seniority_range=[SeniorityLevel.MID, SeniorityLevel.SENIOR],
            common_skills=["medication_safety"],
            related_roles=[],
        ),
        CanonicalRole(
            id="project_manager",
            role_family_id="project_management",
            title="Project Manager",
            aliases=["PM", "Delivery Manager"],
            description="Coordinates delivery across stakeholders",
            seniority_range=[SeniorityLevel.MID, SeniorityLevel.SENIOR, SeniorityLevel.MANAGER],
            common_skills=["stakeholder_coordination"],
            related_roles=["software_engineer"],
        ),
    )

    role_aliases = (
        RoleAlias(
            alias="Software Developer",
            canonical_role_id="software_engineer",
            source=SourceType.EXTERNAL_TAXONOMY_REFERENCE,
            confidence=ConfidenceLevel.SUGGESTED,
        ),
        RoleAlias(
            alias="PM",
            canonical_role_id="project_manager",
            source=SourceType.USER_PROVIDED,
            confidence=ConfidenceLevel.PROFILE_SUPPORTED,
        ),
    )

    skill_clusters = (
        SkillCluster(
            id="programming",
            domain_id="technology",
            label="Programming",
            aliases=["coding"],
        ),
        SkillCluster(
            id="electrical_design",
            domain_id="engineering",
            label="Electrical Design",
            aliases=["power design"],
        ),
        SkillCluster(
            id="clinical_safety",
            domain_id="healthcare",
            label="Clinical Safety",
            aliases=["patient safety"],
        ),
        SkillCluster(
            id="delivery_management",
            domain_id="business_operations",
            label="Delivery Management",
            aliases=["delivery"],
        ),
    )

    skills = (
        Skill(
            id="python",
            cluster_id="programming",
            label="Python",
            aliases=["Python3"],
            evidence_examples=["Shipped a Python service to production"],
            tool_examples=["pytest", "Django"],
        ),
        Skill(
            id="load_calculations",
            cluster_id="electrical_design",
            label="Load Calculations",
            aliases=["electrical load calc"],
            evidence_examples=["Completed panel load schedule"],
            tool_examples=["ETAP"],
        ),
        Skill(
            id="medication_safety",
            cluster_id="clinical_safety",
            label="Medication Safety",
            aliases=["med safety"],
            evidence_examples=["Led medication reconciliation review"],
            tool_examples=["EHR"],
        ),
        Skill(
            id="stakeholder_coordination",
            cluster_id="delivery_management",
            label="Stakeholder Coordination",
            aliases=["stakeholder management"],
            evidence_examples=["Ran weekly cross-team status reviews"],
            tool_examples=["Jira", "Confluence"],
        ),
    )

    pathway_goals = (
        PathwayGoal(
            id="gap_to_software_engineer",
            pathway_type=PathwayType.SKILL_GAP,
            target_role_id="software_engineer",
            goal_text="Close skill gaps toward Software Engineer",
            source=SourceType.USER_PROVIDED,
            confidence=ConfidenceLevel.PROFILE_SUPPORTED,
        ),
        PathwayGoal(
            id="switch_to_project_manager",
            pathway_type=PathwayType.CAREER_SWITCH,
            target_role_id="project_manager",
            goal_text="Switch from engineering IC work into project management",
            source=SourceType.MODEL_INFERRED,
            confidence=ConfidenceLevel.SUGGESTED,
        ),
    )

    return TaxonomySeedCatalog(
        domains=domains,
        role_families=role_families,
        canonical_roles=canonical_roles,
        role_aliases=role_aliases,
        skill_clusters=skill_clusters,
        skills=skills,
        pathway_goals=pathway_goals,
    )


SEED_CATALOG: TaxonomySeedCatalog = _build_seed_catalog()


def get_seed_catalog() -> TaxonomySeedCatalog:
    """Return the internal illustrative seed catalog (immutable tuple payload)."""
    return SEED_CATALOG
