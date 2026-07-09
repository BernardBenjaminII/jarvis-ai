from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CheckResult:
    stage: str
    name: str
    passed: bool
    message: str = ""
    fatal: bool = False
    duration_ms: float = 0.0
