from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Source:
    name: str
    trust_tier: int = 2
    source_type: str = "unknown"
    base_url: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class Topic:
    path: str
    name: str
    parent_path: str | None = None
    desired_depth: str = "medium"


@dataclass(slots=True)
class Document:
    title: str
    document_type: str = "unknown"
    language: str = "unknown"
    publication_year: int | None = None
    edition: str | None = None
    source_name: str | None = None
    trust_score: int = 50
    quality_score: int = 50


@dataclass(slots=True)
class FileAsset:
    document_id: int
    file_path: Path
    sha256: str
    size_bytes: int
    extension: str
    verification_status: str = "unknown"
    verification_message: str | None = None
    magic_type: str | None = None
