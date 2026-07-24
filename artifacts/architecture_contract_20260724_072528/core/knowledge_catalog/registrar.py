from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.database import connect, migrate
from core.semantic_digest.pipeline import process_document


SUPPORTED = {".pdf", ".txt", ".md", ".json", ".xml", ".html", ".htm", ".epub", ".zim", ".csv"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def infer_collection_id(file_path: Path) -> str | None:
    try:
        parts = file_path.parts
        idx = parts.index("Knowledge")
        rel = parts[idx + 1 :]
    except ValueError:
        return None

    folders = list(rel[:-1])[:3]
    return ".".join(p.lower().replace(" ", "_") for p in folders) if folders else None


def register_file(path: Path, db_path: Path = DEFAULT_CATALOG_DB) -> dict:
    path = Path(path)
    migrate(db_path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)

    digest = process_document(path)
    now = utc_now()
    collection_id = infer_collection_id(path)

    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO catalog_documents (
                file_path, sha256, title, file_type, size_bytes,
                source_name, collection_id, created_at, updated_at,
                detected_type, inspection_reason, readable, content_chars
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                sha256=excluded.sha256,
                title=excluded.title,
                file_type=excluded.file_type,
                size_bytes=excluded.size_bytes,
                collection_id=excluded.collection_id,
                updated_at=excluded.updated_at,
                detected_type=excluded.detected_type,
                inspection_reason=excluded.inspection_reason,
                readable=excluded.readable,
                content_chars=excluded.content_chars
            """,
            (
                digest["file_path"], digest["sha256"], digest["title"],
                digest["file_type"], digest["size_bytes"], None, collection_id,
                now, now, digest.get("detected_type"), digest.get("inspection_reason"),
                1 if digest.get("readable") else 0, digest.get("content_chars", 0),
            ),
        )

        if collection_id:
            conn.execute(
                """
                INSERT OR IGNORE INTO collection_documents
                (collection_id, file_path, sha256, confidence, assigned_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (collection_id, digest["file_path"], digest["sha256"], 0.8, "path_collection", now),
            )

        if digest.get("subject"):
            conn.execute(
                """
                INSERT OR REPLACE INTO document_subjects
                (file_path, sha256, subject, confidence, assigned_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    digest["file_path"], digest["sha256"], digest["subject"],
                    digest.get("confidence", 0.0), digest.get("assigned_by", "semantic_extraction"), now,
                ),
            )

        for concept in digest.get("concepts", []):
            conn.execute(
                """
                INSERT OR REPLACE INTO document_concepts
                (file_path, sha256, concept, confidence, assigned_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    digest["file_path"], digest["sha256"], concept,
                    digest.get("confidence", 0.0), digest.get("assigned_by", "semantic_extraction"), now,
                ),
            )

        for keyword in digest.get("keywords", []):
            conn.execute(
                """
                INSERT OR REPLACE INTO document_keywords
                (file_path, keyword, confidence, assigned_by, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (digest["file_path"], keyword, digest.get("confidence", 0.0), digest.get("assigned_by", "semantic_extraction"), now),
            )

        for idx, heading in enumerate(digest.get("headings", [])[:80]):
            conn.execute(
                """
                INSERT OR REPLACE INTO document_headings
                (file_path, heading, position, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (digest["file_path"], heading, idx, now),
            )

        for term in digest.get("terms", [])[:80]:
            conn.execute(
                """
                INSERT OR REPLACE INTO document_terms
                (file_path, term, created_at)
                VALUES (?, ?, ?)
                """,
                (digest["file_path"], term, now),
            )

        conn.commit()

    return digest


def register_tree(root: Path, db_path: Path = DEFAULT_CATALOG_DB) -> dict:
    registered = 0
    skipped = 0

    for path in Path(root).rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED:
            skipped += 1
            continue
        register_file(path, db_path=db_path)
        registered += 1

    return {"registered": registered, "skipped": skipped}
