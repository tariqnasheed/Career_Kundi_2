"""
agents/chatbot
==================
AI Assistant Chatbot (§4.7).

Public entry point (the ONLY symbol the route layer should import):

    from app.agents.chatbot.graph import run_chat_turn_pipeline

See ``graph.py`` for the hand-built 7-node LangGraph wiring, ``agents.py``
for the concrete Guardrail / MemoryAgent / IntentClassifier /
ActionDispatch / Planner / Executor / Reflector implementations, ``state.py``
for the per-turn pipeline state shape, and ``mock_data.py`` for the
content-aware offline stand-ins used when no LLM API key is configured.
"""
