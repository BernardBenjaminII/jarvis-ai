from __future__ import annotations

import sqlite3

from knowledge_engine.concepts.extractor import ExtractedConcept


def init_concepts(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunk_concepts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_uuid TEXT NOT NULL,
            file_path TEXT NOT NULL,
            concept TEXT NOT NULL,
            concept_type TEXT NOT NULL,
            domain TEXT,
            confidence REAL NOT NULL,
            evidence TEXT,
            extractor TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chunk_uuid, concept, concept_type)
        )
        """
    )


class ChunkConceptStore:
    def __init__(self, db):
        self.db = db

    def replace_concepts(
        self,
        chunk_uuid: str,
        file_path: str,
        concepts: list[ExtractedConcept],
    ) -> int:
        with self.db.connect() as conn:
            init_concepts(conn)

            conn.execute(
                "DELETE FROM chunk_concepts WHERE chunk_uuid=?",
                (chunk_uuid,),
            )

            for item in concepts:
                conn.execute(
                    """
                    INSERT INTO chunk_concepts(
                        chunk_uuid,
                        file_path,
                        concept,
                        concept_type,
                        domain,
                        confidence,
                        evidence,
                        extractor
                    )
                    VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        chunk_uuid,
                        file_path,
                        item.concept,
                        item.concept_type,
                        item.domain,
                        item.confidence,
                        item.evidence,
                        "rule_based_concept_extractor_v1",
                    ),
                )

            conn.execute(
                """
                UPDATE document_chunks
                SET concept_state='extracted'
                WHERE chunk_uuid=?
                """,
                (chunk_uuid,),
            )

            conn.commit()

        return len(concepts)
