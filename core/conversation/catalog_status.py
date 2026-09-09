"""Deterministic, read-only answers for catalog infrastructure questions."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any


_CATALOG = re.compile(r"\b(?:knowledge\s+catalog|catalog(?:\.sqlite)?)\b", re.I)
_STATUS = re.compile(
    r"\b(?:can\s+you\s+(?:see|access|reach|connect)|do\s+you\s+have\s+access|"
    r"is\s+(?:it|the\s+(?:knowledge\s+)?catalog)\s+(?:available|accessible|online)|"
    r"catalog\s+(?:status|health)|where\s+is\s+the\s+(?:knowledge\s+)?catalog)\b",
    re.I,
)
_CONTENT = re.compile(
    r"\b(?:summari[sz]e|explain|compare|teach|quote|according\s+to|what\s+does|"
    r"documents?\s+about|information\s+about)\b",
    re.I,
)

_TOPIC_REQUESTS = (
    re.compile(
        r"^\s*what\s+(?:qualified\s+)?(?:documents?|sources?|materials?)\s+"
        r"(?:do\s+you\s+have|are\s+available)\s+"
        r"(?:(?:in|from)\s+(?:the\s+)?(?:knowledge\s+)?catalog\s+)?"
        r"(?:about|on|covering)\s+(?P<topic>.+?)[?.!]*$",
        re.I,
    ),
    re.compile(
        r"\bdocuments?\s+(?:that\s+)?(?:cover|about|on|related\s+to)\s+"
        r"(?:the\s+)?(?:topic\s+of\s+)?(?P<topic>.+?)\s+"
        r"(?:in|within)\s+(?:the\s+)?(?:knowledge\s+)?catalog\b",
        re.I,
    ),
    re.compile(
        r"\b(?:does|do)\s+(?:the\s+)?(?:knowledge\s+)?catalog\s+(?:have|contain)\s+"
        r"(?:any\s+)?documents?\s+(?:about|on|covering)\s+(?P<topic>.+?)[?.!]*$",
        re.I,
    ),
)

_METADATA_FIELDS = {
    "document_subjects": ("subject", "file_path"),
    "document_keywords": ("keyword", "file_path"),
    "document_concepts": ("concept", "file_path"),
    "catalog_documents": ("title", "collection_id", "file_path"),
    "runtime_documents": ("title", "subject", "file_path"),
    "documents": ("title", "document_type", "id"),
    "topics": ("name", "path", "id"),
}

_COUNT_TABLES = (
    "file_assets",
    "catalog_documents",
    "runtime_documents",
    "document_subjects",
    "document_chunks",
)


def catalog_status_request(query: str) -> bool:
    """True only for a single-purpose catalog availability/health question."""
    text = " ".join(str(query or "").split())
    return bool(text and _CATALOG.search(text) and _STATUS.search(text) and not _CONTENT.search(text))


def catalog_topic_request(query: str) -> str | None:
    """Extract a requested catalog topic only from explicit inventory questions."""
    text = " ".join(str(query or "").split())
    for pattern in _TOPIC_REQUESTS:
        match = pattern.search(text)
        if match:
            topic = match.group("topic").strip(" ?.!,:;\"'")
            if 2 <= len(topic) <= 120:
                return topic
    return None


def inspect_catalog_topic(database_path: str | Path, topic: str, limit: int = 25) -> dict[str, Any]:
    """Search catalog identity metadata; never infer inventory from passages."""
    path = Path(database_path)
    result: dict[str, Any] = {
        "catalog_path": str(path), "topic": topic, "status": "unavailable",
        "matches": [], "checked_fields": [], "match_rule": "case-insensitive metadata substring",
    }
    if not path.is_file():
        result["error"] = "The configured catalog database does not exist."
        return result
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=4) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only=ON")
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            seen: set[tuple[str, str]] = set()

            # Prefer canonical, searchable runtime documents.  Topic terms may
            # be distributed across title, path, and assigned subject; requiring
            # the complete phrase inside one field misses valid documents such
            # as a vegetable guide classified as agriculture/gardening.
            topic_tokens = tuple(dict.fromkeys(
                token.casefold()
                for token in re.findall(r"[A-Za-z0-9_]{2,}", topic)
            ))

            if "runtime_documents" in tables and topic_tokens:
                runtime_columns = {
                    row[1]
                    for row in connection.execute(
                        'PRAGMA table_info("runtime_documents")'
                    )
                }
                required = {"id", "title", "file_path"}
                if required.issubset(runtime_columns):
                    token_clauses = []
                    params: list[Any] = []
                    has_subjects = "document_subjects" in tables
                    subject_columns = (
                        {
                            row[1]
                            for row in connection.execute(
                                'PRAGMA table_info("document_subjects")'
                            )
                        }
                        if has_subjects
                        else set()
                    )
                    subject_lookup = {"file_path", "subject"}.issubset(
                        subject_columns
                    )

                    for token in topic_tokens:
                        clauses = [
                            'LOWER(COALESCE(d.title, "")) LIKE ?',
                            'LOWER(COALESCE(d.file_path, "")) LIKE ?',
                        ]
                        value = f"%{token}%"
                        params.extend((value, value))
                        if subject_lookup:
                            clauses.append(
                                "EXISTS (SELECT 1 FROM document_subjects ds "
                                "WHERE ds.file_path = d.file_path "
                                'AND LOWER(COALESCE(ds.subject, "")) LIKE ?)'
                            )
                            params.append(value)
                        token_clauses.append("(" + " OR ".join(clauses) + ")")

                    content_select = (
                        "d.content_chars"
                        if "content_chars" in runtime_columns
                        else "NULL AS content_chars"
                    )
                    chunk_select = (
                        "(SELECT COUNT(*) FROM runtime_chunks rc "
                        "WHERE rc.document_id = d.id) AS chunk_count"
                        if "runtime_chunks" in tables
                        else "NULL AS chunk_count"
                    )
                    content_order = (
                        "COALESCE(d.content_chars, 0)"
                        if "content_chars" in runtime_columns
                        else "0"
                    )
                    sql = f"""
                        SELECT d.id, d.title, d.file_path,
                               {content_select}, {chunk_select}
                        FROM runtime_documents d
                        WHERE {" AND ".join(token_clauses)}
                        ORDER BY
                            CASE WHEN LOWER(d.title) LIKE LOWER(?) THEN 0 ELSE 1 END,
                            {content_order} DESC,
                            d.title, d.file_path
                        LIMIT ?
                    """
                    runtime_rows = connection.execute(
                        sql,
                        (*params, f"%{topic}%", limit),
                    ).fetchall()
                    result["checked_fields"].extend(
                        ["runtime_documents.title", "runtime_documents.file_path"]
                    )
                    if subject_lookup:
                        result["checked_fields"].append(
                            "document_subjects.subject"
                        )
                    for row in runtime_rows:
                        data = dict(row)
                        identity = str(data.get("file_path") or data.get("id"))
                        seen.add(("document", identity))
                        data["searchable"] = bool(
                            int(data.get("content_chars") or 0) > 0
                            and int(data.get("chunk_count") or 0) > 0
                        )
                        result["matches"].append(
                            {"table": "runtime_documents", **data}
                        )

            needle = f"%{topic}%"
            for table, preferred in _METADATA_FIELDS.items():
                if table == "runtime_documents":
                    continue
                if table not in tables or len(result["matches"]) >= limit:
                    continue
                columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
                search_fields = [field for field in preferred[:-1] if field in columns]
                identity_fields = [field for field in ("file_path", "title", "id") if field in columns]
                if not search_fields or not identity_fields:
                    continue
                selected = list(dict.fromkeys((*identity_fields, *search_fields)))
                where = " OR ".join(f'LOWER(COALESCE("{field}", \"\")) LIKE LOWER(?)' for field in search_fields)
                sql = f'SELECT {", ".join(f"\"{field}\"" for field in selected)} FROM "{table}" WHERE {where} LIMIT ?'
                rows = connection.execute(sql, (*([needle] * len(search_fields)), limit)).fetchall()
                result["checked_fields"].extend(f"{table}.{field}" for field in search_fields)
                for row in rows:
                    data = dict(row)
                    identity = str(data.get("file_path") or data.get("title") or data.get("id") or "")
                    key = ("document", identity)
                    if key in seen:
                        continue
                    seen.add(key)
                    result["matches"].append({"table": table, **data})
                    if len(result["matches"]) >= limit:
                        break
            result["status"] = "found" if result["matches"] else "not_found"
    except (OSError, sqlite3.Error, ValueError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def render_catalog_topic(result: dict[str, Any]) -> str:
    topic = result["topic"]
    if result["status"] == "unavailable":
        return f"I could not inspect the Knowledge Catalog for {topic}. Presence is unverified. Reason: {result.get('error', 'catalog unavailable')}"
    if result["status"] == "not_found":
        return (
            f"I found no catalog metadata matching {topic}. This means no matching subject, "
            "keyword, concept, title, or registered path was found; it does not prove that an "
            "unclassified file is absent from disk."
        )
    searchable = [
        item for item in result["matches"]
        if item.get("table") == "runtime_documents" and item.get("searchable")
    ]
    if searchable:
        lines = [
            f"I found {len(searchable)} searchable catalog document(s) for {topic}:"
        ]
        for item in searchable[:10]:
            title = item.get("title") or Path(str(item.get("file_path") or "")).name
            characters = int(item.get("content_chars") or 0)
            chunks = int(item.get("chunk_count") or 0)
            chunk_label = "chunk" if chunks == 1 else "chunks"
            lines.append(f"- {title}")
            lines.append(
                f"  Searchable coverage: {characters:,} characters in "
                f"{chunks:,} {chunk_label}."
            )
            lines.append(f"  Source: {item.get('file_path')}")
        if len(searchable) > 10:
            lines.append(f"- {len(searchable) - 10} additional document(s) omitted.")
        lines.append(
            "These documents are extracted and searchable; use a specific question "
            "to retrieve and cite their relevant passages."
        )
        return "\n".join(lines)

    lines = [f"Yes. I found {len(result['matches'])} catalog metadata match(es) for {topic}."]
    for item in result["matches"][:10]:
        identity = item.get("file_path") or item.get("title") or f"record {item.get('id')}"
        lines.append(f"- {identity} (matched in {item['table']})")
    if len(result["matches"]) > 10:
        lines.append(f"- {len(result['matches']) - 10} additional match(es) omitted.")
    lines.append("These are catalog inventory matches; content readability and answer relevance require separate qualification.")
    return "\n".join(lines)


def inspect_catalog(database_path: str | Path) -> dict[str, Any]:
    """Inspect the configured SQLite catalog without reading document content."""
    path = Path(database_path)
    result: dict[str, Any] = {
        "catalog_path": str(path),
        "exists": path.is_file(),
        "readable": False,
        "status": "unavailable",
        "tables": [],
        "counts": {},
    }
    if not result["exists"]:
        result["error"] = "The configured catalog database does not exist."
        return result

    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=3) as connection:
            connection.execute("PRAGMA query_only=ON")
            check = connection.execute("PRAGMA quick_check").fetchone()
            tables = tuple(
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                if row[0] and not str(row[0]).startswith("sqlite_")
            )
            result["readable"] = True
            result["integrity"] = str(check[0] if check else "unknown")
            result["tables"] = list(tables)
            for table in _COUNT_TABLES:
                if table in tables:
                    quoted = table.replace('"', '""')
                    result["counts"][table] = int(
                        connection.execute(f'SELECT COUNT(*) FROM "{quoted}"').fetchone()[0]
                    )
            result["status"] = "available"
    except (OSError, sqlite3.Error, ValueError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def render_catalog_status(result: dict[str, Any]) -> str:
    path = result["catalog_path"]
    if result["status"] != "available":
        return (
            "No. I cannot currently verify access to the configured Knowledge Catalog. "
            f"Configured database: {path}. "
            f"Reason: {result.get('error', 'read-only inspection failed')}"
        )

    counts = result.get("counts") or {}
    count_text = ", ".join(f"{name}: {value:,}" for name, value in counts.items())
    details = f" Indexed records checked: {count_text}." if count_text else ""
    return (
        "Yes. I can access the configured Knowledge Catalog through its read-only "
        f"SQLite database at {path}. The database opened successfully; integrity "
        f"check: {result.get('integrity', 'unknown')}; catalog tables found: "
        f"{len(result.get('tables') or [])}.{details} This confirms catalog access, "
        "not that every file is extracted, embedded, or relevant to a particular question."
    )
