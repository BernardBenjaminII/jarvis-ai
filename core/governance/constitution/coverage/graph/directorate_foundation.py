from __future__ import annotations

import json
from pathlib import Path

from ..fingerprints import canonical_fingerprint
from .directorate_builder import build_directorate_foundation
from .directorate_contracts import DIRECTORATE_PROJECTION_SCHEMA_VERSION
from .directorate_integrity import verify_directorate_foundation_integrity
from .directorate_models import DirectorateFoundationAssessment


class ConstitutionalDirectorateFoundationEngine:
    def assess(
        self,
        *,
        pack3b2a_directory: Path,
    ) -> DirectorateFoundationAssessment:
        source = json.loads(
            (
                pack3b2a_directory
                / "constitutional_repository_projection.json"
            ).read_text(encoding="utf-8")
        )

        article_intelligence_fingerprint = str(
            source.get("article_intelligence_fingerprint", "")
        )
        graph_foundation_fingerprint = str(
            source.get("graph_foundation_fingerprint", "")
        )
        authority_graph_fingerprint = str(
            source.get("authority_graph_fingerprint", "")
        )
        repository_projection_fingerprint = str(
            source.get("repository_projection_fingerprint", "")
        )
        repository_nodes = source.get("nodes", [])

        diagnostics: list[str] = []
        for label, value in (
            ("Article intelligence", article_intelligence_fingerprint),
            ("Graph foundation", graph_foundation_fingerprint),
            ("Authority graph", authority_graph_fingerprint),
            ("Repository projection", repository_projection_fingerprint),
        ):
            if not value:
                diagnostics.append(f"{label} fingerprint is missing.")

        if not isinstance(repository_nodes, list):
            repository_nodes = []
            diagnostics.append("Repository node registry is invalid.")

        nodes, edges = build_directorate_foundation(repository_nodes)
        integrity = verify_directorate_foundation_integrity(nodes, edges)
        diagnostics.extend(integrity.diagnostics)

        basis = {
            "schema_version": DIRECTORATE_PROJECTION_SCHEMA_VERSION,
            "article_intelligence_fingerprint": article_intelligence_fingerprint,
            "graph_foundation_fingerprint": graph_foundation_fingerprint,
            "authority_graph_fingerprint": authority_graph_fingerprint,
            "repository_projection_fingerprint": repository_projection_fingerprint,
            "nodes": [node.to_dict() for node in nodes],
            "edges": [edge.to_dict() for edge in edges],
            "integrity": integrity.to_dict(),
            "diagnostics": diagnostics,
        }

        return DirectorateFoundationAssessment(
            schema_version=DIRECTORATE_PROJECTION_SCHEMA_VERSION,
            article_intelligence_fingerprint=article_intelligence_fingerprint,
            graph_foundation_fingerprint=graph_foundation_fingerprint,
            authority_graph_fingerprint=authority_graph_fingerprint,
            repository_projection_fingerprint=repository_projection_fingerprint,
            directorate_foundation_fingerprint=canonical_fingerprint(basis),
            nodes=nodes,
            edges=edges,
            integrity=integrity,
            diagnostics=tuple(diagnostics),
        )
