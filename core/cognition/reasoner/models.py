"""Canonical models for Genesis IV-A5 Executive Reasoner."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from core.cognition.evidence_correlation import HypothesisAssessment
from core.cognition.hypothesis import Hypothesis
from core.cognition.situation import SituationSnapshot

from .enums import ReasoningDisposition, ReasoningStatus
from .errors import InvalidReasoningResultError


def _required(value: str, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise InvalidReasoningResultError(f"{field_name} must not be empty")
    return normalized


def _probability(value: float, field_name: str) -> float:
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise InvalidReasoningResultError(
            f"{field_name} must be finite and between 0.0 and 1.0"
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


def _strings(values: Sequence[str] | None, field_name: str) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(sorted({_required(item, field_name) for item in values}))


def _labels(values: Mapping[str, str] | None) -> tuple[tuple[str, str], ...]:
    if not values:
        return ()
    normalized: list[tuple[str, str]] = []
    for key, value in values.items():
        normalized.append(
            (_required(key, "label key"), _required(value, "label value"))
        )
    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class HypothesisRanking:
    """Reasoning-layer ranking of one assessed hypothesis."""

    hypothesis_id: str
    assessment_id: str
    rank: int
    score: float
    confidence: float
    support_score: float
    contradiction_score: float
    coverage: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "hypothesis_id",
            _required(self.hypothesis_id, "hypothesis_id"),
        )
        object.__setattr__(
            self,
            "assessment_id",
            _required(self.assessment_id, "assessment_id"),
        )
        if self.rank < 1:
            raise InvalidReasoningResultError("rank must be at least 1")

        score = float(self.score)
        if not math.isfinite(score) or not -1.0 <= score <= 1.0:
            raise InvalidReasoningResultError(
                "score must be finite and between -1.0 and 1.0"
            )
        object.__setattr__(self, "score", score)

        for field_name in (
            "confidence",
            "support_score",
            "contradiction_score",
            "coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability(getattr(self, field_name), field_name),
            )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "assessment_id": self.assessment_id,
            "rank": self.rank,
            "score": self.score,
            "confidence": self.confidence,
            "support_score": self.support_score,
            "contradiction_score": self.contradiction_score,
            "coverage": self.coverage,
        }


@dataclass(frozen=True, slots=True)
class ExecutiveReasoningResult:
    """Immutable executive judgment over competing hypotheses."""

    reasoning_id: str
    situation_id: str
    status: ReasoningStatus
    disposition: ReasoningDisposition
    rankings: tuple[HypothesisRanking, ...]
    selected_hypothesis_id: str | None
    confidence: float
    margin: float
    rationale: str
    unresolved_assumptions: tuple[str, ...] = ()
    evidence_requests: tuple[str, ...] = ()
    labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reasoning_id",
            _required(self.reasoning_id, "reasoning_id"),
        )
        object.__setattr__(
            self,
            "situation_id",
            _required(self.situation_id, "situation_id"),
        )
        if not isinstance(self.status, ReasoningStatus):
            object.__setattr__(
                self,
                "status",
                ReasoningStatus(str(self.status)),
            )
        if not isinstance(self.disposition, ReasoningDisposition):
            object.__setattr__(
                self,
                "disposition",
                ReasoningDisposition(str(self.disposition)),
            )

        rankings = tuple(sorted(self.rankings, key=lambda item: item.rank))
        if not rankings:
            raise InvalidReasoningResultError(
                "reasoning result must contain at least one ranking"
            )
        expected = tuple(range(1, len(rankings) + 1))
        actual = tuple(item.rank for item in rankings)
        if actual != expected:
            raise InvalidReasoningResultError(
                "ranking sequence must be contiguous and begin at 1"
            )
        object.__setattr__(self, "rankings", rankings)

        if self.selected_hypothesis_id is not None:
            selected = _required(
                self.selected_hypothesis_id,
                "selected_hypothesis_id",
            )
            if selected not in {item.hypothesis_id for item in rankings}:
                raise InvalidReasoningResultError(
                    "selected hypothesis is absent from rankings"
                )
            object.__setattr__(self, "selected_hypothesis_id", selected)

        if (
            self.disposition is ReasoningDisposition.SELECTED
            and self.selected_hypothesis_id is None
        ):
            raise InvalidReasoningResultError(
                "SELECTED disposition requires selected_hypothesis_id"
            )
        if (
            self.disposition is not ReasoningDisposition.SELECTED
            and self.selected_hypothesis_id is not None
        ):
            raise InvalidReasoningResultError(
                "non-selected dispositions must not select a hypothesis"
            )

        object.__setattr__(
            self,
            "confidence",
            _probability(self.confidence, "confidence"),
        )
        object.__setattr__(
            self,
            "margin",
            _probability(self.margin, "margin"),
        )
        object.__setattr__(
            self,
            "rationale",
            _required(self.rationale, "rationale"),
        )
        object.__setattr__(
            self,
            "unresolved_assumptions",
            _strings(self.unresolved_assumptions, "unresolved assumption"),
        )
        object.__setattr__(
            self,
            "evidence_requests",
            _strings(self.evidence_requests, "evidence request"),
        )
        object.__setattr__(self, "labels", _labels(dict(self.labels)))

    def label_map(self) -> dict[str, str]:
        return dict(self.labels)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "reasoning_id": self.reasoning_id,
            "situation_id": self.situation_id,
            "status": self.status.value,
            "disposition": self.disposition.value,
            "rankings": [
                ranking.to_canonical_dict() for ranking in self.rankings
            ],
            "selected_hypothesis_id": self.selected_hypothesis_id,
            "confidence": self.confidence,
            "margin": self.margin,
            "rationale": self.rationale,
            "unresolved_assumptions": list(self.unresolved_assumptions),
            "evidence_requests": list(self.evidence_requests),
            "labels": self.label_map(),
        }

    def fingerprint(self) -> str:
        return hashlib.sha256(
            _canonical_json(self.to_canonical_dict()).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class ReasoningPolicy:
    """Deterministic thresholds governing executive judgment."""

    minimum_selection_score: float = 0.35
    minimum_confidence: float = 0.35
    minimum_coverage: float = 0.50
    minimum_margin: float = 0.10
    contested_contradiction_threshold: float = 0.35

    def __post_init__(self) -> None:
        score = float(self.minimum_selection_score)
        if not math.isfinite(score) or not -1.0 <= score <= 1.0:
            raise InvalidReasoningResultError(
                "minimum_selection_score must be between -1.0 and 1.0"
            )
        object.__setattr__(self, "minimum_selection_score", score)

        for field_name in (
            "minimum_confidence",
            "minimum_coverage",
            "minimum_margin",
            "contested_contradiction_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True, slots=True)
class ReasoningQuery:
    """Repository query for executive reasoning results."""

    situation_id: str | None = None
    disposition: ReasoningDisposition | None = None
    minimum_confidence: float | None = None
    limit: int | None = None
    strongest_first: bool = False

    def __post_init__(self) -> None:
        if self.minimum_confidence is not None:
            object.__setattr__(
                self,
                "minimum_confidence",
                _probability(
                    self.minimum_confidence,
                    "minimum_confidence",
                ),
            )
        if self.limit is not None and self.limit < 1:
            raise InvalidReasoningResultError("limit must be at least 1")


def derive_reasoning_identity(
    *,
    situation: SituationSnapshot,
    hypotheses: Sequence[Hypothesis],
    assessments: Sequence[HypothesisAssessment],
    policy: ReasoningPolicy,
) -> str:
    payload = {
        "situation_id": situation.situation_id,
        "hypothesis_ids": sorted(
            hypothesis.hypothesis_id for hypothesis in hypotheses
        ),
        "assessment_ids": sorted(
            assessment.assessment_id for assessment in assessments
        ),
        "policy": {
            "minimum_selection_score": policy.minimum_selection_score,
            "minimum_confidence": policy.minimum_confidence,
            "minimum_coverage": policy.minimum_coverage,
            "minimum_margin": policy.minimum_margin,
            "contested_contradiction_threshold": (
                policy.contested_contradiction_threshold
            ),
        },
    }
    return "rsn_" + hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()
