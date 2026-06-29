"""NPI Orchestrator: a multi-agent system for the New Product Introduction process.

One specialized agent governs each of the six NPI phases (PH1 NEEDS -> PH6
LAUNCH); the :class:`NPIOrchestrator` routes a project across them, threading
gate hand-offs forward and tracking GO / NO-GO decisions.
"""

from __future__ import annotations

from .agents import PhaseAgent
from .meta import decision_label, normalize_decision, split_phase_response
from .orchestrator import NPIOrchestrator, PhaseResult
from .customer_router import CustomerRoutePlan, OrchestrationPlan, plan_agent_calls, route_customer_input
from .phases import PHASES, PHASES_BY_ID, Phase, get_phase, phase_ids_from
from .response_synth import CustomerResponse, synthesize_customer_response
from .runner import run_agent_turn, runtime_ready
from .runtime_env import DEFAULT_BACKEND
from .workflow import CustomerWorkflowResult, run_customer_workflow

__all__ = [
    "PhaseAgent",
    "NPIOrchestrator",
    "PhaseResult",
    "CustomerRoutePlan",
    "OrchestrationPlan",
    "CustomerResponse",
    "CustomerWorkflowResult",
    "plan_agent_calls",
    "route_customer_input",
    "run_customer_workflow",
    "synthesize_customer_response",
    "PHASES",
    "PHASES_BY_ID",
    "Phase",
    "get_phase",
    "phase_ids_from",
    "run_agent_turn",
    "runtime_ready",
    "DEFAULT_BACKEND",
    "split_phase_response",
    "decision_label",
    "normalize_decision",
]
