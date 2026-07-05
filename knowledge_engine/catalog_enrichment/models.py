from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogEnrichment:
    object_uuid: str
    aliases: str
    search_terms: str
    entities: str
    topics: str
    enrichment_json: str
    status: str
    error: str | None = None
