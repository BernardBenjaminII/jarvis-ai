from __future__ import annotations

import sqlite3

from knowledge_engine.knowledge_graph.models import GraphEdge, GraphNode


def init_knowledge_graph(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS graph_nodes (
            node_uuid TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            name TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            source_object_uuid TEXT,
            confidence REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(node_type, canonical_name)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS graph_edges (
            edge_uuid TEXT PRIMARY KEY,
            source_node_uuid TEXT NOT NULL,
            target_node_uuid TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            source_object_uuid TEXT,
            confidence REAL NOT NULL,
            evidence TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_node_uuid, target_node_uuid, relationship_type, source_object_uuid),
            FOREIGN KEY(source_node_uuid) REFERENCES graph_nodes(node_uuid),
            FOREIGN KEY(target_node_uuid) REFERENCES graph_nodes(node_uuid)
        )
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(node_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_graph_nodes_name ON graph_nodes(canonical_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_graph_edges_type ON graph_edges(relationship_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_node_uuid)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_node_uuid)")


def upsert_node(conn: sqlite3.Connection, node: GraphNode) -> None:
    conn.execute("""
        INSERT INTO graph_nodes (
            node_uuid, node_type, name, canonical_name, source_object_uuid, confidence
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(node_type, canonical_name) DO UPDATE SET
            name=excluded.name,
            confidence=max(graph_nodes.confidence, excluded.confidence),
            updated_at=CURRENT_TIMESTAMP
    """, (
        node.node_uuid,
        node.node_type,
        node.name,
        node.canonical_name,
        node.source_object_uuid,
        node.confidence,
    ))


def upsert_edge(conn: sqlite3.Connection, edge: GraphEdge) -> None:
    conn.execute("""
        INSERT INTO graph_edges (
            edge_uuid,
            source_node_uuid,
            target_node_uuid,
            relationship_type,
            source_object_uuid,
            confidence,
            evidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_node_uuid, target_node_uuid, relationship_type, source_object_uuid)
        DO UPDATE SET
            confidence=max(graph_edges.confidence, excluded.confidence),
            evidence=excluded.evidence,
            updated_at=CURRENT_TIMESTAMP
    """, (
        edge.edge_uuid,
        edge.source_node_uuid,
        edge.target_node_uuid,
        edge.relationship_type,
        edge.source_object_uuid,
        edge.confidence,
        edge.evidence,
    ))
