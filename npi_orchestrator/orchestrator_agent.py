"""NPI Orchestrator agent: decide which phase agents to call and in what order.

The Orchestrator agent reads customer needs, maps them to the six specialists
(Need, Concept, Bid, Develop, Validate, Launch), and returns an explicit
**ordered** call list — not only a contiguous PHx..PHy range.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .phases import PHASES, get_phase, phase_ids_from
from .runner import run_agent_turn

_ORCH_START = "<!--NPI_ORCH:"
_ORCH_END = "-->"

# Backward-compatible alias used by older persisted state / parsers.
_ROUTE_START = _ORCH_START
_ROUTE_END = _ORCH_END

_ORCHESTRATOR_PROMPT = """You are the **NPI Orchestrator Agent**. Your job is to read
customer needs and decide **which phase agents to call**, **in which order**, and why.

You do NOT run the gates yourself — you dispatch work to the right specialists.

## Available phase agents (NPI lifecycle)

| Phase | Agent | Call when customer needs… |
|-------|-------|---------------------------|
| PH1 NEEDS | **Need** | VOC, funding, business case, new opportunity, market fit |
| PH2 CONCEPT | **Concept** | Architecture down-select, TRL, feasibility, concept freeze |
| PH3 BID | **Bid** | Quote, SOR, pricing, award, plant, commercial offer |
| PH4 DEVELOP | **Develop** | Design freeze, DVP, integration, application engineering risks |
| PH5 VALIDATE | **Validate** | PPAP, production readiness, validation, homologation |
| PH6 LAUNCH | **Launch** | SOP, ramp, supplier readiness, NPO closure, serial quality |

## Your task

1. Write a concise **project brief** (2–6 sentences) from the customer input.
2. Infer **current_phase** — where the program actually is today.
3. Build **agents_to_call**: an ordered JSON array of phase ids (e.g. `["PH3","PH4","PH5"]`)
   listing exactly which agents to invoke, in the sequence they should run.

### Ordering rules
- List agents in the order they should **execute** (first agent first).
- Usually respect NPI lifecycle order (PH1 before PH2, etc.) **among the agents you pick**.
- You may call **one agent only** if the ask is narrow (e.g. only `["PH5"]` for PPAP status).
- You may call **non-contiguous** agents when the ask spans disconnected gates
  (e.g. `["PH1","PH3"]` for funding check then bid readiness) — explain why in order_rationale.
- Include **earlier** agents when the customer clearly has NOT passed those gates and
  context is needed (e.g. add PH1 before PH3 for a brand-new quote request).
- Do **not** call agents that add no value for this specific ask.

4. **order_rationale** — one or two sentences on why this sequence and why skipped agents.

## Customer input

{customer_input}

## Mandatory last line

