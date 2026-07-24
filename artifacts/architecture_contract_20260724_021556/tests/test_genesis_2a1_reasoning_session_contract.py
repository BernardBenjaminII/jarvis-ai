"""Genesis II-A1 contract verification."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import NAMESPACE_URL

import pytest

from core.reasoning.session import (
    ReasoningSession,
    ReasoningSessionId,
    ReasoningSessionMetadata,
    ReasoningSessionState,
    SessionAttribute,
)


def test_reasoning_session_identifier_is_deterministic() -> None:
    first = ReasoningSessionId.derive(
        namespace=NAMESPACE_URL,
        material="jarvis://mission/alpha/reasoning/session/1",
    )
    second = ReasoningSessionId.derive(
        namespace=NAMESPACE_URL,
        material="jarvis://mission/alpha/reasoning/session/1",
    )

    assert first == second
    assert str(first) == str(second)


def test_reasoning_session_identifier_rejects_invalid_uuid() -> None:
    with pytest.raises(ValueError):
        ReasoningSessionId.from_value("not-a-uuid")


def test_metadata_is_normalized_and_deterministically_ordered() -> None:
    metadata = ReasoningSessionMetadata(
        created_by=" executive-director ",
        mission_id=" mission-001 ",
        objective_id=" ",
        attributes=(
            SessionAttribute("priority", "high"),
            SessionAttribute("domain", "knowledge"),
        ),
    )

    assert metadata.created_by == "executive-director"
    assert metadata.mission_id == "mission-001"
    assert metadata.objective_id is None
    assert metadata.attributes == (
        SessionAttribute("domain", "knowledge"),
        SessionAttribute("priority", "high"),
    )


def test_metadata_rejects_duplicate_attribute_keys() -> None:
    with pytest.raises(ValueError):
        ReasoningSessionMetadata(
            created_by="executive-director",
            attributes=(
                SessionAttribute("priority", "high"),
                SessionAttribute("priority", "critical"),
            ),
        )


def test_session_defaults_to_created_revision_zero() -> None:
    session = ReasoningSession(
        session_id=ReasoningSessionId.derive(
            namespace=NAMESPACE_URL,
            material="jarvis://mission/alpha/reasoning/session/1",
        ),
        metadata=ReasoningSessionMetadata(created_by="executive-director"),
    )

    assert session.state is ReasoningSessionState.CREATED
    assert session.revision == 0


def test_session_contract_is_immutable() -> None:
    session = ReasoningSession(
        session_id=ReasoningSessionId.derive(
            namespace=NAMESPACE_URL,
            material="jarvis://mission/alpha/reasoning/session/immutable",
        ),
        metadata=ReasoningSessionMetadata(created_by="executive-director"),
    )

    with pytest.raises(FrozenInstanceError):
        session.revision = 1  # type: ignore[misc]


def test_session_rejects_negative_revision() -> None:
    with pytest.raises(ValueError):
        ReasoningSession(
            session_id=ReasoningSessionId.derive(
                namespace=NAMESPACE_URL,
                material="jarvis://mission/alpha/reasoning/session/invalid",
            ),
            metadata=ReasoningSessionMetadata(created_by="executive-director"),
            revision=-1,
        )


def test_state_vocabulary_is_complete_and_stable() -> None:
    assert tuple(state.value for state in ReasoningSessionState) == (
        "created",
        "initialized",
        "collecting_evidence",
        "reasoning",
        "review",
        "completed",
        "failed",
        "cancelled",
    )
