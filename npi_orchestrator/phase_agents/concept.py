"""PH2 CONCEPT - Concept agent (Concept Design Freeze gate)."""

from __future__ import annotations

from pathlib import Path

from ..agents import PhaseAgent
from ..phases import get_phase


def create_concept_agent(
    workspace: Path,
    *,
    model: str | None = None,
    backend: str | None = None,
    timeout_sec: int = 600,
) -> PhaseAgent:
    return PhaseAgent(
        phase=get_phase("PH2"),
        workspace=workspace,
        model=model,
        backend=backend,
        timeout_sec=timeout_sec,
    )
