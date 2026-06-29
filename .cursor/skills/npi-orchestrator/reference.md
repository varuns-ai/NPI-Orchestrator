# NPI Orchestrator — reference

## Module layout

```
NPI Orchestrator/
├── streamlit_npi.py              # Dashboard
├── npi_orchestrator/
│   ├── orchestrator_agent.py     # Orchestrator agent (plan_agent_calls)
│   ├── orchestrator.py           # NPIOrchestrator, PhaseResult
│   ├── workflow.py               # run_customer_workflow
│   ├── response_synth.py         # Customer response agent
│   ├── customer_router.py        # Re-exports orchestrator_agent
│   ├── agents.py                 # PhaseAgent base
│   ├── phases.py                 # PHASES, get_phase, phase_ids_from
│   ├── phase_agents/             # need, concept, bid, develop, validate, launch
│   ├── meta.py                   # NPI_META parsing, gate decisions
│   ├── runner.py                 # run_agent_turn, runtime_ready
│   ├── runtime_env.py            # DEFAULT_BACKEND = "cli"
│   ├── samples/                  # automotive_eturbo, byd_2030_ppc
│   └── __main__.py               # CLI
├── ARCHITECTURE.md
└── npi-orchestrator-architecture.png
```

## OrchestrationPlan fields

```python
@dataclass
class OrchestrationPlan:  # alias: CustomerRoutePlan
    customer_input: str
    project_brief: str
    current_phase_id: str       # PH1..PH6
    agents_to_call: list[str]   # ordered execution list
    rationale: str
    order_rationale: str
    orchestrator_visible: str     # prose before NPI_ORCH JSON
```

Properties: `phases_to_run`, `agent_names`, `agent_sequence_label`, `current_scope`.

## NPI_ORCH JSON (Orchestrator agent)

```json
{
  "current_phase": "PH3",
  "project_brief": "2-6 sentence brief",
  "agents_to_call": ["PH1", "PH3", "PH5"],
  "rationale": "why these agents",
  "order_rationale": "why this sequence"
}
```

Legacy keys still parsed: `start_phase`, `end_phase`, `phases_to_run`, `<!--NPI_ROUTE:`.

## NPI_META JSON (phase agents)

```json
{
  "phase": "PH3",
  "gate": "Bid & Value Confirmation",
  "gate_decision": "GO | GO_WITH_CONDITIONS | NO_GO | PENDING",
  "deliverables": [{"name": "...", "status": "complete|in_progress|missing", "owner": "...", "system": "..."}],
  "risks": [{"risk": "...", "severity": "high|medium|low", "mitigation": "..."}],
  "actions": ["..."],
  "handoff": "notes for next agent in plan"
}
```

Normalized decisions: `GO`, `GO_WITH_CONDITIONS`, `NO_GO`, `PENDING`.

## NPI_RESPONSE JSON (response agent)

```json
{
  "overall_status": "on_track | at_risk | blocked | needs_info",
  "key_points": ["..."],
  "next_steps": ["..."],
  "gates_summary": "one line"
}
```

## Sample scenarios

| ID | Program |
|----|---------|
| `automotive_eturbo` | European OEM Aurora-S 48V eTurbo, 2028 SOP |
| `byd_2030_ppc` | BYD Dynasty-P PHEV vs Audi PPC + E³ 1.2, 2030 SOP |

```python
from npi_orchestrator.samples import get_scenario, list_scenarios
scenario = get_scenario("byd_2030_ppc")
orch = scenario.build_orchestrator(workspace)
wf = scenario.build_workflow(workspace)
```

## Persistence

- State file: `.npi_project_state.json` (gitignored)
- `orch.save()` / `NPIOrchestrator.load(path)` include `route_plan` when present

## Public API (`npi_orchestrator` package)

```python
from npi_orchestrator import (
    NPIOrchestrator,
    PhaseResult,
    OrchestrationPlan,
    CustomerRoutePlan,
    plan_agent_calls,
    route_customer_input,
    run_customer_workflow,
    synthesize_customer_response,
    PHASES,
    get_phase,
    DEFAULT_BACKEND,
    runtime_ready,
)
```
