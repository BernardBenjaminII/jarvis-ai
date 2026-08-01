from __future__ import annotations

import json
from pathlib import Path

from ..fingerprints import canonical_fingerprint
from .authority_builder import build_authority_graph
from .authority_contracts import AUTHORITY_GRAPH_SCHEMA_VERSION
from .authority_integrity import verify_authority_graph_integrity
from .authority_metrics import compute_authority_graph_metrics
from .authority_models import AuthorityGraphAssessment


class ConstitutionalAuthorityGraphEngine:
    def assess(
        self,
        *,
        pack3a_directory: Path,
    ) -> AuthorityGraphAssessment:
        source_path = pack3a_directory / "constitutional_graph_foundation.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))

        graph_foundation_fingerprint = str(
            source.get("graph_fingerprint", "")
        )
        article_intelligence_fingerprint = str(
            source.get("article_intelligence_fingerprint", "")
        )
        graph_nodes = source.get("nodes", [])
        graph_edges = source.get("edges", [])
        diagnostics: list[str] = []

        if not graph_foundation_fingerprint:
            diagnostics.append("Graph foundation fingerprint is missing.")
        if not article_intelligence_fingerprint:
            diagnostics.append("Article intelligence fingerprint is missing.")
        if not isinstance(graph_nodes, list):
            graph_nodes = []
            diagnostics.append("Graph foundation node registry is invalid.")
        if not isinstance(graph_edges, list):
            graph_edges = []
            diagnostics.append("Graph foundation edge registry is invalid.")

        nodes, edges = build_authority_graph(graph_nodes, graph_edges)
        integrity = verify_authority_graph_integrity(nodes, edges)
        metrics = compute_authority_graph_metrics(nodes, edges)
        diagnostics.extend(integrity.diagnostics)

        basis = {
            "schema_version": AUTHORITY_GRAPH_SCHEMA_VERSION,
            "graph_foundation_fingerprint": graph_foundation_fingerprint,
            "article_intelligence_fingerprint": article_intelligence_fingerprint,
            "nodes": [node.to_dict() for node in nodes],
            "edges": [edge.to_dict() for edge in edges],
            "metrics": metrics.to_dict(),
            "integrity": integrity.to_dict(),
            "diagnostics": diagnostics,
        }

        return AuthorityGraphAssessment(
            schema_version=AUTHORITY_GRAPH_SCHEMA_VERSION,
            graph_foundation_fingerprint=graph_foundation_fingerprint,
            article_intelligence_fingerprint=article_intelligence_fingerprint,
            authority_graph_fingerprint=canonical_fingerprint(basis),
            nodes=nodes,
            edges=edges,
            metrics=metrics,
            integrity=integrity,
            diagnostics=tuple(diagnostics),
        )
