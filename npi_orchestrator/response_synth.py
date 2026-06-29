"""Synthesize a customer-facing reply from phase agent gate assessments.

After the intake router and phase agents have run, the response synthesizer
reads their decisions and produces a clear answer to the original customer ask.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .runner import run_agent_turn

_RESPONSE_START = "<!--NPI_RESPONSE:"
_RESPONSE_END = "-->"

_SYNTH_PROMPT = """You are the **NPI Customer Response Agent**. Phase specialists have
assessed the customer's request across the NPI process. Your job is to write a
**customer-facing reply** that directly answers their original ask.

## Original customer input

{customer_input}

## Routing decision

- Current phase: **{current_phase}**
- Agents consulted: **{agents_consulted}**
- Routing rationale: {rationale}

## Phase agent assessments

{phase_summaries}

## Your task

Write a professional, concise reply **to the customer** (or their program contact)
that:

1. **Acknowledges** what they asked for.
2. **Answers** their question with specifics from the phase assessments — not
   generic NPI boilerplate.
3. States the **overall NPI status** (on track, at risk, blocked, or needs more
   info) and the **gate decisions** that matter for their ask.
4. Lists **concrete next steps** with owners/timelines where the agents provided them.
5. Flags **top risks or blockers** honestly if any phase returned NO-GO or conditions.
6. Keeps a helpful, partnership tone — this is Garrett advancing the program.

Format as a short letter or email (greeting, body with bullets where helpful,
closing). Do **not** expose internal agent names or HTML metadata in the prose.

## Mandatory last line

On the **very last line**, output exactly one HTML comment with valid one-line JSON
and no text after it:
`<!--NPI_RESPONSE:{{"overall_status":"on_track|at_risk|blocked|needs_info","key_points":["..."],"next_steps":["..."],"gates_summary":"one line"}}-->`
"""


@dataclass
class CustomerResponse:
    """Customer-facing output from the workflow."""

    visible: str
    overall_status: str
    key_points: list[str]
    next_steps: list[str]
    gates_summary: str
    raw_response: str = ""


def _parse_response_meta(raw: str) -> tuple[str, dict[str, Any]]:
    text = (raw or "").strip()
    idx = text.rfind(_RESPONSE_START)
    if idx == -1:
        return text, {}
    end = text.find(_RESPONSE_END, idx + len(_RESPONSE_START))
    if end == -1:
        return text, {}
    blob = text[idx + len(_RESPONSE_START) : end].strip()
    visible = (text[:idx] + text[end + len(_RESPONSE_END) :]).strip()
    try:
        meta = json.loads(blob)
    except json.JSONDecodeError:
        return text, {}
    if not isinstance(meta, dict):
        return visible, {}
    return visible, meta


def _format_phase_summaries(phase_results: list) -> str:
    if not phase_results:
        return "(no phase agents ran)"
    blocks: list[str] = []
    for res in phase_results:
        block = [
            f"### {res.phase_id} {res.scope} — {res.agent_name} agent",
            f"Gate: {res.gate}",
            f"Decision: **{res.decision_label}**",
            "",
            res.visible[:3000],
        ]
        if res.actions:
            block.append("")
            block.append("Next actions: " + "; ".join(res.actions[:5]))
        if res.risks:
            risks = [r.get("risk", str(r)) for r in res.risks[:3]]
            block.append("Top risks: " + "; ".join(risks))
        blocks.append("\n".join(block))
    return "\n\n---\n\n".join(blocks)


def _heuristic_status(phase_results: list) -> str:
    if not phase_results:
        return "needs_info"
    decisions = [r.gate_decision for r in phase_results]
    if "NO_GO" in decisions:
        return "blocked"
    if "GO_WITH_CONDITIONS" in decisions:
        return "at_risk"
    if all(d == "GO" for d in decisions):
        return "on_track"
    return "needs_info"


def synthesize_customer_response(
    *,
    customer_input: str,
    route_plan,
    phase_results: list,
    workspace: Path,
    model: str | None = None,
    backend: str | None = None,
    timeout_sec: int = 300,
) -> CustomerResponse:
    """Generate a customer-facing reply from phase agent results."""
    agents = ", ".join(r.agent_name for r in phase_results) or "none"
    prompt = _SYNTH_PROMPT.format(
        customer_input=customer_input.strip(),
        current_phase=route_plan.current_scope,
        agents_consulted=agents,
        rationale=route_plan.rationale or "(not provided)",
        phase_summaries=_format_phase_summaries(phase_results),
    )
    raw = run_agent_turn(
        prompt,
        workspace=workspace,
        model=model,
        timeout_sec=timeout_sec,
        backend=backend,
    )
    visible, meta = _parse_response_meta(raw)
    status = str(meta.get("overall_status") or _heuristic_status(phase_results))
    return CustomerResponse(
        visible=visible,
        overall_status=status,
        key_points=list(meta.get("key_points") or []),
        next_steps=list(meta.get("next_steps") or []),
        gates_summary=str(meta.get("gates_summary") or ""),
        raw_response=raw,
    )
