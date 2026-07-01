"""
tools/graph_rag.py
======================
GraphRAG: a `networkx` knowledge graph connecting skills, roles,
industries, and learning resources, queried via graph traversal rather than
flat vector similarity. This is what answers relational questions a vector
store alone cannot, e.g. "what skills bridge Data Analyst to Data
Scientist?" or "what should I learn right after SQL on a Data Engineer
track?" (§2 "GraphRAG").

Persistence mirrors the RAG vector store: built from
`app.data.seed_graph` on first boot and pickled to
`settings.graph_store_path`; subsequent agent activity (ResourceFinderAgent
discovering a new course, JobEnricherAgent linking a newly scraped role to
its skill cluster) calls the `add_*_edge` helpers to grow the graph in
place, and `save_knowledge_graph()` persists it.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import networkx as nx

from app.core.config import settings
from app.core.logging import get_logger
from app.data.seed_graph import (
    INDUSTRIES,
    ROLE_IN_INDUSTRY,
    ROLE_REQUIRES_SKILL,
    ROLES,
    SKILL_BRIDGES_ROLE,
    SKILL_PREREQUISITES,
    SKILL_RELATED,
    SKILLS,
)

logger = get_logger(__name__)

_GRAPH_SINGLETON: nx.MultiDiGraph | None = None


def _build_seed_graph() -> nx.MultiDiGraph:
    """Construct the initial knowledge graph from app/data/seed_graph.py."""
    g = nx.MultiDiGraph()

    for role in ROLES:
        g.add_node(role, node_type="role")
    for skill in SKILLS:
        g.add_node(skill, node_type="skill")
    for industry in INDUSTRIES:
        g.add_node(industry, node_type="industry")

    for role, skill, importance in ROLE_REQUIRES_SKILL:
        g.add_edge(role, skill, relation="requires", importance=importance)
    for skill_a, skill_b in SKILL_PREREQUISITES:
        g.add_edge(skill_a, skill_b, relation="prerequisite_of")
    for skill, role in SKILL_BRIDGES_ROLE:
        g.add_edge(skill, role, relation="bridges")
    for skill_a, skill_b in SKILL_RELATED:
        g.add_edge(skill_a, skill_b, relation="related_to")
        g.add_edge(skill_b, skill_a, relation="related_to")
    for role, industry in ROLE_IN_INDUSTRY:
        g.add_edge(role, industry, relation="in_industry")

    return g


def get_knowledge_graph() -> nx.MultiDiGraph:
    """Return the process-wide knowledge graph singleton, loading from disk or seeding fresh."""
    global _GRAPH_SINGLETON
    if _GRAPH_SINGLETON is not None:
        return _GRAPH_SINGLETON

    path = Path(settings.graph_store_path)
    if path.exists():
        logger.info("knowledge_graph_loading_from_disk", path=str(path))
        with open(path, "rb") as f:
            _GRAPH_SINGLETON = pickle.load(f)
    else:
        logger.info("knowledge_graph_building_from_seed")
        _GRAPH_SINGLETON = _build_seed_graph()
        save_knowledge_graph()

    return _GRAPH_SINGLETON


def save_knowledge_graph() -> None:
    """Persist the current in-memory graph to disk so growth survives restarts."""
    path = Path(settings.graph_store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(get_knowledge_graph(), f)


# --- Traversal queries used by feature agents -----------------------------------------

def get_skills_for_role(role: str) -> list[dict]:
    """Return every skill a role `requires`, with importance, sorted critical-first."""
    g = get_knowledge_graph()
    if role not in g:
        return []
    order = {"critical": 0, "high": 1, "medium": 2, "nice-to-have": 3}
    edges = [
        {"skill": target, **data}
        for _, target, data in g.out_edges(role, data=True)
        if data.get("relation") == "requires"
    ]
    return sorted(edges, key=lambda e: order.get(e.get("importance", "medium"), 2))


def get_bridge_skills(role_a: str, role_b: str) -> list[str]:
    """
    Answer "what skills bridge role_a to role_b": skills required by role_b
    that role_a does NOT require, prioritizing ones explicitly tagged as a
    `bridges` edge into role_b.
    """
    g = get_knowledge_graph()
    skills_a = {s["skill"] for s in get_skills_for_role(role_a)}
    skills_b = {s["skill"] for s in get_skills_for_role(role_b)}
    gap = skills_b - skills_a

    explicit_bridges = {
        source for source, target, data in g.in_edges(role_b, data=True) if data.get("relation") == "bridges"
    }
    # Rank explicit bridge skills first, then remaining gap skills.
    ranked = [s for s in gap if s in explicit_bridges] + [s for s in gap if s not in explicit_bridges]
    return ranked


def get_prerequisites(skill: str) -> list[str]:
    """Return skills that should be learned BEFORE the given skill."""
    g = get_knowledge_graph()
    if skill not in g:
        return []
    return [
        source for source, target, data in g.in_edges(skill, data=True) if data.get("relation") == "prerequisite_of"
    ]


def get_related_skills(skill: str) -> list[str]:
    """Return laterally related/complementary skills (for roadmap 'lateral connections')."""
    g = get_knowledge_graph()
    if skill not in g:
        return []
    return [
        target for _, target, data in g.out_edges(skill, data=True) if data.get("relation") == "related_to"
    ]


def get_industries_for_role(role: str) -> list[str]:
    g = get_knowledge_graph()
    if role not in g:
        return []
    return [target for _, target, data in g.out_edges(role, data=True) if data.get("relation") == "in_industry"]


def add_skill_resource_edge(resource_title: str, resource_url: str, skill: str) -> None:
    """
    Record that a (possibly newly-scraped) learning resource teaches a
    skill, growing the graph at runtime as ResourceFinderAgent discovers new
    material. Idempotent: re-adding the same edge is a no-op in networkx.
    """
    g = get_knowledge_graph()
    g.add_node(resource_title, node_type="resource", url=resource_url)
    g.add_edge(resource_title, skill, relation="resource_for")
    save_knowledge_graph()


def ensure_role_node(role: str, skills: list[str] | None = None) -> None:
    """
    Add a custom/unrecognized role (§4.3 'Add New Role') to the graph on the
    fly, optionally wiring it to a list of skills discovered via web
    scraping (RoleTaxonomyAgent), so subsequent traversal queries work for
    roles outside the static O*NET/ESCO seed set.
    """
    g = get_knowledge_graph()
    if role not in g:
        g.add_node(role, node_type="role")
    for skill in skills or []:
        if skill not in g:
            g.add_node(skill, node_type="skill")
        g.add_edge(role, skill, relation="requires", importance="medium")
    save_knowledge_graph()
