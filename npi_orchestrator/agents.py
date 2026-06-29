"""Per-phase NPI agents.

Each :class:`PhaseAgent` wraps one :class:`~npi_orchestrator.phases.Phase` and
knows how to (a) build a specialized system preamble describing its scope, gate
deliverable and mission, and (b) run a turn through the shared Cursor backend.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .meta import split_phase_response
from .phases import Phase
from .runner import run_agent_turn

_GATE_FRAMING = """You are **{agent_name}**, the specialist agent that governs phase **{phase_id} - {scope}** of the NPI (New Product Introduction) process.

**Your phase gate / milestone:** {gate}
**Your mission:** {mission}

You own this phase end-to-end. Your job is to assess readiness to pass the gate,
chase the right deliverables, flag risks, and produce a clear GO / NO-GO
recommendation for the gate review. Stay strictly within your phase scope; if
work belongs to an earlier or later phase, say so and defer it.

## How to respond
1. **Read the project context and any upstream hand-off** before assessing.
2. Assess gate deliverables for this phase: is each complete, in progress, or
   missing? Be specific to THIS project, not generic.
3. Surface the **top risks** and concrete next actions with owners where you can.
4. Give a single **gate recommendation**: GO, GO_WITH_CONDITIONS, or NO_GO
   (use PENDING only if you genuinely lack the information to decide, and list
   exactly what you need).
5. Write a short **hand-off** note for the next phase agent.

Keep the answer scannable: use short sections and bullet lists. Be candid and
specific; this feeds a real gate review.

## Mandatory last line
On the **very last line** of your reply, output exactly one HTML comment with
**valid one-line JSON** and no text after it:
`<!--NPI_META:{{"phase":"{phase_id}","gate":"{gate}","gate_decision":"GO|GO_WITH_CONDITIONS|NO_GO|PENDING","deliverables":[{{"name":"...","status":"complete|in_progress|missing","owner":"...","system":"..."}}],"risks":[{{"risk":"...","severity":"high|medium|low","mitigation":"..."}}],"actions":["..."],"handoff":"one or two sentences for the next phase"}}-->`
"""


@dataclass
class PhaseAgent:
    """A specialized agent for a single NPI phase."""

    phase: Phase
    workspace: Path
    model: str | None = None
    backend: str | None = None
    timeout_sec: int = 600

    @property
    def name(self) -> str:
        return self.phase.agent_name

    def preamble(self) -> str:
        return _GATE_FRAMING.format(
            agent_name=self.phase.agent_name,
            phase_id=self.phase.id,
            scope=self.phase.scope,
            gate=self.phase.gate,
            mission=self.phase.mission,
        )

    def build_prompt(
        self,
        *,
        project_brief: str,
        upstream: Sequence[tuple[str, str]] | None = None,
        instruction: str | None = None,
    ) -> str:
        """Compose the full prompt: preamble + project + upstream hand-offs + ask."""
        parts: list[str] = [self.preamble().strip(), ""]
        parts.append("## Project context")
        parts.append(project_brief.strip() or "(no project brief provided)")
        parts.append("")

        ups = list(upstream or [])
        if ups:
            parts.append("## Upstream hand-offs (earlier phases, oldest first)")
            for phase_label, handoff in ups:
                parts.append(f"**{phase_label}:** {handoff.strip()}")
            parts.append("")

        parts.append(f"## Your task for gate '{self.phase.gate}'")
        if instruction and instruction.strip():
            parts.append(instruction.strip())
        else:
            parts.append(
                "Assess readiness for this phase gate based on the project context above, "
                "then give your gate recommendation."
            )
        parts.append("")
        parts.append(f"Respond now as the {self.phase.agent_name}.")
        return "\n".join(parts)

    def run(
        self,
        *,
        project_brief: str,
        upstream: Sequence[tuple[str, str]] | None = None,
        instruction: str | None = None,
    ) -> tuple[str, dict]:
        """Run one turn; return (visible markdown, parsed NPI_META dict)."""
        prompt = self.build_prompt(
            project_brief=project_brief, upstream=upstream, instruction=instruction
        )
        raw = run_agent_turn(
            prompt,
            workspace=self.workspace,
            model=self.model,
            timeout_sec=self.timeout_sec,
            backend=self.backend,
        )
        return split_phase_response(raw)
