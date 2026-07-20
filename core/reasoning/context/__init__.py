"""Public Genesis II-A3 constitutional reasoning-context surface."""

from core.reasoning.context.context import (
    ContextManager,
    ReasoningContextManager,
)
from core.reasoning.context.contracts import (
    DecisionCriterion,
    OpenReasoningQuestion,
    ReasoningAssumption,
    ReasoningConstraint,
    ReasoningContext,
    ReasoningContextAttribute,
    ReasoningContextId,
)
from core.reasoning.context.errors import (
    DuplicateReasoningContextKeyError,
    ReasoningContextContractError,
    ReasoningContextError,
)

__all__ = [
    "ContextManager",
    "DecisionCriterion",
    "DuplicateReasoningContextKeyError",
    "OpenReasoningQuestion",
    "ReasoningAssumption",
    "ReasoningConstraint",
    "ReasoningContext",
    "ReasoningContextAttribute",
    "ReasoningContextContractError",
    "ReasoningContextError",
    "ReasoningContextId",
    "ReasoningContextManager",
]
