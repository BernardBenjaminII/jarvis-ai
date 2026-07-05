from __future__ import annotations

import sqlite3

from knowledge_engine.catalog_enrichment.models import CatalogEnrichment


def init_catalog_enrichment(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS catalog_enrichment (
            object_uuid TEXT PRIMARY KEY,
            aliases TEXT,
            search_terms TEXT,
            entities TEXT,
            topics TEXT,
            enrichment_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL,
            error TEXT,
            enriched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(object_uuid) REFERENCES knowledge_objects(object_uuid)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_catalog_enrichment_status
        ON catalog_enrichment(status)
        """
    )


def upsert_enrichment(conn: sqlite3.Connection, enrichment: CatalogEnrichment) -> None:
    conn.execute(
        """
        INSERT INTO catalog_enrichment (
            object_uuid,
            aliases,
            search_terms,
            entities,
            topics,
            enrichment_json,
            status,
            error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(object_uuid) DO UPDATE SET
            aliases=excluded.aliases,
            search_terms=excluded.search_terms,
            entities=excluded.entities,
            topics=excluded.topics,
            enrichment_json=excluded.enrichment_json,
            status=excluded.status,
            error=excluded.error,
            enriched_at=CURRENT_TIMESTAMP
        """,
        (
            enrichment.object_uuid,
            enrichment.aliases,
            enrichment.search_terms,
            enrichment.entities,
            enrichment.topics,
            enrichment.enrichment_json,
            enrichment.status,
            enrichment.error,
        ),
    )
