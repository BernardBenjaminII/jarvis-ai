from __future__ import annotations

import json
from pathlib import Path


DEFAULT_FAISS_DIR = Path("/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss")


def scalar(conn, sql: str, params: tuple = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0] or 0) if row else 0


def table_exists(conn, name: str) -> bool:
    return scalar(
        conn,
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ) > 0


def grouped(conn, sql: str) -> list[tuple]:
    return [tuple(row) for row in conn.execute(sql).fetchall()]


def run_checks(conn, faiss_dir: str | Path = DEFAULT_FAISS_DIR) -> dict:
    faiss_dir = Path(faiss_dir)

    report: dict = {
        "tables": {},
        "counts": {},
        "states": {},
        "issues": [],
        "warnings": [],
        "faiss": {},
        "health_score": 100,
    }

    required_tables = [
        "discovered_files",
        "knowledge_objects",
        "knowledge_object_files",
        "knowledge_registry",
        "document_text",
        "document_chunks",
        "chunk_embeddings",
        "librarian_catalog",
        "catalog_enrichment",
	"graph_nodes", 
	"graph_edges",
    ]

    for table in required_tables:
        report["tables"][table] = table_exists(conn, table)

    missing = [t for t, ok in report["tables"].items() if not ok]
    if missing:
        report["issues"].append(f"Missing tables: {', '.join(missing)}")

    def count_table(table: str) -> int:
        if not table_exists(conn, table):
            return 0
        return scalar(conn, f"SELECT COUNT(*) FROM {table}")

    for table in required_tables:
        report["counts"][table] = count_table(table)

    if table_exists(conn, "knowledge_registry"):
        report["states"]["registry"] = grouped(
            conn,
            """
            SELECT assimilation_state, COUNT(*)
            FROM knowledge_registry
            GROUP BY assimilation_state
            ORDER BY assimilation_state
            """,
        )

    if table_exists(conn, "document_chunks"):
        report["states"]["chunks"] = grouped(
            conn,
            """
            SELECT embedding_state, COUNT(*)
            FROM document_chunks
            GROUP BY embedding_state
            ORDER BY embedding_state
            """,
        )

    if table_exists(conn, "resource_inspections"):
        report["counts"]["resource_inspections"] = count_table("resource_inspections")
        report["states"]["resource_inspections"] = grouped(
            conn,
            """
            SELECT status, COUNT(*)
            FROM resource_inspections
            GROUP BY status
            ORDER BY status
            """,
        )

    if table_exists(conn, "catalog_enrichment"):
        report["states"]["catalog_enrichment"] = grouped(
            conn,
            """
            SELECT status, COUNT(*)
            FROM catalog_enrichment
            GROUP BY status
            ORDER BY status
            """,
        )

    # Object membership checks.
    if table_exists(conn, "knowledge_objects") and table_exists(conn, "knowledge_object_files"):
        objects_without_members = scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM knowledge_objects ko
            LEFT JOIN knowledge_object_files kof
              ON kof.object_uuid = ko.object_uuid
            WHERE kof.object_uuid IS NULL
            """,
        )
        report["counts"]["objects_without_members"] = objects_without_members
        if objects_without_members:
            report["issues"].append(f"{objects_without_members} knowledge object(s) have no member files")

    # Librarian coverage.
    if table_exists(conn, "knowledge_objects") and table_exists(conn, "librarian_catalog"):
        uncataloged = scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM knowledge_objects ko
            LEFT JOIN librarian_catalog lc
              ON lc.object_uuid = ko.object_uuid
            WHERE lc.object_uuid IS NULL
            """,
        )
        report["counts"]["uncataloged_objects"] = uncataloged
        if uncataloged:
            report["warnings"].append(f"{uncataloged} knowledge object(s) missing librarian catalog entries")

    # Enrichment coverage.
    if table_exists(conn, "librarian_catalog") and table_exists(conn, "catalog_enrichment"):
        unenriched = scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM librarian_catalog lc
            LEFT JOIN catalog_enrichment ce
              ON ce.object_uuid = lc.object_uuid
            WHERE ce.object_uuid IS NULL
            """,
        )
        report["counts"]["unenriched_catalog_entries"] = unenriched
        if unenriched:
            report["warnings"].append(f"{unenriched} librarian catalog entrie(s) missing enrichment")

        if table_exists(conn, "graph_nodes"):
            report["counts"]["graph_nodes"] = count_table("graph_nodes")
            report["states"]["graph_nodes"] = grouped(
                conn,
                """
                SELECT node_type, COUNT(*)
                FROM graph_nodes
                GROUP BY node_type
                ORDER BY COUNT(*) DESC
                """,
            )

    if table_exists(conn, "graph_edges"):
        report["counts"]["graph_edges"] = count_table("graph_edges")
        report["states"]["graph_edges"] = grouped(
            conn,
            """
            SELECT relationship_type, COUNT(*)
            FROM graph_edges
            GROUP BY relationship_type
            ORDER BY COUNT(*) DESC
            """,
        )

    # Chunk membership link checks.
    if table_exists(conn, "document_chunks") and table_exists(conn, "knowledge_object_files"):
        chunks_without_object = scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM document_chunks dc
            LEFT JOIN knowledge_object_files kof
              ON kof.file_path = dc.file_path
            WHERE kof.object_uuid IS NULL
            """,
        )
        report["counts"]["chunks_without_object"] = chunks_without_object
        if chunks_without_object:
            report["issues"].append(f"{chunks_without_object} chunk(s) are not linked to a knowledge object")

    # Embedded chunk consistency.
    if table_exists(conn, "document_chunks") and table_exists(conn, "chunk_embeddings"):
        embedded_chunks = scalar(
            conn,
            "SELECT COUNT(*) FROM document_chunks WHERE embedding_state='embedded'",
        )
        embeddings = scalar(conn, "SELECT COUNT(*) FROM chunk_embeddings")
        report["counts"]["embedded_chunks"] = embedded_chunks
        report["counts"]["embedding_rows"] = embeddings

        if embedded_chunks != embeddings:
            report["issues"].append(
                f"Embedded chunk count ({embedded_chunks}) does not match chunk_embeddings rows ({embeddings})"
            )

    # FAISS files.
    index_path = faiss_dir / "chunks.faiss"
    map_path = faiss_dir / "chunks_map.json"
    report["faiss"]["index_path"] = str(index_path)
    report["faiss"]["map_path"] = str(map_path)
    report["faiss"]["index_exists"] = index_path.exists()
    report["faiss"]["map_exists"] = map_path.exists()

    if not index_path.exists() or not map_path.exists():
        report["warnings"].append("FAISS index files are missing")
    else:
        try:
            chunk_map = json.loads(map_path.read_text(encoding="utf-8"))
            report["faiss"]["mapped_vectors"] = len(chunk_map)
        except Exception as exc:
            report["issues"].append(f"Could not read FAISS map: {exc}")
            report["faiss"]["mapped_vectors"] = 0

    # Metadata-search sanity: resources with enrichment should have searchable fields.
    if table_exists(conn, "catalog_enrichment"):
        empty_enrichment = scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM catalog_enrichment
            WHERE COALESCE(aliases, '') = ''
              AND COALESCE(search_terms, '') = ''
              AND COALESCE(entities, '') = ''
              AND COALESCE(topics, '') = ''
            """,
        )
        report["counts"]["empty_enrichment_rows"] = empty_enrichment
        if empty_enrichment:
            report["warnings"].append(f"{empty_enrichment} enrichment row(s) have no searchable metadata")

    penalty = 0
    penalty += len(report["issues"]) * 15
    penalty += len(report["warnings"]) * 5
    report["health_score"] = max(0, 100 - penalty)

    return report
