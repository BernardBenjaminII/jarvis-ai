"""Immutable cognitive workspace domain models."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable
from uuid import UUID, uuid4

from core.cognition.workspace.enums import (
    HypothesisStatus,
    WorkspaceEventKind,
    WorkspaceStatus,
)
from core.cognition.workspace.errors import CognitiveWorkspaceError


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def _require_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise CognitiveWorkspaceError(f"{field_name} must not be empty")
    return normalized


def _require_confidence(value: float) -> float:
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise CognitiveWorkspaceError(
            "confidence must be between 0.0 and 1.0"
        )
    return normalized


def _stable_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return f"{prefix}_{sha256(payload).hexdigest()[:24]}"


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """Canonical reference to evidence considered by the workspace."""

    evidence_id: str
    summary: str
    source_uri: str | None = None
    credibility: float = 0.5

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_id",
            _require_text(self.evidence_id, "evidence_id"),
        )
        object.__setattr__(
            self,
            "summary",
            _require_text(self.summary, "summary"),
        )
        object.__setattr__(
            self,
            "credibility",
            _require_confidence(self.credibility),
        )

        if self.source_uri is not None:
            normalized = self.source_uri.strip()
            object.__setattr__(
                self,
                "source_uri",
                normalized or None,
            )


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """One explicit candidate explanation or conclusion."""

    hypothesis_id: str
    statement: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    confidence: float = 0.0
    evidence_ids: tuple[str, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "hypothesis_id",
            _require_text(self.hypothesis_id, "hypothesis_id"),
        )
        object.__setattr__(
            self,
            "statement",
            _require_text(self.statement, "statement"),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_confidence(self.confidence),
        )
        object.__setattr__(
            self,
            "evidence_ids",
            tuple(dict.fromkeys(self.evidence_ids)),
        )
        object.__setattr__(
            self,
            "rationale",
            self.rationale.strip(),
        )

    @classmethod
    def create(
        cls,
        statement: str,
        *,
        confidence: float = 0.0,
        status: HypothesisStatus = HypothesisStatus.PROPOSED,
        rationale: str = "",
    ) -> "Hypothesis":
        normalized = _require_text(statement, "statement")
        return cls(
            hypothesis_id=_stable_id("hyp", normalized),
            statement=normalized,
            confidence=confidence,
            status=status,
            rationale=rationale,
        )

    def attach_evidence(self, evidence_id: str) -> "Hypothesis":
        normalized = _require_text(evidence_id, "evidence_id")
        if normalized in self.evidence_ids:
            return self
        return replace(
            self,
            evidence_ids=(*self.evidence_ids, normalized),
        )

    def transition(
        self,
        status: HypothesisStatus,
        *,
        confidence: float | None = None,
        rationale: str | None = None,
    ) -> "Hypothesis":
        return replace(
            self,
            status=status,
            confidence=(
                self.confidence
                if confidence is None
                else _require_confidence(confidence)
            ),
            rationale=(
                self.rationale
                if rationale is None
                else rationale.strip()
            ),
        )


@dataclass(frozen=True, slots=True)
class Assumption:
    """An explicit assumption accepted provisionally."""

    assumption_id: str
    statement: str
    confidence: float = 0.5
    challenged: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assumption_id",
            _require_text(self.assumption_id, "assumption_id"),
        )
        object.__setattr__(
            self,
            "statement",
            _require_text(self.statement, "statement"),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_confidence(self.confidence),
        )

    @classmethod
    def create(
        cls,
        statement: str,
        *,
        confidence: float = 0.5,
    ) -> "Assumption":
        normalized = _require_text(statement, "statement")
        return cls(
            assumption_id=_stable_id("asm", normalized),
            statement=normalized,
            confidence=confidence,
        )


@dataclass(frozen=True, slots=True)
class OpenQuestion:
    """A question whose answer may materially change the workspace."""

    question_id: str
    prompt: str
    priority: int = 50
    resolved: bool = False
    answer: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "question_id",
            _require_text(self.question_id, "question_id"),
        )
        object.__setattr__(
            self,
            "prompt",
            _require_text(self.prompt, "prompt"),
        )

        if not 0 <= self.priority <= 100:
            raise CognitiveWorkspaceError(
                "priority must be between 0 and 100"
            )

        if self.answer is not None:
            normalized = self.answer.strip()
            object.__setattr__(
                self,
                "answer",
                normalized or None,
            )

        if self.resolved and self.answer is None:
            raise CognitiveWorkspaceError(
                "resolved questions require an answer"
            )

    @classmethod
    def create(
        cls,
        prompt: str,
        *,
        priority: int = 50,
    ) -> "OpenQuestion":
        normalized = _require_text(prompt, "prompt")
        return cls(
            question_id=_stable_id("qst", normalized),
            prompt=normalized,
            priority=priority,
        )

    def resolve(self, answer: str) -> "OpenQuestion":
        normalized = _require_text(answer, "answer")
        return replace(
            self,
            resolved=True,
            answer=normalized,
        )


@dataclass(frozen=True, slots=True)
class WorkspaceEvent:
    """Append-only cognitive event."""

    event_id: str
    kind: WorkspaceEventKind
    occurred_at: datetime
    subject_id: str
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_id",
            _require_text(self.event_id, "event_id"),
        )
        object.__setattr__(
            self,
            "subject_id",
            _require_text(self.subject_id, "subject_id"),
        )
        object.__setattr__(
            self,
            "detail",
            _require_text(self.detail, "detail"),
        )

        if self.occurred_at.tzinfo is None:
            raise CognitiveWorkspaceError(
                "occurred_at must be timezone-aware"
            )

    @classmethod
    def create(
        cls,
        kind: WorkspaceEventKind,
        subject_id: str,
        detail: str,
    ) -> "WorkspaceEvent":
        occurred_at = utc_now()
        normalized_subject = _require_text(subject_id, "subject_id")
        normalized_detail = _require_text(detail, "detail")
        event_seed = (
            kind.value,
            normalized_subject,
            normalized_detail,
            occurred_at.isoformat(),
            uuid4().hex,
        )
        return cls(
            event_id=_stable_id("evt", *event_seed),
            kind=kind,
            occurred_at=occurred_at,
            subject_id=normalized_subject,
            detail=normalized_detail,
        )


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshot:
    """Read-only summary of workspace state."""

    workspace_id: str
    objective: str
    status: WorkspaceStatus
    hypothesis_count: int
    evidence_count: int
    assumption_count: int
    unresolved_question_count: int
    strongest_hypothesis_id: str | None
    strongest_confidence: float | None
    revision: int


@dataclass(frozen=True, slots=True)
class CognitiveWorkspace:
    """Immutable explicit working state for one reasoning objective."""

    workspace_id: str
    objective: str
    status: WorkspaceStatus = WorkspaceStatus.OPEN
    hypotheses: tuple[Hypothesis, ...] = ()
    evidence: tuple[EvidenceReference, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    questions: tuple[OpenQuestion, ...] = ()
    events: tuple[WorkspaceEvent, ...] = ()
    revision: int = 0
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "workspace_id",
            _require_text(self.workspace_id, "workspace_id"),
        )
        object.__setattr__(
            self,
            "objective",
            _require_text(self.objective, "objective"),
        )

        if self.revision < 0:
            raise CognitiveWorkspaceError(
                "revision must not be negative"
            )

        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise CognitiveWorkspaceError(
                "workspace timestamps must be timezone-aware"
            )

        self._require_unique(
            (item.hypothesis_id for item in self.hypotheses),
            "hypothesis",
        )
        self._require_unique(
            (item.evidence_id for item in self.evidence),
            "evidence",
        )
        self._require_unique(
            (item.assumption_id for item in self.assumptions),
            "assumption",
        )
        self._require_unique(
            (item.question_id for item in self.questions),
            "question",
        )
        self._require_unique(
            (item.event_id for item in self.events),
            "event",
        )

    @staticmethod
    def _require_unique(
        values: Iterable[str],
        label: str,
    ) -> None:
        normalized = tuple(values)
        if len(normalized) != len(set(normalized)):
            raise CognitiveWorkspaceError(
                f"duplicate {label} identities are forbidden"
            )

    @classmethod
    def create(
        cls,
        objective: str,
        *,
        workspace_id: str | None = None,
    ) -> "CognitiveWorkspace":
        normalized_objective = _require_text(objective, "objective")
        identifier = (
            workspace_id.strip()
            if workspace_id is not None
            else f"cws_{uuid4().hex}"
        )
        event = WorkspaceEvent.create(
            WorkspaceEventKind.WORKSPACE_CREATED,
            identifier,
            f"Workspace created for objective: {normalized_objective}",
        )
        return cls(
            workspace_id=identifier,
            objective=normalized_objective,
            events=(event,),
        )

    def evolve(self, **changes: object) -> "CognitiveWorkspace":
        """Return the next immutable workspace revision."""

        return replace(
            self,
            revision=self.revision + 1,
            updated_at=utc_now(),
            **changes,
        )

    def snapshot(self) -> WorkspaceSnapshot:
        active_hypotheses = tuple(
            hypothesis
            for hypothesis in self.hypotheses
            if hypothesis.status
            not in {
                HypothesisStatus.REJECTED,
                HypothesisStatus.RESOLVED,
            }
        )
        strongest = (
            max(
                active_hypotheses,
                key=lambda item: (
                    item.confidence,
                    item.hypothesis_id,
                ),
            )
            if active_hypotheses
            else None
        )
        return WorkspaceSnapshot(
            workspace_id=self.workspace_id,
            objective=self.objective,
            status=self.status,
            hypothesis_count=len(self.hypotheses),
            evidence_count=len(self.evidence),
            assumption_count=len(self.assumptions),
            unresolved_question_count=sum(
                not question.resolved
                for question in self.questions
            ),
            strongest_hypothesis_id=(
                strongest.hypothesis_id
                if strongest is not None
                else None
            ),
            strongest_confidence=(
                strongest.confidence
                if strongest is not None
                else None
            ),
            revision=self.revision,
        )
