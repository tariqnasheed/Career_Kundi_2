"""
agents/roadmap
===================
Career Roadmap (§4.5).

Public entry points (everything the API route layer should call):

    from app.agents.roadmap.graph import run_roadmap_generation_pipeline, run_skill_refresh_pipeline

See `graph.py` for the LangGraph wiring (a hand-built 9-node `StateGraph`
for full generation, plus the standard `build_revision_pipeline()` shape
for the lightweight single-skill refresh), `agents.py` for the concrete
Guardrail/Planner/RoleTaxonomy/SkillDecomposer/ResourceFinder/StudyMaterial/
PracticeGenerator/TimelineOptimizer/Reflector implementations, `state.py`
for both pipelines' state shapes, and `mock_data.py` for the content-aware
offline stand-ins used when no LLM API key is configured.
"""
