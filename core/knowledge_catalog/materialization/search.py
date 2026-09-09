from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from .engine import migrate_runtime_materialization


_FTS_QUERY_STOPWORDS = frozenset({
    "a",
    "an",
    "and",
    "are",
    "about",
    "can",
    "could",
    "define",
    "did",
    "do",
    "does",
    "explain",
    "for",
    "how",
    "in",
    "is",
    "me",
    "of",
    "on",
    "or",
    "should",
    "tell",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "would",
})


# Technical identifiers whose meaning depends on punctuation.
_SYMBOL_IDENTIFIER_RE = re.compile(
    r"""
    (?<![A-Za-z0-9_])
    (
        [A-Za-z][A-Za-z0-9]*(?:\+\+|\#)
        |
        \.[A-Za-z][A-Za-z0-9]*
        |
        [A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+
    )
    (?![A-Za-z0-9_])
    """,
    re.VERBOSE,
)


def _extract_symbol_identifiers(query: str) -> tuple[str, ...]:
    """Extract punctuation-bearing technical identifiers.

    Examples:
        C++
        C#
        .NET
        AES-256

    The original spelling is preserved for literal retrieval.
    """

    value = str(query or "").strip()

    if not value:
        return ()

    identifiers = []

    for match in _SYMBOL_IDENTIFIER_RE.finditer(value):
        token = match.group(1).strip()

        if token:
            identifiers.append(token)

    # Stable de-duplication, case-insensitive.
    seen = set()
    result = []

    for token in identifiers:
        key = token.casefold()

        if key not in seen:
            seen.add(key)
            result.append(token)

    return tuple(result)


def _fts_query(query: str) -> str:
    """Build an FTS query from substantive FTS-safe terms.

    Question framing such as "what is" must not dominate retrieval.

    Punctuation-bearing identifiers such as C++, C#, and .NET are handled
    separately by literal identifier retrieval because SQLite FTS5 unicode61
    does not preserve their semantic punctuation reliably.
    """

    tokens = [
        token
        for token in re.findall(r"[A-Za-z0-9_]{2,}", str(query or "").casefold())
        if token not in _FTS_QUERY_STOPWORDS
    ]

    symbol_parts = {
        part
        for identifier in _extract_symbol_identifiers(query)
        for part in re.findall(r"[A-Za-z0-9_]{2,}", identifier.casefold())
    }

    # Do not allow lossy fragments of punctuation-sensitive identifiers
    # to masquerade as equivalent FTS terms.
    tokens = [
        token
        for token in tokens
        if token not in symbol_parts
    ]

    return " OR ".join(
        f'"{token}"'
        for token in tokens[:16]
    )


def _confidence(rank: float, ordinal: int) -> float:
    value = 1.0 / (1.0 + abs(rank))
    value *= max(0.45, 1.0 - ordinal * 0.035)

    return max(0.0, min(1.0, value))


def _literal_identifier_rows(
    conn: sqlite3.Connection,
    identifiers: tuple[str, ...],
    limit: int,
) -> list[sqlite3.Row]:
    """Retrieve chunks containing punctuation-sensitive identifiers.

    Matching is performed against:
      1. chunk text
      2. document title
      3. file path

    Exact punctuation is retained through SQLite instr().
    """

    if not identifiers:
        return []

    clauses = []
    params: list[Any] = []

    for identifier in identifiers:
        clauses.append(
            """
            (
                instr(lower(c.chunk_text), lower(?)) > 0
                OR instr(lower(d.title), lower(?)) > 0
                OR instr(lower(d.file_path), lower(?)) > 0
            )
            """
        )

        params.extend([
            identifier,
            identifier,
            identifier,
        ])

    params.append(max(1, int(limit)))

    sql = f"""
        SELECT
            c.id AS chunk_id,
            c.document_id,
            d.title,
            d.file_path,
            c.chunk_text,
            0.0 AS rank
        FROM runtime_chunks c
        JOIN runtime_documents d
            ON d.id = c.document_id
        WHERE {" OR ".join(clauses)}
        ORDER BY
            CASE
                WHEN instr(lower(d.title), lower(?)) > 0 THEN 0
                WHEN instr(lower(c.chunk_text), lower(?)) > 0 THEN 1
                WHEN instr(lower(d.file_path), lower(?)) > 0 THEN 2
                ELSE 3
            END,
            d.file_path,
            c.chunk_index
        LIMIT ?
    """

    # Ranking uses the first identifier as the primary subject.
    primary = identifiers[0]

    where_params = params[:-1]

    final_params = [
        *where_params,
        primary,
        primary,
        primary,
        params[-1],
    ]

    return conn.execute(
        sql,
        final_params,
    ).fetchall()


