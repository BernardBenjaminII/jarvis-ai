"""Genesis VI-A6.5 deterministic Executive recovery."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from typing import Callable, Iterable, Protocol, Sequence

from .integrity import ExecutiveIntegrityEngine


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: object) -> str:
    return sha256(_json(value).encode()).hexdigest()


def _value(value: object) -> object:
    return getattr(value, "value", value)


class RecoveryError(RuntimeError):
    pass


class RecoveryRefusedError(RecoveryError):
    pass


class RecoveryPointNotFoundError(RecoveryError):
    pass


class RecoveryReconstructionError(RecoveryError):
    pass


class RecoveryPolicyKind(str, Enum):
    LATEST_CERTIFIED = "latest_certified"
    LATEST_RECOVERABLE = "latest_recoverable"
    EXACT_SEQUENCE = "exact_sequence"
    EXACT_CHECKPOINT_ID = "exact_checkpoint_id"
    EXACT_FINGERPRINT = "exact_fingerprint"


class RecoveryStatus(str, Enum):
    RECOVERED = "recovered"
    REFUSED = "refused"
    NOT_FOUND = "not_found"
    RECONSTRUCTION_FAILED = "reconstruction_failed"


@dataclass(frozen=True, slots=True)
class RecoveryPolicy:
    kind: RecoveryPolicyKind = RecoveryPolicyKind.LATEST_CERTIFIED
    sequence: int | None = None
    checkpoint_id: str | None = None
    fingerprint: str | None = None

    def __post_init__(self) -> None:
        required = {
            RecoveryPolicyKind.EXACT_SEQUENCE: self.sequence,
            RecoveryPolicyKind.EXACT_CHECKPOINT_ID: self.checkpoint_id,
            RecoveryPolicyKind.EXACT_FINGERPRINT: self.fingerprint,
        }
        if self.kind in required and required[self.kind] in (None, ""):
            raise ValueError(f"{self.kind.value} requires its selector value.")
        if self.sequence is not None and self.kind is not RecoveryPolicyKind.EXACT_SEQUENCE:
            raise ValueError("sequence is valid only with exact_sequence.")
        if self.checkpoint_id is not None and self.kind is not RecoveryPolicyKind.EXACT_CHECKPOINT_ID:
            raise ValueError("checkpoint_id is valid only with exact_checkpoint_id.")
        if self.fingerprint is not None and self.kind is not RecoveryPolicyKind.EXACT_FINGERPRINT:
            raise ValueError("fingerprint is valid only with exact_fingerprint.")

    @classmethod
    def latest_certified(cls) -> "RecoveryPolicy": return cls()
    @classmethod
    def latest_recoverable(cls) -> "RecoveryPolicy": return cls(RecoveryPolicyKind.LATEST_RECOVERABLE)
    @classmethod
    def exact_sequence(cls, value: int) -> "RecoveryPolicy": return cls(RecoveryPolicyKind.EXACT_SEQUENCE, sequence=value)
    @classmethod
    def exact_checkpoint_id(cls, value: str) -> "RecoveryPolicy": return cls(RecoveryPolicyKind.EXACT_CHECKPOINT_ID, checkpoint_id=value)
    @classmethod
    def exact_fingerprint(cls, value: str) -> "RecoveryPolicy": return cls(RecoveryPolicyKind.EXACT_FINGERPRINT, fingerprint=value)

    def canonical_dict(self) -> dict[str, object]:
        return {"kind": self.kind.value, "sequence": self.sequence, "checkpoint_id": self.checkpoint_id, "fingerprint": self.fingerprint}


@dataclass(frozen=True, slots=True)
class RecoveryAuthorization:
    certified: bool
    disposition: str
    report_fingerprint: str
    checkpoints_examined: int
    findings_count: int

    @classmethod
    def from_report(cls, report: object) -> "RecoveryAuthorization":
        return cls(bool(getattr(report, "certified", False)), str(_value(getattr(report, "disposition", ""))), str(getattr(report, "report_fingerprint", "")), int(getattr(report, "checkpoints_examined", 0)), len(tuple(getattr(report, "findings", ()))))

    def canonical_dict(self) -> dict[str, object]:
        return {"certified": self.certified, "disposition": self.disposition, "report_fingerprint": self.report_fingerprint, "checkpoints_examined": self.checkpoints_examined, "findings_count": self.findings_count}


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    session_id: str
    status: RecoveryStatus
    policy: RecoveryPolicy
    checkpoint_id: str | None
    sequence: int | None
    checkpoint_fingerprint: str | None
    authorization: RecoveryAuthorization
    used_prefix_fallback: bool
    detail: str
    state_fingerprint: str | None
    occurred_at: datetime
    report_fingerprint: str

    @classmethod
    def create(cls, **values: object) -> "RecoveryReport":
        occurred_at = values.pop("occurred_at", None) or datetime.now(timezone.utc)
        material = dict(values)
        material["status"] = _value(material["status"])
        material["policy"] = material["policy"].canonical_dict()
        material["authorization"] = material["authorization"].canonical_dict()
        material["occurred_at"] = occurred_at.isoformat()
        return cls(**values, occurred_at=occurred_at, report_fingerprint=_hash(material))

    def canonical_dict(self) -> dict[str, object]:
        return {"session_id": self.session_id, "status": self.status.value, "policy": self.policy.canonical_dict(), "checkpoint_id": self.checkpoint_id, "sequence": self.sequence, "checkpoint_fingerprint": self.checkpoint_fingerprint, "authorization": self.authorization.canonical_dict(), "used_prefix_fallback": self.used_prefix_fallback, "detail": self.detail, "state_fingerprint": self.state_fingerprint, "occurred_at": self.occurred_at.isoformat()}

    def verify_fingerprint(self) -> bool:
        return _hash(self.canonical_dict()) == self.report_fingerprint


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    state: object
    report: RecoveryReport


class CheckpointRepository(Protocol):
    def history(self, session_id: str) -> Iterable[object]: ...


class _PrefixRepository:
    def __init__(self, checkpoints: Sequence[object]) -> None: self._items = tuple(checkpoints)
    def history(self, session_id: str) -> tuple[object, ...]: return tuple(x for x in self._items if str(getattr(x, "session_id", "")) == session_id)


def _seq(cp: object) -> int: return int(getattr(cp, "sequence"))
def _id(cp: object) -> str: return str(getattr(cp, "checkpoint_id"))
def _fp(cp: object) -> str:
    for name in ("checkpoint_digest", "fingerprint", "digest"):
        if getattr(cp, name, None): return str(getattr(cp, name))
    canonical = getattr(cp, "canonical_dict", None)
    return _hash(canonical() if callable(canonical) else vars(cp))
def _payload(cp: object) -> object:
    if hasattr(cp, "payload"): return getattr(cp, "payload")
    raise RecoveryReconstructionError("Checkpoint exposes no payload.")


class ExecutiveRecoveryEngine:
    """Restores only integrity-certified checkpoint chains."""
    def __init__(self, repository: CheckpointRepository, *, integrity_engine: ExecutiveIntegrityEngine | None = None, integrity_policy: object | None = None, restorer: Callable[[object], object] | None = None) -> None:
        self.repository = repository
        self.integrity_policy = integrity_policy
        self.integrity_engine = integrity_engine or self._engine(repository)
        self.restorer = restorer or (lambda payload: payload)

    def _engine(self, repository: CheckpointRepository) -> ExecutiveIntegrityEngine:
        return ExecutiveIntegrityEngine(repository) if self.integrity_policy is None else ExecutiveIntegrityEngine(repository, policy=self.integrity_policy)

    def recover(self, session_id: str, *, policy: RecoveryPolicy | None = None) -> RecoveryResult:
        policy = policy or RecoveryPolicy.latest_certified()
        checkpoints = tuple(sorted(self.repository.history(session_id), key=_seq))
        if not checkpoints: raise RecoveryPointNotFoundError(f"No checkpoints for {session_id}.")
        checkpoint, integrity_report, fallback = self._select(session_id, checkpoints, policy)
        auth = RecoveryAuthorization.from_report(integrity_report)
        if checkpoint is None or not auth.certified:
            report = RecoveryReport.create(session_id=session_id, status=RecoveryStatus.REFUSED, policy=policy, checkpoint_id=None, sequence=None, checkpoint_fingerprint=None, authorization=auth, used_prefix_fallback=fallback, detail="Recovery refused: no certified recovery point satisfied policy.", state_fingerprint=None)
            raise RecoveryRefusedError(f"{report.detail} Report: {report.report_fingerprint}")
        try:
            state = self.restorer(_payload(checkpoint))
        except Exception as exc:
            raise RecoveryReconstructionError(type(exc).__name__) from exc
        report = RecoveryReport.create(session_id=session_id, status=RecoveryStatus.RECOVERED, policy=policy, checkpoint_id=_id(checkpoint), sequence=_seq(checkpoint), checkpoint_fingerprint=_fp(checkpoint), authorization=auth, used_prefix_fallback=fallback, detail="Executive state recovered from a certified checkpoint.", state_fingerprint=_hash(state))
        return RecoveryResult(state, report)

    def _select(self, session_id: str, checkpoints: Sequence[object], policy: RecoveryPolicy) -> tuple[object | None, object, bool]:
        if policy.kind is RecoveryPolicyKind.LATEST_CERTIFIED:
            report = self.integrity_engine.verify_session(session_id)
            return (checkpoints[-1] if report.certified else None), report, False
        if policy.kind is RecoveryPolicyKind.LATEST_RECOVERABLE:
            for end in range(len(checkpoints), 0, -1):
                report = self._engine(_PrefixRepository(checkpoints[:end])).verify_session(session_id)
                if report.certified: return checkpoints[end - 1], report, end != len(checkpoints)
            return None, self.integrity_engine.verify_session(session_id), False
        selected = next((cp for cp in checkpoints if (policy.kind is RecoveryPolicyKind.EXACT_SEQUENCE and _seq(cp) == policy.sequence) or (policy.kind is RecoveryPolicyKind.EXACT_CHECKPOINT_ID and _id(cp) == policy.checkpoint_id) or (policy.kind is RecoveryPolicyKind.EXACT_FINGERPRINT and _fp(cp) == policy.fingerprint)), None)
        if selected is None: return None, self.integrity_engine.verify_session(session_id), False
        end = checkpoints.index(selected) + 1
        report = self._engine(_PrefixRepository(checkpoints[:end])).verify_session(session_id)
        return (selected if report.certified else None), report, end != len(checkpoints)


__all__ = ["CheckpointRepository", "ExecutiveRecoveryEngine", "RecoveryAuthorization", "RecoveryError", "RecoveryPointNotFoundError", "RecoveryPolicy", "RecoveryPolicyKind", "RecoveryReconstructionError", "RecoveryRefusedError", "RecoveryReport", "RecoveryResult", "RecoveryStatus"]
