---
name: npi-orchestrator
description: >-
  Run, extend, and debug the NPI Orchestrator multi-agent system for New Product
  Introduction (NPI). Use when the user mentions NPI Orchestrator, NPI phase
  agents (Need, Concept, Bid, Develop, Validate, Launch), customer-driven NPI
  workflow, gate GO/NO-GO, PPAP/SOR/bid readiness, orchestrator agent routing,
  streamlit_npi, or automotive NPI samples (eTurbo, BYD PPC).
---

# NPI Orchestrator

Multi-agent NPI system: **Orchestrator agent** picks which phase agents to call
(in order) from customer needs → phase agents assess gates → **Response agent**
composes the customer reply.

**Repo:** https://github.com/varuns-ai/NPI-Orchestrator  
**Workspace root:** directory containing `streamlit_npi.py` and `npi_orchestrator/`

## Architecture (customer-driven, not fixed PH1→PH6)

```
customer needs → Orchestrator agent (agents_to_call + order)
              → selected phase agents only (hand-offs from prior agents in plan)
              → Response agent → customer reply
```

| Phase | Agent | Gate |
|-------|-------|------|
| PH1 NEEDS | Need | Project Funding |
| PH2 CONCEPT | Concept | Concept Design Freeze |
| PH3 BID | Bid | Bid & Value Confirmation |
| PH4 DEVELOP | Develop | Application Design Freeze |
| PH5 VALIDATE | Validate | PPAP / Launch Readiness |
| PH6 LAUNCH | Launch | SOP / NPO Closure |

**Routing examples:** PPAP-only → `["PH5"]`; funding + quote → `["PH1","PH3"]`; full program → all six.

Diagram: `npi-orchestrator-architecture.png` · Details: [reference.md](reference.md)

## Prerequisites

```powershell
pip install -r requirements.txt
cursor-agent login   # default keyless CLI backend
```

Backend: `cli` (default) | `sdk` (`CURSOR_API_KEY`) | `auto`. Check with `runtime_ready()` from `npi_orchestrator.runner`.

## Agent workflow checklist

When the user wants an NPI assessment from customer input:

```
- [ ] Confirm workspace is NPI Orchestrator root
- [ ] Get customer needs (text or sample scenario)
- [ ] Plan: Orchestrator agent → review agents_to_call + order
- [ ] Run selected phase agents (or full workflow)
- [ ] Synthesize / present customer response + gate decisions
```

**Prefer library API** (same as Streamlit):

```python
from pathlib import Path
from npi_orchestrator import plan_agent_calls, run_customer_workflow

ws = Path(".")  # NPI Orchestrator root

plan = plan_agent_calls("What is our PPAP status for supplier X?", workspace=ws)
# plan.agents_to_call, plan.agent_sequence_label, plan.rationale

orch, wf = run_customer_workflow(
    "Customer ABC needs eTurbo quote — SOR draft ready",
    workspace=ws,
    project_name="Turbo X",
)
print(wf.route_plan.agent_sequence_label)
print(wf.customer_response.visible)
```

**Streamlit UI:**

```powershell
python -m streamlit run streamlit_npi.py
```

Buttons: **Plan agent calls** (orchestration only) · **Run agentic workflow** (full pipeline) · **Run full gate review** (all six, bypasses Orchestrator).

**CLI:**

```powershell
python -m npi_orchestrator --list
python -m npi_orchestrator --sample automotive_eturbo --full
python -m npi_orchestrator --customer-input "..." --name "Project" --full
python -m npi_orchestrator --phase Bid --brief "..." --full
python -m npi_orchestrator --all --brief-file brief.txt --save
```

## Key modules

| Module | Role |
|--------|------|
| `orchestrator_agent.py` | `plan_agent_calls()` — Orchestrator agent, `agents_to_call` |
| `orchestrator.py` | `NPIOrchestrator` — run phases, hand-offs, `.npi_project_state.json` |
| `workflow.py` | `run_customer_workflow()` — end-to-end pipeline |
| `response_synth.py` | Customer-facing reply synthesis |
| `phases.py` | Six `Phase` definitions — edit framework here |
| `phase_agents/` | One factory per agent (need, concept, bid, …) |
| `samples/` | `automotive_eturbo`, `byd_2030_ppc` pre-built scenarios |

## Structured contracts

Agents append one-line JSON in HTML comments (parsed by `meta.py` / orchestrator):

- **Orchestrator:** `<!--NPI_ORCH:{"agents_to_call":["PH3","PH5"],...}-->`
- **Phase agent:** `<!--NPI_META:{"gate_decision":"GO",...}-->`
- **Response:** `<!--NPI_RESPONSE:{"overall_status":"on_track",...}-->`

Hand-offs thread only from agents **earlier in `plan.agents_to_call`**, not all prior lifecycle phases.

## Common tasks

| User ask | Action |
|----------|--------|
| Which agents run for this ask? | `plan_agent_calls()` or Streamlit **Plan agent calls** |
| Full customer workflow | `run_customer_workflow()` or **Run agentic workflow** |
| One gate only | `orch.run_phase("PH5")` or `--phase Validate` |
| Demo without live agents | `--sample automotive_eturbo --full` |
| Add sample scenario | New module in `samples/`, register in `samples/registry.py` |
| Change phase behavior | Edit `phase_agents/<agent>.py` or `agents.py` preamble |
| Change routing logic | Edit `orchestrator_agent.py` prompt / `_heuristic_agents` |

## Extension rules

1. **Framework changes** → `phases.py` first; factories follow `PHASES`.
2. **New routing** → `orchestrator_agent.py`; keep `CustomerRoutePlan` / `OrchestrationPlan` fields stable.
3. **Do not** commit `.npi_project_state.json` or secrets (gitignored).
4. **PowerShell:** use `;` not `&&` for chained commands on Windows.

## More

- Module map and contracts: [reference.md](reference.md)
- User-request patterns: [examples.md](examples.md)
