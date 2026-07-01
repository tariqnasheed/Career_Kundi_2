"""
agents/job_search
=====================
Job Search & Discovery (§4.1) + Interview Pack Generation (§4.2).

Public entry points (everything the API route layer should call):

    from app.agents.job_search.graph import run_job_enrichment_pipeline, run_interview_pack_pipeline

See `graph.py` for the LangGraph wiring, `agents.py` for the concrete
Guardrail/Planner/Executor/CrossVerifier/Reflector implementations,
`state.py` for the two pipelines' state shapes, and `mock_data.py` for the
offline, content-aware stand-ins used when no LLM API key is configured.
"""
