from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .contracts import ClaimModality, ConstitutionalDomain, DiagnosticSeverity, ExtractionStatus


@dataclass(frozen=True, slots=True)
class ExtractionPolicy:
    include_constitutional_documents: bool = True
    include_architecture_documents: bool = True
    include_adrs: bool = True
    include_non_normative_declarations: bool = False
    minimum_text_length: int = 8
    maximum_claim_length: int = 1200


@dataclass(frozen=True, slots=True)
class ConstitutionalSource:
    repository_id: str
    path: str
    document_id: str | None
    title: str | None
    source_sha256: str
    source_kind: str
    status: str | None


@dataclass(frozen=True, slots=True)
class EvidenceLocator:
    path: str
    start_line: int
    end_line: int
    section_path: tuple[str, ...]
    excerpt_sha256: str


@dataclass(frozen=True, slots=True)
class ConstitutionalClaim:
    claim_id: str
    source_repository_id: str
    source_document_id: str | None
    text: str
    normalized_text: str
    modality: ClaimModality
    domain: ConstitutionalDomain
    status: ExtractionStatus
    locator: EvidenceLocator
    confidence_basis: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExtractionDiagnostic:
    path: str
    message: str
    severity: DiagnosticSeverity
    line: int | None = None


@dataclass(frozen=True, slots=True)
class ConstitutionalExtractionStatistics:
    source_documents: int
    claims: int
    normative_claims: int
    declarations: int
    review_required: int
    diagnostics: int
    domains: tuple[tuple[str, int], ...]
    modalities: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ConstitutionalExtractionReport:
    schema_version: str
    engine_version: str
    repository_fingerprint: str
    sources: tuple[ConstitutionalSource, ...]
    claims: tuple[ConstitutionalClaim, ...]
    diagnostics: tuple[ExtractionDiagnostic, ...]
    statistics: ConstitutionalExtractionStatistics
    fingerprint: str


def to_primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    if is_dataclass(value):
        return {key: to_primitive(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): to_primitive(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [to_primitive(item) for item in value]
    return value
