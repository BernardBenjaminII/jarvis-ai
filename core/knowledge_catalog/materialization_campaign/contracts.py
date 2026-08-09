from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class CandidateDisposition(str, Enum):
    PENDING = "PENDING"
    MATERIALIZED = "MATERIALIZED"
    SKIPPED_ALREADY_PRESENT = "SKIPPED_ALREADY_PRESENT"
    SKIPPED_UNSUPPORTED = "SKIPPED_UNSUPPORTED"
    SKIPPED_MISSING = "SKIPPED_MISSING"
    SKIPPED_EMPTY = "SKIPPED_EMPTY"
    FAILED_EXTRACTION = "FAILED_EXTRACTION"
    FAILED_MATERIALIZATION = "FAILED_MATERIALIZATION"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True, slots=True)
class CampaignConfig:
    project_root: Path
    runtime_catalog: Path
    knowledge_root: Path
    checkpoint_db: Path
    report_dir: Path
    batch_size: int = 100
    max_batches: int | None = None
    max_documents: int | None = None
    stop_on_error: bool = False
    dry_run: bool = True
    retry_failures: bool = False

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key, value in tuple(result.items()):
            if isinstance(value, Path):
                result[key] = str(value)
        return result


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_id: str
    path: str
    extension: str
    sha256: str | None = None
    title: str | None = None
    category: str | None = None
    source_row: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CandidateResult:
    candidate_id: str
    path: str
    disposition: CandidateDisposition
    detail: str
    runtime_document_delta: int = 0
    runtime_chunk_delta: int = 0
    runtime_fts_delta: int = 0
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["disposition"] = self.disposition.value
        return result


@dataclass(frozen=True, slots=True)
class BatchReport:
    batch_id: str
    ordinal: int
    candidate_count: int
    started_at: str
    completed_at: str
    elapsed_seconds: float
    status: str
    results: tuple[CandidateResult, ...]
    pre_counts: dict[str, int]
    post_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "ordinal": self.ordinal,
            "candidate_count": self.candidate_count,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "elapsed_seconds": self.elapsed_seconds,
            "status": self.status,
            "results": [item.to_dict() for item in self.results],
            "pre_counts": dict(self.pre_counts),
            "post_counts": dict(self.post_counts),
        }


@dataclass(frozen=True, slots=True)
class CampaignRunReport:
    campaign_id: str
    status: str
    classification: str
    started_at: str
    completed_at: str
    elapsed_seconds: float
    dry_run: bool
    batches_completed: int
    candidates_examined: int
    disposition_counts: dict[str, int]
    pre_counts: dict[str, int]
    post_counts: dict[str, int]
    checkpoint_db: str
    reports: tuple[BatchReport, ...]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "status": self.status,
            "classification": self.classification,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "elapsed_seconds": self.elapsed_seconds,
            "dry_run": self.dry_run,
            "batches_completed": self.batches_completed,
            "candidates_examined": self.candidates_examined,
            "disposition_counts": dict(self.disposition_counts),
            "pre_counts": dict(self.pre_counts),
            "post_counts": dict(self.post_counts),
            "checkpoint_db": self.checkpoint_db,
            "reports": [item.to_dict() for item in self.reports],
            "recommendations": list(self.recommendations),
        }
