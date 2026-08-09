from __future__ import annotations
from collections import Counter
from pathlib import Path
from typing import Any

from .classifier import classify_record, SUPPORTED_DEFAULT
from .contracts import MaterializerEligibilityReport
from .source_inspection import inspect_materializer_source
from .sqlite_tools import open_ro, exists, rows, cols

class MaterializerEligibilityAudit:
    def __init__(
        self,
        *,
        project_root: Path,
        runtime_catalog: Path,
        inventory_catalog: Path,
        knowledge_root: Path,
    ) -> None:
        self.project_root = project_root
        self.runtime_catalog = runtime_catalog
        self.inventory_catalog = inventory_catalog
        self.knowledge_root = knowledge_root

    def _candidate_rows(self) -> tuple[list[dict[str, Any]], str]:
        runtime = open_ro(self.runtime_catalog)
        inventory = open_ro(self.inventory_catalog)
        try:
            if exists(runtime, "knowledge_classifications"):
                return rows(runtime, "knowledge_classifications"), (
                    f"{self.runtime_catalog}:knowledge_classifications"
                )
            for table in ("documents", "knowledge_index", "library_catalog"):
                if exists(inventory, table):
                    values = rows(inventory, table)
                    if values:
                        return values, f"{self.inventory_catalog}:{table}"
            return [], "none"
        finally:
            runtime.close()
            inventory.close()

    def execute(self) -> MaterializerEligibilityReport:
        implementation = inspect_materializer_source(self.project_root)
        supported = set(
            implementation["supported_extensions"] or SUPPORTED_DEFAULT
        )

        runtime = open_ro(self.runtime_catalog)
        inventory = open_ro(self.inventory_catalog)
        try:
            runtime_paths = set()
            if exists(runtime, "runtime_documents"):
                columns = cols(runtime, "runtime_documents")
                key = "file_path" if "file_path" in columns else None
                if key:
                    runtime_paths = {
                        str(r[key]) for r in rows(runtime, "runtime_documents")
                        if r.get(key)
                    }

            failed_paths = set()
            for table in ("materialization_failures", "failures", "inspections"):
                if exists(runtime, table):
                    for row in rows(runtime, table):
                        text = " ".join(str(v) for v in row.values())
                        if any(token in text.casefold() for token in ("fail", "error")):
                            for key in ("file_path", "document_path", "path", "source_path"):
                                if row.get(key):
                                    failed_paths.add(str(row[key]))

            duplicate_paths = set()
            for conn, table in (
                (runtime, "duplicates"),
                (inventory, "duplicates"),
            ):
                if exists(conn, table):
                    for row in rows(conn, table):
                        for key in ("file_path", "document_path", "path", "source_path"):
                            if row.get(key):
                                duplicate_paths.add(str(row[key]))

            candidates, candidate_source = self._candidate_rows()

            dispositions = [
                classify_record(
                    row,
                    knowledge_root=self.knowledge_root,
                    supported_extensions=supported,
                    runtime_paths=runtime_paths,
                    duplicate_paths=duplicate_paths,
                    failed_paths=failed_paths,
                    deferred_states={
                        "deferred", "quarantined", "rejected", "blocked",
                    },
                )
                for row in candidates
            ]

            counts = Counter(item["disposition"] for item in dispositions)
            eligible = counts.get("ELIGIBLE_NOT_SELECTED", 0)
            already = counts.get("ALREADY_MATERIALIZED", 0)
            failures = (
                counts.get("FAILED_MATERIALIZATION", 0)
                + counts.get("FAILED_EXTRACTION", 0)
            )
            total = len(dispositions)

            if total == 0:
                classification = "NO_MATERIALIZER_CANDIDATES_FOUND"
            elif eligible > already:
                classification = "ELIGIBLE_CORPUS_NOT_SELECTED"
            elif failures > already:
                classification = "MATERIALIZATION_FAILURES_DOMINATE"
            elif counts.get("UNSUPPORTED_MEDIA_TYPE", 0) > already:
                classification = "FORMAT_SUPPORT_LIMITS_MATERIALIZATION"
            else:
                classification = "MATERIALIZER_SELECTION_HEALTHY"

            status = (
                "EXCELLENT"
                if classification == "MATERIALIZER_SELECTION_HEALTHY"
                else "FAILED"
            )

            authority_map = {
                "inventory_metadata": str(self.inventory_catalog),
                "classification_and_runtime": str(self.runtime_catalog),
                "candidate_source": candidate_source,
                "physical_knowledge_root": str(self.knowledge_root),
                "runtime_documents_table": (
                    f"{self.runtime_catalog}:runtime_documents"
                ),
                "runtime_chunks_table": (
                    f"{self.runtime_catalog}:runtime_chunks"
                ),
                "runtime_fts_table": (
                    f"{self.runtime_catalog}:runtime_chunks_fts"
                ),
            }

            summary: dict[str, Any] = {
                "candidate_count": total,
                "runtime_document_count": len(runtime_paths),
                "supported_extensions": sorted(supported),
                "disposition_counts": dict(sorted(counts.items())),
                "eligible_not_selected": eligible,
                "already_materialized": already,
                "eligible_selection_gap": max(0, eligible - already),
                "selection_rate_among_eligible": (
                    0.0 if eligible + already == 0
                    else already / (eligible + already)
                ),
                "failure_count": failures,
                "missing_source_count": counts.get("MISSING_SOURCE_FILE", 0),
                "unsupported_count": counts.get("UNSUPPORTED_MEDIA_TYPE", 0),
                "container_count": counts.get("CONTAINER_OR_ARCHIVE", 0),
            }

            recommendations = []
            if eligible:
                recommendations.append(
                    "Repair or expand materializer candidate selection before changing retrieval ranking."
                )
                recommendations.append(
                    "Run a bounded materialization campaign against ELIGIBLE_NOT_SELECTED records."
                )
            if counts.get("UNSUPPORTED_MEDIA_TYPE", 0):
                recommendations.append(
                    "Add extractors only for high-volume unsupported formats proven valuable."
                )
            if counts.get("MISSING_SOURCE_FILE", 0):
                recommendations.append(
                    "Reconcile stale catalog paths before scheduling materialization."
                )
            recommendations.append(
                "Preserve split authority: inventory metadata and runtime retrieval have different canonical stores."
            )

            return MaterializerEligibilityReport(
                status=status,
                classification=classification,
                implementation=implementation,
                authority_map=authority_map,
                dispositions=tuple(dispositions),
                summary=summary,
                recommendations=tuple(recommendations),
            )
        finally:
            runtime.close()
            inventory.close()
