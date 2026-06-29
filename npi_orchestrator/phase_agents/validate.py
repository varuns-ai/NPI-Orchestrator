"""PH5 VALIDATE - Validate agent (PPAP / Launch Readiness gate)."""

from __future__ import annotations

from pathlib import Path

from ..agents import PhaseAgent
from ..phases import get_phase


def create_validate_agent(
    workspace: Path,
    *,
    model: str | None = None,
    backend: str | None = None,
    timeout_sec: int = 600,
) -> PhaseAgent:
    return PhaseAgent(
        phase=get_phase("PH5"),
        workspace=workspace,
        model=model,
        backend=backend,
        timeout_sec=timeout_sec,
    )
