from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .authority import authority_rank, classify_authority
from .models import ClaimRecord


class ExtractionArtifactError(RuntimeError):
    pass


def _first(mapping: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExtractionArtifactError(f"Missing extraction artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ExtractionArtifactError(f"Invalid JSON extraction artifact: {path}: {exc}") from exc


def load_extraction(extraction_directory: Path) -> tuple[str, str, tuple[ClaimRecord, ...]]:
    summary = _load_json(extraction_directory / "constitutional_extraction.json")
    raw_claims = _load_json(extraction_directory / "constitutional_claims.json")

    repository_fingerprint = str(_first(summary, "repository_fingerprint"))
    extraction_fingerprint = str(_first(summary, "extraction_fingerprint", "fingerprint"))

    if isinstance(raw_claims, dict):
        claims_data = raw_claims.get("claims", [])
    else:
        claims_data = raw_claims

    if not isinstance(claims_data, list):
        raise ExtractionArtifactError("constitutional_claims.json must contain a list or {'claims': [...]}")

    records: list[ClaimRecord] = []
    for index, item in enumerate(claims_data):
        if not isinstance(item, dict):
            raise ExtractionArtifactError(f"Claim at index {index} is not an object")

        source_path = str(_first(item, "source_path", "path", "document_path"))
        level = classify_authority(source_path)
        record = ClaimRecord(
            claim_id=str(_first(item, "claim_id", "identifier", "id")),
            source_path=source_path,
            text=str(_first(item, "text", "statement", "claim", "excerpt")),
            modality=str(_first(item, "modality", default="unspecified")),
            domain=str(_first(item, "domain", "constitutional_domain", default="general")),
            line_start=int(_first(item, "line_start", "start_line", default=0) or 0),
            line_end=int(_first(item, "line_end", "end_line", default=0) or 0),
            repository_id=str(_first(item, "repository_id", "source_repository_id")),
            source_hash=str(_first(item, "source_hash", "source_sha256")),
            excerpt_hash=str(_first(item, "excerpt_hash", "claim_hash")),
            authority=level.value,
            authority_rank=authority_rank(level),
        )
        if not record.claim_id or not record.text:
            raise ExtractionArtifactError(f"Claim at index {index} lacks claim identifier or text")
        records.append(record)

    records.sort(key=lambda claim: (claim.source_path, claim.line_start, claim.line_end, claim.claim_id))
    return repository_fingerprint, extraction_fingerprint, tuple(records)
