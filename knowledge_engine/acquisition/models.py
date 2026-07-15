"""
Immutable models for JARVIS knowledge acquisition.

Phase VII-A1 is read-only. These models describe acquisition requests,
discovered source candidates, and deterministic acquisition plans.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


def _normalized_extension(value: str) -> str:
    normalized = value.strip().lower()

    if not normalized:
        raise ValueError("file extension must not be empty")

    if not normalized.startswith("."):
        normalized = f".{normalized}"

    return normalized


@dataclass(frozen=True)
class AcquisitionRequest:
    """One bounded request to discover potential knowledge sources."""

    request_id: str
    roots: tuple[str, ...]
    recursive: bool = True
    include_hidden: bool = False
    follow_symlinks: bool = False
    max_files: int = 1000
    allowed_extensions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized_request_id = self.request_id.strip()

        if not normalized_request_id:
            raise ValueError("request_id must not be empty")

        normalized_roots = tuple(
            root.strip()
            for root in self.roots
            if root.strip()
        )

        if not normalized_roots:
            raise ValueError(
                "roots must contain at least one non-empty path"
            )

        if self.max_files < 1:
            raise ValueError("max_files must be at least 1")

        normalized_extensions = tuple(
            sorted({
                _normalized_extension(extension)
                for extension in self.allowed_extensions
            })
        )

        object.__setattr__(
            self,
            "request_id",
            normalized_request_id,
        )
        object.__setattr__(
            self,
            "roots",
            normalized_roots,
        )
        object.__setattr__(
            self,
            "allowed_extensions",
            normalized_extensions,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceCandidate:
    """One immutable source discovered by an acquisition provider."""

    provider_id: str
    source_uri: str
    local_path: str
    filename: str
    extension: str
    media_type: str
    candidate_type: str
    size_bytes: int
    checksum_sha256: str

    def __post_init__(self) -> None:
        required = {
            "provider_id": self.provider_id,
            "source_uri": self.source_uri,
            "local_path": self.local_path,
            "filename": self.filename,
            "media_type": self.media_type,
            "candidate_type": self.candidate_type,
            "checksum_sha256": self.checksum_sha256,
        }

        for name, value in required.items():
            if not value.strip():
                raise ValueError(f"{name} must not be empty")

        if self.size_bytes < 0:
            raise ValueError("size_bytes must not be negative")

        if len(self.checksum_sha256) != 64:
            raise ValueError(
                "checksum_sha256 must contain 64 hexadecimal characters"
            )

        try:
            int(self.checksum_sha256, 16)
        except ValueError as exc:
            raise ValueError(
                "checksum_sha256 must be hexadecimal"
            ) from exc

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AcquisitionPlan:
    """Deterministic result produced by one acquisition provider."""

    request_id: str
    provider_id: str
    candidates: tuple[SourceCandidate, ...]
    roots_scanned: tuple[str, ...]
    skipped_count: int = 0
    truncated: bool = False

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")

        if not self.provider_id.strip():
            raise ValueError("provider_id must not be empty")

        if self.skipped_count < 0:
            raise ValueError("skipped_count must not be negative")

        candidate_paths = [
            candidate.local_path
            for candidate in self.candidates
        ]

        if candidate_paths != sorted(candidate_paths):
            raise ValueError(
                "candidates must be ordered by local_path"
            )

        if len(candidate_paths) != len(set(candidate_paths)):
            raise ValueError(
                "candidate local paths must be unique"
            )

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def total_bytes(self) -> int:
        return sum(
            candidate.size_bytes
            for candidate in self.candidates
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "roots_scanned": list(self.roots_scanned),
            "skipped_count": self.skipped_count,
            "truncated": self.truncated,
            "candidates": [
                candidate.to_dict()
                for candidate in self.candidates
            ],
        }

        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(serialized).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "candidate_count": self.candidate_count,
            "total_bytes": self.total_bytes,
            "roots_scanned": list(self.roots_scanned),
            "skipped_count": self.skipped_count,
            "truncated": self.truncated,
            "fingerprint": self.fingerprint,
            "candidates": [
                candidate.to_dict()
                for candidate in self.candidates
            ],
        }
