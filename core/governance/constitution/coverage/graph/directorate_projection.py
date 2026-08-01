from __future__ import annotations

import json
from pathlib import Path

from ..fingerprints import canonical_fingerprint
from .directorate_assignment import build_assignment_edges
from .directorate_graph import ConstitutionalDirectorateGraph
from .directorate_integrity import verify_directorate_foundation_integrity
from .directorate_metrics import compute_directorate_metrics
from .directorate_models import DirectorateEdge, DirectorateNode


class ConstitutionalDirectorateProjectionEngine:
    def assess(
        self,
        *,
        pack3b2b1_directory: Path,
    ) -> dict[str, object]:
        source = json.loads(
            (
                pack3b2b1_directory
                / "constitutional_directorate_foundation.json"
            ).read_text(encoding="utf-8")
        )

        nodes = tuple(
            DirectorateNode(
                node_id=str(item["node_id"]),
                node_kind=__import__(
                    "core.governance.constitution.coverage.graph.directorate_contracts",
                    fromlist=["DirectorateNodeKind"],
                ).DirectorateNodeKind(str(item["node_kind"])),
                label=str(item["label"]),
                canonical_key=str(item["canonical_key"]),
                attributes=dict(item.get("attributes", {})),
                fingerprint=str(item.get("fingerprint", "")),
            )
            for item in source.get("nodes", [])
        )
        foundation_edges = tuple(
            DirectorateEdge(
                edge_id=str(item["edge_id"]),
                source_node_id=str(item["source_node_id"]),
                target_node_id=str(item["target_node_id"]),
                edge_kind=__import__(
                    "core.governance.constitution.coverage.graph.directorate_contracts",
                    fromlist=["DirectorateEdgeKind"],
                ).DirectorateEdgeKind(str(item["edge_kind"])),
                attributes=dict(item.get("attributes", {})),
                fingerprint=str(item.get("fingerprint", "")),
            )
            for item in source.get("edges", [])
        )

        assignment_edges = build_assignment_edges(nodes)
        edges = tuple(
            sorted(
                (*foundation_edges, *assignment_edges),
                key=lambda item: item.edge_id,
            )
        )

        integrity = verify_directorate_foundation_integrity(nodes, edges)
        metrics = compute_directorate_metrics(nodes, edges)
        diagnostics = list(integrity.diagnostics)
        if metrics["unowned_domain_ids"]:
            diagnostics.append("Unowned repository ownership domains detected.")

        basis = {
            "schema_version": source.get("schema_version", "1.0.0"),
            "article_intelligence_fingerprint": source.get("article_intelligence_fingerprint", ""),
            "graph_foundation_fingerprint": source.get("graph_foundation_fingerprint", ""),
            "authority_graph_fingerprint": source.get("authority_graph_fingerprint", ""),
            "repository_projection_fingerprint": source.get("repository_projection_fingerprint", ""),
            "directorate_foundation_fingerprint": source.get("directorate_foundation_fingerprint", ""),
            "nodes": [node.to_dict() for node in nodes],
            "edges": [edge.to_dict() for edge in edges],
            "metrics": metrics,
            "integrity": integrity.to_dict(),
            "diagnostics": diagnostics,
        }
        projection_fingerprint = canonical_fingerprint(basis)

        graph = ConstitutionalDirectorateGraph(nodes, edges)
        return {
            **basis,
            "directorate_projection_fingerprint": projection_fingerprint,
            "graph": graph,
        }
