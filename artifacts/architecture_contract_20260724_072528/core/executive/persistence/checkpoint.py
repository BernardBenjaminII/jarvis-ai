"""Immutable executive checkpoint records and deterministic wire encoding."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID


CHECKPOINT_FORMAT = "jarvis.executive.checkpoint"
CHECKPOINT_FORMAT_VERSION = 1
ZERO_DIGEST = "0" * 64
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class CheckpointError(RuntimeError):
    """Base error for checkpoint construction and decoding."""


class CheckpointFormatError(CheckpointError):
    """Raised when checkpoint bytes do not satisfy the wire format."""


class CheckpointIntegrityError(CheckpointError):
    """Raised when checkpoint content fails cryptographic verification."""


class CheckpointSequenceError(CheckpointError):
    """Raised when checkpoint sequence or parent linkage is invalid."""


class CheckpointStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


def _validate_identifier(name: str, value: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"{name} must match {_IDENTIFIER_PATTERN.pattern!r}; got {value!r}"
        )
    return value


def _validate_digest(name: str, value: str, *, allow_zero: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    normalized = value.lower()
    if not _DIGEST_PATTERN.fullmatch(normalized):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    if normalized == ZERO_DIGEST and not allow_zero:
        raise ValueError(f"{name} cannot be the zero digest")
    return normalized


def _normalize_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("created_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("created_at must be timezone-aware")
    return value.astimezone(timezone.utc)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _freeze_metadata(metadata: Mapping[str, str]) -> Mapping[str, str]:
    normalized: dict[str, str] = {}
    for key, value in metadata.items():
        if not isinstance(key, str) or not key:
            raise ValueError("metadata keys must be non-empty strings")
        if not isinstance(value, str):
            raise TypeError("metadata values must be strings")
        normalized[key] = value
    return MappingProxyType(dict(sorted(normalized.items())))


@dataclass(frozen=True, slots=True)
class ExecutiveCheckpoint:
    """A fully materialized, immutable executive checkpoint."""

    checkpoint_id: str
    session_id: str
    sequence: int
    created_at: datetime
    schema_name: str
    schema_version: int
    payload_sha256: str
    checkpoint_sha256: str
    parent_checkpoint_sha256: str
    payload: bytes = field(repr=False)
    mission_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    status: CheckpointStatus = CheckpointStatus.ACTIVE

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "checkpoint_id", _validate_identifier("checkpoint_id", self.checkpoint_id)
        )
        object.__setattr__(
            self, "session_id", _validate_identifier("session_id", self.session_id)
        )
        if self.mission_id is not None:
            object.__setattr__(
                self, "mission_id", _validate_identifier("mission_id", self.mission_id)
            )
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool):
            raise TypeError("sequence must be an integer")
        if self.sequence < 1:
            raise ValueError("sequence must be at least 1")
        object.__setattr__(self, "created_at", _normalize_timestamp(self.created_at))
        if not isinstance(self.schema_name, str) or not self.schema_name:
            raise ValueError("schema_name must be a non-empty string")
        if not isinstance(self.schema_version, int) or self.schema_version < 1:
            raise ValueError("schema_version must be a positive integer")
        if not isinstance(self.payload, bytes):
            raise TypeError("payload must be bytes")
        object.__setattr__(
            self,
            "payload_sha256",
            _validate_digest("payload_sha256", self.payload_sha256),
        )
        object.__setattr__(
            self,
            "checkpoint_sha256",
            _validate_digest("checkpoint_sha256", self.checkpoint_sha256),
        )
        object.__setattr__(
            self,
            "parent_checkpoint_sha256",
            _validate_digest(
                "parent_checkpoint_sha256",
                self.parent_checkpoint_sha256,
                allow_zero=True,
            ),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))
        if not isinstance(self.status, CheckpointStatus):
            object.__setattr__(self, "status", CheckpointStatus(self.status))

    @property
    def payload_size(self) -> int:
        return len(self.payload)

    def verify(self) -> None:
        payload_digest = hashlib.sha256(self.payload).hexdigest()
        if payload_digest != self.payload_sha256:
            raise CheckpointIntegrityError(
                f"payload digest mismatch for {self.checkpoint_id}"
            )
        expected = compute_checkpoint_sha256(
            checkpoint_id=self.checkpoint_id,
            session_id=self.session_id,
            mission_id=self.mission_id,
            sequence=self.sequence,
            created_at=self.created_at,
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            payload_sha256=self.payload_sha256,
            parent_checkpoint_sha256=self.parent_checkpoint_sha256,
            metadata=self.metadata,
            status=self.status,
        )
        if expected != self.checkpoint_sha256:
            raise CheckpointIntegrityError(
                f"checkpoint digest mismatch for {self.checkpoint_id}"
            )


@dataclass(frozen=True, slots=True)
class CheckpointSummary:
    checkpoint_id: str
    session_id: str
    sequence: int
    created_at: datetime
    checkpoint_sha256: str
    parent_checkpoint_sha256: str
    payload_sha256: str
    payload_size: int
    mission_id: str | None = None
    status: CheckpointStatus = CheckpointStatus.ACTIVE

    @classmethod
    def from_checkpoint(cls, checkpoint: ExecutiveCheckpoint) -> "CheckpointSummary":
        return cls(
            checkpoint_id=checkpoint.checkpoint_id,
            session_id=checkpoint.session_id,
            mission_id=checkpoint.mission_id,
            sequence=checkpoint.sequence,
            created_at=checkpoint.created_at,
            checkpoint_sha256=checkpoint.checkpoint_sha256,
            parent_checkpoint_sha256=checkpoint.parent_checkpoint_sha256,
            payload_sha256=checkpoint.payload_sha256,
            payload_size=checkpoint.payload_size,
            status=checkpoint.status,
        )


def compute_checkpoint_sha256(
    *,
    checkpoint_id: str,
    session_id: str,
    mission_id: str | None,
    sequence: int,
    created_at: datetime,
    schema_name: str,
    schema_version: int,
    payload_sha256: str,
    parent_checkpoint_sha256: str,
    metadata: Mapping[str, str],
    status: CheckpointStatus,
) -> str:
    manifest = {
        "checkpoint_id": checkpoint_id,
        "created_at": _normalize_timestamp(created_at).isoformat(
            timespec="microseconds"
        ).replace("+00:00", "Z"),
        "format": CHECKPOINT_FORMAT,
        "format_version": CHECKPOINT_FORMAT_VERSION,
        "metadata": dict(sorted(metadata.items())),
        "mission_id": mission_id,
        "parent_checkpoint_sha256": parent_checkpoint_sha256,
        "payload_sha256": payload_sha256,
        "schema_name": schema_name,
        "schema_version": schema_version,
        "sequence": sequence,
        "session_id": session_id,
        "status": status.value,
    }
    return hashlib.sha256(_canonical_json_bytes(manifest)).hexdigest()


def create_checkpoint(
    *,
    session_id: str,
    sequence: int,
    payload: bytes,
    schema_name: str,
    schema_version: int,
    parent_checkpoint_sha256: str = ZERO_DIGEST,
    mission_id: str | None = None,
    metadata: Mapping[str, str] | None = None,
    created_at: datetime | None = None,
    status: CheckpointStatus = CheckpointStatus.ACTIVE,
) -> ExecutiveCheckpoint:
    created = _normalize_timestamp(created_at or datetime.now(timezone.utc))
    checkpoint_id = f"{session_id}:{sequence:08d}"
    frozen_metadata = _freeze_metadata(metadata or {})
    payload_digest = hashlib.sha256(payload).hexdigest()
    checkpoint_digest = compute_checkpoint_sha256(
        checkpoint_id=checkpoint_id,
        session_id=session_id,
        mission_id=mission_id,
        sequence=sequence,
        created_at=created,
        schema_name=schema_name,
        schema_version=schema_version,
        payload_sha256=payload_digest,
        parent_checkpoint_sha256=parent_checkpoint_sha256,
        metadata=frozen_metadata,
        status=status,
    )
    checkpoint = ExecutiveCheckpoint(
        checkpoint_id=checkpoint_id,
        session_id=session_id,
        mission_id=mission_id,
        sequence=sequence,
        created_at=created,
        schema_name=schema_name,
        schema_version=schema_version,
        payload_sha256=payload_digest,
        checkpoint_sha256=checkpoint_digest,
        parent_checkpoint_sha256=parent_checkpoint_sha256,
        payload=payload,
        metadata=frozen_metadata,
        status=status,
    )
    checkpoint.verify()
    return checkpoint


def encode_checkpoint(checkpoint: ExecutiveCheckpoint) -> bytes:
    checkpoint.verify()
    document = {
        "checkpoint_id": checkpoint.checkpoint_id,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "created_at": checkpoint.created_at.isoformat(
            timespec="microseconds"
        ).replace("+00:00", "Z"),
        "format": CHECKPOINT_FORMAT,
        "format_version": CHECKPOINT_FORMAT_VERSION,
        "metadata": dict(checkpoint.metadata),
        "mission_id": checkpoint.mission_id,
        "parent_checkpoint_sha256": checkpoint.parent_checkpoint_sha256,
        "payload_hex": checkpoint.payload.hex(),
        "payload_sha256": checkpoint.payload_sha256,
        "schema_name": checkpoint.schema_name,
        "schema_version": checkpoint.schema_version,
        "sequence": checkpoint.sequence,
        "session_id": checkpoint.session_id,
        "status": checkpoint.status.value,
    }
    return _canonical_json_bytes(document) + b"\n"


def decode_checkpoint(data: bytes) -> ExecutiveCheckpoint:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckpointFormatError("checkpoint is not valid UTF-8 JSON") from exc

    if not isinstance(document, dict):
        raise CheckpointFormatError("checkpoint document must be an object")
    if document.get("format") != CHECKPOINT_FORMAT:
        raise CheckpointFormatError("unsupported checkpoint format")
    if document.get("format_version") != CHECKPOINT_FORMAT_VERSION:
        raise CheckpointFormatError("unsupported checkpoint format version")

    try:
        created_at_text = document["created_at"]
        if not isinstance(created_at_text, str):
            raise TypeError("created_at must be text")
        created_at = datetime.fromisoformat(created_at_text.replace("Z", "+00:00"))
        payload = bytes.fromhex(document["payload_hex"])
        checkpoint = ExecutiveCheckpoint(
            checkpoint_id=document["checkpoint_id"],
            session_id=document["session_id"],
            mission_id=document.get("mission_id"),
            sequence=document["sequence"],
            created_at=created_at,
            schema_name=document["schema_name"],
            schema_version=document["schema_version"],
            payload_sha256=document["payload_sha256"],
            checkpoint_sha256=document["checkpoint_sha256"],
            parent_checkpoint_sha256=document["parent_checkpoint_sha256"],
            payload=payload,
            metadata=document.get("metadata", {}),
            status=CheckpointStatus(document.get("status", "active")),
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise CheckpointFormatError("checkpoint fields are invalid") from exc

    checkpoint.verify()
    return checkpoint
