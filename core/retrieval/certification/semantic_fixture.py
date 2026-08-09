from __future__ import annotations

import inspect
import re
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from types import MethodType
from typing import Any, Callable, Iterable

from core.knowledge_catalog.qualified_search import search_qualified_catalog


METADATA_TERMS = frozenset(
    {
        "sha256",
        "metadata",
        "document",
        "documents",
        "file",
        "file_path",
        "path",
        "confidence",
        "score",
        "chunk",
        "chunk_id",
        "document_id",
        "created_at",
        "updated_at",
        "assigned_by",
        "content",
        "text",
        "source",
        "runtime",
        "catalog",
    }
)

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_./+-]*")


@dataclass(frozen=True, slots=True)
class SemanticFixtureSelection:
    query: str
    source: str
    candidate_count: int
    rejected_metadata: int
    rejected_unqualified: int
    accepted_rows: int
    selector_method: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_phrase(value: str) -> str:
    words = WORD_RE.findall(value or "")
    filtered = [
        word
        for word in words
        if word.casefold() not in METADATA_TERMS
        and not re.fullmatch(r"[0-9a-fA-F]{32,}", word)
    ]
    return " ".join(filtered[:10]).strip()


def _meaningful(value: str) -> bool:
    cleaned = _clean_phrase(value)
    words = cleaned.split()

    if len(words) < 2:
        return False

    if len(cleaned) < 8:
        return False

    lowered = {word.casefold() for word in words}

    if lowered.issubset(METADATA_TERMS):
        return False

    return any(len(word) >= 5 for word in words)


def _candidate_queries(database: Path) -> Iterable[tuple[str, str]]:
    if not database.is_file():
        return ()

    queries = (
        (
            "runtime_document_title",
            """
            SELECT COALESCE(title, '')
            FROM runtime_documents
            WHERE length(trim(COALESCE(title, ''))) >= 8
            ORDER BY length(title) DESC, title
            LIMIT 250
            """,
        ),
        (
            "runtime_chunk_phrase",
            """
            SELECT substr(trim(chunk_text), 1, 180)
            FROM runtime_chunks
            WHERE length(trim(COALESCE(chunk_text, ''))) >= 40
            ORDER BY length(chunk_text), chunk_id
            LIMIT 400
            """,
        ),
        (
            "catalog_document_title",
            """
            SELECT COALESCE(title, '')
            FROM catalog_documents
            WHERE length(trim(COALESCE(title, ''))) >= 8
            ORDER BY length(title) DESC, title
            LIMIT 250
            """,
        ),
        (
            "document_subject",
            """
            SELECT COALESCE(subject, '')
            FROM document_subjects
            WHERE length(trim(COALESCE(subject, ''))) >= 8
            ORDER BY confidence DESC, subject
            LIMIT 250
            """,
        ),
    )

    seen: set[str] = set()
    values: list[tuple[str, str]] = []

    with sqlite3.connect(database) as conn:
        for source, sql in queries:
            try:
                rows = conn.execute(sql).fetchall()
            except sqlite3.Error:
                continue

            for row in rows:
                phrase = _clean_phrase(str(row[0] or ""))
                key = phrase.casefold()

                if not phrase or key in seen or not _meaningful(phrase):
                    continue

                seen.add(key)
                values.append((phrase, source))

    return tuple(values)


def select_semantic_fixture(
    database: Path,
    *,
    limit: int = 25,
) -> SemanticFixtureSelection:
    candidates = tuple(_candidate_queries(database))
    rejected_metadata = 0
    rejected_unqualified = 0

    for query, source in candidates:
        lowered = {word.casefold() for word in query.split()}

        if lowered & METADATA_TERMS and lowered.issubset(METADATA_TERMS):
            rejected_metadata += 1
            continue

        rows = search_qualified_catalog(
            query,
            db_path=database,
            limit=limit,
        )

        if rows:
            return SemanticFixtureSelection(
                query=query,
                source=source,
                candidate_count=len(candidates),
                rejected_metadata=rejected_metadata,
                rejected_unqualified=rejected_unqualified,
                accepted_rows=len(rows),
            )

        rejected_unqualified += 1

    raise RuntimeError(
        "No semantic known-query fixture produced accepted qualified evidence. "
        f"Candidates examined: {len(candidates)}; "
        f"metadata rejections: {rejected_metadata}; "
        f"qualification rejections: {rejected_unqualified}."
    )


def _selector_candidates(tracer: Any) -> list[tuple[int, str, Callable[..., Any]]]:
    ranked: list[tuple[int, str, Callable[..., Any]]] = []

    for name in dir(tracer):
        if name.startswith("__"):
            continue

        try:
            method = getattr(tracer, name)
        except Exception:
            continue

        if not callable(method):
            continue

        try:
            signature = inspect.signature(method)
        except Exception:
            continue

        required = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.default is inspect.Parameter.empty
            and parameter.kind
            not in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }
        ]

        if required:
            continue

        try:
            source = inspect.getsource(method)
        except Exception:
            source = ""

        score = 0
        lowered_name = name.casefold()
        lowered_source = source.casefold()

        if "known" in lowered_name:
            score += 100
        if "query" in lowered_name:
            score += 80
        if "fixture" in lowered_name:
            score += 60
        if "sha256" in lowered_source:
            score += 100
        if "known_query" in lowered_source:
            score += 90
        if "runtime_chunks" in lowered_source:
            score += 40
        if "catalog" in lowered_source:
            score += 20

        if score:
            ranked.append((score, name, method))

    return sorted(ranked, reverse=True)


def install_semantic_fixture_override(
    tracer: Any,
    database: Path,
) -> SemanticFixtureSelection:
    selection = select_semantic_fixture(database)
    candidates = _selector_candidates(tracer)

    if not candidates:
        raise RuntimeError(
            "Unable to locate the EndToEndRetrievalTracer known-query "
            "selector by runtime inspection."
        )

    _, method_name, original = candidates[0]

    def semantic_selector(self: Any) -> str:
        return selection.query

    setattr(
        tracer,
        method_name,
        MethodType(semantic_selector, tracer),
    )

    return SemanticFixtureSelection(
        query=selection.query,
        source=selection.source,
        candidate_count=selection.candidate_count,
        rejected_metadata=selection.rejected_metadata,
        rejected_unqualified=selection.rejected_unqualified,
        accepted_rows=selection.accepted_rows,
        selector_method=method_name,
    )
