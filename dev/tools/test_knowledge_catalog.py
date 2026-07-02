from pathlib import Path
from tempfile import TemporaryDirectory

from core.knowledge_catalog.database import connect
from core.knowledge_catalog.service import initialize_catalog, register_file


def main() -> None:
    with TemporaryDirectory() as td:
        db = Path(td) / "catalog.sqlite"
        stats = initialize_catalog(db)

        assert stats["sources"] > 0
        assert stats["topics"] > 0

        doc_id = register_file(
            db_path=db,
            title="Smoke Test Document",
            file_path=Path(td) / "smoke.pdf",
            sha256="abc123",
            size_bytes=1234,
            extension=".pdf",
            topic_path="computing/linux",
            source_name="MIT OpenCourseWare",
            verification_status="verified",
            verification_message="test",
            magic_type="pdf",
            trust_score=90,
            quality_score=80,
        )

        assert doc_id > 0

        with connect(db) as conn:
            docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            files = conn.execute("SELECT COUNT(*) FROM file_assets").fetchone()[0]
            links = conn.execute("SELECT COUNT(*) FROM document_topics").fetchone()[0]

        assert docs == 1
        assert files == 1
        assert links == 1

    print("[OK] Knowledge Catalog smoke test passed")


if __name__ == "__main__":
    main()
