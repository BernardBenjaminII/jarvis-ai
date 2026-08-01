from __future__ import annotations

import json
from pathlib import Path

from .models import ConstitutionalAnalysis


class ConstitutionalAnalysisReporter:
    def write(self, analysis: ConstitutionalAnalysis, output_directory: Path) -> tuple[Path, ...]:
        output_directory.mkdir(parents=True, exist_ok=True)

        relationships = [item.to_dict() for item in analysis.relationships]
        by_type = {
            relationship_type: [
                item for item in relationships if item["relationship_type"] == relationship_type
            ]
            for relationship_type in ("duplicates", "supports", "contradicts", "refines")
        }

        graph = {
            "schema_version": analysis.schema_version,
            "repository_fingerprint": analysis.repository_fingerprint,
            "extraction_fingerprint": analysis.extraction_fingerprint,
            "analysis_fingerprint": analysis.analysis_fingerprint,
            "nodes": [claim.to_dict() for claim in analysis.claims],
            "edges": relationships,
        }

        summary = analysis.to_dict()
        summary.pop("claims")
        summary.pop("relationships")

        artifacts = {
            "constitutional_analysis.json": summary,
            "constitutional_graph.json": graph,
            "constitutional_conflicts.json": {
                "analysis_fingerprint": analysis.analysis_fingerprint,
                "conflicts": by_type["contradicts"],
            },
            "constitutional_duplicates.json": {
                "analysis_fingerprint": analysis.analysis_fingerprint,
                "duplicates": by_type["duplicates"],
            },
            "constitutional_concordance.json": {
                "analysis_fingerprint": analysis.analysis_fingerprint,
                "supports": by_type["supports"],
                "refines": by_type["refines"],
            },
            "constitutional_authority.json": {
                "analysis_fingerprint": analysis.analysis_fingerprint,
                "resolutions": [
                    item for item in relationships if item["authority_resolution"]
                ],
            },
        }

        written: list[Path] = []
        for name, payload in artifacts.items():
            path = output_directory / name
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            written.append(path)

        report = output_directory / "constitutional_analysis_report.md"
        s = analysis.statistics
        report.write_text(
            "\n".join(
                [
                    "# Genesis VII-C2 Constitutional Analysis Report",
                    "",
                    f"**Repository fingerprint:** `{analysis.repository_fingerprint}`",
                    f"**Extraction fingerprint:** `{analysis.extraction_fingerprint}`",
                    f"**Analysis fingerprint:** `{analysis.analysis_fingerprint}`",
                    "",
                    "## Statistics",
                    "",
                    f"- Claims: {s.claims}",
                    f"- Relationships: {s.relationships}",
                    f"- Duplicates: {s.duplicates}",
                    f"- Supports: {s.supports}",
                    f"- Contradictions: {s.contradictions}",
                    f"- Refinements: {s.refines}",
                    f"- Authority resolutions: {s.authority_resolutions}",
                    f"- Diagnostics: {s.diagnostics}",
                    "",
                    "## Scope",
                    "",
                    "This deterministic engine identifies candidate constitutional relationships.",
                    "It does not ratify doctrine or semantically adjudicate ambiguous claims.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        written.append(report)
        return tuple(written)
