"""Schema-versioned envelope for all constitutional Government payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .canonical import canonical_fingerprint, canonical_json
from .errors import (
    GovernmentFingerprintError,
    GovernmentPayloadError,
    UnsupportedGovernmentSchemaError,
)


GOVERNMENT_SCHEMA_VERSION = "1.0.0"
SUPPORTED_GOVERNMENT_SCHEMA_VERSIONS = frozenset({GOVERNMENT_SCHEMA_VERSION})
SUPPORTED_PAYLOAD_TYPES = frozenset(
    {
        "constitutional_object",
        "organizational_relationship",
        "organizational_graph",
    }
)


@dataclass(frozen=True, slots=True)
class GovernmentEnvelope:
    """Canonical transport and persistence envelope."""

    payload_type: str
    payload: Mapping[str, Any]
    schema_version: str = GOVERNMENT_SCHEMA_VERSION
    metadata: Mapping[str, str] = field(default_factory=dict)
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version not in SUPPORTED_GOVERNMENT_SCHEMA_VERSIONS:
            raise UnsupportedGovernmentSchemaError(
                f"unsupported Government schema version: {self.schema_version}"
            )
        if self.payload_type not in SUPPORTED_PAYLOAD_TYPES:
            raise GovernmentPayloadError(
                f"unsupported Government payload type: {self.payload_type}"
            )
        if not isinstance(self.payload, Mapping):
            raise GovernmentPayloadError("payload must be a mapping")

        normalized_metadata = dict(
            sorted((str(key), str(value)) for key, value in self.metadata.items())
        )
        normalized_payload = dict(self.payload)

        object.__setattr__(self, "metadata", normalized_metadata)
        object.__setattr__(self, "payload", normalized_payload)
        object.__setattr__(
            self,
            "fingerprint",
            canonical_fingerprint(self._unsigned_dict()),
        )

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "payload_type": self.payload_type,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._unsigned_dict(),
            "fingerprint": self.fingerprint,
        }

    def to_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GovernmentEnvelope":
        required = {
            "schema_version",
            "payload_type",
            "payload",
            "metadata",
            "fingerprint",
        }
        missing = required.difference(payload)
        if missing:
            raise GovernmentPayloadError(
                "Government envelope is missing: " + ", ".join(sorted(missing))
            )

        envelope = cls(
            schema_version=str(payload["schema_version"]),
            payload_type=str(payload["payload_type"]),
            payload=dict(payload["payload"]),
            metadata=dict(payload["metadata"]),
        )
        supplied = str(payload["fingerprint"])
        if supplied != envelope.fingerprint:
            raise GovernmentFingerprintError(
                "Government envelope fingerprint does not match its content"
            )
        return envelope

    @classmethod
    def from_json(cls, serialized: str) -> "GovernmentEnvelope":
        import json

        try:
            payload = json.loads(serialized)
        except json.JSONDecodeError as exc:
            raise GovernmentPayloadError("invalid Government JSON") from exc
        if not isinstance(payload, dict):
            raise GovernmentPayloadError("Government envelope JSON must be an object")
        return cls.from_dict(payload)
