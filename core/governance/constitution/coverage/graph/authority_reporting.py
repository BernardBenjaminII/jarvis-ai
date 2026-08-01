from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .authority_models import AuthorityGraphAssessment


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(payload), encoding="utf-8")
    return path


class ConstitutionalAuthorityGraphReporter:
    def write(
        self,
        assessment: AuthorityGraphAssessment,
        output_directory: Path,
    ) -> tuple[Path, ...]:
        output_directory.mkdir(parents=True, exist_ok=True)

        common = {
            "schema_version": assessment.schema_version,
            "graph_foundation_fingerprint": assessment.graph_foundation_fingerprint,
            "article_intelligence_fingerprint": assessment.article_intelligence_fingerprint,
            "authority_graph_fingerprint": assessment.authority_graph_fingerprint,
        }

        written = [
            _write_json(
                output_directory / "constitutional_authority_graph.json",
                assessment.to_dict(),
            ),
            _write_json(
                output_directory / "constitutional_authority_nodes.json",
                {
                    **common,
                    "nodes": [node.to_dict() for node in assessment.nodes],
                },
            ),
            _write_json(
                output_directory / "constitutional_authority_edges.json",
                {
                    **common,
                    "edges": [edge.to_dict() for edge in assessment.edges],
                },
            ),
            _write_json(
                output_directory / "constitutional_authority_metrics.json",
                {
                    **common,
                    "metrics": assessment.metrics.to_dict(),
                },
            ),
            _write_json(
                output_directory / "constitutional_authority_integrity.json",
                {
                    **common,
                    "integrity": assessment.integrity.to_dict(),
                },
            ),
        ]

        report = output_directory / "constitutional_authority_summary.md"
        report.write_text(
            "\n".join([
                "# Genesis VII-C4.3 Pack 3B-1 — Constitutional Authority Graph",
                "",
                f"**Graph foundation fingerprint:** `{assessment.graph_foundation_fingerprint}`",
                f"**Article intelligence fingerprint:** `{assessment.article_intelligence_fingerprint}`",
                f"**Authority graph fingerprint:** `{assessment.authority_graph_fingerprint}`",
                "",
                "## Authority statistics",
                "",
                f"- Constitutional articles: {assessment.metrics.article_count}",
                f"- Governed artifacts: {assessment.metrics.governed_artifact_count}",
                f"- Governance domains: {assessment.metrics.governance_domain_count}",
                f"- Authorization edges: {assessment.metrics.authorization_edge_count}",
                f"- Exercised articles: {assessment.metrics.exercised_article_count}",
                f"- Unexercised articles: {assessment.metrics.unexercised_article_count}",
                f"- Authority utilization: {assessment.metrics.authority_utilization_ratio:.2%}",
                f"- Integrity valid: {assessment.integrity.is_valid}",
                f"- Diagnostics: {len(assessment.diagnostics)}",
                "",
                "## Authority-class distribution",
                "",
                *[
                    f"- `{key}`: {value}"
                    for key, value
                    in assessment.metrics.authority_class_distribution.items()
                ],
                "",
            ]),
            encoding="utf-8",
        )
        written.append(report)
        return tuple(written)
