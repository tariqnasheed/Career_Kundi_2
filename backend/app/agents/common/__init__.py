"""
agents/common
=================
The shared multi-agent framework implementing the platform-wide mandate
(§3 "Multi-Agent Architecture Mandate"): every feature pipeline follows the

    Guardrail -> Planner -> Executor -> Reflector

pattern, orchestrated as a LangGraph `StateGraph` with a revision loop
between Executor and Reflector. Rather than each feature reimplementing
input sanitization, prompt-injection detection, citation-integrity
checking, confidence scoring, and graph wiring from scratch, every feature
package imports from here:

    from app.agents.common.base import BaseAgent
    from app.agents.common.guardrail import BaseGuardrailAgent
    from app.agents.common.reflector import BaseReflectorAgent
    from app.agents.common.cost_monitor import CostMonitor
    from app.agents.common.graph_utils import build_revision_pipeline
    from app.agents.common.prompts import build_system_prompt
    from app.agents.common.security import sanitize_input, check_for_injection
    from app.agents.common.state import BaseAgentState

This is what makes "No exceptions — every feature gets the full pattern"
(the user's binding scope decision) tractable: the pattern is written once,
correctly, and every feature is a thin domain-specific layer on top.
"""
