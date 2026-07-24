"""VI-A6.6 lifecycle-to-timeline adapter."""
from __future__ import annotations
from .contracts import TimelineContext, TimelineEventDraft, TimelineEventKind, TimelineSubsystem

_MAP = {
    "boot_started": TimelineEventKind.EXECUTIVE_BOOT_STARTED,
    "boot_completed": TimelineEventKind.EXECUTIVE_BOOT_COMPLETED,
    "session_created": TimelineEventKind.SESSION_CREATED,
    "session_activated": TimelineEventKind.SESSION_ACTIVATED,
    "checkpoint_started": TimelineEventKind.CHECKPOINT_STARTED,
    "checkpoint_completed": TimelineEventKind.CHECKPOINT_CREATED,
    "session_suspended": TimelineEventKind.SESSION_SUSPENDED,
    "recovery_started": TimelineEventKind.RECOVERY_STARTED,
    "recovery_completed": TimelineEventKind.RECOVERY_COMPLETED,
    "session_completed": TimelineEventKind.SESSION_COMPLETED,
    "session_aborted": TimelineEventKind.SESSION_ABORTED,
    "shutdown_started": TimelineEventKind.EXECUTIVE_SHUTDOWN_STARTED,
    "shutdown_completed": TimelineEventKind.EXECUTIVE_SHUTDOWN_COMPLETED,
    "failure_recorded": TimelineEventKind.EXECUTIVE_FAILURE,
}

def lifecycle_event_to_draft(event: object, *, mission_id: str | None = None) -> TimelineEventDraft:
    raw = getattr(event, "kind")
    value = getattr(raw, "value", str(raw))
    if value not in _MAP:
        raise ValueError(f"Unsupported lifecycle event: {value}")
    state = getattr(event, "lifecycle_state", None)
    return TimelineEventDraft(
        subsystem=TimelineSubsystem.LIFECYCLE,
        kind=_MAP[value],
        context=TimelineContext(
            session_id=getattr(event, "session_id", None),
            mission_id=mission_id,
        ),
        payload={
            "detail": getattr(event, "detail", ""),
            "lifecycle_state": getattr(state, "value", str(state)),
            "source_sequence": getattr(event, "sequence", None),
            "source_fingerprint": getattr(event, "event_fingerprint", None),
        },
        occurred_at=getattr(event, "occurred_at", None),
    )
