from __future__ import annotations

from knowledge_engine.storage.db import KnowledgeDB
from knowledge_engine.chunking.builder import DocumentChunkBuilder
from knowledge_engine.chunking.store import init_chunks


def main() -> None:
    db = KnowledgeDB()

    with db.connect() as conn:
        init_chunks(conn)
        before = conn.execute(
            "SELECT COUNT(*) FROM document_chunks"
        ).fetchone()[0]

        ready = conn.execute(
            """
            SELECT COUNT(*)
            FROM knowledge_registry
            WHERE assimilation_state='ready_for_chunking'
            """
        ).fetchone()[0]

    print(f"Ready for chunking: {ready}")
    print(f"Chunks before: {before}")

    result = DocumentChunkBuilder(db).build_ready_documents(limit=5)

    print()
    print("Builder result:")
    print(result)

    with db.connect() as conn:
        after = conn.execute(
            "SELECT COUNT(*) FROM document_chunks"
        ).fetchone()[0]

        ready_embedding = conn.execute(
            """
            SELECT COUNT(*)
            FROM knowledge_registry
            WHERE assimilation_state='ready_for_embedding'
            """
        ).fetchone()[0]

        sample = conn.execute(
            """
            SELECT file_path, chunk_index, chunk_type, char_count, embedding_state
            FROM document_chunks
            ORDER BY created_at DESC
            LIMIT 10
            """
        ).fetchall()

    print()
    print(f"Chunks after: {after}")
    print(f"Ready for embedding: {ready_embedding}")

    print()
    print("Sample chunks:")
    for row in sample:
        print(
            f"{row['chunk_index']:>3} | "
            f"{row['chunk_type']:<18} | "
            f"{row['char_count']:>5} chars | "
            f"{row['embedding_state']:<12} | "
            f"{row['file_path']}"
        )


if __name__ == "__main__":
    main()

