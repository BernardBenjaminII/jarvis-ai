"""Public contracts for managed reasoning sessions.

Genesis II-A1 introduces immutable session contracts only. Lifecycle services,
transition policies, persistence, execution, and executive governance belong to
later Genesis II phases.
"""

from .contracts import (
    ReasoningSession,
    ReasoningSessionId,
    ReasoningSessionMetadata,
    ReasoningSessionState,
    SessionAttribute,
)

__all__ = [
    "ReasoningSession",
    "ReasoningSessionId",
    "ReasoningSessionMetadata",
    "ReasoningSessionState",
    "SessionAttribute",
]
