"""Deterministic snapshot serialization for Genesis VI-A6.2."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .canonical import to_canonical_value
from .contracts import (
    DIGEST_ALGORITHM,
    IntegrityMetadata,
    PersistenceIntegrityStatus,
    SchemaIdentity,
)


CANONICAL_ENCODING = "utf-8"
CANONICAL_MEDIA_TYPE = "application/vnd.jarvis.persistence+json"


class SerializationError(ValueError):
    """Raised when canonical serialization or decoding fails."""


@dataclass(frozen=True, slots=True)
class SerializedSnapshot:
    """Canonical bytes and integrity metadata for one snapshot."""

    schema: SchemaIdentity
    payload: bytes
    integrity: IntegrityMetadata
    media_type: str = CANONICAL_MEDIA_TYPE
    encoding: str = CANONICAL_ENCODING

    @property
    def size(self) -> int:
        return len(self.payload)

    @property
    def text(self) -> str:
        return self.payload.decode(self.encoding)


class CanonicalSnapshotSerializer:
    """Serialize executive state into one authoritative byte sequence."""

    def dumps(
        self,
        value: Any,
        *,
        schema: SchemaIdentity | None = None,
    ) -> SerializedSnapshot:
        active_schema = schema or SchemaIdentity()
        document = {
            "payload": to_canonical_value(value),
            "schema": {
                "name": active_schema.name,
                "version": active_schema.version,
            },
        }

        try:
            text = json.dumps(
                document,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        except (TypeError, ValueError) as exc:
            raise SerializationError(str(exc)) from exc

        payload = text.encode(CANONICAL_ENCODING)
        digest = hashlib.sha256(payload).hexdigest()

        return SerializedSnapshot(
            schema=active_schema,
            payload=payload,
            integrity=IntegrityMetadata(
                algorithm=DIGEST_ALGORITHM,
                digest=digest,
                status=PersistenceIntegrityStatus.VERIFIED,
            ),
        )

    def loads(self, payload: bytes | str) -> dict[str, Any]:
        """Decode canonical bytes into validated plain JSON data."""

        if isinstance(payload, bytes):
            try:
                text = payload.decode(CANONICAL_ENCODING)
            except UnicodeDecodeError as exc:
                raise SerializationError(
                    "payload is not valid UTF-8"
                ) from exc
        elif isinstance(payload, str):
            text = payload
        else:
            raise SerializationError(
                "payload must be bytes or string"
            )

        try:
            document = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SerializationError(
                "payload is not valid canonical JSON"
            ) from exc

        if not isinstance(document, dict):
            raise SerializationError(
                "canonical document must be an object"
            )
        if tuple(sorted(document)) != ("payload", "schema"):
            raise SerializationError(
                "canonical document must contain payload and schema"
            )

        schema = document["schema"]
        if not isinstance(schema, dict):
            raise SerializationError("schema must be an object")
        if set(schema) != {"name", "version"}:
            raise SerializationError(
                "schema must contain name and version"
            )

        SchemaIdentity(
            name=schema["name"],
            version=schema["version"],
        )
        return document

    def verify(self, snapshot: SerializedSnapshot) -> bool:
        """Verify the SHA-256 digest of a serialized snapshot."""

        actual = hashlib.sha256(snapshot.payload).hexdigest()
        return actual == snapshot.integrity.digest


__all__ = [
    "CANONICAL_ENCODING",
    "CANONICAL_MEDIA_TYPE",
    "CanonicalSnapshotSerializer",
    "SerializedSnapshot",
    "SerializationError",
]
