"""Canonical fixtures for Genesis II reasoning contracts."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import NAMESPACE_URL, UUID

from core.reasoning.context import (
    DecisionCriterion,
    OpenReasoningQuestion,
    ReasoningAssumption,
    ReasoningConstraint,
    ReasoningContext,
    ReasoningContextAttribute,
    ReasoningContextId,
)
from core.reasoning.session import (
    ReasoningSession,
    ReasoningSessionId,
    ReasoningSessionMetadata,
    ReasoningSessionState,
    SessionAttribute,
)


DEFAULT_NAMESPACE: UUID = NAMESPACE_URL
DEFAULT_MATERIAL = "jarvis://genesis/reasoning/session/default"
DEFAULT_CONTEXT_MATERIAL = "jarvis://genesis/reasoning/context/default"
DEFAULT_CREATED_BY = "executive-director"
DEFAULT_REASONING_QUESTION = (
    "What course of action best satisfies the stated objective?"
)


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
    """Construct a valid immutable reasoning-session snapshot."""

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


def make_context_identifier(
    *,
    namespace: str | UUID = DEFAULT_NAMESPACE,
    material: str = DEFAULT_CONTEXT_MATERIAL,
) -> ReasoningContextId:
    """Construct a deterministic constitutional reasoning-context identifier."""

    return ReasoningContextId.derive(
        namespace=namespace,
        material=material,
    )


def make_reasoning_context(
    *,
    context_id: ReasoningContextId | None = None,
    session_id: ReasoningSessionId | None = None,
    question: str = DEFAULT_REASONING_QUESTION,
    purpose: str | None = "Establish the constitutional reasoning frame.",
    mission_id: str | None = "mission-genesis-ii",
    objective_id: str | None = "objective-reasoning-context",
    constraints: Iterable[ReasoningConstraint] = (),
    assumptions: Iterable[ReasoningAssumption] = (),
    decision_criteria: Iterable[DecisionCriterion] = (),
    open_questions: Iterable[OpenReasoningQuestion] = (),
    attributes: Iterable[ReasoningContextAttribute] = (),
    revision: int = 0,
    schema_version: str = "1.0.0",
    namespace: str | UUID = DEFAULT_NAMESPACE,
    material: str = DEFAULT_CONTEXT_MATERIAL,
) -> ReasoningContext:
    """Construct a valid immutable constitutional reasoning context."""

    resolved_context_id = context_id or make_context_identifier(
        namespace=namespace,
        material=material,
    )
    resolved_session_id = session_id or make_identifier(
        namespace=namespace,
        material=DEFAULT_MATERIAL,
    )

    return ReasoningContext(
        context_id=resolved_context_id,
        session_id=resolved_session_id,
        question=question,
        purpose=purpose,
        mission_id=mission_id,
        objective_id=objective_id,
        constraints=tuple(constraints),
        assumptions=tuple(assumptions),
        decision_criteria=tuple(decision_criteria),
        open_questions=tuple(open_questions),
        attributes=tuple(attributes),
        revision=revision,
        schema_version=schema_version,
    )


__all__ = [
    "DEFAULT_CONTEXT_MATERIAL",
    "DEFAULT_CREATED_BY",
    "DEFAULT_MATERIAL",
    "DEFAULT_NAMESPACE",
    "DEFAULT_REASONING_QUESTION",
    "make_context_identifier",
    "make_identifier",
    "make_metadata",
    "make_reasoning_context",
    "make_reasoning_session",
]
