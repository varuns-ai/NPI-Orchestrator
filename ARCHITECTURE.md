# Architecture

The NPI Orchestrator reuses the backend pattern from the workspace's other
agent tools: a thin runner that calls either the **Cursor Python SDK** or the
keyless **`cursor-agent` CLI**, with everything above it framework-specific.

## Modules

| Module | Responsibility |
|--------|----------------|
| `npi_orchestrator/runtime_env.py` | Backend resolution (auto / sdk / cli), readiness checks. No SDK import at load time. |
| `npi_orchestrator/runner.py` | `run_agent_turn(...)` - one prompt in, agent markdown out. |
| `npi_orchestrator/phases.py` | The framework: six `Phase` records (scope, gate, agent mission). |
| `npi_orchestrator/phase_agents/` | One factory module per agent: Need, Concept, Bid, Develop, Validate, Launch. |
| `npi_orchestrator/workflow.py` | `run_customer_workflow` — route → phase agents → customer response. |
| `npi_orchestrator/response_synth.py` | Customer Response Agent — synthesizes the reply to the customer ask. |
| `npi_orchestrator/customer_router.py` | Intake router: customer input -> phase range + project brief. |
| `npi_orchestrator/meta.py` | Parse the `NPI_META` HTML-comment JSON each agent appends (gate decision, deliverables, risks, hand-off). |
| `npi_orchestrator/agents.py` | `PhaseAgent` - builds a phase-specific system preamble and runs a turn. |
| `npi_orchestrator/orchestrator.py` | `NPIOrchestrator` - routes customer input, runs phases in order, threads hand-offs, persists JSON. |
| `npi_orchestrator/__main__.py` | CLI (`--list`, `--phase`, `--all`, `--save`). |
| `streamlit_npi.py` | Dashboard UI. |

## Data flow

1. The user supplies **customer needs** (and optionally a project brief).
2. `run_customer_workflow` calls the intake router (keyless CLI by default).
3. Relevant phase agents run in order (Need → … → Launch), each via `cursor-agent`.
4. The Response Agent composes a **customer-facing reply** from gate decisions.
5. Optional: `run_phase(id)` for manual single-phase runs.
3. The agent answers with human-readable markdown **plus** a trailing
   `<!--NPI_META:{...}-->` comment.
4. `meta.split_phase_response` separates the two; the orchestrator stores a
   `PhaseResult` (decision, deliverables, risks, actions, hand-off).
5. `run_all` repeats for PH1..PH6, feeding each phase the accumulated hand-offs.

## The gate contract (`NPI_META`)

```json
{
  "phase": "PH3",
  "gate": "Bid & Value Confirmation",
  "gate_decision": "GO | GO_WITH_CONDITIONS | NO_GO | PENDING",
  "deliverables": [{"name": "...", "status": "complete|in_progress|missing", "owner": "...", "system": "..."}],
  "risks": [{"risk": "...", "severity": "high|medium|low", "mitigation": "..."}],
  "actions": ["..."],
  "handoff": "one or two sentences for the next phase"
}
```

This structured tail is what lets the orchestrator reason about the program
without re-parsing prose, and what powers the gate-status strip in the UI.

## Extending

- **Change the framework:** edit `PHASES` in `phases.py` (add/remove phases or
  edit the agent persona/mission). Everything else adapts.
- **Add a cross-phase reviewer:** add a method on `NPIOrchestrator` that feeds
  all `PhaseResult.handoff` notes into one more `run_agent_turn` call.
