from __future__ import annotations

from contextvars import ContextVar
from pathlib import Path
from typing import Any, Iterable, Mapping

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.search import search_catalog
from core.retrieval.qualification import (
    EvidenceCandidate,
    QualificationDiagnostic,
    QualificationEngine,
    QualificationResult,
)


_LAST_TRACE: ContextVar[dict[str, Any] | None] = ContextVar(
    "jarvis_last_qualification_trace",
    default=None,
)

_LAST_RESULT: ContextVar[QualificationResult | None] = ContextVar(
    "jarvis_last_qualification_result",
    default=None,
)


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)

    try:
        return dict(value)
    except Exception:
        return {}


def candidate_from_row(
    row: Mapping[str, Any] | Any,
    *,
    ordinal: int,
) -> EvidenceCandidate:
    data = _mapping(row)

    source_path = str(
        data.get("file_path")
        or data.get("source_path")
        or data.get("path")
        or ""
    )
    source_id = str(
        data.get("source_id")
        or data.get("chunk_id")
        or data.get("document_id")
        or source_path
        or f"candidate-{ordinal}"
    )
    title = str(
        data.get("title")
        or data.get("document_title")
        or Path(source_path).name
        or source_id
    )
    subject = str(
        data.get("subject")
        or data.get("topic")
        or data.get("domain")
        or ""
    )
    excerpt = str(
        data.get("excerpt")
        or data.get("chunk_text")
        or data.get("text")
        or data.get("content")
        or data.get("summary")
        or ""
    )
    backend = str(
        data.get("backend")
        or data.get("retrieval_backend")
        or data.get("assigned_by")
        or "runtime_fts"
    )

    raw_score = data.get("retrieval_score")

    if raw_score is None:
        raw_score = data.get("confidence")

    if raw_score is None:
        raw_score = data.get("score", 0.0)

    try:
        retrieval_score = float(raw_score or 0.0)
    except (TypeError, ValueError):
        retrieval_score = 0.0

    return EvidenceCandidate(
        source_id=source_id,
        source_path=source_path,
        title=title,
        subject=subject,
        excerpt=excerpt,
        backend=backend,
        retrieval_score=retrieval_score,
        metadata={
            "raw_row": data,
            "ordinal": ordinal,
        },
    )


def qualified_row(evidence: Any) -> dict[str, Any]:
    raw = dict(
        evidence.candidate.metadata.get("raw_row")
        or {}
    )

    raw.update(
        {
            "qualification_decision": evidence.decision.value,
            "qualification_score": evidence.score.final,
            "qualification_explanation": evidence.explanation,
            "qualification_components": evidence.score.to_dict(),
        }
    )

    raw.setdefault(
        "file_path",
        evidence.candidate.source_path,
    )
    raw.setdefault(
        "source_path",
        evidence.candidate.source_path,
    )
    raw.setdefault(
        "title",
        evidence.candidate.title,
    )
    raw.setdefault(
        "subject",
        evidence.candidate.subject,
    )
    raw.setdefault(
        "excerpt",
        evidence.candidate.excerpt,
    )
    raw.setdefault(
        "confidence",
        evidence.score.final,
    )
    raw.setdefault(
        "assigned_by",
        "qualification_engine",
    )

    return raw


def qualify_rows(
    query: str,
    rows: Iterable[Mapping[str, Any] | Any],
    *,
    engine: QualificationEngine | None = None,
) -> tuple[list[dict[str, Any]], QualificationResult]:
    active_engine = engine or QualificationEngine()
    row_list = list(rows)

    candidates = tuple(
        candidate_from_row(
            row,
            ordinal=index,
        )
        for index, row in enumerate(
            row_list,
            start=1,
        )
    )

    result = active_engine.evaluate(
        query,
        candidates,
    )

    accepted_rows = [
        qualified_row(item)
        for item in result.accepted
    ]

    diagnostics = [
        QualificationDiagnostic.from_evidence(
            query,
            item,
        ).to_dict()
        for item in (
            *result.accepted,
            *result.rejected,
        )
    ]

    _LAST_RESULT.set(result)

    _LAST_TRACE.set(
        {
            "query": query,
            "candidate_count": result.total_candidates,
            "accepted_count": len(result.accepted),
            "rejected_count": len(result.rejected),
            "threshold": result.threshold,
            "runtime_statistics": dict(
                result.runtime_statistics
            ),
            "diagnostics": diagnostics,
        }
    )

    return accepted_rows, result


def search_qualified_catalog(
    query: str,
    *,
    db_path: Path = DEFAULT_CATALOG_DB,
    limit: int = 25,
    engine: QualificationEngine | None = None,
) -> list[dict[str, Any]]:
    raw_rows = search_catalog(
        query,
        db_path=db_path,
        limit=limit,
    )

    accepted_rows, _ = qualify_rows(
        query,
        raw_rows,
        engine=engine,
    )

    return accepted_rows


def get_last_qualification_result() -> QualificationResult | None:
    return _LAST_RESULT.get()


def get_last_qualification_trace() -> dict[str, Any] | None:
    value = _LAST_TRACE.get()

    return None if value is None else dict(value)


def clear_last_qualification_state() -> None:
    _LAST_RESULT.set(None)
    _LAST_TRACE.set(None)
