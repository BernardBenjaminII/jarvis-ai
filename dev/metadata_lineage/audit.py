from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import MetadataLineageReport
from .discovery import discover_databases
from .join_analysis import (
    candidate_pairs,
    evaluate_same_database_join,
    lineage_paths,
)
from .sqlite_profile import profile_database


class MetadataJoinLineageAudit:
    def __init__(
        self,
        *,
        project_root: Path,
        knowledge_root: Path | None = None,
    ) -> None:
        self.project_root = project_root
        self.knowledge_root = knowledge_root

    def execute(self) -> MetadataLineageReport:
        paths = discover_databases(
            project_root=self.project_root,
            knowledge_root=self.knowledge_root,
        )

        databases = []
        profiles = []

        for path in paths:
            database, table_profiles = profile_database(path)
            databases.append(database)
            profiles.extend(table_profiles)

        joins = [
            evaluate_same_database_join(pair)
            for pair in candidate_pairs(profiles)
        ]
        joins.sort(
            key=lambda item: (
                -float(item.get("score") or 0.0),
                item["left_database"],
                item["left_table"],
                item["right_table"],
            )
        )

        lineages = lineage_paths(joins, profiles)
        preferred = [
            item
            for item in joins
            if item["recommendation"]
            == "preferred_join"
        ]
        usable = [
            item
            for item in joins
            if item["recommendation"]
            in {
                "preferred_join",
                "usable_with_validation",
            }
        ]
        propagation = [
            item
            for item in lineages
            if item["metadata_propagation_possible"]
        ]

        if not databases:
            classification = "NO_DATABASES_DISCOVERED"
        elif not joins:
            classification = "NO_JOIN_CANDIDATES"
        elif not propagation:
            classification = "NO_SAFE_METADATA_LINEAGE"
        elif preferred:
            classification = "PREFERRED_METADATA_LINEAGE_DISCOVERED"
        else:
            classification = "VALIDATED_METADATA_LINEAGE_AVAILABLE"

        status = (
            "EXCELLENT"
            if classification
            in {
                "PREFERRED_METADATA_LINEAGE_DISCOVERED",
                "VALIDATED_METADATA_LINEAGE_AVAILABLE",
            }
            else "FAILED"
        )

        summary: dict[str, Any] = {
            "database_count": len(databases),
            "table_count": len(profiles),
            "join_candidate_count": len(joins),
            "preferred_join_count": len(preferred),
            "usable_join_count": len(usable),
            "metadata_lineage_count": len(lineages),
            "propagation_path_count": len(propagation),
            "top_joins": joins[:20],
            "top_lineage_paths": sorted(
                lineages,
                key=lambda item: -float(item["score"]),
            )[:20],
        }

        recommendations = []

        if propagation:
            recommendations.append(
                "Use the highest-scoring lineage path in an in-memory category-to-subject simulation."
            )
            recommendations.append(
                "Do not persist metadata mappings until orphan and ambiguity rates are reviewed."
            )
        else:
            recommendations.append(
                "Do not build a runtime metadata adapter until a safe lineage path is proven."
            )

        if any(
            item.get("normalized_key") == "path"
            and item["recommendation"]
            in {
                "preferred_join",
                "usable_with_validation",
            }
            for item in joins
        ):
            recommendations.append(
                "Prefer canonical path lineage over titles for metadata propagation."
            )

        return MetadataLineageReport(
            status=status,
            classification=classification,
            databases=tuple(databases),
            table_profiles=tuple(profiles),
            join_candidates=tuple(joins),
            lineage_paths=tuple(lineages),
            summary=summary,
            recommendations=tuple(recommendations),
        )
