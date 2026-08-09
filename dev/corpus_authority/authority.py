from __future__ import annotations
from pathlib import Path
from typing import Any
from .sqlite_tools import open_ro, count_rows, table_exists, schema_signature

CORE_TABLES = (
    "documents",
    "knowledge_index",
    "library_catalog",
    "runtime_documents",
    "runtime_chunks",
    "runtime_chunks_fts",
    "document_subjects",
    "knowledge_classifications",
)

def profile_database(path: Path, configured_runtime: Path) -> dict[str, Any]:
    conn = open_ro(path)
    try:
        counts = {table: count_rows(conn, table) for table in CORE_TABLES}
        present = [table for table in CORE_TABLES if table_exists(conn, table)]
        score = 0.0
        reasons = []
        if path.resolve() == configured_runtime.resolve():
            score += 50.0
            reasons.append("configured DEFAULT_CATALOG_DB")
        if counts["runtime_chunks_fts"] > 0:
            score += 20.0
            reasons.append("populated runtime FTS")
        if counts["runtime_documents"] > 0:
            score += 10.0
            reasons.append("populated runtime documents")
        if counts["knowledge_index"] > 0 or counts["documents"] > 0:
            score += 10.0
            reasons.append("populated catalog registry")
        if "backup" in str(path).casefold() or "before_" in path.name.casefold():
            score -= 40.0
            reasons.append("backup naming")
        if path.name == "catalog.sqlite":
            score += 5.0
        return {
            "path": str(path.resolve()),
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "modified_ns": path.stat().st_mtime_ns,
            "core_tables_present": present,
            "table_counts": counts,
            "schema_object_count": len(schema_signature(conn)),
            "authority_score": score,
            "authority_reasons": reasons,
            "configured_runtime": path.resolve() == configured_runtime.resolve(),
        }
    finally:
        conn.close()

def authority_candidates(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(profiles, key=lambda item: (-item["authority_score"], item["path"]))
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
        item["recommended_role"] = (
            "authoritative_runtime_catalog" if index == 1 else
            "secondary_or_historical_catalog"
        )
    return ranked
