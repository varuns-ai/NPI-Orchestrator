"""Backend checks and PATH resolution (no Cursor SDK import at module load).

Mirrors the Czech tutor runtime so the NPI Orchestrator can talk to either the
Cursor Python SDK (``CURSOR_API_KEY`` + ``cursor-sdk``) or the keyless
``cursor-agent`` CLI.
"""

from __future__ import annotations

import os
import shutil

DEFAULT_MODEL = "auto"
DEFAULT_BACKEND = "cli"  # keyless cursor-agent CLI (run: cursor-agent login)
ENV_BACKEND = "NPI_BACKEND"
ENV_MODEL = "CURSOR_AGENT_MODEL"


def resolve_cursor_agent_exe() -> str | None:
    for name in ("cursor-agent.cmd", "cursor-agent.exe", "cursor-agent"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _effective_backend(backend: str | None) -> str:
    b = (backend or os.environ.get(ENV_BACKEND, DEFAULT_BACKEND)).strip().lower()
    if b not in ("auto", "sdk", "cli"):
        raise ValueError(f"Unknown backend {b!r}; use auto, sdk, or cli.")
    return b


def sdk_dependencies_met() -> bool:
    """True when ``CURSOR_API_KEY`` is set and ``cursor-sdk`` is installed."""
    if not os.environ.get("CURSOR_API_KEY"):
        return False
    try:
        import cursor_sdk  # noqa: F401
    except ImportError:
        return False
    return True


def runtime_ready(backend: str | None = None) -> tuple[bool, str]:
    """Return ``(ok, error_message)``. Empty message when ok."""
    try:
        b = _effective_backend(backend)
    except ValueError as exc:
        return False, str(exc)
    has_cli = resolve_cursor_agent_exe() is not None
    has_sdk = sdk_dependencies_met()
    if b == "cli":
        if has_cli:
            return True, ""
        return False, (
            "cursor-agent not found in PATH. Install Cursor Agent CLI and run: cursor-agent login"
        )
    if b == "sdk":
        if not os.environ.get("CURSOR_API_KEY"):
            return False, "Set CURSOR_API_KEY for SDK backend."
        try:
            import cursor_sdk  # noqa: F401
        except ImportError:
            return False, "Install SDK: pip install -r requirements-sdk.txt"
        return True, ""
    if has_sdk or has_cli:
        return True, ""
    return False, (
        "Need either cursor-agent in PATH (run: cursor-agent login) or "
        "CURSOR_API_KEY plus cursor-sdk (pip install -r requirements-sdk.txt)."
    )