def _lexical_fts_rows(
    query: str,
    *,
    db_path: str | Path,
    limit: int,
) -> list[dict[str, Any]]:
    """Retrieve current catalog chunks directly from the canonical FTS index.

    The semantic index is intentionally separate from materialization and may
    temporarily lag newly admitted runtime documents.  This read-only lane
    prevents that lag from becoming a total recall failure.  Results still go
    through the normal qualification engine.
    """

    fts_query = _fts_query(query)

    if not fts_query:
        return []

    catalog = Path(db_path)
    uri = f"file:{catalog.resolve()}?mode=ro"

    with sqlite3.connect(uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                c.id AS chunk_id,
                c.document_id,
                d.title,
                d.file_path,
                c.chunk_text,
                bm25(runtime_chunks_fts) AS rank
            FROM runtime_chunks_fts
            JOIN runtime_chunks c
                ON c.id = runtime_chunks_fts.rowid
            JOIN runtime_documents d
                ON d.id = c.document_id
            WHERE runtime_chunks_fts MATCH ?
            ORDER BY rank, d.file_path, c.chunk_index
            LIMIT ?
            """,
            (fts_query, max(1, int(limit))),
        ).fetchall()

    output = []

    for ordinal, row in enumerate(rows):
        rank = float(row["rank"] or 0.0)
        output.append(
            {
                "subject": str(row["title"] or "runtime knowledge"),
                "title": str(row["title"] or "runtime knowledge"),
                "file_path": str(row["file_path"] or ""),
                "source_path": str(row["file_path"] or ""),
                "chunk_id": int(row["chunk_id"]),
                "document_id": int(row["document_id"]),
                "excerpt": str(row["chunk_text"] or ""),
                "chunk_text": str(row["chunk_text"] or ""),
                "retrieval_score": _confidence(rank, ordinal),
                "confidence": _confidence(rank, ordinal),
                "assigned_by": "runtime_fts_recall",
            }
        )

    return output


def search_runtime_knowledge(
    query: str,
    *,
    db_path: str | Path = DEFAULT_CATALOG_DB,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """
    Runtime knowledge retrieval.

    GENESIS_RECALL_R4_R11_A5_R9_R11

    The production semantic/hybrid retrieval pipeline is now the
    primary runtime retrieval path.

    HybridSemanticRetrievalService already performs semantic vector
    retrieval, lexical/title reranking, deduplication, source-family
    suppression, canonical/fragment competition, and diversity
    handling.

    This adapter preserves the historical row contract consumed by
    qualified_search while carrying the certified modern retrieval
    scores forward explicitly.

    Read only. No database mutation occurs here.
    """

    normalized = str(query or "").strip()

    if not normalized:
        return []

    from core.retrieval.hybrid_rerank.service import (
        HybridSemanticRetrievalService,
    )

    runtime_catalog = Path(db_path)

    semantic_db = (
        Path("/media/abdullah/JARVIS_RUNTIME_L")
        / "knowledge"
        / "semantic_index.sqlite"
    )

    service = HybridSemanticRetrievalService(
        runtime_catalog=runtime_catalog,
        semantic_db=semantic_db,
    )

    result = service.search(
        normalized,
        top_k=max(1, int(limit)),
        candidate_pool=max(
            50,
            max(1, int(limit)),
        ),
    )

    # Exact lexical recall is evaluated alongside semantic retrieval.  Put it
    # first so newly materialized, exact-topic evidence cannot be crowded out
    # by a stale semantic candidate pool.  Qualification remains authoritative.
    output = _lexical_fts_rows(
        normalized,
        db_path=runtime_catalog,
        limit=max(1, int(limit)),
    )

    seen_chunk_ids = {
        int(row["chunk_id"])
        for row in output
    }

    for candidate in result.candidates:
        chunk_id = int(candidate.runtime_chunk_id)

        if chunk_id in seen_chunk_ids:
            continue

        seen_chunk_ids.add(chunk_id)
        output.append(
            {
                "subject": str(
                    candidate.document_title
                    or "runtime knowledge"
                ),
                "title": str(
                    candidate.document_title
                    or "runtime knowledge"
                ),
                "file_path": str(
                    candidate.file_path
                    or ""
                ),
                "source_path": str(
                    candidate.file_path
                    or ""
                ),
                "chunk_id": chunk_id,
                "document_id": int(
                    candidate.runtime_document_id
                ),
                "excerpt": str(
                    candidate.text_preview
                    or ""
                ),
                "chunk_text": str(
                    candidate.text_preview
                    or ""
                ),

                # Certified modern retrieval signals.
                "hybrid_score": float(
                    candidate.hybrid_score
                ),
                "semantic_score": float(
                    candidate.semantic_score
                ),

                # Preserve the historical confidence field for
                # downstream compatibility. It now reflects the
                # selected production hybrid score rather than an
                # unrelated ordinal BM25 conversion.
                "confidence": float(
                    candidate.hybrid_score
                ),

                "assigned_by":
                    "runtime_semantic_hybrid",
            }
        )

    return output[:max(1, int(limit))]
