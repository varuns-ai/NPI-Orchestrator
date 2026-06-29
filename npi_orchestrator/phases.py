"""The NPI (New Product Introduction) framework: 6 phases and gates.

Transcribed from the "NPI Process Overview - NPI Phases" framework. Each
:class:`Phase` captures the scope, its gate/milestone deliverable, and the
agent that governs it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    """One NPI phase and everything an agent needs to govern its gate."""

    id: str  # e.g. "PH1"
    scope: str  # e.g. "NEEDS"
    gate: str  # gate / milestone deliverable, e.g. "Project Funding"
    agent_name: str  # persona title for the phase agent
    mission: str  # one-line mission for the agent

    @property
    def label(self) -> str:
        return f"{self.id} - {self.scope}"


PHASES: list[Phase] = [
    Phase(
        id="PH1",
        scope="NEEDS",
        gate="Project Funding",
        agent_name="Need",
        mission=(
            "Validate the customer/market need and build the business case to secure "
            "project funding (NPO creation and budget)."
        ),
    ),
    Phase(
        id="PH2",
        scope="CONCEPT",
        gate="Concept Design Freeze",
        agent_name="Concept",
        mission=(
            "Generate and down-select concepts, prove technical feasibility (TRL), and "
            "freeze the concept design with a substantiated business case."
        ),
    ),
    Phase(
        id="PH3",
        scope="BID",
        gate="Bid & Value Confirmation",
        agent_name="Bid",
        mission=(
            "Confirm requirements (SOR), price and quote the technical offer, win the "
            "award, and confirm value before committing to development."
        ),
    ),
    Phase(
        id="PH4",
        scope="DEVELOP",
        gate="Application Design Freeze",
        agent_name="Develop",
        mission=(
            "Mature the application design, manage DVP&R and risk reviews, and reach a "
            "validated application design freeze ready for production validation."
        ),
    ),
    Phase(
        id="PH5",
        scope="VALIDATE",
        gate="PPAP / Launch Readiness",
        agent_name="Validate",
        mission=(
            "Drive production launch authorization, complete PPAP and design review for "
            "production, and confirm launch readiness."
        ),
    ),
    Phase(
        id="PH6",
        scope="LAUNCH",
        gate="SOP / NPO Closure",
        agent_name="Launch",
        mission=(
            "Execute Start of Production (SOP), transition to serial demand/SIOP, capture "
            "NPS, and close out the NPO."
        ),
    ),
]

PHASES_BY_ID: dict[str, Phase] = {p.id: p for p in PHASES}

# Scope / agent-name aliases -> phase id (e.g. "need", "bid", "develop").
_SCOPE_ALIASES: dict[str, str] = {}
for _p in PHASES:
    _SCOPE_ALIASES[_p.id] = _p.id
    _SCOPE_ALIASES[_p.scope] = _p.id
    _SCOPE_ALIASES[_p.agent_name.upper()] = _p.id
_SCOPE_ALIASES["NEED"] = "PH1"
_SCOPE_ALIASES["NEEDS"] = "PH1"


def get_phase(phase_id: str) -> Phase:
    """Look up a phase by id, scope, or agent name (case-insensitive).

    Accepts ``PH3``, ``bid``, ``Develop``, ``needs``, etc.
    """
    key = phase_id.strip().upper()
    resolved = _SCOPE_ALIASES.get(key)
    if resolved is None:
        valid = ", ".join(f"{p.id}/{p.scope}/{p.agent_name}" for p in PHASES)
        raise KeyError(f"Unknown phase {phase_id!r}. Valid: {valid}.")
    return PHASES_BY_ID[resolved]


def phase_ids_from(start_id: str, end_id: str | None = None) -> list[str]:
    """Return ordered phase ids from *start_id* through *end_id* (inclusive).

    If *end_id* is omitted, runs from *start_id* through PH6 (Launch).
    """
    start = get_phase(start_id)
    end = get_phase(end_id) if end_id else PHASES[-1]
    ids = [p.id for p in PHASES]
    si, ei = ids.index(start.id), ids.index(end.id)
    if si > ei:
        raise ValueError(f"start {start.id} is after end {end.id}")
    return ids[si : ei + 1]
