# NPI Orchestrator — examples

## Plan only (no gate runs)

**User:** "Which NPI agents should we call for a PPAP status question?"

```python
from pathlib import Path
from npi_orchestrator import plan_agent_calls

plan = plan_agent_calls(
    "OEM asks: what is PPAP status for our eTurbo line?",
    workspace=Path("."),
)
print(plan.agents_to_call)           # e.g. ['PH5']
print(plan.agent_sequence_label)     # e.g. 'Validate'
print(plan.rationale)
```

## Full agentic workflow

**User:** "Run the NPI workflow for this customer email."

```python
from pathlib import Path
from npi_orchestrator import run_customer_workflow

orch, wf = run_customer_workflow(
    """Customer ABC requests 48V eTurbo quote for 50k/yr.
    SOR draft ready — what is bid readiness and timeline?""",
    workspace=Path("."),
    project_name="Aurora-S eTurbo",
)
print(wf.route_plan.agent_sequence_label)
for res in wf.phase_results:
    print(res.phase_id, res.decision_label)
print(wf.customer_response.visible)
```

## Load sample without live agents

**User:** "Show me the BYD PPC sample output."

```powershell
python -m npi_orchestrator --sample byd_2030_ppc --full
```

Or in Streamlit: sidebar → select sample → **Load sample**.

## Single phase (manual)

**User:** "Run only the Bid agent for this brief."

```powershell
python -m npi_orchestrator --phase Bid --name "Turbo X" --brief "SOR ready, 50k/yr" --full
```

## Extend routing heuristics

**User:** "Add homologation keyword to route to Validate."

Edit `_heuristic_agents` in `orchestrator_agent.py` — add keyword to PH5 intent list:

```python
("PH5", ["ppap", "homologation", "validation", ...]),
```

## Add a new sample scenario

1. Create `npi_orchestrator/samples/my_scenario.py` with `CUSTOMER_INPUT`, `PROJECT_BRIEF`, phase result builders, `_route_plan()`, `build_sample_orchestrator`, `build_sample_workflow`.
2. Register in `samples/registry.py`.
3. Test: `python -m npi_orchestrator --sample my_scenario --full`

## Debug "which agents were called?"

After workflow:

```python
wf.route_plan.agents_to_call
[w.agent_name for w in wf.phase_results]
```

Skipped agents: phases in `PHASES` not in `wf.route_plan.agents_to_call`.