On the **very last line**, output exactly one HTML comment with valid one-line JSON
and no text after it:
`<!--NPI_ORCH:{{"current_phase":"PH1","project_brief":"...","agents_to_call":["PH1","PH3"],"rationale":"why these agents","order_rationale":"why this order"}}-->`
"""


@dataclass
class OrchestrationPlan:
    """Orchestrator output: which agents to call, in order."""

    customer_input: str
    project_brief: str
    current_phase_id: str
    agents_to_call: list[str]
    rationale: str
    order_rationale: str = ""
    orchestrator_visible: str = ""
    raw_response: str = ""
    # Derived for UI / legacy consumers (first and last in agents_to_call).
    start_phase_id: str = ""
    end_phase_id: str = ""

    def __post_init__(self) -> None:
        if self.agents_to_call:
            self.start_phase_id = self.start_phase_id or self.agents_to_call[0]
            self.end_phase_id = self.end_phase_id or self.agents_to_call[-1]

    @property
    def phases_to_run(self) -> list[str]:
        """Alias used by workflow and UI."""
        return self.agents_to_call

    @property
    def current_scope(self) -> str:
        return get_phase(self.current_phase_id).scope

    @property
    def start_scope(self) -> str:
        return get_phase(self.start_phase_id).scope if self.start_phase_id else ""

    @property
    def end_scope(self) -> str:
        return get_phase(self.end_phase_id).scope if self.end_phase_id else ""

    @property
    def agent_names(self) -> list[str]:
        return [get_phase(pid).agent_name for pid in self.agents_to_call]

    @property
    def agent_sequence_label(self) -> str:
        return " → ".join(self.agent_names) if self.agent_names else "(none)"


# Backward compatibility with earlier code / saved JSON.
CustomerRoutePlan = OrchestrationPlan


def _parse_orch_meta(raw: str) -> tuple[str, dict[str, Any]]:
    text = (raw or "").strip()
    for marker in (_ORCH_START, "<!--NPI_ROUTE:"):
        idx = text.rfind(marker)
        if idx == -1:
            continue
        end = text.find("-->", idx + len(marker))
        if end == -1:
            continue
        blob = text[idx + len(marker) : end].strip()
        visible = (text[:idx] + text[end + 3 :]).strip()
        try:
            meta = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(meta, dict):
            return visible, meta
    return text, {}


def _coerce_phase(value: Any, default: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return default
    try:
        return get_phase(value).id
    except KeyError:
        return default


def _coerce_agent_list(value: Any, *, fallback: list[str]) -> list[str]:
    """Parse agents_to_call / phases_to_run; dedupe preserving order."""
    raw: list[Any] = []
    if isinstance(value, list):
        raw = value
    elif isinstance(value, str):
        raw = re.split(r"[\s,→]+", value)

    out: list[str] = []
    seen: set[str] = set()

    for item in raw:
        if not isinstance(item, str) or not item.strip():
            continue
        try:
            pid = get_phase(item).id
        except KeyError:
            continue
        if pid not in seen:
            seen.add(pid)
            out.append(pid)

    if not out:
        return fallback

    return out


def _heuristic_agents(customer_input: str) -> tuple[list[str], str, str]:
    """Keyword-based fallback: detect intents and build agent call list."""
    text = customer_input.lower()
    intents: list[tuple[str, list[str]]] = [
        ("PH1", ["funding", "business case", "voc", "customer need", "opportunity", "npo"]),
        ("PH2", ["concept", "trl", "feasibility", "proto", "architecture", "down-select"]),
        ("PH3", ["bid", "quote", "pricing", "award", "sor", "technical offer", "commercial"]),
        ("PH4", ["develop", "design freeze", "dvp", "application design", "integration", "pre-prod"]),
        ("PH5", ["ppap", "launch readiness", "production launch", "validation", "homologation"]),
        ("PH6", ["sop", "start of production", "npo closure", "serial launch", "ramp", "nps"]),
    ]

    matched: list[str] = []
    for pid, keywords in intents:
        if any(k in text for k in keywords):
            matched.append(pid)

    if not matched:
        matched = [p.id for p in PHASES]
        return (
            matched,
            "No specific gate detected; calling all agents Need through Launch.",
            "Full NPI review in lifecycle order.",
        )

    # Always sort matched intents in lifecycle order for execution.
    order = {p.id: i for i, p in enumerate(PHASES)}
    matched.sort(key=lambda x: order[x])

    # If only late-phase intent, ensure context agent if early gates implied missing.
    if matched[0] != "PH1" and any(k in text for k in ("new", "opportunity", "funding")):
        if "PH1" not in matched:
            matched.insert(0, "PH1")

    current = matched[0]
    labels = " + ".join(get_phase(p).agent_name for p in matched)
    return (
        matched,
        f"Heuristic: customer ask maps to {labels}.",
        "Agents ordered PH1→PH6 among those matched.",
    )


def plan_agent_calls(
    customer_input: str,
    *,
    workspace: Path,
    model: str | None = None,
    backend: str | None = None,
    timeout_sec: int = 300,
) -> OrchestrationPlan:
    """Orchestrator agent: customer needs → ordered list of phase agents to call."""
    text = (customer_input or "").strip()
    if not text:
        raise ValueError("Customer input is empty.")

    prompt = _ORCHESTRATOR_PROMPT.format(customer_input=text)
    raw = run_agent_turn(
        prompt,
        workspace=workspace,
        model=model,
        timeout_sec=timeout_sec,
        backend=backend,
    )
    visible, meta = _parse_orch_meta(raw)

    if not meta:
        agents, rationale, order_rationale = _heuristic_agents(text)
        meta = {
            "current_phase": agents[0],
            "project_brief": text,
            "agents_to_call": agents,
            "rationale": rationale,
            "order_rationale": order_rationale,
        }

    current = _coerce_phase(meta.get("current_phase"), "PH1")
    brief = str(meta.get("project_brief") or text).strip()
    rationale = str(meta.get("rationale") or "").strip()
    order_rationale = str(meta.get("order_rationale") or "").strip()

    # Support legacy start_phase / end_phase in model output.
    fallback_range: list[str] = []
    if meta.get("start_phase") or meta.get("end_phase"):
        try:
            start = _coerce_phase(meta.get("start_phase"), current)
            end = _coerce_phase(meta.get("end_phase"), "PH6")
            fallback_range = phase_ids_from(start, end)
        except ValueError:
            fallback_range = phase_ids_from(current, current)

    agents_raw = meta.get("agents_to_call") or meta.get("phases_to_run") or fallback_range
    if not agents_raw and meta.get("start_phase"):
        try:
            agents_raw = phase_ids_from(
                _coerce_phase(meta.get("start_phase"), current),
                _coerce_phase(meta.get("end_phase"), "PH6"),
            )
        except ValueError:
            agents_raw = [current]

    agents = _coerce_agent_list(
        agents_raw,
        fallback=_heuristic_agents(text)[0],
    )

    return OrchestrationPlan(
        customer_input=text,
        project_brief=brief,
        current_phase_id=current,
        agents_to_call=agents,
        rationale=rationale,
        order_rationale=order_rationale,
        orchestrator_visible=visible,
        raw_response=raw,
    )


def route_customer_input(
    customer_input: str,
    *,
    workspace: Path,
    model: str | None = None,
    backend: str | None = None,
    timeout_sec: int = 300,
) -> OrchestrationPlan:
    """Backward-compatible alias for :func:`plan_agent_calls`."""
    return plan_agent_calls(
        customer_input,
        workspace=workspace,
        model=model,
        backend=backend,
        timeout_sec=timeout_sec,
    )
