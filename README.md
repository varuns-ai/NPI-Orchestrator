# NPI Orchestrator

A multi-agent system for the **New Product Introduction (NPI)** process. One
specialized agent governs each of the six NPI phases, and an **orchestrator**
routes a project across them, threading gate hand-offs forward and producing a
clear **GO / NO-GO** recommendation at every gate.

The framework is taken directly from the *NPI Process Overview - NPI Phases*
chart:

| Phase | Scope | Gate / milestone | Agent |
|-------|-------|------------------|-------|
| PH1 | NEEDS | Project Funding | **Need** |
| PH2 | CONCEPT | Concept Design Freeze | **Concept** |
| PH3 | BID | Bid & Value Confirmation | **Bid** |
| PH4 | DEVELOP | Application Design Freeze | **Develop** |
| PH5 | VALIDATE | PPAP / Launch Readiness | **Validate** |
| PH6 | LAUNCH | SOP / NPO Closure | **Launch** |

## How it works

```
customer needs
     |
     v
[Intake Router]  --cursor-agent CLI (keyless)-->
     |  which agents: Need / Concept / Bid / Develop / Validate / Launch
     v
[Phase agents]   --cursor-agent CLI-->  gate GO/NO-GO + hand-offs
     |
     v
[Response Agent] --cursor-agent CLI-->  customer-facing reply
```

**Agentic workflow:** paste the customer's ask. The orchestrator (1) routes to
the right phase agents, (2) runs each via the keyless `cursor-agent` CLI, and
(3) synthesizes a reply that directly answers the customer.

**Manual mode:** enter a project brief and run any single phase agent or the
full gate review across all six phases.

## Setup

```powershell
pip install -r requirements.txt
```

Pick a backend:

- **CLI (default, keyless):** install the Cursor Agent CLI and run `cursor-agent login`.
- **SDK:** `pip install -r requirements-sdk.txt` and set `CURSOR_API_KEY`.

## Use

### Dashboard (Streamlit)

Double-click `Run-NPI-Orchestrator-Streamlit.bat`, or:

```powershell
python -m streamlit run streamlit_npi.py
```

Click **Load sample** in the sidebar. Scenarios:

| ID | Program |
|----|---------|
| `automotive_eturbo` | European OEM Aurora-S 48V eTurbo (2028 SOP) |
| `byd_2030_ppc` | BYD Dynasty-P PHEV vs Audi PPC + E³ 1.2 (2030 SOP) |

Enter customer needs, click **Run agentic workflow**, and read the synthesized
customer response plus per-phase gate assessments.

### Sample output (CLI, no agents)

```powershell
python -m npi_orchestrator --sample automotive_eturbo --full
python -m npi_orchestrator --sample byd_2030_ppc --full
```

### Command line

```powershell
# Print the framework (phases, gates, activities)
python -m npi_orchestrator --list

# Full agentic workflow from customer input (routes + phase agents + customer reply)
python -m npi_orchestrator --customer-input "Customer ABC needs eTurbo quote, SOR draft ready" --name "Turbo X" --full

# Run one phase agent (by id, scope, or agent name)
python -m npi_orchestrator --phase Bid --name "Turbo X" --brief "Customer ABC eTurbo, 50k/yr..."

# Run the full gate review and save the state file
python -m npi_orchestrator --all --name "Turbo X" --brief-file brief.txt --save
```

### As a library

```python
from pathlib import Path
from npi_orchestrator import run_customer_workflow

orch, wf = run_customer_workflow(
    "Customer ABC requests quote for 50k eTurbo/yr — SOR ready",
    workspace=Path("."),
    project_name="Turbo X",
)
print(wf.customer_response.visible)  # reply to send to the customer
```

See `ARCHITECTURE.md` for the module layout.
