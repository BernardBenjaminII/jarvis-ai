"""Canonical fixtures for Genesis II reasoning-session contracts.

These helpers construct valid constitutional objects exclusively through the
certified public contracts introduced in Genesis II-A1.
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import NAMESPACE_URL, UUID

from core.reasoning.session import (
    ReasoningSession,
    ReasoningSessionId,
    ReasoningSessionMetadata,
    ReasoningSessionState,
    SessionAttribute,
)


DEFAULT_NAMESPACE: UUID = NAMESPACE_URL
DEFAULT_MATERIAL = "jarvis://genesis/reasoning/session/default"
DEFAULT_CREATED_BY = "executive-director"


def make_identifier(
    *,
    namespace: str | UUID = DEFAULT_NAMESPACE,
    material: str = DEFAULT_MATERIAL,
) -> ReasoningSessionId:
    """Construct a deterministic constitutional reasoning-session identifier."""

    return ReasoningSessionId.derive(
        namespace=namespace,
        material=material,
    )


def make_metadata(
    *,
    created_by: str = DEFAULT_CREATED_BY,
    mission_id: str | None = "mission-genesis-ii",
    objective_id: str | None = "objective-session-lifecycle",
    correlation_id: str | None = "correlation-genesis-ii-a2r",
    attributes: Iterable[SessionAttribute] = (),
    schema_version: str = "1.0.0",
) -> ReasoningSessionMetadata:
    """Construct valid deterministic reasoning-session metadata."""

    return ReasoningSessionMetadata(
        created_by=created_by,
        mission_id=mission_id,
        objective_id=objective_id,
        correlation_id=correlation_id,
        attributes=tuple(attributes),
        schema_version=schema_version,
    )


def make_reasoning_session(
    *,
    session_id: ReasoningSessionId | None = None,
    metadata: ReasoningSessionMetadata | None = None,
    state: ReasoningSessionState = ReasoningSessionState.CREATED,
    revision: int = 0,
    namespace: str | UUID = DEFAULT_NAMESPACE,
    material: str = DEFAULT_MATERIAL,
) -> ReasoningSession:
    """Construct a valid immutable reasoning-session snapshot.

    Explicit ``session_id`` and ``metadata`` values take precedence. Namespace
    and material are used only when a session identifier is not supplied.
    """

    resolved_session_id = session_id or make_identifier(
        namespace=namespace,
        material=material,
    )
    resolved_metadata = metadata or make_metadata()

    return ReasoningSession(
        session_id=resolved_session_id,
        metadata=resolved_metadata,
        state=state,
        revision=revision,
    )


__all__ = [
    "DEFAULT_CREATED_BY",
    "DEFAULT_MATERIAL",
    "DEFAULT_NAMESPACE",
    "make_identifier",
    "make_metadata",
    "make_reasoning_session",
]
