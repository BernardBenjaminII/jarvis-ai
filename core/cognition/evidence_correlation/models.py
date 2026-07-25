"""Canonical models for Genesis IV-A4 Executive Evidence Correlation Engine."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from core.cognition.hypothesis import Hypothesis
from core.cognition.situation import SituationSnapshot

from .enums import (
    AssessmentStatus,
    EvidencePolarity,
    EvidenceStrength,
)
from .errors import (
    HypothesisCompatibilityError,
    InvalidAssessmentError,
    InvalidEvidenceLinkError,
    SituationCompatibilityError,
)


_STRENGTH_SCORE = {
    EvidenceStrength.TRACE: 0.10,
    EvidenceStrength.WEAK: 0.25,
    EvidenceStrength.MODERATE: 0.50,
    EvidenceStrength.STRONG: 0.75,
    EvidenceStrength.DECISIVE: 1.00,
}


def _required(value: str, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise InvalidAssessmentError(f"{field_name} must not be empty")
    return normalized


def _probability(value: float, field_name: str) -> float:
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise InvalidAssessmentError(
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


def _labels(
    values: Mapping[str, str] | None,
) -> tuple[tuple[str, str], ...]:
    if not values:
        return ()

    normalized: list[tuple[str, str]] = []
    for key, value in values.items():
        clean_key = _required(key, "label key")
        clean_value = _required(value, "label value")
        normalized.append((clean_key, clean_value))
    return tuple(sorted(normalized))


def _questions(values: Sequence[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(sorted({_required(item, "missing evidence question") for item in values}))


def _require_hypothesis(value: Hypothesis) -> Hypothesis:
    if not isinstance(value, Hypothesis):
        raise HypothesisCompatibilityError(
            "assessment inputs must be Genesis IV-A3 Hypothesis objects"
        )
    return value


def _require_situation(value: SituationSnapshot) -> SituationSnapshot:
    if not isinstance(value, SituationSnapshot):
        raise SituationCompatibilityError(
            "assessment inputs must include a Genesis IV-A2 SituationSnapshot"
        )
    return value


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    """Explicit relation between an observation and a hypothesis."""

    observation_id: str
    hypothesis_id: str
    polarity: EvidencePolarity
    strength: EvidenceStrength
    reliability: float
    admissible: bool = True
    rationale: str | None = None

    def __post_init__(self) -> None:
        try:
            observation_id = str(self.observation_id).strip()
            hypothesis_id = str(self.hypothesis_id).strip()
            if not observation_id or not hypothesis_id:
                raise InvalidEvidenceLinkError(
                    "observation_id and hypothesis_id must not be empty"
                )
            object.__setattr__(self, "observation_id", observation_id)
            object.__setattr__(self, "hypothesis_id", hypothesis_id)

            if not isinstance(self.polarity, EvidencePolarity):
                object.__setattr__(
                    self,
                    "polarity",
                    EvidencePolarity(str(self.polarity)),
                )
            if not isinstance(self.strength, EvidenceStrength):
                object.__setattr__(
                    self,
                    "strength",
                    EvidenceStrength(str(self.strength)),
                )

            reliability = float(self.reliability)
            if not math.isfinite(reliability) or not 0.0 <= reliability <= 1.0:
                raise InvalidEvidenceLinkError(
                    "reliability must be finite and between 0.0 and 1.0"
                )
            object.__setattr__(self, "reliability", reliability)

            if self.rationale is not None:
                rationale = str(self.rationale).strip()
                object.__setattr__(self, "rationale", rationale or None)
        except InvalidEvidenceLinkError:
            raise
        except Exception as exc:
            raise InvalidEvidenceLinkError(str(exc)) from exc

    @property
    def weighted_score(self) -> float:
        """Return normalized signed contribution to hypothesis support."""

        if not self.admissible or self.polarity is EvidencePolarity.NEUTRAL:
            return 0.0

        sign = 1.0 if self.polarity is EvidencePolarity.SUPPORTS else -1.0
        return sign * _STRENGTH_SCORE[self.strength] * self.reliability

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return deterministic evidence-link data."""

        return {
            "observation_id": self.observation_id,
            "hypothesis_id": self.hypothesis_id,
            "polarity": self.polarity.value,
            "strength": self.strength.value,
            "reliability": self.reliability,
            "admissible": self.admissible,
            "rationale": self.rationale,
            "weighted_score": self.weighted_score,
        }


