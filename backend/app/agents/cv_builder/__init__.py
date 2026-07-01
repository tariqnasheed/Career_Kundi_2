"""
agents/cv_builder
======================
CV Builder & ATS Optimization (§4.3).

Public entry points (everything the API route layer should call):

    from app.agents.cv_builder.graph import run_cv_generation_pipeline, run_bullet_improvement_pipeline

See `graph.py` for the LangGraph wiring, `agents.py` for the concrete
Guardrail/Planner/Executor/Reflector implementations (plus the shared
`_check_bullet_fabrication()` safety net), `state.py` for the two
pipelines' state shapes, `mock_data.py` for the zero-fabrication-by-
construction offline stand-in used when no LLM API key is configured, and
`render.py` for the deterministic, non-generative step that turns an
approved draft into `GeneratedCV.rendered_content`.
"""
