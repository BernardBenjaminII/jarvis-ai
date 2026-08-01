from __future__ import annotations

from pathlib import Path

from .models import ConstitutionalGraphFoundationAssessment
from .serialization import write_canonical_json


class ConstitutionalGraphFoundationReporter:
    def write(
        self,
        assessment: ConstitutionalGraphFoundationAssessment,
        output_directory: Path,
    ) -> tuple[Path, ...]:
        output_directory.mkdir(parents=True, exist_ok=True)

        common = {
            "schema_version": assessment.schema_version,
            "article_intelligence_fingerprint": assessment.article_intelligence_fingerprint,
            "graph_fingerprint": assessment.graph_fingerprint,
        }

        written = [
            write_canonical_json(
                output_directory / "constitutional_graph_foundation.json",
                assessment.to_dict(),
            ),
            write_canonical_json(
                output_directory / "constitutional_graph_nodes.json",
                {
                    **common,
                    "nodes": [node.to_dict() for node in assessment.nodes],
                },
            ),
            write_canonical_json(
                output_directory / "constitutional_graph_edges.json",
                {
                    **common,
                    "edges": [edge.to_dict() for edge in assessment.edges],
                },
            ),
            write_canonical_json(
                output_directory / "constitutional_graph_metrics.json",
                {
                    **common,
                    "metrics": assessment.metrics.to_dict(),
                },
            ),
            write_canonical_json(
                output_directory / "constitutional_graph_integrity.json",
                {
                    **common,
                    "integrity": assessment.integrity.to_dict(),
                },
            ),
        ]

        report = output_directory / "constitutional_graph_foundation_report.md"
        report.write_text(
            "\n".join([
                "# Genesis VII-C4.3 Pack 3A — Constitutional Graph Foundation",
                "",
                f"**Article intelligence fingerprint:** `{assessment.article_intelligence_fingerprint}`",
                f"**Graph fingerprint:** `{assessment.graph_fingerprint}`",
                "",
                "## Graph statistics",
                "",
                f"- Nodes: {assessment.metrics.node_count}",
                f"- Edges: {assessment.metrics.edge_count}",
                f"- Connected nodes: {assessment.metrics.connected_node_count}",
                f"- Isolated nodes: {assessment.metrics.isolated_node_count}",
                f"- Graph density: {assessment.metrics.graph_density:.12f}",
                f"- Integrity valid: {assessment.integrity.is_valid}",
                f"- Diagnostics: {len(assessment.diagnostics)}",
                "",
                "## Node types",
                "",
                *[
                    f"- `{key}`: {value}"
                    for key, value in assessment.metrics.node_type_counts.items()
                ],
                "",
                "## Edge types",
                "",
                *[
                    f"- `{key}`: {value}"
                    for key, value in assessment.metrics.edge_type_counts.items()
                ],
                "",
            ]),
            encoding="utf-8",
        )
        written.append(report)
        return tuple(written)
