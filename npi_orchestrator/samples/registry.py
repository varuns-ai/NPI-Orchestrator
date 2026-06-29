"""Registry of pre-built NPI sample scenarios."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..orchestrator import NPIOrchestrator
from ..workflow import CustomerWorkflowResult

from . import automotive_eturbo, byd_2030_ppc


@dataclass(frozen=True)
class SampleScenario:
    id: str
    name: str
    customer_input: str
    project_brief: str
    build_orchestrator: Callable[[Path], NPIOrchestrator]
    build_workflow: Callable[[Path], CustomerWorkflowResult]


SCENARIOS: dict[str, SampleScenario] = {
    automotive_eturbo.SCENARIO_ID: SampleScenario(
        id=automotive_eturbo.SCENARIO_ID,
        name=automotive_eturbo.SCENARIO_NAME,
        customer_input=automotive_eturbo.CUSTOMER_INPUT,
        project_brief=automotive_eturbo.PROJECT_BRIEF,
        build_orchestrator=automotive_eturbo.build_sample_orchestrator,
        build_workflow=automotive_eturbo.build_sample_workflow,
    ),
    byd_2030_ppc.SCENARIO_ID: SampleScenario(
        id=byd_2030_ppc.SCENARIO_ID,
        name=byd_2030_ppc.SCENARIO_NAME,
        customer_input=byd_2030_ppc.CUSTOMER_INPUT,
        project_brief=byd_2030_ppc.PROJECT_BRIEF,
        build_orchestrator=byd_2030_ppc.build_sample_orchestrator,
        build_workflow=byd_2030_ppc.build_sample_workflow,
    ),
}

DEFAULT_SCENARIO_ID = automotive_eturbo.SCENARIO_ID


def get_scenario(scenario_id: str | None) -> SampleScenario:
    key = (scenario_id or DEFAULT_SCENARIO_ID).strip().lower()
    if key not in SCENARIOS:
        valid = ", ".join(SCENARIOS)
        raise KeyError(f"Unknown sample scenario {scenario_id!r}. Valid: {valid}.")
    return SCENARIOS[key]


def list_scenarios() -> list[tuple[str, str]]:
    return [(s.id, s.name) for s in SCENARIOS.values()]
