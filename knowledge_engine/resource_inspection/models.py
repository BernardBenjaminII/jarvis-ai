from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceInspection:
    object_uuid: str
    object_path: str
    object_type: str
    title: str | None
    description: str | None
    language: str | None
    primary_subject: str | None
    keywords: str | None
    metadata_json: str
    status: str
    error: str | None = None