@dataclass(frozen=True, slots=True)
class HypothesisAssessment:
    """Immutable evidence assessment for one hypothesis."""

    assessment_id: str
    situation_id: str
    hypothesis_id: str
    status: AssessmentStatus
    links: tuple[EvidenceLink, ...]
    support_score: float
    contradiction_score: float
    net_score: float
    coverage: float
    confidence: float
    missing_evidence_questions: tuple[str, ...] = ()
    rationale: str | None = None
    labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assessment_id",
            _required(self.assessment_id, "assessment_id"),
        )
        object.__setattr__(
            self,
            "situation_id",
            _required(self.situation_id, "situation_id"),
        )
        object.__setattr__(
            self,
            "hypothesis_id",
            _required(self.hypothesis_id, "hypothesis_id"),
        )

        if not isinstance(self.status, AssessmentStatus):
            object.__setattr__(
                self,
                "status",
                AssessmentStatus(str(self.status)),
            )

        links = tuple(
            sorted(
                self.links,
                key=lambda item: (
                    item.observation_id,
                    item.polarity.value,
                    item.strength.value,
                ),
            )
        )
        if not links:
            raise InvalidAssessmentError(
                "an assessment must contain at least one evidence link"
            )
        if any(link.hypothesis_id != self.hypothesis_id for link in links):
            raise InvalidAssessmentError(
                "all evidence links must target the assessed hypothesis"
            )
        object.__setattr__(self, "links", links)

        object.__setattr__(
            self,
            "support_score",
            _probability(self.support_score, "support_score"),
        )
        object.__setattr__(
            self,
            "contradiction_score",
            _probability(self.contradiction_score, "contradiction_score"),
        )

        net_score = float(self.net_score)
        if not math.isfinite(net_score) or not -1.0 <= net_score <= 1.0:
            raise InvalidAssessmentError(
                "net_score must be finite and between -1.0 and 1.0"
            )
        object.__setattr__(self, "net_score", net_score)

        object.__setattr__(
            self,
            "coverage",
            _probability(self.coverage, "coverage"),
        )
        object.__setattr__(
            self,
            "confidence",
            _probability(self.confidence, "confidence"),
        )
        object.__setattr__(
            self,
            "missing_evidence_questions",
            _questions(self.missing_evidence_questions),
        )
        object.__setattr__(self, "labels", _labels(dict(self.labels)))

        if self.rationale is not None:
            rationale = str(self.rationale).strip()
            object.__setattr__(self, "rationale", rationale or None)

    def label_map(self) -> dict[str, str]:
        """Return labels as a new dictionary."""

        return dict(self.labels)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return deterministic assessment data."""

        return {
            "assessment_id": self.assessment_id,
            "situation_id": self.situation_id,
            "hypothesis_id": self.hypothesis_id,
            "status": self.status.value,
            "links": [link.to_canonical_dict() for link in self.links],
            "support_score": self.support_score,
            "contradiction_score": self.contradiction_score,
            "net_score": self.net_score,
            "coverage": self.coverage,
            "confidence": self.confidence,
            "missing_evidence_questions": list(
                self.missing_evidence_questions
            ),
            "rationale": self.rationale,
            "labels": self.label_map(),
        }

    def fingerprint(self) -> str:
        """Return a complete deterministic assessment fingerprint."""

        return hashlib.sha256(
            _canonical_json(self.to_canonical_dict()).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class AssessmentQuery:
    """Repository query for hypothesis assessments."""

    situation_id: str | None = None
    hypothesis_id: str | None = None
    status: AssessmentStatus | None = None
    minimum_confidence: float | None = None
    minimum_coverage: float | None = None
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
        if self.minimum_coverage is not None:
            object.__setattr__(
                self,
                "minimum_coverage",
                _probability(
                    self.minimum_coverage,
                    "minimum_coverage",
                ),
            )
        if self.limit is not None and self.limit < 1:
            raise InvalidAssessmentError("limit must be at least 1")


def derive_assessment_identity(
    *,
    situation: SituationSnapshot,
    hypothesis: Hypothesis,
    links: Sequence[EvidenceLink],
) -> str:
    """Derive a stable semantic identity for an assessment."""

    _require_situation(situation)
    _require_hypothesis(hypothesis)

    payload = {
        "situation_id": situation.situation_id,
        "hypothesis_id": hypothesis.hypothesis_id,
        "links": [
            link.to_canonical_dict()
            for link in sorted(
                links,
                key=lambda item: (
                    item.observation_id,
                    item.polarity.value,
                    item.strength.value,
                ),
            )
        ],
    }
    return "asm_" + hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()
