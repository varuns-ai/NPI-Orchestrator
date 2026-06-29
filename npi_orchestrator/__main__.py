"""CLI for the NPI Orchestrator.

Examples
--------
List the framework::

    python -m npi_orchestrator --list

Run a single phase agent::

    python -m npi_orchestrator --phase PH3 --name "Turbo X" --brief "..." 

Run the whole gate review across all six phases and save state::

    python -m npi_orchestrator --all --name "Turbo X" --brief-file brief.txt --save
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .orchestrator import NPIOrchestrator
from .phases import PHASES, get_phase
from .runtime_env import DEFAULT_BACKEND
from .runner import runtime_ready
from .samples import get_scenario, list_scenarios


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _configure_stdio_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def _print_framework() -> None:
    print("NPI Process - phases, gates and agents\n")
    for p in PHASES:
        print(f"{p.id}  {p.scope:<9}  gate: {p.gate}")
        print(f"      agent: {p.agent_name} - {p.mission}")
        print()


def _resolve_customer(args: argparse.ArgumentParser, ns: argparse.Namespace) -> str:
    if ns.customer_file:
        path = Path(ns.customer_file)
        if not path.exists():
            args.error(f"--customer-file not found: {path}")
        return path.read_text(encoding="utf-8")
    if ns.customer_input:
        return ns.customer_input
    return ""


def _resolve_brief(args: argparse.ArgumentParser, ns: argparse.Namespace) -> str:
    if ns.brief_file:
        path = Path(ns.brief_file)
        if not path.exists():
            args.error(f"--brief-file not found: {path}")
        return path.read_text(encoding="utf-8")
    if ns.brief:
        return ns.brief
    return ""


def _print_result(res, *, full: bool) -> None:
    print("=" * 72)
    print(f"{res.phase_id} - {res.scope}  |  gate: {res.gate}  |  decision: {res.decision_label}")
    print("=" * 72)
    print(res.visible if full else (res.visible[:1200] + ("..." if len(res.visible) > 1200 else "")))
    print()


def main(argv: list[str] | None = None) -> int:
    _configure_stdio_utf8()
    parser = argparse.ArgumentParser(
        prog="python -m npi_orchestrator",
        description=(
            "NPI Orchestrator: one specialist agent per NPI phase (PH1 NEEDS -> PH6 LAUNCH), "
            "coordinated to produce gate GO/NO-GO recommendations. Uses Cursor SDK "
            "(CURSOR_API_KEY + cursor-sdk) or keyless cursor-agent CLI."
        ),
    )
    parser.add_argument("--list", action="store_true", help="Print the NPI framework and exit.")
    parser.add_argument(
        "--sample",
        nargs="?",
        const="automotive_eturbo",
        default=None,
        metavar="SCENARIO",
        help="Print sample outputs (no agents). Scenarios: "
        + ", ".join(sid for sid, _ in list_scenarios()),
    )
    parser.add_argument("--name", default="Untitled NPI project", help="Project name.")
    parser.add_argument("--brief", default=None, help="Project brief text.")
    parser.add_argument("--brief-file", default=None, help="Path to a file with the project brief.")
    parser.add_argument(
        "--customer-input",
        default=None,
        help="Customer ask / status; orchestrator routes to the right phase agent(s).",
    )
    parser.add_argument(
        "--customer-file",
        default=None,
        help="Path to a file with customer input.",
    )
    parser.add_argument(
        "--phase",
        default=None,
        help="Run a single phase agent (e.g. PH1..PH6).",
    )
    parser.add_argument("--all", action="store_true", help="Run all six phase agents in order.")
    parser.add_argument(
        "--instruction",
        default=None,
        help="Extra instruction passed to the phase agent(s).",
    )
    parser.add_argument(
        "--stop-on-no-go",
        action="store_true",
        help="With --all, stop at the first NO-GO gate.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Persist project state to .npi_project_state.json in the workspace.",
    )
    parser.add_argument("--model", default=None, help="Model id (default: auto / CURSOR_AGENT_MODEL).")
    parser.add_argument(
        "--backend",
        default=DEFAULT_BACKEND,
        choices=("auto", "sdk", "cli"),
        help=f"cli (default, keyless), auto, or sdk.",
    )
    parser.add_argument("--timeout", type=int, default=600, help="Seconds per agent call.")
    parser.add_argument("--full", action="store_true", help="Print full agent replies (no truncation).")
    args = parser.parse_args(argv)

    if args.list:
        _print_framework()
        return 0

    if args.sample is not None:
        try:
            scenario = get_scenario(args.sample)
        except KeyError as exc:
            parser.error(str(exc))
        orch = scenario.build_orchestrator(_workspace_root())
        print(f"Sample scenario: {scenario.name}\n")
        print("CUSTOMER INPUT")
        print("-" * 40)
        print(scenario.customer_input.strip())
        print()
        if orch.customer_response:
            print("=" * 72)
            print("CUSTOMER RESPONSE")
            print("=" * 72)
            print(orch.customer_response.visible)
            print()
        for phase in PHASES:
            res = orch.results.get(phase.id)
            if not res:
                continue
            _print_result(res, full=args.full)
        return 0

    if not args.phase and not args.all and not args.customer_input and not args.customer_file:
        parser.error("Choose --list, --phase PHx, --all, or --customer-input.")
    if sum(bool(x) for x in (args.phase, args.all, args.customer_input or args.customer_file)) > 1:
        parser.error("Use only one of --phase, --all, or --customer-input/--customer-file.")
    if args.phase:
        try:
            get_phase(args.phase)
        except KeyError as exc:
            parser.error(str(exc))

    ok, err = runtime_ready(args.backend)
    if not ok:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    brief = _resolve_brief(parser, args)
    customer = _resolve_customer(parser, args)
    if not brief.strip() and not customer.strip():
        parser.error("Provide --brief, --brief-file, --customer-input, or --customer-file.")

    ws = _workspace_root()
    orch = NPIOrchestrator(
        workspace=ws,
        project_name=args.name,
        project_brief=brief.strip() or customer.strip(),
        model=args.model,
        backend=args.backend,
        timeout_sec=args.timeout,
    )

    print(f"Project: {orch.project_name}\n")

    try:
        if args.customer_input or args.customer_file:
            wf = orch.run_customer_workflow(
                customer,
                stop_on_no_go=args.stop_on_no_go,
                on_phase=lambda r: _print_result(r, full=args.full),
            )
            plan = wf.route_plan
            print(f"Routing: current {plan.current_scope} -> run {plan.start_scope} through {plan.end_scope}")
            print(f"Agents consulted: {', '.join(wf.agents_consulted)}")
            print(f"Rationale: {plan.rationale}\n")
            print("=" * 72)
            print(f"CUSTOMER RESPONSE  |  status: {wf.overall_status_label}")
            print("=" * 72)
            print(wf.customer_response.visible if args.full else wf.customer_response.visible[:2000])
            if not args.full and len(wf.customer_response.visible) > 2000:
                print("...")
            print()
        elif args.phase:
            res = orch.run_phase(args.phase, instruction=args.instruction)
            _print_result(res, full=args.full)
        else:
            orch.run_all(
                stop_on_no_go=args.stop_on_no_go,
                on_result=lambda r: _print_result(r, full=args.full),
            )
            print("Gate summary")
            print("-" * 40)
            for label, gate, decision in orch.summary_rows():
                print(f"{label:<16} {gate:<28} {decision}")
            print()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    if args.save:
        path = orch.save()
        print(f"Saved project state to {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
