"""C-6 Mission Transparency projection service."""
from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.conversation.contracts import ExecutiveRequestContext

from core.observability.contracts import MissionTransparencySnapshot, TransparencyEvent


class ExecutiveObservabilityService:
    """Builds UI-safe operational projections from public execution artifacts.

    The service exposes stages, evidence counts, confidence, assignments, and
    declared gaps. It intentionally does not expose private chain-of-thought.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._latest: MissionTransparencySnapshot | None = None

    def project(self, *, context: ExecutiveRequestContext, result: Any) -> MissionTransparencySnapshot:
        trace = tuple(getattr(result, "trace", ()) or ())
        assignments = tuple(getattr(result, "assignments", ()) or ())
        grounding = getattr(result, "grounding", None)
        knowledge_state = getattr(result, "knowledge_state", None)

        events = tuple(
            TransparencyEvent(
                sequence=index,
                stage=str(getattr(item, "stage", "unknown")),
                status=str(getattr(item, "status", "unknown")),
                summary=str(getattr(item, "detail", "")),
                data=dict(getattr(item, "data", {}) or {}),
            )
            for index, item in enumerate(trace, start=1)
        )
        directors = tuple(sorted({
            director
            for assignment in assignments
            for director in tuple(getattr(assignment, "directors", ()) or ())
        }))
        evidence = tuple(getattr(grounding, "evidence", ()) or ()) if grounding is not None else ()
        gaps = tuple(getattr(grounding, "gaps", ()) or ()) if grounding is not None else ()
        current_stage = events[-1].stage if events else "conversation.received"
        status = events[-1].status if events else "completed"

        snapshot = MissionTransparencySnapshot(
            request_id=context.request_id,
            session_id=context.session_id,
            objective_count=len(context.objectives),
            mission_count=len(assignments),
            directors=directors,
            current_stage=current_stage,
            status=status,
            confidence=(None if knowledge_state is None else float(knowledge_state.confidence)),
            answerability=(None if knowledge_state is None else str(knowledge_state.answerability)),
            evidence_count=len(evidence),
            knowledge_gap_count=len(gaps),
            contradiction_count=(0 if knowledge_state is None else int(knowledge_state.contradiction_count)),
            events=events,
        )
        with self._lock:
            self._latest = snapshot
        return snapshot

    def latest(self) -> MissionTransparencySnapshot | None:
        with self._lock:
            return self._latest


_DEFAULT_SERVICE = ExecutiveObservabilityService()


def get_default_observability_service() -> ExecutiveObservabilityService:
    return _DEFAULT_SERVICE
