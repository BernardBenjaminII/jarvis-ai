from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


class ConstitutionalDirectorateProjectionReporter:
    def write(
        self,
        assessment: dict[str, object],
        output_directory: Path,
    ) -> tuple[Path, ...]:
        graph = assessment["graph"]
        common = {
            "schema_version": assessment["schema_version"],
            "article_intelligence_fingerprint": assessment["article_intelligence_fingerprint"],
            "graph_foundation_fingerprint": assessment["graph_foundation_fingerprint"],
            "authority_graph_fingerprint": assessment["authority_graph_fingerprint"],
            "repository_projection_fingerprint": assessment["repository_projection_fingerprint"],
            "directorate_foundation_fingerprint": assessment["directorate_foundation_fingerprint"],
            "directorate_projection_fingerprint": assessment["directorate_projection_fingerprint"],
        }

        projection_payload = {
            **common,
            "nodes": [node.to_dict() for node in graph.nodes],
            "edges": [edge.to_dict() for edge in graph.edges],
            "metrics": assessment["metrics"],
            "integrity": assessment["integrity"],
            "diagnostics": assessment["diagnostics"],
        }

        written = [
            _write_json(
                output_directory / "constitutional_directorate_projection.json",
                projection_payload,
            ),
            _write_json(
                output_directory / "constitutional_directorate_nodes.json",
                {**common, "nodes": projection_payload["nodes"]},
            ),
            _write_json(
                output_directory / "constitutional_directorate_edges.json",
                {**common, "edges": projection_payload["edges"]},
            ),
            _write_json(
                output_directory / "constitutional_directorate_metrics.json",
                {**common, "metrics": assessment["metrics"]},
            ),
            _write_json(
                output_directory / "constitutional_directorate_integrity.json",
                {**common, "integrity": assessment["integrity"]},
            ),
        ]

        report = output_directory / "constitutional_directorate_summary.md"
        metrics = assessment["metrics"]
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            "\n".join(
                [
                    "# Genesis VII-C4.3 Pack 3B-2B.2 — Directorate Projection",
                    "",
                    f"**Directorate projection fingerprint:** `{assessment['directorate_projection_fingerprint']}`",
                    "",
                    f"- Ownership domains: {metrics['ownership_domain_count']}",
                    f"- Owned domains: {metrics['owned_domain_count']}",
                    f"- Unowned domains: {len(metrics['unowned_domain_ids'])}",
                    f"- Ownership completeness: {metrics['ownership_completeness_ratio']:.2%}",
                    f"- Diagnostics: {len(assessment['diagnostics'])}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        written.append(report)
        return tuple(written)
