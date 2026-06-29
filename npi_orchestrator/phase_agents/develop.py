"""PH4 DEVELOP - Develop agent (Application Design Freeze gate)."""

from __future__ import annotations

from pathlib import Path

from ..agents import PhaseAgent
from ..phases import get_phase


def create_develop_agent(
    workspace: Path,
    *,
    model: str | None = None,
    backend: str | None = None,
    timeout_sec: int = 600,
) -> PhaseAgent:
    return PhaseAgent(
        phase=get_phase("PH4"),
        workspace=workspace,
        model=model,
        backend=backend,
        timeout_sec=timeout_sec,
    )
