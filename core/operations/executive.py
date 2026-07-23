"""Executive telemetry adapter for the Operations interface."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Mapping
from .contracts import ExecutiveProvider
from .enums import ExecutiveState
from .models import ExecutiveSnapshot, Provenance, utc_now

class DefaultExecutiveProvider:
    def collect_executive_state(self) -> Mapping[str, Any]:
        return {"state":"ready","readiness":1.0,"detail":"Executive telemetry adapter is ready.","source":"operations","source_version":"genesis-vi-a1"}

class ExecutiveTelemetryAdapter:
    def __init__(self, provider: ExecutiveProvider | None = None) -> None:
        self._provider = provider or DefaultExecutiveProvider()

    def collect(self, *, captured_at: datetime | None = None) -> ExecutiveSnapshot:
        now = captured_at or utc_now()
        try:
            record = dict(self._provider.collect_executive_state())
        except Exception as exc:
            record = {"state":"failed","readiness":0.0,"detail":f"{type(exc).__name__}: {exc}","source":type(self._provider).__name__,"source_version":"provider-error"}
        state = self._state(record.get("state"))
        return ExecutiveSnapshot(
            state=state,
            readiness=self._readiness(record.get("readiness"), state),
            detail=str(record.get("detail", "")).strip(),
            active_mission_id=_text(record.get("active_mission_id")),
            active_objective_id=_text(record.get("active_objective_id")),
            current_activity=_text(record.get("current_activity")),
            pending_decisions=_count(record.get("pending_decisions")),
            pending_recommendations=_count(record.get("pending_recommendations")),
            observation_count=_count(record.get("observation_count")),
            inference_count=_count(record.get("inference_count")),
            plan_count=_count(record.get("plan_count")),
            last_transition_at=record.get("last_transition_at") if isinstance(record.get("last_transition_at"), datetime) else now,
            captured_at=now,
            provenance=Provenance(str(record.get("source", type(self._provider).__name__)), str(record.get("source_version", "genesis-vi-a1")), now),
        )

    @staticmethod
    def _state(value: Any) -> ExecutiveState:
        try:
            return value if isinstance(value, ExecutiveState) else ExecutiveState(str(value or "ready").lower())
        except ValueError:
            return ExecutiveState.DEGRADED

    @staticmethod
    def _readiness(value: Any, state: ExecutiveState) -> float:
        defaults = {ExecutiveState.READY:1.0, ExecutiveState.DEGRADED:0.35, ExecutiveState.FAILED:0.0, ExecutiveState.STOPPED:0.0, ExecutiveState.PAUSED:0.5}
        if value is None:
            return defaults.get(state, 0.85)
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        if number > 1.0:
            number /= 100.0
        return max(0.0, min(1.0, number))

def _text(value: Any) -> str | None:
    if value is None: return None
    text = str(value).strip()
    return text or None

def _count(value: Any) -> int:
    try: return max(0, int(value or 0))
    except (TypeError, ValueError): return 0
