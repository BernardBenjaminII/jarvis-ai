from __future__ import annotations

import json

from knowledge_engine.catalog_enrichment.extractor import enrich_row
from knowledge_engine.catalog_enrichment.models import CatalogEnrichment
from knowledge_engine.catalog_enrichment.store import (
    init_catalog_enrichment,
    upsert_enrichment,
)


class CatalogEnrichmentBuilder:
    def __init__(self, db):
        self.db = db

    def build(self, root_filter: str | None = None, limit: int | None = None) -> dict:
        enriched = 0
        errors: list[tuple[str, str]] = []

        sql = """
            SELECT
                lc.object_uuid,
                lc.object_path,
                lc.object_type,
                lc.canonical_title,
                lc.display_title,
                lc.subject,
                lc.keywords,
                lc.language,
                lc.description,
                lc.quality_score,
                lc.metadata_json
            FROM librarian_catalog lc
            WHERE 1=1
        """

        params: list[object] = []

        if root_filter:
            sql += " AND lc.object_path LIKE ?"
            params.append(f"%{root_filter}%")

        sql += " ORDER BY lc.object_path"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        with self.db.connect() as conn:
            init_catalog_enrichment(conn)
            rows = conn.execute(sql, params).fetchall()

            for row in rows:
                try:
                    data = enrich_row(row)

                    upsert_enrichment(
                        conn,
                        CatalogEnrichment(
                            object_uuid=row["object_uuid"],
                            aliases=data["aliases"],
                            search_terms=data["search_terms"],
                            entities=data["entities"],
                            topics=data["topics"],
                            enrichment_json=data["enrichment_json"],
                            status="enriched",
                            error=None,
                        ),
                    )

                    enriched += 1

                except Exception as exc:
                    errors.append((row["object_path"], str(exc)))

                    upsert_enrichment(
                        conn,
                        CatalogEnrichment(
                            object_uuid=row["object_uuid"],
                            aliases="",
                            search_terms="",
                            entities="",
                            topics="",
                            enrichment_json=json.dumps({}),
                            status="failed",
                            error=str(exc),
                        ),
                    )

            conn.commit()

        return {
            "resources_enriched": enriched,
            "enrichment_errors": errors,
        }
