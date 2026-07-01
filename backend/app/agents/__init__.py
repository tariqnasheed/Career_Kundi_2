"""
app/agents
=============
Every feature's multi-agent pipeline lives under this package:

    agents/common/        shared Guardrail/Planner/Executor/Reflector base
                           classes + LangGraph wiring helpers (this is the
                           framework every feature builds on — see
                           agents/common/__init__.py)
    agents/job_search/     Job Search & Discovery + Interview Pack generation
    agents/cv_builder/     CV/Resume Builder
    agents/roadmap/        Career Roadmap Generator
    agents/chatbot/        AI Assistant Chatbot

Each feature package exposes a single `run_<feature>_pipeline(...)`
coroutine that API routes call — the LangGraph internals (nodes, edges,
revision loops) are an implementation detail the route layer never touches
directly.
"""
