from __future__ import annotations

from pathlib import Path

from core.knowledge_catalog.database import connect, migrate
from core.knowledge_catalog.models import Document, FileAsset
from core.knowledge_catalog.repository import CatalogRepository
from core.knowledge_catalog.seed import seed_catalog


def initialize_catalog(db_path: Path) -> dict[str, int]:
    migrate(db_path)
    with connect(db_path) as conn:
        repo = CatalogRepository(conn)
        seed_catalog(repo)
        conn.commit()
        return repo.stats()


def register_file(
    db_path: Path,
    title: str,
    file_path: Path,
    sha256: str,
    size_bytes: int,
    extension: str,
    topic_path: str | None = None,
    source_name: str | None = None,
    verification_status: str = "unknown",
    verification_message: str | None = None,
    magic_type: str | None = None,
    trust_score: int = 50,
    quality_score: int = 50,
) -> int:
    migrate(db_path)

    with connect(db_path) as conn:
        repo = CatalogRepository(conn)

        doc_id = repo.create_document(
            Document(
                title=title,
                document_type=extension.lstrip(".") or "unknown",
                source_name=source_name,
                trust_score=trust_score,
                quality_score=quality_score,
            )
        )

        repo.add_file_asset(
            FileAsset(
                document_id=doc_id,
                file_path=file_path,
                sha256=sha256,
                size_bytes=size_bytes,
                extension=extension,
                verification_status=verification_status,
                verification_message=verification_message,
                magic_type=magic_type,
            )
        )

        if topic_path:
            repo.link_document_topic(doc_id, topic_path)

        conn.commit()
        return doc_id
