"""Run a single agent turn via Cursor Python SDK (model **auto**) or keyless `cursor-agent` CLI.

Backend-agnostic: any NPI phase agent or the orchestrator funnels its prompt
through :func:`run_agent_turn`.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .runtime_env import (
    DEFAULT_MODEL,
    ENV_MODEL,
    _effective_backend,
    resolve_cursor_agent_exe,
    runtime_ready,
    sdk_dependencies_met,
)

__all__ = [
    "DEFAULT_MODEL",
    "ENV_MODEL",
    "resolve_cursor_agent_exe",
    "runtime_ready",
    "sdk_dependencies_met",
    "run_agent_turn",
]


def _run_cli(prompt: str, *, workspace: Path, model: str, timeout_sec: int) -> str:
    exe = resolve_cursor_agent_exe()
    if not exe:
        raise RuntimeError(
            "cursor-agent not found in PATH. Install Cursor Agent CLI and run: cursor-agent login"
        )
    cmd = [
        exe,
        "--print",
        "--trust",
        "--mode",
        "ask",
        "--model",
        model,
        "--workspace",
        str(workspace.resolve()),
        prompt,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_sec,
        shell=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"cursor-agent exited {proc.returncode}:\n{(proc.stderr or proc.stdout)[:6000]}"
        )
    return (proc.stdout or "").strip()


def _run_sdk(prompt: str, *, workspace: Path, model: str) -> str:
    from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions

    api_key = os.environ.get("CURSOR_API_KEY")
    if not api_key:
        raise RuntimeError("CURSOR_API_KEY is not set (required for Cursor SDK).")

    options = AgentOptions(
        api_key=api_key,
        model=model,
        local=LocalAgentOptions(cwd=str(workspace.resolve())),
    )
    try:
        result = Agent.prompt(prompt, options)
    except CursorAgentError as exc:
        raise RuntimeError(f"Cursor SDK error: {exc}") from exc

    if result.status != "finished":
        body = (result.result or "").strip() or "(no body)"
        raise RuntimeError(f"Agent status {result.status!r}: {body[:4000]}")
    return (result.result or "").strip()


def run_agent_turn(
    prompt: str,
    *,
    workspace: Path,
    model: str | None = None,
    timeout_sec: int = 600,
    backend: str | None = None,
) -> str:
    """Send one prompt; return the agent's text reply (markdown).

    * **backend** ``auto`` (default): SDK when ``CURSOR_API_KEY`` + ``cursor-sdk``
      are available, else ``cursor-agent`` CLI. If SDK fails, falls back to CLI
      when ``cursor-agent`` is on ``PATH``.
    * **backend** ``sdk``: SDK only.
    * **backend** ``cli``: subprocess ``cursor-agent`` only (keyless when logged in).
    """
    b = _effective_backend(backend)
    resolved_model = (model or os.environ.get(ENV_MODEL) or DEFAULT_MODEL).strip()

    if b == "sdk":
        return _run_sdk(prompt, workspace=workspace, model=resolved_model)
    if b == "cli":
        return _run_cli(prompt, workspace=workspace, model=resolved_model, timeout_sec=timeout_sec)

    if sdk_dependencies_met():
        try:
            return _run_sdk(prompt, workspace=workspace, model=resolved_model)
        except RuntimeError:
            if resolve_cursor_agent_exe():
                return _run_cli(
                    prompt, workspace=workspace, model=resolved_model, timeout_sec=timeout_sec
                )
            raise

    return _run_cli(prompt, workspace=workspace, model=resolved_model, timeout_sec=timeout_sec)
