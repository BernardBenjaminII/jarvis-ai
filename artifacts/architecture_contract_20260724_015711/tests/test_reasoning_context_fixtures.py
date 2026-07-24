"""Certification tests for Genesis II-A3 canonical context fixtures."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.reasoning.context import (
    ReasoningConstraint,
    ReasoningContext,
    ReasoningContextId,
)
from tests.fixtures.reasoning import (
    DEFAULT_REASONING_QUESTION,
    make_context_identifier,
    make_reasoning_context,
)


def test_context_identifier_fixture_is_deterministic() -> None:
    first = make_context_identifier()
    second = make_context_identifier()

    assert isinstance(first, ReasoningContextId)
    assert first == second


def test_context_fixture_is_valid_and_deterministic() -> None:
    first = make_reasoning_context()
    second = make_reasoning_context()

    assert isinstance(first, ReasoningContext)
    assert first == second
    assert first.question == DEFAULT_REASONING_QUESTION
    assert first.revision == 0


def test_context_fixture_supports_overrides() -> None:
    constraint = ReasoningConstraint(
        "determinism",
        "Equivalent inputs must produce equivalent context.",
    )
    context = make_reasoning_context(
        question="What must the context preserve?",
        constraints=(constraint,),
        revision=3,
    )

    assert context.question == "What must the context preserve?"
    assert context.constraints == (constraint,)
    assert context.revision == 3


def test_context_fixture_does_not_bypass_validation() -> None:
    with pytest.raises(ValueError):
        make_reasoning_context(question="")

    with pytest.raises(ValueError):
        make_reasoning_context(revision=-1)


def test_context_fixture_constructs_immutable_objects() -> None:
    context = make_reasoning_context()

    with pytest.raises(FrozenInstanceError):
        context.question = "Changed"  # type: ignore[misc]
