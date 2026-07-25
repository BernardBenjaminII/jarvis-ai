"""Canonical models for Genesis IV-A3 Executive Hypothesis Engine."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from core.cognition.situation import SituationSnapshot

from .enums import HypothesisKind, HypothesisStatus
from .errors import InvalidHypothesisError, SituationCompatibilityError


def _required(value: str, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise InvalidHypothesisError(f"{field_name} must not be empty")
    return normalized


def _confidence(value: float) -> float:
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise InvalidHypothesisError(
            "confidence must be finite and between 0.0 and 1.0"
        )
    return normalized


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _string_tuple(
    values: Sequence[str] | None,
    field_name: str,
) -> tuple[str, ...]:
    if not values:
        return ()
    normalized = tuple(sorted({_required(item, field_name) for item in values}))
    return normalized


def _labels(
    values: Mapping[str, str] | None,
) -> tuple[tuple[str, str], ...]:
    if not values:
        return ()
    pairs: list[tuple[str, str]] = []
    for key, value in values.items():
        normalized_key = _required(key, "label key")
        normalized_value = _required(value, "label value")
        pairs.append((normalized_key, normalized_value))
    return tuple(sorted(pairs))


def _require_situation(value: SituationSnapshot) -> SituationSnapshot:
    if not isinstance(value, SituationSnapshot):
        raise SituationCompatibilityError(
            "hypotheses must reference a Genesis IV-A2 SituationSnapshot"
        )
    return value


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """Immutable candidate explanation for an executive situation."""

    hypothesis_id: str
    situation_id: str
    statement: str
    kind: HypothesisKind
    status: HypothesisStatus
    confidence: float
    supporting_observation_ids: tuple[str, ...] = ()
    contradicting_observation_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    rationale: str | None = None
    labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "hypothesis_id",
            _required(self.hypothesis_id, "hypothesis_id"),
        )
        object.__setattr__(
            self,
            "situation_id",
            _required(self.situation_id, "situation_id"),
        )
        object.__setattr__(
            self,
            "statement",
            _required(self.statement, "statement"),
        )

        if not isinstance(self.kind, HypothesisKind):
            object.__setattr__(
                self,
                "kind",
                HypothesisKind(str(self.kind)),
            )

        if not isinstance(self.status, HypothesisStatus):
            object.__setattr__(
                self,
                "status",
                HypothesisStatus(str(self.status)),
            )

        object.__setattr__(self, "confidence", _confidence(self.confidence))
        object.__setattr__(
            self,
            "supporting_observation_ids",
            _string_tuple(
                self.supporting_observation_ids,
                "supporting observation ID",
            ),
        )
        object.__setattr__(
            self,
            "contradicting_observation_ids",
            _string_tuple(
                self.contradicting_observation_ids,
                "contradicting observation ID",
            ),
        )
        object.__setattr__(
            self,
            "assumptions",
            _string_tuple(self.assumptions, "assumption"),
        )
        object.__setattr__(
            self,
            "unresolved_questions",
            _string_tuple(
                self.unresolved_questions,
                "unresolved question",
            ),
        )
        object.__setattr__(
            self,
            "labels",
            _labels(dict(self.labels)),
        )

        overlap = (
            set(self.supporting_observation_ids)
            & set(self.contradicting_observation_ids)
        )
        if overlap:
            raise InvalidHypothesisError(
                "an observation cannot both support and contradict "
                f"the same hypothesis: {sorted(overlap)}"
            )

        if self.rationale is not None:
            rationale = str(self.rationale).strip()
            object.__setattr__(self, "rationale", rationale or None)

    def label_map(self) -> dict[str, str]:
        """Return labels as a new dictionary."""

        return dict(self.labels)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return deterministic serialized hypothesis data."""

        return {
            "hypothesis_id": self.hypothesis_id,
            "situation_id": self.situation_id,
            "statement": self.statement,
            "kind": self.kind.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "supporting_observation_ids": list(
                self.supporting_observation_ids
            ),
            "contradicting_observation_ids": list(
                self.contradicting_observation_ids
            ),
            "assumptions": list(self.assumptions),
            "unresolved_questions": list(self.unresolved_questions),
            "rationale": self.rationale,
            "labels": self.label_map(),
        }

    def fingerprint(self) -> str:
        """Return a deterministic complete-record fingerprint."""

        return hashlib.sha256(
            _canonical_json(self.to_canonical_dict()).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class HypothesisProposal:
    """Input contract used to generate a hypothesis."""

    statement: str
    kind: HypothesisKind = HypothesisKind.EXPLANATORY
    confidence: float = 0.5
    supporting_observation_ids: tuple[str, ...] = ()
    contradicting_observation_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    rationale: str | None = None
    labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "statement",
            _required(self.statement, "statement"),
        )
        if not isinstance(self.kind, HypothesisKind):
            object.__setattr__(
                self,
                "kind",
                HypothesisKind(str(self.kind)),
            )
        object.__setattr__(self, "confidence", _confidence(self.confidence))
        object.__setattr__(
            self,
            "supporting_observation_ids",
            _string_tuple(
                self.supporting_observation_ids,
                "supporting observation ID",
            ),
        )
        object.__setattr__(
            self,
            "contradicting_observation_ids",
            _string_tuple(
                self.contradicting_observation_ids,
                "contradicting observation ID",
            ),
        )
        object.__setattr__(
            self,
            "assumptions",
            _string_tuple(self.assumptions, "assumption"),
        )
        object.__setattr__(
            self,
            "unresolved_questions",
            _string_tuple(
                self.unresolved_questions,
                "unresolved question",
            ),
        )
        object.__setattr__(
            self,
            "labels",
            _labels(dict(self.labels)),
        )


@dataclass(frozen=True, slots=True)
class HypothesisQuery:
    """Repository query for hypotheses."""

    situation_id: str | None = None
    kind: HypothesisKind | None = None
    status: HypothesisStatus | None = None
    minimum_confidence: float | None = None
    limit: int | None = None
    strongest_first: bool = False

    def __post_init__(self) -> None:
        if self.minimum_confidence is not None:
            object.__setattr__(
                self,
                "minimum_confidence",
                _confidence(self.minimum_confidence),
            )
        if self.limit is not None and self.limit < 1:
            raise InvalidHypothesisError("limit must be at least 1")


def derive_hypothesis_identity(
    *,
    situation: SituationSnapshot,
    proposal: HypothesisProposal,
) -> str:
    """Derive a stable semantic hypothesis identity."""

    _require_situation(situation)
    payload = {
        "situation_id": situation.situation_id,
        "statement": proposal.statement,
        "kind": proposal.kind.value,
        "supporting_observation_ids": list(
            proposal.supporting_observation_ids
        ),
        "contradicting_observation_ids": list(
            proposal.contradicting_observation_ids
        ),
        "assumptions": list(proposal.assumptions),
        "unresolved_questions": list(proposal.unresolved_questions),
    }
    return "hyp_" + hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()
