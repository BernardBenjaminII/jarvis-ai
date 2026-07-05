from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalResult:
    chunk_uuid: str
    file_path: str
    chunk_index: int
    text: str
    vector_score: float
    metadata_score: float
    hybrid_score: float
    object_uuid: str | None
    resource_title: str | None
    resource_type: str | None
    subject: str | None
    quality_score: float | None
