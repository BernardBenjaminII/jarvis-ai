from __future__ import annotations

import hashlib
import json
import uuid

from knowledge_engine.knowledge_graph.extractor import canonicalize, extract_named_entities
from knowledge_engine.knowledge_graph.models import GraphEdge, GraphNode
from knowledge_engine.knowledge_graph.store import (
    init_knowledge_graph,
    upsert_edge,
    upsert_node,
)


def node_uuid(node_type: str, canonical_name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"node:{node_type}:{canonical_name}"))


def edge_uuid(source: str, rel: str, target: str, object_uuid: str | None) -> str:
    seed = f"edge:{source}:{rel}:{target}:{object_uuid or ''}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


class KnowledgeGraphBuilder:
    def __init__(self, db):
        self.db = db

    def build(self, root_filter: str | None = None, limit: int | None = None) -> dict:
        nodes_built = 0
        edges_built = 0
        errors: list[tuple[str, str]] = []

        sql = """
            SELECT
                lc.object_uuid,
                lc.object_path,
                lc.object_type,
                lc.display_title,
                lc.canonical_title,
                lc.subject,
                lc.keywords,
                lc.description,
                lc.metadata_json,
                COALESCE(ce.aliases, '') AS aliases,
                COALESCE(ce.search_terms, '') AS search_terms,
                COALESCE(ce.entities, '') AS entities,
                COALESCE(ce.topics, '') AS topics,
                COALESCE(ce.enrichment_json, '{}') AS enrichment_json
            FROM librarian_catalog lc
            LEFT JOIN catalog_enrichment ce
              ON ce.object_uuid = lc.object_uuid
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
            init_knowledge_graph(conn)
            rows = conn.execute(sql, params).fetchall()

            for row in rows:
                try:
                    title = row["display_title"] or row["canonical_title"] or row["object_path"]
                    resource_canonical = canonicalize(title)

                    resource_node = GraphNode(
                        node_uuid=node_uuid("resource", row["object_uuid"]),
                        node_type="resource",
                        name=title,
                        canonical_name=row["object_uuid"],
                        source_object_uuid=row["object_uuid"],
                        confidence=1.0,
                    )
                    upsert_node(conn, resource_node)
                    nodes_built += 1

                    resource_type_node = GraphNode(
                        node_uuid=node_uuid("resource_type", canonicalize(row["object_type"])),
                        node_type="resource_type",
                        name=row["object_type"],
                        canonical_name=canonicalize(row["object_type"]),
                        source_object_uuid=None,
                        confidence=1.0,
                    )
                    upsert_node(conn, resource_type_node)
                    nodes_built += 1

                    edge = GraphEdge(
                        edge_uuid=edge_uuid(resource_node.node_uuid, "is_type", resource_type_node.node_uuid, row["object_uuid"]),
                        source_node_uuid=resource_node.node_uuid,
                        target_node_uuid=resource_type_node.node_uuid,
                        relationship_type="is_type",
                        source_object_uuid=row["object_uuid"],
                        confidence=1.0,
                        evidence="librarian_catalog.object_type",
                    )
                    upsert_edge(conn, edge)
                    edges_built += 1

                    if row["subject"]:
                        subject_node = GraphNode(
                            node_uuid=node_uuid("subject", canonicalize(row["subject"])),
                            node_type="subject",
                            name=row["subject"],
                            canonical_name=canonicalize(row["subject"]),
                            source_object_uuid=None,
                            confidence=0.9,
                        )
                        upsert_node(conn, subject_node)
                        nodes_built += 1

                        edge = GraphEdge(
                            edge_uuid=edge_uuid(resource_node.node_uuid, "has_subject", subject_node.node_uuid, row["object_uuid"]),
                            source_node_uuid=resource_node.node_uuid,
                            target_node_uuid=subject_node.node_uuid,
                            relationship_type="has_subject",
                            source_object_uuid=row["object_uuid"],
                            confidence=0.9,
                            evidence="librarian_catalog.subject",
                        )
                        upsert_edge(conn, edge)
                        edges_built += 1

                    extracted = extract_named_entities(
                        row["display_title"],
                        row["canonical_title"],
                        row["subject"],
                        row["keywords"],
                        row["description"],
                        row["aliases"],
                        row["search_terms"],
                        row["entities"],
                        row["topics"],
                        row["metadata_json"],
                        row["enrichment_json"],
                    )

                    for entity_type, name, confidence in extracted:
                        canonical = canonicalize(name)
                        if not canonical:
                            continue

                        entity_node = GraphNode(
                            node_uuid=node_uuid(entity_type, canonical),
                            node_type=entity_type,
                            name=name,
                            canonical_name=canonical,
                            source_object_uuid=None,
                            confidence=confidence,
                        )
                        upsert_node(conn, entity_node)
                        nodes_built += 1

                        rel = "mentions" if entity_type == "entity" else "about"

                        edge = GraphEdge(
                            edge_uuid=edge_uuid(resource_node.node_uuid, rel, entity_node.node_uuid, row["object_uuid"]),
                            source_node_uuid=resource_node.node_uuid,
                            target_node_uuid=entity_node.node_uuid,
                            relationship_type=rel,
                            source_object_uuid=row["object_uuid"],
                            confidence=confidence,
                            evidence="catalog_enrichment",
                        )
                        upsert_edge(conn, edge)
                        edges_built += 1

                except Exception as exc:
                    errors.append((row["object_path"], str(exc)))

            conn.commit()

        return {
            "graph_nodes_upserted": nodes_built,
            "graph_edges_upserted": edges_built,
            "graph_errors": errors,
        }
