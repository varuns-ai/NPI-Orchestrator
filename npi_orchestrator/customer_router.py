"""Customer intake router: map free-form customer input to NPI phase orchestration.

The router agent reads what the customer/program team is asking for, infers
where the project sits in the NPI lifecycle, and returns a structured plan:
which phase agents to run (Need -> Concept -> Bid -> Develop -> Validate ->
Launch) and a normalized project brief for them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .phases import PHASES, get_phase, phase_ids_from
from .runner import run_agent_turn

_ROUTE_START = "<!--NPI_ROUTE:"
_ROUTE_END = "-->"

_INTAKE_PROMPT = """You are the **NPI Customer Intake Router**. Your job is to read a customer's
message (or an internal program team's status update) and decide how the NPI
Orchestrator should route the work across the six phase agents below.

## NPI phase agents (run in this order)

| Phase | Agent | Gate / milestone |
|-------|-------|------------------|
| PH1 NEEDS | **Need** | Project Funding |
| PH2 CONCEPT | **Concept** | Concept Design Freeze |
| PH3 BID | **Bid** | Bid & Value Confirmation |
| PH4 DEVELOP | **Develop** | Application Design Freeze |
| PH5 VALIDATE | **Validate** | PPAP / Launch Readiness |
| PH6 LAUNCH | **Launch** | SOP / NPO Closure |

## Your task

1. Summarize the customer's ask into a concise **project brief** (2-6 sentences)
   covering product, customer, volumes, requirements, current status, and risks.
2. Infer the **current phase** the project is in (where work is actually happening).
3. Choose **start_phase** (first agent to run) and **end_phase** (last agent to
   run, inclusive). Usually start at the current phase and run forward through
   Launch; if the customer only asks about one gate, you may set start=end.
4. Explain your **rationale** in one or two sentences.

Routing rules:
- Brand-new opportunity / funding question -> start PH1 (Need).
- Concept exploration / TRL / design freeze -> PH2 (Concept).
- Quoting, SOR, award, pricing -> PH3 (Bid).
- Application design / DVP&R / design freeze -> PH4 (Develop).
- PPAP / production readiness -> PH5 (Validate).
- SOP / NPO closure / serial launch -> PH6 (Launch).
- When unsure, start at PH1 and run through PH6.
- Never skip earlier phases if the customer clearly has not passed their gates.

## Customer input

{customer_input}

## Mandatory last line

On the **very last line**, output exactly one HTML comment with valid one-line JSON
and no text after it:
`<!--NPI_ROUTE:{{"current_phase":"PH1|PH2|PH3|PH4|PH5|PH6","start_phase":"PH1","end_phase":"PH6","project_brief":"...","rationale":"..."}}-->`
"""


@dataclass
class CustomerRoutePlan:
    """Orchestration plan derived from customer input."""

    customer_input: str
    project_brief: str
    current_phase_id: str
    start_phase_id: str
    end_phase_id: str
    phases_to_run: list[str]
    rationale: str
    raw_response: str = ""

    @property
    def current_scope(self) -> str:
        return get_phase(self.current_phase_id).scope

    @property
    def start_scope(self) -> str:
        return get_phase(self.start_phase_id).scope

    @property
    def end_scope(self) -> str:
        return get_phase(self.end_phase_id).scope


def _parse_route_meta(raw: str) -> tuple[str, dict[str, Any]]:
    text = (raw or "").strip()
    idx = text.rfind(_ROUTE_START)
    if idx == -1:
        return text, {}
    end = text.find(_ROUTE_END, idx + len(_ROUTE_START))
    if end == -1:
        return text, {}
    blob = text[idx + len(_ROUTE_START) : end].strip()
    visible = (text[:idx] + text[end + len(_ROUTE_END) :]).strip()
    try:
        meta = json.loads(blob)
    except json.JSONDecodeError:
        return text, {}
    if not isinstance(meta, dict):
        return visible, {}
    return visible, meta


def _heuristic_route(customer_input: str) -> dict[str, str]:
    """Keyword fallback when the router agent does not return parseable JSON."""
    text = customer_input.lower()
    rules: list[tuple[str, list[str]]] = [
        ("PH6", ["sop", "start of production", "npo closure", "serial launch", "nps"]),
        ("PH5", ["ppap", "launch readiness", "production launch", "validation"]),
        ("PH4", ["design freeze", "develop", "dvp", "application design", "pre-prod"]),
        ("PH3", ["bid", "quote", "pricing", "award", "sor", "technical offer"]),
        ("PH2", ["concept", "trl", "feasibility", "proto", "design review"]),
        ("PH1", ["funding", "business case", "voc", "customer need", "opportunity"]),
    ]
    for phase_id, keywords in rules:
        if any(k in text for k in keywords):
            return {
                "current_phase": phase_id,
                "start_phase": phase_id,
                "end_phase": "PH6",
                "rationale": f"Heuristic: matched keywords for {phase_id}.",
            }
    return {
        "current_phase": "PH1",
        "start_phase": "PH1",
        "end_phase": "PH6",
        "rationale": "No specific phase detected; defaulting to full NPI review from Need through Launch.",
    }


def _coerce_phase(value: Any, default: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return default
    try:
        return get_phase(value).id
    except KeyError:
        return default


def route_customer_input(
    customer_input: str,
    *,
    workspace: Path,
    model: str | None = None,
    backend: str | None = None,
    timeout_sec: int = 300,
) -> CustomerRoutePlan:
    """Analyze customer input and return which phase agents to run."""
    text = (customer_input or "").strip()
    if not text:
        raise ValueError("Customer input is empty.")

    prompt = _INTAKE_PROMPT.format(customer_input=text)
    raw = run_agent_turn(
        prompt,
        workspace=workspace,
        model=model,
        timeout_sec=timeout_sec,
        backend=backend,
    )
    _visible, meta = _parse_route_meta(raw)

    if not meta:
        meta = _heuristic_route(text)
        meta["project_brief"] = text

    current = _coerce_phase(meta.get("current_phase"), "PH1")
    start = _coerce_phase(meta.get("start_phase"), current)
    end = _coerce_phase(meta.get("end_phase"), "PH6")
    brief = str(meta.get("project_brief") or text).strip()
    rationale = str(meta.get("rationale") or "").strip()

    # Ensure start is not after current when customer is mid-program (soft rule).
    phase_order = [p.id for p in PHASES]
    if phase_order.index(start) > phase_order.index(current):
        start = current

    try:
        to_run = phase_ids_from(start, end)
    except ValueError:
        end = start
        to_run = phase_ids_from(start, end)

    return CustomerRoutePlan(
        customer_input=text,
        project_brief=brief,
        current_phase_id=current,
        start_phase_id=start,
        end_phase_id=end,
        phases_to_run=to_run,
        rationale=rationale,
        raw_response=raw,
    )
