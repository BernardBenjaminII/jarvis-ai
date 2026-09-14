"""Operational defaults, independent of request classification and tool authority."""
from __future__ import annotations
import os

STANCES = {
    "assistant": {
        "role": "general assistant",
        "mission": "Provide practical assistance across subjects.",
        "guidance": "Provide general-purpose assistance tailored to the detected platform.",
    },
    "engineering": {
        "role": "systems engineer",
        "mission": "Support software development and system maintenance.",
        "guidance": "For relevant technical requests, emphasize reproducibility, diagnostics, and maintainable solutions.",
    },
    "security": {
        "role": "security analyst",
        "mission": "Support authorized security investigation and evidence analysis.",
        "guidance": "For relevant security requests, emphasize target scope, evidence, reproducible findings, and defensive remediation. A security stance grants no permission to execute tools.",
    },
    "research": {
        "role": "research assistant",
        "mission": "Evaluate sources and explain evidence.",
        "guidance": "For relevant research requests, emphasize source quality, evidence gaps, and clear attribution.",
    },
}
DEFAULTS = {"kali": "security", "ubuntu": "engineering"}


def resolve_stance(environment, override=None):
    value = override if override is not None else os.getenv("JARVIS_STANCE", "auto")
    value = value.strip().lower() or "auto"
    if value != "auto" and value not in STANCES:
        raise ValueError("JARVIS_STANCE must be auto, assistant, engineering, security, or research")
    name = DEFAULTS.get(environment, "assistant") if value == "auto" else value
    return {"name": name, "source": "platform" if value == "auto" else "override", **STANCES[name]}
