"""Certification tests for canonical reasoning-session fixtures."""

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
from tests.fixtures.reasoning import (
    DEFAULT_CREATED_BY,
    DEFAULT_MATERIAL,
    DEFAULT_NAMESPACE,
    make_identifier,
    make_metadata,
    make_reasoning_session,
)


def test_fixture_defaults_match_certified_contract_vocabulary() -> None:
    assert DEFAULT_NAMESPACE == NAMESPACE_URL
    assert DEFAULT_CREATED_BY == "executive-director"
    assert DEFAULT_MATERIAL


def test_identifier_fixture_is_valid_and_deterministic() -> None:
    first = make_identifier()
    second = make_identifier()

    assert isinstance(first, ReasoningSessionId)
    assert first == second
    assert str(first) == str(second)


def test_identifier_fixture_supports_material_override() -> None:
    first = make_identifier(material="jarvis://fixture/one")
    second = make_identifier(material="jarvis://fixture/two")

    assert first != second


def test_metadata_fixture_constructs_certified_metadata() -> None:
    metadata = make_metadata(
        attributes=(
            SessionAttribute("priority", "high"),
            SessionAttribute("domain", "reasoning"),
        )
    )

    assert isinstance(metadata, ReasoningSessionMetadata)
    assert metadata.created_by == DEFAULT_CREATED_BY
    assert metadata.attributes == (
        SessionAttribute("domain", "reasoning"),
        SessionAttribute("priority", "high"),
    )


def test_metadata_fixture_supports_explicit_overrides() -> None:
    metadata = make_metadata(
        created_by="reasoning-director",
        mission_id=None,
        objective_id=None,
        correlation_id=None,
        schema_version="2.0.0",
    )

    assert metadata.created_by == "reasoning-director"
    assert metadata.mission_id is None
    assert metadata.objective_id is None
    assert metadata.correlation_id is None
    assert metadata.schema_version == "2.0.0"


def test_session_fixture_uses_constitutional_defaults() -> None:
    session = make_reasoning_session()

    assert isinstance(session, ReasoningSession)
    assert session.state is ReasoningSessionState.CREATED
    assert session.revision == 0
    assert session.metadata.created_by == DEFAULT_CREATED_BY


def test_session_fixture_is_deterministic() -> None:
    first = make_reasoning_session()
    second = make_reasoning_session()

    assert first == second


def test_session_fixture_supports_state_and_revision_overrides() -> None:
    session = make_reasoning_session(
        state=ReasoningSessionState.REVIEW,
        revision=4,
    )

    assert session.state is ReasoningSessionState.REVIEW
    assert session.revision == 4


def test_session_fixture_preserves_explicit_contract_objects() -> None:
    identifier = make_identifier(material="jarvis://fixture/explicit")
    metadata = make_metadata(created_by="fixture-certifier")

    session = make_reasoning_session(
        session_id=identifier,
        metadata=metadata,
    )

    assert session.session_id is identifier
    assert session.metadata is metadata


def test_fixture_objects_remain_immutable() -> None:
    session = make_reasoning_session()

    with pytest.raises(FrozenInstanceError):
        session.revision = 1  # type: ignore[misc]


def test_fixtures_do_not_bypass_contract_validation() -> None:
    with pytest.raises(ValueError):
        make_metadata(created_by=" ")

    with pytest.raises(ValueError):
        make_reasoning_session(revision=-1)
