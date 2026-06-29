"""Backward-compatible re-exports for the NPI Orchestrator agent.

The intake router has been replaced by :mod:`orchestrator_agent`, which returns
an explicit ordered ``agents_to_call`` list based on customer needs.
"""

from __future__ import annotations

from .orchestrator_agent import (
    CustomerRoutePlan,
    OrchestrationPlan,
    plan_agent_calls,
    route_customer_input,
)

__all__ = [
    "CustomerRoutePlan",
    "OrchestrationPlan",
    "plan_agent_calls",
    "route_customer_input",
]
