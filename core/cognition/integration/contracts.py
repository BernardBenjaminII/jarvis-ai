"""Immutable contracts for cognitive workspace integration."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


def _text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _confidence(value: float) -> float:
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")
    return normalized


def stable_identifier(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(part.strip() for part in parts).encode("utf-8")
    return f"{prefix}_{sha256(payload).hexdigest()[:24]}"


@dataclass(frozen=True, slots=True)
class HypothesisSeed:
    statement: str
    confidence: float = 0.0
    rationale: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "statement", _text(self.statement, "statement"))
        object.__setattr__(self, "confidence", _confidence(self.confidence))
        object.__setattr__(self, "rationale", self.rationale.strip())


@dataclass(frozen=True, slots=True)
class EvidenceSeed:
    hypothesis_statement: str
    summary: str
    source_uri: str | None = None
    credibility: float = 0.5
    evidence_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "hypothesis_statement", _text(self.hypothesis_statement, "hypothesis_statement"))
        object.__setattr__(self, "summary", _text(self.summary, "summary"))
        object.__setattr__(self, "credibility", _confidence(self.credibility))
        if self.source_uri is not None:
            object.__setattr__(self, "source_uri", self.source_uri.strip() or None)
        if self.evidence_id is not None:
            object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))


@dataclass(frozen=True, slots=True)
class AssumptionSeed:
    statement: str
    confidence: float = 0.5

    def __post_init__(self) -> None:
        object.__setattr__(self, "statement", _text(self.statement, "statement"))
        object.__setattr__(self, "confidence", _confidence(self.confidence))


@dataclass(frozen=True, slots=True)
class QuestionSeed:
    prompt: str
    priority: int = 50

    def __post_init__(self) -> None:
        object.__setattr__(self, "prompt", _text(self.prompt, "prompt"))
        if not 0 <= self.priority <= 100:
            raise ValueError("priority must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class WorkspaceIntegrationRequest:
    objective: str
    hypotheses: tuple[HypothesisSeed, ...] = ()
    evidence: tuple[EvidenceSeed, ...] = ()
    assumptions: tuple[AssumptionSeed, ...] = ()
    questions: tuple[QuestionSeed, ...] = ()
    workspace_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "objective", _text(self.objective, "objective"))
        if self.workspace_id is not None:
            object.__setattr__(self, "workspace_id", _text(self.workspace_id, "workspace_id"))
        statements = tuple(item.statement for item in self.hypotheses)
        if len(statements) != len(set(statements)):
            raise ValueError("duplicate hypothesis statements are forbidden")
        known = set(statements)
        missing = sorted({item.hypothesis_statement for item in self.evidence} - known)
        if missing:
            raise ValueError("evidence references unknown hypotheses: " + ", ".join(missing))
