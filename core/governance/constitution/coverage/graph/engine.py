from __future__ import annotations

import json
from pathlib import Path

from ..fingerprints import canonical_fingerprint
from .builder import build_foundation_graph
from .contracts import GRAPH_FOUNDATION_SCHEMA_VERSION
from .integrity import verify_graph_integrity
from .metrics import compute_graph_metrics
from .models import ConstitutionalGraphFoundationAssessment


class ConstitutionalGraphFoundationEngine:
    def assess(
        self,
        *,
        pack2_directory: Path,
    ) -> ConstitutionalGraphFoundationAssessment:
        source = json.loads(
            (pack2_directory / "constitutional_article_usage.json").read_text(
                encoding="utf-8"
            )
        )

        article_intelligence_fingerprint = str(
            source.get("article_intelligence_fingerprint", "")
        )
        article_usage = source.get("article_usage", [])
        diagnostics: list[str] = []

        if not article_intelligence_fingerprint:
            diagnostics.append("Article intelligence fingerprint is missing.")
        if not isinstance(article_usage, list):
            article_usage = []
            diagnostics.append("Article usage registry is invalid.")

        nodes, edges = build_foundation_graph(article_usage)
        integrity = verify_graph_integrity(nodes, edges)
        metrics = compute_graph_metrics(nodes, edges)

        diagnostics.extend(integrity.diagnostics)

        basis = {
            "schema_version": GRAPH_FOUNDATION_SCHEMA_VERSION,
            "article_intelligence_fingerprint": article_intelligence_fingerprint,
            "nodes": [node.to_dict() for node in nodes],
            "edges": [edge.to_dict() for edge in edges],
            "metrics": metrics.to_dict(),
            "integrity": integrity.to_dict(),
            "diagnostics": diagnostics,
        }

        return ConstitutionalGraphFoundationAssessment(
            schema_version=GRAPH_FOUNDATION_SCHEMA_VERSION,
            article_intelligence_fingerprint=article_intelligence_fingerprint,
            graph_fingerprint=canonical_fingerprint(basis),
            nodes=nodes,
            edges=edges,
            metrics=metrics,
            integrity=integrity,
            diagnostics=tuple(diagnostics),
        )
