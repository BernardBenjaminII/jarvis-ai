from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

class MaterializationStage(str, Enum):
    DISCOVERED="DISCOVERED"
    VALIDATED="VALIDATED"
    EXTRACTING="EXTRACTING"
    EXTRACTED="EXTRACTED"
    CHUNKED="CHUNKED"
    WRITING="WRITING"
    COMPLETE="COMPLETE"
    SKIPPED="SKIPPED"
    FAILED="FAILED"
    QUARANTINED="QUARANTINED"

@dataclass(frozen=True, slots=True)
class EngineConfig:
    runtime_catalog: Path
    inventory_catalog: Path
    knowledge_root: Path
    checkpoint_db: Path
    report_dir: Path
    workers: int = 4
    batch_size: int = 100
    dry_run: bool = True
    stop_on_error: bool = False
    retry_failures: bool = False
    target_chunk_chars: int = 3200
    overlap_chars: int = 320
    minimum_chunk_chars: int = 120
    throttle_seconds: float = 0.0
    def to_dict(self)->dict[str,Any]:
        d=asdict(self)
        for k,v in tuple(d.items()):
            if isinstance(v,Path): d[k]=str(v)
        return d

@dataclass(frozen=True, slots=True)
class WorkItem:
    candidate_id: str
    path: str
    title: str
    category: str|None
    extension: str
    sha256: str|None=None

@dataclass(frozen=True, slots=True)
class Artifact:
    candidate_id: str
    path: str
    title: str
    category: str|None
    sha256: str
    media_type: str
    content_text: str
    chunks: tuple[dict[str,Any],...]
    extraction_seconds: float

@dataclass(frozen=True, slots=True)
class Result:
    candidate_id: str
    path: str
    stage: MaterializationStage
    detail: str
    document_delta: int=0
    chunk_delta: int=0
    fts_delta: int=0
    extraction_seconds: float=0.0
    write_seconds: float=0.0
    def to_dict(self):
        d=asdict(self); d["stage"]=self.stage.value; return d
