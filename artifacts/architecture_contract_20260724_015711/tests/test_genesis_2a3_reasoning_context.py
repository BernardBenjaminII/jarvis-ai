"""Certification tests for Genesis II-A3 reasoning context."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.reasoning.context import (
    DecisionCriterion,
    DuplicateReasoningContextKeyError,
    OpenReasoningQuestion,
    ReasoningAssumption,
    ReasoningConstraint,
    ReasoningContext,
    ReasoningContextAttribute,
    ReasoningContextId,
    ReasoningContextManager,
)
from tests.fixtures.reasoning import make_reasoning_context


def test_context_identifier_is_deterministic() -> None:
    first = ReasoningContextId.derive(material="jarvis://context/a")
    second = ReasoningContextId.derive(material="jarvis://context/a")
    third = ReasoningContextId.derive(material="jarvis://context/b")

    assert first == second
    assert first != third


def test_context_normalizes_and_orders_keyed_collections() -> None:
    context = make_reasoning_context(
        constraints=(
            ReasoningConstraint("zeta", "Z"),
            ReasoningConstraint("alpha", "A"),
        ),
        assumptions=(
            ReasoningAssumption("two", "Second"),
            ReasoningAssumption("one", "First"),
        ),
        decision_criteria=(
            DecisionCriterion("speed", "Fast execution", 40),
            DecisionCriterion("safety", "Avoid unacceptable harm", 100),
        ),
        open_questions=(
            OpenReasoningQuestion("unknown-b", "What is B?", 20),
            OpenReasoningQuestion("unknown-a", "What is A?", 90),
        ),
        attributes=(
            ReasoningContextAttribute("mode", "deliberative"),
            ReasoningContextAttribute("domain", "architecture"),
        ),
    )

    assert tuple(item.key for item in context.constraints) == (
        "alpha",
        "zeta",
    )
    assert tuple(item.key for item in context.assumptions) == (
        "one",
        "two",
    )
    assert tuple(item.key for item in context.decision_criteria) == (
        "safety",
        "speed",
    )
    assert tuple(item.key for item in context.open_questions) == (
        "unknown-a",
        "unknown-b",
    )
    assert tuple(item.key for item in context.attributes) == (
        "domain",
        "mode",
    )


@pytest.mark.parametrize(
    ("field_name", "items"),
    (
        (
            "constraints",
            (
                ReasoningConstraint("same", "First"),
                ReasoningConstraint("same", "Second"),
            ),
        ),
        (
            "assumptions",
            (
                ReasoningAssumption("same", "First"),
                ReasoningAssumption("same", "Second"),
            ),
        ),
        (
            "decision_criteria",
            (
                DecisionCriterion("same", "First"),
                DecisionCriterion("same", "Second"),
            ),
        ),
        (
            "open_questions",
            (
                OpenReasoningQuestion("same", "First"),
                OpenReasoningQuestion("same", "Second"),
            ),
        ),
        (
            "attributes",
            (
                ReasoningContextAttribute("same", "First"),
                ReasoningContextAttribute("same", "Second"),
            ),
        ),
    ),
)
def test_context_rejects_duplicate_keys(
    field_name: str,
    items: tuple[object, object],
) -> None:
    with pytest.raises(DuplicateReasoningContextKeyError):
        make_reasoning_context(**{field_name: items})


def test_context_is_immutable() -> None:
    context = make_reasoning_context()

    with pytest.raises(FrozenInstanceError):
        context.revision = 1  # type: ignore[misc]


def test_context_defaults_to_revision_zero() -> None:
    context = make_reasoning_context()

    assert context.revision == 0


def test_context_rejects_blank_primary_question() -> None:
    with pytest.raises(ValueError):
        make_reasoning_context(question=" ")


@pytest.mark.parametrize("weight", (0, 101, -1))
def test_decision_criterion_rejects_invalid_weight(weight: int) -> None:
    with pytest.raises(ValueError):
        DecisionCriterion("criterion", "Description", weight)


def test_manager_adds_constraint_immutably() -> None:
    context = make_reasoning_context()
    constraint = ReasoningConstraint(
        "offline-capability",
        "The system must remain useful without network access.",
    )

    successor = ReasoningContextManager.add_constraint(
        context,
        constraint,
    )

    assert successor is not context
    assert context.constraints == ()
    assert successor.constraints == (constraint,)
    assert successor.revision == 1


def test_manager_rejects_duplicate_key() -> None:
    context = make_reasoning_context(
        assumptions=(
            ReasoningAssumption("network", "Network is available."),
        )
    )

    with pytest.raises(DuplicateReasoningContextKeyError):
        ReasoningContextManager.add_assumption(
            context,
            ReasoningAssumption(
                "network",
                "Network is unavailable.",
            ),
        )


def test_manager_replaces_question_immutably() -> None:
    context = make_reasoning_context()

    successor = ReasoningContextManager.replace_question(
        context,
        "Which architecture provides the strongest long-term advantage?",
    )

    assert successor.question != context.question
    assert successor.revision == context.revision + 1


def test_context_preserves_session_identity() -> None:
    context = make_reasoning_context()

    successor = ReasoningContextManager.add_attribute(
        context,
        ReasoningContextAttribute("phase", "II-A3"),
    )

    assert successor.session_id == context.session_id
    assert successor.context_id == context.context_id
