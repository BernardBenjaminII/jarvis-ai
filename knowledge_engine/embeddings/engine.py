from __future__ import annotations

import json
from pathlib import Path

from knowledge_engine.embeddings.provider import LocalEmbeddingProvider
from knowledge_engine.storage.database import KnowledgeDatabase


class EmbeddingEngine:
    def __init__(self, db_path: Path):
        self.db = KnowledgeDatabase(db_path)
        self.db.initialize()
        self.provider = LocalEmbeddingProvider()

    def ensure_schema(self) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunk_embeddings (
                    chunk_uuid TEXT PRIMARY KEY,
                    vector_json TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def build_missing(self, limit: int | None = None) -> dict:
        self.ensure_schema()

        sql = """
        SELECT
            dc.chunk_uuid,
            dc.file_path,
            dc.chunk_index,
            dc.text
        FROM document_chunks dc
        LEFT JOIN chunk_embeddings ce
            ON ce.chunk_uuid = dc.chunk_uuid
        WHERE ce.chunk_uuid IS NULL
          AND dc.text IS NOT NULL
          AND TRIM(dc.text) != ''
        ORDER BY dc.file_path, dc.chunk_index
        """

        if limit:
            sql += f" LIMIT {int(limit)}"

        embedded = 0
        skipped = 0

        with self.db.connect() as conn:
            rows = conn.execute(sql).fetchall()

            for row in rows:
                chunk_uuid = row["chunk_uuid"]
                text = row["text"]

                try:
                    vector = self.provider.embed(text)

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO chunk_embeddings
                            (
				chunk_uuid,
				provider,
				model,
				dimensions,
				vector_json
			    )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            chunk_uuid,
			    "sentence-transformers",
                            self.provider.model_name,
                            len(vector),
                            json.dumps(vector)

                        ),
                    )

                    embedded += 1

                except Exception as exc:
                    print("=" * 80)
                    print("[Embedding Error]")
                    print(f"Chunk UUID : {chunk_uuid}")
                    print(f"File       : {row['file_path']}")
                    print(f"Chunk      : {row['chunk_index']}")
                    print(f"Text repr  : {repr(text)}")
                    print(f"Exception  : {exc}")
                    skipped += 1

            conn.commit()

        return {
            "embedded": embedded,
            "skipped": skipped,
            "model": self.provider.model_name,
        }
