"""NPIOrchestrator: routes a project across the six NPI phase agents.

The orchestrator instantiates one :class:`~npi_orchestrator.agents.PhaseAgent`
per phase, feeds each phase the project brief plus the hand-off notes from the
phases before it, records every gate result, and can persist/reload the whole
project state as JSON.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .agents import PhaseAgent
from .customer_router import CustomerRoutePlan, plan_agent_calls
from .meta import decision_label, normalize_decision
from .phase_agents import AGENT_FACTORIES
from .phases import PHASES, Phase, get_phase, phase_ids_from
from .response_synth import CustomerResponse, synthesize_customer_response
from .runtime_env import DEFAULT_BACKEND

STATE_FILENAME = ".npi_project_state.json"


@dataclass
class PhaseResult:
    """The outcome of running one phase agent."""

    phase_id: str
    scope: str
    gate: str
    agent_name: str
    visible: str
    gate_decision: str
    deliverables: list[dict] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    handoff: str = ""
    ran_at: str = ""

    @property
    def decision_label(self) -> str:
        return decision_label(self.gate_decision)


class NPIOrchestrator:
    """Coordinate the NPI phase agents for a single project."""

    def __init__(
        self,
        *,
        workspace: Path,
        project_name: str,
        project_brief: str,
        model: str | None = None,
        backend: str | None = None,
        timeout_sec: int = 600,
    ) -> None:
        self.workspace = Path(workspace)
        self.project_name = project_name
        self.project_brief = project_brief
        self.model = model
        self.backend = backend
        self.timeout_sec = timeout_sec
        self.results: dict[str, PhaseResult] = {}
        self.route_plan: CustomerRoutePlan | None = None
        self.customer_response: CustomerResponse | None = None
        self.workflow_result = None  # set by run_customer_workflow / workflow module

    def agent_for(self, phase: Phase) -> PhaseAgent:
        factory = AGENT_FACTORIES.get(phase.id)
        if factory is not None:
            return factory(
                self.workspace,
                model=self.model,
                backend=self.backend,
                timeout_sec=self.timeout_sec,
            )
        return PhaseAgent(
            phase=phase,
            workspace=self.workspace,
            model=self.model,
            backend=self.backend,
            timeout_sec=self.timeout_sec,
        )

    def _upstream_handoffs(self, phase: Phase) -> list[tuple[str, str]]:
        """Hand-off notes from agents that ran earlier in the orchestrated order."""
        ups: list[tuple[str, str]] = []
        if self.route_plan and self.route_plan.phases_to_run:
            for pid in self.route_plan.phases_to_run:
                if pid == phase.id:
                    break
                res = self.results.get(pid)
                if res and res.handoff:
                    ups.append((get_phase(pid).label, res.handoff))
            return ups
        for p in PHASES:
            if p.id == phase.id:
                break
            res = self.results.get(p.id)
            if res and res.handoff:
                ups.append((p.label, res.handoff))
        return ups

    def run_phase(self, phase_id: str, *, instruction: str | None = None) -> PhaseResult:
        """Run a single phase agent and store its result."""
        phase = get_phase(phase_id)
        agent = self.agent_for(phase)
        visible, meta = agent.run(
            project_brief=self.project_brief,
            upstream=self._upstream_handoffs(phase),
            instruction=instruction,
        )
        result = PhaseResult(
            phase_id=phase.id,
            scope=phase.scope,
            gate=phase.gate,
            agent_name=phase.agent_name,
            visible=visible,
            gate_decision=normalize_decision(meta.get("gate_decision")),
            deliverables=list(meta.get("deliverables") or []),
            risks=list(meta.get("risks") or []),
            actions=list(meta.get("actions") or []),
            handoff=str(meta.get("handoff") or "").strip(),
            ran_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        self.results[phase.id] = result
        return result

    def run_phases(
        self,
        phase_ids: list[str],
        *,
        stop_on_no_go: bool = False,
        on_result=None,
        instruction: str | None = None,
    ) -> list[PhaseResult]:
        """Run a specific ordered list of phase agents."""
        out: list[PhaseResult] = []
        for pid in phase_ids:
            res = self.run_phase(pid, instruction=instruction)
            out.append(res)
            if on_result is not None:
                on_result(res)
            if stop_on_no_go and res.gate_decision == "NO_GO":
                break
        return out

    def plan_from_customer_input(self, customer_input: str) -> CustomerRoutePlan:
        """Orchestrator agent: decide which phase agents to call and in what order."""
        plan = plan_agent_calls(
            customer_input,
            workspace=self.workspace,
            model=self.model,
            backend=self.backend,
            timeout_sec=min(self.timeout_sec, 300),
        )
        self.route_plan = plan
        self.project_brief = plan.project_brief
        return plan

    def run_from_customer_input(
        self,
        customer_input: str,
        *,
        stop_on_no_go: bool = False,
        on_result=None,
        instruction: str | None = None,
        synthesize: bool = True,
    ) -> tuple[CustomerRoutePlan, list[PhaseResult], CustomerResponse | None]:
        """Route from customer input, run phase agents, optionally synthesize reply."""
        plan = self.plan_from_customer_input(customer_input)
        results = self.run_phases(
            plan.phases_to_run,
            stop_on_no_go=stop_on_no_go,
            on_result=on_result,
            instruction=instruction,
        )
        response: CustomerResponse | None = None
        if synthesize and results:
            response = synthesize_customer_response(
                customer_input=customer_input,
                route_plan=plan,
                phase_results=results,
                workspace=self.workspace,
                model=self.model,
                backend=self.backend or DEFAULT_BACKEND,
                timeout_sec=min(self.timeout_sec, 300),
            )
            self.customer_response = response
        return plan, results, response

    def run_customer_workflow(
        self,
        customer_input: str,
        *,
        stop_on_no_go: bool = False,
        on_route=None,
        on_phase=None,
    ):
        """Full agentic workflow; delegates to :mod:`workflow` and stores the result."""
        from .workflow import run_customer_workflow

        _orch, result = run_customer_workflow(
            customer_input,
            workspace=self.workspace,
            project_name=self.project_name,
            model=self.model,
            backend=self.backend,
            timeout_sec=self.timeout_sec,
            stop_on_no_go=stop_on_no_go,
            on_route=on_route,
            on_phase=on_phase,
        )
        self.results = _orch.results
        self.route_plan = _orch.route_plan
        self.customer_response = result.customer_response
        self.workflow_result = result
        return result

    def run_all(
        self,
        *,
        stop_on_no_go: bool = False,
        on_result=None,
    ) -> list[PhaseResult]:
        """Run all six phases in order, threading hand-offs forward.

        * ``stop_on_no_go``: halt the pipeline at the first NO_GO gate.
        * ``on_result``: optional callback ``fn(PhaseResult)`` invoked after each
          phase (handy for streaming progress to a UI).
        """
        out: list[PhaseResult] = []
        for phase in PHASES:
            res = self.run_phase(phase.id)
            out.append(res)
            if on_result is not None:
                on_result(res)
            if stop_on_no_go and res.gate_decision == "NO_GO":
                break
        return out

    def run_range(
        self,
        start_phase_id: str,
        end_phase_id: str | None = None,
        *,
        stop_on_no_go: bool = False,
        on_result=None,
        instruction: str | None = None,
    ) -> list[PhaseResult]:
        """Run phases from *start_phase_id* through *end_phase_id* (default: Launch)."""
        return self.run_phases(
            phase_ids_from(start_phase_id, end_phase_id),
            stop_on_no_go=stop_on_no_go,
            on_result=on_result,
            instruction=instruction,
        )

    # --- persistence ---------------------------------------------------------

    def to_dict(self) -> dict:
        data = {
            "project_name": self.project_name,
            "project_brief": self.project_brief,
            "model": self.model,
            "backend": self.backend,
            "results": {pid: asdict(r) for pid, r in self.results.items()},
        }
        if self.route_plan is not None:
            data["route_plan"] = asdict(self.route_plan)
        if self.customer_response is not None:
            cr = self.customer_response
            data["customer_response"] = {
                "visible": cr.visible,
                "overall_status": cr.overall_status,
                "key_points": cr.key_points,
                "next_steps": cr.next_steps,
                "gates_summary": cr.gates_summary,
            }
        return data

    def save(self, path: Path | None = None) -> Path:
        target = Path(path) if path else self.workspace / STATE_FILENAME
        target.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return target

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        workspace: Path | None = None,
        backend: str | None = None,
    ) -> "NPIOrchestrator":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        ws = Path(workspace) if workspace else Path(path).resolve().parent
        orch = cls(
            workspace=ws,
            project_name=data.get("project_name", "Untitled NPI project"),
            project_brief=data.get("project_brief", ""),
            model=data.get("model"),
            backend=backend if backend is not None else data.get("backend"),
        )
        for pid, rd in (data.get("results") or {}).items():
            orch.results[pid] = PhaseResult(**rd)
        rp = data.get("route_plan")
        if isinstance(rp, dict):
            agents = rp.get("agents_to_call") or rp.get("phases_to_run") or []
            orch.route_plan = CustomerRoutePlan(
                customer_input=rp.get("customer_input", ""),
                project_brief=rp.get("project_brief", ""),
                current_phase_id=rp.get("current_phase_id", "PH1"),
                agents_to_call=list(agents),
                rationale=rp.get("rationale", ""),
                order_rationale=rp.get("order_rationale", ""),
                orchestrator_visible=rp.get("orchestrator_visible", ""),
                raw_response=rp.get("raw_response", ""),
            )
        return orch

    # --- reporting -----------------------------------------------------------

    def summary_rows(self) -> list[tuple[str, str, str]]:
        """(phase label, gate, decision label) for every phase, run or not."""
        rows: list[tuple[str, str, str]] = []
        for phase in PHASES:
            res = self.results.get(phase.id)
            decision = res.decision_label if res else "Not run"
            rows.append((phase.label, phase.gate, decision))
        return rows
