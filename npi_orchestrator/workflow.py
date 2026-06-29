"""Agentic customer workflow: route -> phase agents -> customer response.

End-to-end pipeline driven by customer needs. Each step calls the Cursor
keyless ``cursor-agent`` CLI (backend ``cli``) by default.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .customer_router import CustomerRoutePlan
from .orchestrator import NPIOrchestrator, PhaseResult
from .response_synth import CustomerResponse, synthesize_customer_response
from .runtime_env import DEFAULT_BACKEND

_STATUS_LABEL = {
    "on_track": "On track",
    "at_risk": "At risk (conditions)",
    "blocked": "Blocked",
    "needs_info": "Needs more information",
}


@dataclass
class CustomerWorkflowResult:
    """Complete outcome of the customer-driven agentic workflow."""

    customer_input: str
    route_plan: CustomerRoutePlan
    phase_results: list[PhaseResult]
    customer_response: CustomerResponse
    backend: str = DEFAULT_BACKEND
    ran_at: str = ""

    @property
    def overall_status_label(self) -> str:
        return _STATUS_LABEL.get(
            self.customer_response.overall_status,
            self.customer_response.overall_status,
        )

    @property
    def agents_consulted(self) -> list[str]:
        return [r.agent_name for r in self.phase_results]

    def to_dict(self) -> dict:
        return {
            "customer_input": self.customer_input,
            "route_plan": asdict(self.route_plan),
            "phase_results": [asdict(r) for r in self.phase_results],
            "customer_response": {
                "visible": self.customer_response.visible,
                "overall_status": self.customer_response.overall_status,
                "key_points": self.customer_response.key_points,
                "next_steps": self.customer_response.next_steps,
                "gates_summary": self.customer_response.gates_summary,
            },
            "backend": self.backend,
            "ran_at": self.ran_at,
        }


def run_customer_workflow(
    customer_input: str,
    *,
    workspace: Path,
    project_name: str = "Untitled NPI project",
    model: str | None = None,
    backend: str | None = None,
    timeout_sec: int = 600,
    stop_on_no_go: bool = False,
    on_route=None,
    on_phase=None,
) -> tuple[NPIOrchestrator, CustomerWorkflowResult]:
    """Run the full agentic workflow for a customer ask.

    Steps:
    1. **Intake router** — infer current NPI phase and which agents to call.
    2. **Phase agents** — Need / Concept / Bid / Develop / Validate / Launch
       assess their gates and thread hand-offs.
    3. **Response synthesizer** — compose a customer-facing reply.

    Returns ``(orchestrator, workflow_result)``. The orchestrator holds all
    phase results; ``workflow_result.customer_response.visible`` is the reply
    to send to the customer.
    """
    resolved_backend = backend or DEFAULT_BACKEND
    orch = NPIOrchestrator(
        workspace=workspace,
        project_name=project_name,
        project_brief=customer_input,
        model=model,
        backend=resolved_backend,
        timeout_sec=timeout_sec,
    )

    # Step 1 — route
    plan = orch.plan_from_customer_input(customer_input)
    if on_route is not None:
        on_route(plan)

    # Step 2 — run relevant phase agents
    phase_results: list[PhaseResult] = []
    for pid in plan.phases_to_run:
        res = orch.run_phase(pid)
        phase_results.append(res)
        if on_phase is not None:
            on_phase(res)
        if stop_on_no_go and res.gate_decision == "NO_GO":
            break

    # Step 3 — synthesize customer response
    response = synthesize_customer_response(
        customer_input=customer_input,
        route_plan=plan,
        phase_results=phase_results,
        workspace=workspace,
        model=model,
        backend=resolved_backend,
        timeout_sec=min(timeout_sec, 300),
    )

    result = CustomerWorkflowResult(
        customer_input=customer_input,
        route_plan=plan,
        phase_results=phase_results,
        customer_response=response,
        backend=resolved_backend,
        ran_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    orch.workflow_result = result
    return orch, result
