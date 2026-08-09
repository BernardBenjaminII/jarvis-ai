from __future__ import annotations
from pathlib import Path
from typing import Any
from .sqlite_tools import (
    open_ro, table_exists, count_rows, columns, populated_count,
    distinct_count, file_identity_columns, qident
)

STAGES = (
    ("physical_catalog_registry", "documents"),
    ("search_metadata_registry", "knowledge_index"),
    ("library_registry", "library_catalog"),
    ("classified_files", "knowledge_classifications"),
    ("runtime_documents", "runtime_documents"),
    ("runtime_chunks", "runtime_chunks"),
    ("runtime_fts", "runtime_chunks_fts"),
)

def stage_profiles(path: Path) -> list[dict[str, Any]]:
    conn = open_ro(path)
    try:
        result = []
        for stage, table in STAGES:
            cols = columns(conn, table)
            identities = file_identity_columns(conn, table)
            result.append({
                "stage": stage,
                "table": table,
                "present": table_exists(conn, table),
                "row_count": count_rows(conn, table),
                "columns": cols,
                "identity_columns": identities,
                "identity_population": {
                    col: populated_count(conn, table, col) for col in identities
                },
                "identity_distinct": {
                    col: distinct_count(conn, table, col) for col in identities
                },
            })
        return result
    finally:
        conn.close()

def _best_identity(left: dict[str, Any], right: dict[str, Any]) -> tuple[str, str] | None:
    pairs = (
        ("path", "file_path"),
        ("path", "document_path"),
        ("document_path", "file_path"),
        ("file_path", "file_path"),
        ("relative_path", "relative_path"),
        ("sha256", "sha256"),
        ("id", "document_id"),
        ("document_id", "document_id"),
    )
    lcols = set(left["columns"])
    rcols = set(right["columns"])
    for lcol, rcol in pairs:
        if lcol in lcols and rcol in rcols:
            return lcol, rcol
    return None

def lineage_edges(path: Path, stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conn = open_ro(path)
    try:
        result = []
        for left, right in zip(stages, stages[1:]):
            pair = _best_identity(left, right)
            edge = {
                "source_stage": left["stage"],
                "source_table": left["table"],
                "target_stage": right["stage"],
                "target_table": right["table"],
                "source_rows": left["row_count"],
                "target_rows": right["row_count"],
                "identity_pair": None,
                "matched_source_rows": None,
                "source_match_rate": None,
                "target_to_source_ratio": (
                    0.0 if left["row_count"] == 0
                    else right["row_count"] / left["row_count"]
                ),
                "classification": "unverified",
                "error": None,
            }
            if not left["present"] or not right["present"]:
                edge["classification"] = "missing_stage"
                result.append(edge)
                continue
            if pair is None:
                edge["classification"] = "no_identity_join"
                result.append(edge)
                continue
            lcol, rcol = pair
            edge["identity_pair"] = [lcol, rcol]
            try:
                matched = int(conn.execute(
                    f"SELECT COUNT(DISTINCT l.rowid) "
                    f"FROM {qident(left['table'])} l "
                    f"JOIN {qident(right['table'])} r "
                    f"ON CAST(l.{qident(lcol)} AS TEXT)=CAST(r.{qident(rcol)} AS TEXT) "
                    f"WHERE l.{qident(lcol)} IS NOT NULL "
                    f"AND TRIM(CAST(l.{qident(lcol)} AS TEXT))<>''"
                ).fetchone()[0])
                source_populated = left["identity_population"].get(lcol, left["row_count"])
                rate = 0.0 if source_populated == 0 else matched / source_populated
                edge["matched_source_rows"] = matched
                edge["source_match_rate"] = rate
                edge["classification"] = (
                    "strong_lineage" if rate >= .90 else
                    "partial_lineage" if rate >= .25 else
                    "weak_lineage"
                )
            except Exception as exc:
                edge["classification"] = "join_error"
                edge["error"] = f"{type(exc).__name__}: {exc}"
            result.append(edge)
        return result
    finally:
        conn.close()

def calculate_dropoff(stages: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {stage["stage"]: stage["row_count"] for stage in stages}
    catalog_base = max(
        counts.get("physical_catalog_registry", 0),
        counts.get("search_metadata_registry", 0),
        counts.get("classified_files", 0),
    )
    runtime_docs = counts.get("runtime_documents", 0)
    runtime_chunks = counts.get("runtime_chunks", 0)
    runtime_fts = counts.get("runtime_fts", 0)
    materialization_rate = 0.0 if catalog_base == 0 else runtime_docs / catalog_base
    return {
        "catalog_base": catalog_base,
        "runtime_documents": runtime_docs,
        "runtime_chunks": runtime_chunks,
        "runtime_fts_rows": runtime_fts,
        "materialization_rate": materialization_rate,
        "unmaterialized_catalog_objects": max(0, catalog_base - runtime_docs),
        "chunks_per_runtime_document": 0.0 if runtime_docs == 0 else runtime_chunks / runtime_docs,
        "fts_chunk_coverage": 0.0 if runtime_chunks == 0 else runtime_fts / runtime_chunks,
    }
