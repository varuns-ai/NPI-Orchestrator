"""Parse the structured gate metadata each phase agent appends to its reply.

Every phase agent ends its answer with one HTML comment carrying one-line JSON:

    <!--NPI_META:{"gate_decision":"GO","deliverables":[...],"risks":[...],...}-->

This lets the orchestrator track gate decisions, deliverable readiness, risks
and the hand-off note across phases without re-parsing prose.
"""

from __future__ import annotations

import json
from typing import Any

_META_START = "<!--NPI_META:"
_META_END = "-->"

VALID_DECISIONS = {"GO", "GO_WITH_CONDITIONS", "NO_GO", "PENDING"}


def split_phase_response(raw: str) -> tuple[str, dict[str, Any]]:
    """Split an agent reply into (human-readable markdown, parsed metadata dict)."""
    text = (raw or "").strip()
    idx = text.rfind(_META_START)
    if idx == -1:
        return text, {}
    end = text.find(_META_END, idx + len(_META_START))
    if end == -1:
        return text, {}
    blob = text[idx + len(_META_START) : end].strip()
    visible = (text[:idx] + text[end + len(_META_END) :]).strip()
    try:
        meta = json.loads(blob)
    except json.JSONDecodeError:
        return text, {}
    if not isinstance(meta, dict):
        return visible, {}
    return visible, meta


def phase_reply_visible(raw: str) -> str:
    """The markdown shown to the user (metadata stripped)."""
    return split_phase_response(raw)[0]


def normalize_decision(value: Any) -> str:
    """Coerce a gate decision string into one of :data:`VALID_DECISIONS`."""
    if not isinstance(value, str):
        return "PENDING"
    v = value.strip().upper().replace("-", "_").replace(" ", "_")
    return v if v in VALID_DECISIONS else "PENDING"


def decision_label(decision: str) -> str:
    return {
        "GO": "GO",
        "GO_WITH_CONDITIONS": "GO (with conditions)",
        "NO_GO": "NO-GO",
        "PENDING": "Pending / needs input",
    }.get(decision, "Pending / needs input")
