"""Normalize Knowledge Engine results into reasoning evidence."""

from __future__ import annotations
import hashlib
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any
from core.reasoning.enums import EvidenceKind, EvidenceStance
from core.reasoning.models import EvidenceItem


class KnowledgeEvidenceAdapterError(ValueError):
    """Raised when knowledge output cannot be adapted."""


@dataclass(frozen=True, slots=True)
class AdaptedEvidenceBatch:
    query: str
    evidence: tuple[EvidenceItem, ...]
    rejected_count: int
    source_count: int


def _get(value: Any, names: tuple[str, ...], default: Any = None) -> Any:
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default


def _probability(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if 1.0 < number <= 100.0:
        number /= 100.0
    return max(0.0, min(1.0, number))


def _quality(result: Any) -> float:
    value = _get(result, ("quality_score", "quality"), 1.0)
    if hasattr(value, "score"):
        value = value.score
    elif isinstance(value, Mapping):
        value = value.get("score", 1.0)
    return _probability(value, 1.0)


def _ranking(result: Any) -> dict[str, Any]:
    value = _get(result, ("ranking", "breakdown"), {})
    if hasattr(value, "as_dict"):
        return dict(value.as_dict())
    return dict(value) if isinstance(value, Mapping) else {}


def _evidence_id(source: str, chunk: int | None, text: str) -> str:
    digest = hashlib.sha256(
        f"{source}\x1f{chunk}\x1f{text}".encode("utf-8")
    ).hexdigest()[:20]
    return f"knowledge_{digest}"


def _proposition(text: str) -> str:
    for candidate in re.split(r"(?<=[.!?])\s+", text):
        candidate = " ".join(candidate.split())
        if len(candidate) >= 12:
            return candidate[:500]
    return text[:500]


class KnowledgeEvidenceAdapter:
    """Accept production SearchResult objects or ranked dictionaries."""

    def adapt(
        self,
        query: str,
        results: Iterable[Any],
        *,
        stance: EvidenceStance = EvidenceStance.SUPPORTS,
        minimum_text_length: int = 12,
    ) -> AdaptedEvidenceBatch:
        query = " ".join(query.split())
        if not query:
            raise KnowledgeEvidenceAdapterError("query cannot be empty")

        evidence: list[EvidenceItem] = []
        rejected = 0
        sources: set[str] = set()

        for result in results:
            text = " ".join(str(_get(
                result, ("text", "content", "text_preview", "snippet"), ""
            ) or "").split())
            source = str(_get(
                result, ("source", "file_path", "path", "document_path"), ""
            ) or "").strip()
            raw_chunk = _get(
                result, ("chunk_index", "chunk_number", "chunk_id"), None
            )
            try:
                chunk = int(raw_chunk) if raw_chunk not in (None, "") else None
            except (TypeError, ValueError):
                chunk = None

            if len(text) < minimum_text_length or not source:
                rejected += 1
                continue

            score = _probability(_get(
                result, ("ranking_score", "score", "semantic_score"), 0.5
            ), 0.5)
            quality = _quality(result)
            sources.add(source)
            evidence.append(EvidenceItem(
                evidence_id=_evidence_id(source, chunk, text),
                proposition=_proposition(text),
                stance=stance,
                source_ref=(
                    f"{source}#chunk={chunk}" if chunk is not None else source
                ),
                kind=EvidenceKind.DOCUMENT,
                reliability=quality,
                confidence=score,
                metadata={
                    "query": query,
                    "source": source,
                    "chunk_index": chunk,
                    "retrieval_score": score,
                    "quality_score": quality,
                    "ranking": _ranking(result),
                    "text": text,
                },
            ))

        evidence.sort(key=lambda item: item.evidence_id)
        return AdaptedEvidenceBatch(
            query=query,
            evidence=tuple(evidence),
            rejected_count=rejected,
            source_count=len(sources),
        )
