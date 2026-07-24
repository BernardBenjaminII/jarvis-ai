"""Immutable operations for Genesis II-A3 reasoning context."""

from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from core.reasoning.context.contracts import (
    DecisionCriterion,
    OpenReasoningQuestion,
    ReasoningAssumption,
    ReasoningConstraint,
    ReasoningContext,
    ReasoningContextAttribute,
)
from core.reasoning.context.errors import ReasoningContextContractError
from core.reasoning.context.validators import normalize_keyed_items


TContextItem = TypeVar(
    "TContextItem",
    ReasoningConstraint,
    ReasoningAssumption,
    DecisionCriterion,
    OpenReasoningQuestion,
    ReasoningContextAttribute,
)


class ReasoningContextManager:
    """Apply deterministic immutable updates to reasoning context snapshots."""

    @classmethod
    def replace_question(
        cls,
        context: ReasoningContext,
        question: str,
    ) -> ReasoningContext:
        cls._validate_context(context)
        return replace(
            context,
            question=question,
            revision=context.revision + 1,
        )

    @classmethod
    def add_constraint(
        cls,
        context: ReasoningContext,
        constraint: ReasoningConstraint,
    ) -> ReasoningContext:
        return cls._append_keyed(
            context,
            field_name="constraints",
            item=constraint,
            expected_type=ReasoningConstraint,
        )

    @classmethod
    def add_assumption(
        cls,
        context: ReasoningContext,
        assumption: ReasoningAssumption,
    ) -> ReasoningContext:
        return cls._append_keyed(
            context,
            field_name="assumptions",
            item=assumption,
            expected_type=ReasoningAssumption,
        )

    @classmethod
    def add_decision_criterion(
        cls,
        context: ReasoningContext,
        criterion: DecisionCriterion,
    ) -> ReasoningContext:
        return cls._append_keyed(
            context,
            field_name="decision_criteria",
            item=criterion,
            expected_type=DecisionCriterion,
        )

    @classmethod
    def add_open_question(
        cls,
        context: ReasoningContext,
        question: OpenReasoningQuestion,
    ) -> ReasoningContext:
        return cls._append_keyed(
            context,
            field_name="open_questions",
            item=question,
            expected_type=OpenReasoningQuestion,
        )

    @classmethod
    def add_attribute(
        cls,
        context: ReasoningContext,
        attribute: ReasoningContextAttribute,
    ) -> ReasoningContext:
        return cls._append_keyed(
            context,
            field_name="attributes",
            item=attribute,
            expected_type=ReasoningContextAttribute,
        )

    @classmethod
    def _append_keyed(
        cls,
        context: ReasoningContext,
        *,
        field_name: str,
        item: TContextItem,
        expected_type: type[TContextItem],
    ) -> ReasoningContext:
        cls._validate_context(context)

        if not isinstance(item, expected_type):
            raise ReasoningContextContractError(
                f"{field_name} requires {expected_type.__name__}"
            )

        current = getattr(context, field_name)
        updated = normalize_keyed_items(
            (*current, item),
            collection_name=field_name,
        )

        return replace(
            context,
            **{
                field_name: updated,
                "revision": context.revision + 1,
            },
        )

    @staticmethod
    def _validate_context(context: ReasoningContext) -> None:
        if not isinstance(context, ReasoningContext):
            raise ReasoningContextContractError(
                "operation requires a ReasoningContext"
            )


ContextManager = ReasoningContextManager


__all__ = [
    "ContextManager",
    "ReasoningContextManager",
]
