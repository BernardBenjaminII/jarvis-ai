"""Deterministic canonical serialization and fingerprint helpers."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import Any

from .errors import ArchitectureFingerprintError, ArchitectureSerializationError


def canonicalize(value: Any) -> Any:
    """Convert supported values into deterministic JSON-compatible structures."""

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: canonicalize(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }

    if isinstance(value, Enum):
        return canonicalize(value.value)

    if isinstance(value, Path):
        return value.as_posix()

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value, key=lambda item: str(item)):
            normalized[str(key)] = canonicalize(value[key])
        return normalized

    if isinstance(value, tuple):
        return [canonicalize(item) for item in value]

    if isinstance(value, list):
        return [canonicalize(item) for item in value]

    if isinstance(value, set | frozenset):
        normalized_items = [canonicalize(item) for item in value]
        return sorted(
            normalized_items,
            key=lambda item: json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [canonicalize(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise ArchitectureSerializationError(
        f"Unsupported canonical serialization type: {type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    """Return deterministic compact JSON."""

    try:
        return json.dumps(
            canonicalize(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ArchitectureSerializationError(str(exc)) from exc


def architecture_fingerprint(value: Any, *, algorithm: str = "sha256") -> str:
    """Return a deterministic hexadecimal fingerprint."""

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ArchitectureFingerprintError(
            f"Unsupported fingerprint algorithm: {algorithm}"
        ) from exc

    digest.update(canonical_json(value).encode("utf-8"))
    return digest.hexdigest()


def file_fingerprint(path: str | Path, *, algorithm: str = "sha256") -> str:
    """Fingerprint a file's raw bytes."""

    file_path = Path(path)
    if not file_path.is_file():
        raise ArchitectureFingerprintError(f"File not found: {file_path}")

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ArchitectureFingerprintError(
            f"Unsupported fingerprint algorithm: {algorithm}"
        ) from exc

    with file_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


__all__ = [
    "architecture_fingerprint",
    "canonical_json",
    "canonicalize",
    "file_fingerprint",
]
