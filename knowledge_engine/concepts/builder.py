from __future__ import annotations

from knowledge_engine.concepts.extractor import extract_concepts
from knowledge_engine.concepts.store import ChunkConceptStore


class ConceptBuilder:
    def __init__(self, db):
        self.db = db
        self.store = ChunkConceptStore(db)

    def build_ready_chunks(self, limit: int = 25) -> dict:
        chunks_seen = 0
        concepts_built = 0
        errors: list[tuple[str, str]] = []

        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT chunk_uuid,
                       file_path,
                       text
                FROM document_chunks
                WHERE embedding_state='not_embedded'
                  AND COALESCE(concept_state, 'not_extracted')='not_extracted'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        for row in rows:
            try:
                concepts = extract_concepts(row["text"])
                count = self.store.replace_concepts(
                    row["chunk_uuid"],
                    row["file_path"],
                    concepts,
                )

                chunks_seen += 1
                concepts_built += count

            except Exception as exc:
                errors.append((row["chunk_uuid"], str(exc)))

        return {
            "chunks_seen": chunks_seen,
            "concepts_built": concepts_built,
            "concept_errors": errors,
        }
