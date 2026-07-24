"""Immutable contracts for Genesis II-A3 constitutional reasoning context."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, UUID, uuid5

from core.reasoning.context.validators import (
    normalize_keyed_items,
    normalize_optional_text,
    normalize_required_text,
    normalize_schema_version,
    validate_weight,
)
from core.reasoning.session import ReasoningSessionId


@dataclass(frozen=True, slots=True, order=True)
class ReasoningContextId:
    """Stable UUID-backed identity for a constitutional reasoning context."""

    value: str

    def __post_init__(self) -> None:
        try:
            normalized = str(UUID(str(self.value)))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError(
                "ReasoningContextId value must be a valid UUID"
            ) from exc

        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_value(cls, value: str | UUID) -> "ReasoningContextId":
        return cls(str(value))

    @classmethod
    def derive(
        cls,
        *,
        namespace: str | UUID = NAMESPACE_URL,
        material: str,
    ) -> "ReasoningContextId":
        normalized_material = normalize_required_text(
            material,
            field_name="material",
        )

        try:
            normalized_namespace = (
                namespace
                if isinstance(namespace, UUID)
                else UUID(str(namespace))
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError(
                "namespace must be a valid UUID"
            ) from exc

        return cls(str(uuid5(normalized_namespace, normalized_material)))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ReasoningConstraint:
    """A binding condition that limits valid reasoning or decisions."""

    key: str
    statement: str
    source: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "key",
            normalize_required_text(self.key, field_name="constraint.key"),
        )
        object.__setattr__(
            self,
            "statement",
            normalize_required_text(
                self.statement,
                field_name="constraint.statement",
            ),
        )
        object.__setattr__(
            self,
            "source",
            normalize_optional_text(
                self.source,
                field_name="constraint.source",
            ),
        )


@dataclass(frozen=True, slots=True, order=True)
class ReasoningAssumption:
    """An explicit proposition currently treated as true."""

    key: str
    statement: str
    rationale: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "key",
            normalize_required_text(self.key, field_name="assumption.key"),
        )
        object.__setattr__(
            self,
            "statement",
            normalize_required_text(
                self.statement,
                field_name="assumption.statement",
            ),
        )
        object.__setattr__(
            self,
            "rationale",
            normalize_optional_text(
                self.rationale,
                field_name="assumption.rationale",
            ),
        )


@dataclass(frozen=True, slots=True, order=True)
class DecisionCriterion:
    """A weighted standard against which candidate decisions are judged."""

    key: str
    description: str
    weight: int = 50

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "key",
            normalize_required_text(self.key, field_name="criterion.key"),
        )
        object.__setattr__(
            self,
            "description",
            normalize_required_text(
                self.description,
                field_name="criterion.description",
            ),
        )
        object.__setattr__(self, "weight", validate_weight(self.weight))


@dataclass(frozen=True, slots=True, order=True)
class OpenReasoningQuestion:
    """An unresolved question that the reasoning process must address."""

    key: str
    question: str
    priority: int = 50

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "key",
            normalize_required_text(
                self.key,
                field_name="open_question.key",
            ),
        )
        object.__setattr__(
            self,
            "question",
            normalize_required_text(
                self.question,
                field_name="open_question.question",
            ),
        )
        object.__setattr__(
            self,
            "priority",
            validate_weight(self.priority),
        )


@dataclass(frozen=True, slots=True, order=True)
class ReasoningContextAttribute:
    """Deterministic extension attribute for a reasoning context."""

    key: str
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "key",
            normalize_required_text(self.key, field_name="attribute.key"),
        )
        object.__setattr__(
            self,
            "value",
            normalize_required_text(
                self.value,
                field_name="attribute.value",
            ),
        )


@dataclass(frozen=True, slots=True)
class ReasoningContext:
    """Immutable constitutional state required before evidence collection."""

    context_id: ReasoningContextId
    session_id: ReasoningSessionId
    question: str
    purpose: str | None = None
    mission_id: str | None = None
    objective_id: str | None = None
    constraints: tuple[ReasoningConstraint, ...] = field(default_factory=tuple)
    assumptions: tuple[ReasoningAssumption, ...] = field(default_factory=tuple)
    decision_criteria: tuple[DecisionCriterion, ...] = field(
        default_factory=tuple
    )
    open_questions: tuple[OpenReasoningQuestion, ...] = field(
        default_factory=tuple
    )
    attributes: tuple[ReasoningContextAttribute, ...] = field(
        default_factory=tuple
    )
    revision: int = 0
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, ReasoningContextId):
            raise TypeError(
                "context_id must be a ReasoningContextId"
            )

        if not isinstance(self.session_id, ReasoningSessionId):
            raise TypeError(
                "session_id must be a ReasoningSessionId"
            )

        object.__setattr__(
            self,
            "question",
            normalize_required_text(
                self.question,
                field_name="question",
            ),
        )
        object.__setattr__(
            self,
            "purpose",
            normalize_optional_text(
                self.purpose,
                field_name="purpose",
            ),
        )
        object.__setattr__(
            self,
            "mission_id",
            normalize_optional_text(
                self.mission_id,
                field_name="mission_id",
            ),
        )
        object.__setattr__(
            self,
            "objective_id",
            normalize_optional_text(
                self.objective_id,
                field_name="objective_id",
            ),
        )
        object.__setattr__(
            self,
            "constraints",
            normalize_keyed_items(
                self.constraints,
                collection_name="constraints",
            ),
        )
        object.__setattr__(
            self,
            "assumptions",
            normalize_keyed_items(
                self.assumptions,
                collection_name="assumptions",
            ),
        )
        object.__setattr__(
            self,
            "decision_criteria",
            normalize_keyed_items(
                self.decision_criteria,
                collection_name="decision_criteria",
            ),
        )
        object.__setattr__(
            self,
            "open_questions",
            normalize_keyed_items(
                self.open_questions,
                collection_name="open_questions",
            ),
        )
        object.__setattr__(
            self,
            "attributes",
            normalize_keyed_items(
                self.attributes,
                collection_name="attributes",
            ),
        )

        if isinstance(self.revision, bool) or not isinstance(
            self.revision,
            int,
        ):
            raise TypeError("revision must be an integer")

        if self.revision < 0:
            raise ValueError("revision must be non-negative")

        object.__setattr__(
            self,
            "schema_version",
            normalize_schema_version(self.schema_version),
        )


__all__ = [
    "DecisionCriterion",
    "OpenReasoningQuestion",
    "ReasoningAssumption",
    "ReasoningConstraint",
    "ReasoningContext",
    "ReasoningContextAttribute",
    "ReasoningContextId",
]
