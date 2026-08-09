from __future__ import annotations
from pathlib import Path
from typing import Any
from .contracts import CorpusAuthorityReport
from .discovery import candidate_databases
from .authority import profile_database, authority_candidates
from .pipeline import stage_profiles, lineage_edges, calculate_dropoff

class CorpusAuthorityAudit:
    def __init__(
        self,
        *,
        project_root: Path,
        runtime_catalog: Path,
        knowledge_root: Path,
    ) -> None:
        self.project_root = project_root
        self.runtime_catalog = runtime_catalog
        self.knowledge_root = knowledge_root

    def execute(self) -> CorpusAuthorityReport:
        paths = candidate_databases(
            self.project_root,
            self.runtime_catalog,
            self.knowledge_root,
        )
        profiles = [
            profile_database(path, self.runtime_catalog)
            for path in paths
        ]
        authorities = authority_candidates(profiles)
        authoritative = Path(authorities[0]["path"]) if authorities else self.runtime_catalog
        stages = stage_profiles(authoritative)
        edges = lineage_edges(authoritative, stages)
        dropoff = calculate_dropoff(stages)

        configured_wins = bool(
            authorities
            and Path(authorities[0]["path"]).resolve()
            == self.runtime_catalog.resolve()
        )
        incomplete_runtime = dropoff["materialization_rate"] < 0.50
        fts_complete = dropoff["fts_chunk_coverage"] >= 0.99

        if not authorities:
            classification = "NO_CATALOG_AUTHORITY_FOUND"
        elif not configured_wins:
            classification = "CONFIGURED_CATALOG_AUTHORITY_CONFLICT"
        elif incomplete_runtime:
            classification = "AUTHORITATIVE_CATALOG_RUNTIME_UNDERMATERIALIZED"
        elif not fts_complete:
            classification = "RUNTIME_CHUNKS_NOT_FULLY_INDEXED"
        else:
            classification = "CORPUS_AUTHORITY_AND_PIPELINE_HEALTHY"

        status = (
            "EXCELLENT"
            if classification == "CORPUS_AUTHORITY_AND_PIPELINE_HEALTHY"
            else "FAILED"
        )

        first_failed = next(
            (
                edge for edge in edges
                if edge["classification"] not in {"strong_lineage"}
            ),
            None,
        )

        comparisons = []
        if authorities:
            leader = authorities[0]
            for item in authorities[1:]:
                comparisons.append({
                    "authoritative_path": leader["path"],
                    "candidate_path": item["path"],
                    "authority_score_delta": leader["authority_score"] - item["authority_score"],
                    "size_delta_bytes": leader["size_bytes"] - item["size_bytes"],
                    "schema_object_delta": leader["schema_object_count"] - item["schema_object_count"],
                    "candidate_role": item["recommended_role"],
                })

        summary: dict[str, Any] = {
            "database_count": len(authorities),
            "authoritative_path": str(authoritative),
            "configured_runtime_catalog": str(self.runtime_catalog.resolve()),
            "configured_catalog_is_authoritative": configured_wins,
            "catalog_base": dropoff["catalog_base"],
            "runtime_documents": dropoff["runtime_documents"],
            "runtime_chunks": dropoff["runtime_chunks"],
            "runtime_fts_rows": dropoff["runtime_fts_rows"],
            "materialization_rate": dropoff["materialization_rate"],
            "fts_chunk_coverage": dropoff["fts_chunk_coverage"],
            "first_non_strong_edge": first_failed,
        }

        recommendations = []
        if not configured_wins:
            recommendations.append(
                "Resolve the catalog authority conflict before changing retrieval."
            )
        if incomplete_runtime:
            recommendations.append(
                "Audit the materializer candidate selection and campaign history; the authoritative catalog is severely undermaterialized."
            )
            recommendations.append(
                "Do not tune FTS ranking until runtime document coverage is expanded."
            )
        if fts_complete:
            recommendations.append(
                "FTS coverage of existing runtime chunks is healthy; focus on upstream materialization coverage."
            )
        if first_failed:
            recommendations.append(
                f"Inspect the first non-strong lineage edge: {first_failed['source_stage']} -> {first_failed['target_stage']}."
            )

        return CorpusAuthorityReport(
            status=status,
            classification=classification,
            authorities=tuple(authorities),
            database_comparisons=tuple(comparisons),
            pipeline_stages=tuple(stages),
            lineage_edges=tuple(edges),
            dropoff=dropoff,
            summary=summary,
            recommendations=tuple(recommendations),
        )
