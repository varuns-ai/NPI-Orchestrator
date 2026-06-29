"""NPI Orchestrator - Streamlit dashboard.

Agentic workflow: customer input -> route -> phase agents -> customer response.
Uses the keyless cursor-agent CLI by default (run: cursor-agent login).

Install once (from this folder):

    pip install -r requirements.txt

Launch (double-click ``Run-NPI-Orchestrator-Streamlit.bat`` or):

    python -m streamlit run streamlit_npi.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from npi_orchestrator.orchestrator import NPIOrchestrator, PhaseResult
from npi_orchestrator.phases import PHASES
from npi_orchestrator.runtime_env import DEFAULT_BACKEND
from npi_orchestrator.runner import runtime_ready
from npi_orchestrator.samples import get_scenario, list_scenarios
from npi_orchestrator.workflow import CustomerWorkflowResult

_WORKSPACE = Path(__file__).resolve().parent

_DECISION_COLOR = {
    "GO": "#1a7f37",
    "GO (with conditions)": "#9a6700",
    "NO-GO": "#cf222e",
    "Pending / needs input": "#57606a",
    "Not run": "#8c959f",
}

_STATUS_COLOR = {
    "on_track": "#1a7f37",
    "at_risk": "#9a6700",
    "blocked": "#cf222e",
    "needs_info": "#57606a",
}


def _decision_badge(label: str) -> str:
    color = _DECISION_COLOR.get(label, "#57606a")
    return (
        f"<span style='background:{color};color:white;padding:2px 8px;"
        f"border-radius:10px;font-size:0.8rem;white-space:nowrap'>{label}</span>"
    )


def _status_badge(status: str, label: str) -> str:
    color = _STATUS_COLOR.get(status, "#57606a")
    return (
        f"<span style='background:{color};color:white;padding:4px 12px;"
        f"border-radius:10px;font-size:0.9rem'>{label}</span>"
    )


def _get_orch() -> NPIOrchestrator | None:
    return st.session_state.get("orch")


def _get_workflow() -> CustomerWorkflowResult | None:
    return st.session_state.get("workflow_result")


def _render_result(res: PhaseResult) -> None:
    st.markdown(
        f"#### {res.phase_id} - {res.scope} &nbsp; {_decision_badge(res.decision_label)}",
        unsafe_allow_html=True,
    )
    st.caption(f"Gate: {res.gate} - {res.agent_name} agent - run {res.ran_at}")
    st.markdown(res.visible)
    if res.deliverables:
        with st.expander("Deliverables", expanded=False):
            st.dataframe(res.deliverables, use_container_width=True, hide_index=True)
    if res.risks:
        with st.expander("Risks", expanded=False):
            st.dataframe(res.risks, use_container_width=True, hide_index=True)
    if res.actions:
        with st.expander("Next actions", expanded=False):
            for a in res.actions:
                st.markdown(f"- {a}")


def _render_customer_response(wf: CustomerWorkflowResult) -> None:
    st.subheader("Response to customer")
    st.markdown(
        _status_badge(wf.customer_response.overall_status, wf.overall_status_label),
        unsafe_allow_html=True,
    )
    if wf.customer_response.gates_summary:
        st.caption(wf.customer_response.gates_summary)
    st.markdown(wf.customer_response.visible)
    if wf.customer_response.key_points or wf.customer_response.next_steps:
        c1, c2 = st.columns(2)
        with c1:
            if wf.customer_response.key_points:
                st.markdown("**Key points**")
                for p in wf.customer_response.key_points:
                    st.markdown(f"- {p}")
        with c2:
            if wf.customer_response.next_steps:
                st.markdown("**Next steps**")
                for s in wf.customer_response.next_steps:
                    st.markdown(f"- {s}")


def main() -> None:
    st.set_page_config(page_title="NPI Orchestrator", layout="wide", initial_sidebar_state="expanded")

    if (sample_id := st.session_state.pop("load_sample_id", None)) is not None:
        scenario = get_scenario(sample_id)
        wf = scenario.build_workflow(_WORKSPACE)
        orch = scenario.build_orchestrator(_WORKSPACE)
        st.session_state.orch = orch
        st.session_state.workflow_result = wf
        st.session_state.sample_customer_input = scenario.customer_input
        st.session_state.sample_project_brief = scenario.project_brief
        st.session_state.sample_project_name = scenario.name
        st.session_state.orch_key = None
        st.rerun()

    default_name = st.session_state.get("sample_project_name", "Untitled NPI project")

    with st.sidebar:
        st.header("NPI Orchestrator")
        backend = st.radio(
            "Agent backend",
            ("cli", "auto", "sdk"),
            index=0,
            help="cli (default): keyless cursor-agent CLI. Run `cursor-agent login` once.",
        )
        project_name = st.text_input("Project name", default_name)
        model = st.text_input("Model", "auto", help="Cursor model id (default: auto).") or "auto"
        timeout = st.slider("Timeout per agent (s)", 60, 1200, 600, step=30)
        stop_on_no_go = st.checkbox("Stop at first NO-GO gate", value=False)
        st.divider()
        scenario_ids = [sid for sid, _ in list_scenarios()]
        scenario_labels = {sid: name for sid, name in list_scenarios()}
        selected_sample = st.selectbox(
            "Sample scenario",
            scenario_ids,
            format_func=lambda x: scenario_labels[x],
        )
        if st.button("Load sample", type="secondary"):
            st.session_state.load_sample_id = selected_sample
            st.rerun()
        st.caption("Phase agents (keyless CLI)")
        for p in PHASES:
            st.markdown(f"**{p.id}** {p.scope} — _{p.agent_name}_ — {p.gate}")

    ok, err = runtime_ready(backend)
    if not ok:
        st.error(err)
        st.stop()

    st.title("NPI Orchestrator")
    st.caption(
        "Agentic workflow: **customer input** → **Orchestrator agent** (picks agents + order) → "
        "**Need / Concept / Bid / Develop / Validate / Launch** → **customer response**. "
        "Backend: keyless `cursor-agent` CLI."
    )

    default_customer = st.session_state.get("sample_customer_input", "")
    default_brief = st.session_state.get("sample_project_brief", "")

    customer_input = st.text_area(
        "Customer needs / ask",
        value=default_customer,
        height=140,
        placeholder=(
            "Describe what the customer needs, e.g. "
            "'Customer ABC requests eTurbo quote for 50k/yr — SOR draft ready, awaiting award. "
            "What is our bid readiness and timeline?'"
        ),
        help="This drives routing, phase agent calls, and the final customer reply.",
    )

    project_brief = st.text_area(
        "Project brief (optional — auto-derived from customer input)",
        value=default_brief,
        height=100,
        placeholder="Optional extra context for phase agents.",
    )

    orch = _get_orch()
    key = (project_name, project_brief, customer_input, model, backend, timeout)
    if orch is None or st.session_state.get("orch_key") != key:
        effective_brief = project_brief.strip() or customer_input.strip()
        orch = NPIOrchestrator(
            workspace=_WORKSPACE,
            project_name=project_name,
            project_brief=effective_brief,
            model=model,
            backend=backend or DEFAULT_BACKEND,
            timeout_sec=timeout,
        )
        prev = _get_orch()
        if prev is not None:
            orch.results = prev.results
            orch.route_plan = prev.route_plan
            orch.customer_response = prev.customer_response
            orch.workflow_result = prev.workflow_result
        st.session_state.orch = orch
        st.session_state.orch_key = key

    cols = st.columns([1, 1, 1, 2])
    with cols[0]:
        run_workflow = st.button(
            "Run agentic workflow",
            type="primary",
            disabled=not customer_input.strip(),
        )
    with cols[1]:
        plan_only = st.button(
            "Plan agent calls",
            disabled=not customer_input.strip(),
        )
    with cols[2]:
        run_all = st.button(
            "Run full gate review",
            disabled=not (project_brief.strip() or customer_input.strip()),
        )
    with cols[3]:
        if st.button("Clear"):
            orch.results = {}
            orch.route_plan = None
            orch.customer_response = None
            orch.workflow_result = None
            st.session_state.workflow_result = None
            st.rerun()

    wf = _get_workflow()
    if wf is not None:
        plan = wf.route_plan
        skipped = [p.agent_name for p in PHASES if p.id not in plan.phases_to_run]
        skip_note = f" Skipped: {', '.join(skipped)}." if skipped else ""
        st.info(
            f"**Orchestrator plan:** program at **{plan.current_scope}** → call "
            f"**{plan.agent_sequence_label}** ({' → '.join(plan.phases_to_run)}). "
            f"_{plan.rationale}_"
            + (f" Order: _{plan.order_rationale}_" if plan.order_rationale else "")
            + skip_note
        )
        _render_customer_response(wf)

    elif orch.route_plan is not None:
        plan = orch.route_plan
        skipped = [p.agent_name for p in PHASES if p.id not in plan.phases_to_run]
        skip_note = f" Skipped: {', '.join(skipped)}." if skipped else ""
        st.info(
            f"**Orchestrator plan:** program at **{plan.current_scope}** → call "
            f"**{plan.agent_sequence_label}** ({' → '.join(plan.phases_to_run)}). "
            f"_{plan.rationale}_"
            + (f" Order: _{plan.order_rationale}_" if plan.order_rationale else "")
            + skip_note
        )
        if plan.orchestrator_visible:
            with st.expander("Orchestrator agent notes", expanded=False):
                st.markdown(plan.orchestrator_visible)

    st.subheader("Gate status")
    strip = st.columns(len(PHASES))
    for col, phase in zip(strip, PHASES):
        res = orch.results.get(phase.id)
        label = res.decision_label if res else "Not run"
        with col:
            st.markdown(
                f"**{phase.id}**<br>{phase.scope}<br><small>{phase.agent_name}</small>",
                unsafe_allow_html=True,
            )
            st.markdown(_decision_badge(label), unsafe_allow_html=True)

    if plan_only:
        with st.spinner("Orchestrator agent planning agent calls..."):
            try:
                orch.plan_from_customer_input(customer_input)
                st.session_state.workflow_result = None
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))
        st.rerun()

    if run_workflow:
        progress = st.progress(0.0, text="Step 1/3: Orchestrator agent planning...")
        status = st.empty()
        try:
            def on_route(plan):
                progress.progress(0.1, text="Step 2/3: Running phase agents...")
                status.info(
                    f"Orchestrator → **{plan.agent_sequence_label}** "
                    f"({' → '.join(plan.phases_to_run)})"
                )

            total_phases = 0

            def on_phase(res):
                nonlocal total_phases
                total_phases += 1
                plan = orch.route_plan
                n = len(plan.phases_to_run) if plan else 1
                progress.progress(
                    0.1 + 0.6 * total_phases / n,
                    text=f"Step 2/3: {res.agent_name} agent ({res.scope})...",
                )

            result = orch.run_customer_workflow(
                customer_input,
                stop_on_no_go=stop_on_no_go,
                on_route=on_route,
                on_phase=on_phase,
            )
            progress.progress(0.9, text="Step 3/3: Generating customer response...")
            st.session_state.workflow_result = result
            progress.progress(1.0, text="Workflow complete.")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
        st.rerun()

    if run_all:
        if not orch.project_brief.strip():
            orch.project_brief = customer_input.strip() or project_brief.strip()
        progress = st.progress(0.0, text="Starting gate review...")
        total = len(PHASES)
        for i, phase in enumerate(PHASES, start=1):
            progress.progress((i - 1) / total, text=f"Running {phase.agent_name} agent...")
            res = orch.run_phase(phase.id)
            if stop_on_no_go and res.gate_decision == "NO_GO":
                progress.progress(1.0, text=f"Stopped at {phase.id} (NO-GO).")
                break
        else:
            progress.progress(1.0, text="Gate review complete.")
        st.rerun()

    st.divider()
    st.subheader("Phase agent details")
    tabs = st.tabs([f"{p.id} {p.scope}" for p in PHASES])
    for tab, phase in zip(tabs, PHASES):
        with tab:
            st.markdown(f"**{phase.agent_name}** agent — {phase.mission}")
            c1, c2 = st.columns([3, 1])
            with c1:
                instruction = st.text_input(
                    "Optional instruction",
                    key=f"instr_{phase.id}",
                    placeholder="e.g. focus on PPAP readiness and supplier risk",
                )
            with c2:
                st.write("")
                run_one = st.button(
                    "Run agent",
                    key=f"run_{phase.id}",
                    disabled=not (project_brief.strip() or customer_input.strip()),
                )
            if run_one:
                with st.spinner(f"{phase.agent_name} agent assessing gate..."):
                    try:
                        orch.run_phase(phase.id, instruction=instruction or None)
                    except Exception as exc:  # noqa: BLE001
                        st.error(str(exc))
                st.rerun()

            res = orch.results.get(phase.id)
            if res:
                _render_result(res)
            else:
                st.info("Not run yet.")

    if orch.results:
        st.divider()
        if st.button("Save project state"):
            path = orch.save()
            st.success(f"Saved to {path}")


if __name__ == "__main__":
    main()
