from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from core.knowledge_catalog.search import search_catalog
from core.knowledge_catalog.qualified_search import (
    get_last_qualification_result,
    get_last_qualification_trace,
    search_qualified_catalog,
)

from dev.knowledge_audit.benchmark import canonical_probe_terms

from .contracts import (
    ProbeForensicResult,
    QualificationForensicReport,
)
from .extract import candidate_record


class QualificationRecallAnalyzer:
    def __init__(
        self,
        *,
        database_path: Path,
        limit: int = 10,
    ) -> None:
        self.database_path = database_path
        self.limit = limit

    def execute(self) -> QualificationForensicReport:
        probe_results: list[ProbeForensicResult] = []
        global_reasons: Counter[str] = Counter()

        for probe in canonical_probe_terms():
            raw_rows = list(
                search_catalog(
                    probe.query,
                    db_path=self.database_path,
                    limit=self.limit,
                )
            )
            qualified_rows = list(
                search_qualified_catalog(
                    probe.query,
                    db_path=self.database_path,
                    limit=self.limit,
                )
            )

            trace = get_last_qualification_trace() or {}
            result = get_last_qualification_result()

            threshold = None
            if isinstance(trace, dict):
                threshold = trace.get("threshold")

            if threshold is None and result is not None:
                threshold = getattr(result, "threshold", None)

            diagnostics = []
            if isinstance(trace, dict):
                diagnostics = list(trace.get("diagnostics") or [])

            source_rows = diagnostics or qualified_rows or raw_rows
            candidates = tuple(
                candidate_record(
                    row,
                    raw_rank=index,
                    threshold=threshold,
                )
                for index, row in enumerate(
                    source_rows,
                    start=1,
                )
            )

            reasons = Counter(
                item.rejection_reason
                for item in candidates
                if item.rejection_reason
            )
            global_reasons.update(reasons)

            dominant = (
                reasons.most_common(1)[0][0]
                if reasons
                else None
            )

            recommendations = self._probe_recommendations(
                raw_count=len(raw_rows),
                qualified_count=len(qualified_rows),
                dominant_failure=dominant,
            )

            probe_results.append(
                ProbeForensicResult(
                    probe_id=probe.probe_id,
                    query=probe.query,
                    expected=probe.expected,
                    raw_count=len(raw_rows),
                    qualified_count=len(qualified_rows),
                    candidates=candidates,
                    dominant_failure=dominant,
                    recommendations=recommendations,
                )
            )

        known = [
            item
            for item in probe_results
            if item.expected == "known"
        ]
        raw_hits = sum(item.raw_count > 0 for item in known)
        qualified_hits = sum(
            item.qualified_count > 0
            for item in known
        )

        summary = {
            "known_probe_count": len(known),
            "known_raw_hits": raw_hits,
            "known_qualified_hits": qualified_hits,
            "known_raw_recall": (
                0.0 if not known else raw_hits / len(known)
            ),
            "known_qualified_recall": (
                0.0
                if not known
                else qualified_hits / len(known)
            ),
            "rejection_reasons": dict(
                sorted(global_reasons.items())
            ),
            "top_failure": (
                global_reasons.most_common(1)[0][0]
                if global_reasons
                else None
            ),
        }

        classification = self._classification(summary)
        status = (
            "EXCELLENT"
            if classification
            == "QUALIFICATION_RECALL_OPERATIONAL"
            else "FAILED"
        )

        return QualificationForensicReport(
            status=status,
            classification=classification,
            probes=tuple(probe_results),
            summary=summary,
            recommendations=self._global_recommendations(
                summary
            ),
        )

    @staticmethod
    def _classification(
        summary: dict[str, Any],
    ) -> str:
        raw = float(summary["known_raw_recall"])
        qualified = float(summary["known_qualified_recall"])

        if raw == 0.0:
            return "RETRIEVAL_FAILURE_PRECEDES_QUALIFICATION"

        if qualified == 0.0:
            return "QUALIFICATION_REJECTS_ALL_KNOWN_PROBES"

        if qualified < 0.5:
            return "QUALIFICATION_RECALL_CRITICAL"

        if qualified < 0.8:
            return "QUALIFICATION_RECALL_DEGRADED"

        return "QUALIFICATION_RECALL_OPERATIONAL"

    @staticmethod
    def _probe_recommendations(
        *,
        raw_count: int,
        qualified_count: int,
        dominant_failure: str | None,
    ) -> tuple[str, ...]:
        if raw_count == 0:
            return (
                "Repair retrieval before tuning qualification.",
            )

        if qualified_count > 0:
            return (
                "Preserve the accepted evidence path as regression coverage.",
            )

        mapping = {
            "LEXICAL": (
                "Inspect token overlap and technical identifier normalization.",
                "Compare title, subject, and excerpt lexical coverage.",
            ),
            "PHRASE": (
                "Inspect exact-phrase weighting and punctuation normalization.",
            ),
            "SUBJECT": (
                "Inspect subject aliases and domain metadata quality.",
            ),
            "CONFIDENCE": (
                "Inspect retrieval-score normalization and confidence weighting.",
            ),
            "FINAL_THRESHOLD": (
                "Measure score margins before changing the acceptance threshold.",
            ),
            "UNKNOWN": (
                "Capture complete qualification diagnostics for this candidate.",
            ),
        }

        return tuple(
            mapping.get(
                dominant_failure or "UNKNOWN",
                mapping["UNKNOWN"],
            )
        )

    @staticmethod
    def _global_recommendations(
        summary: dict[str, Any],
    ) -> tuple[str, ...]:
        top = summary.get("top_failure")
        recommendations = [
            "Do not change thresholds until score margins are reviewed.",
            "Promote every known probe into permanent regression coverage.",
        ]

        if top == "LEXICAL":
            recommendations.append(
                "Prioritize lexical coverage and token normalization."
            )
        elif top == "PHRASE":
            recommendations.append(
                "Prioritize phrase normalization and exact-match weighting."
            )
        elif top == "SUBJECT":
            recommendations.append(
                "Prioritize subject aliases and metadata normalization."
            )
        elif top == "CONFIDENCE":
            recommendations.append(
                "Prioritize retrieval-score and confidence calibration."
            )
        elif top == "FINAL_THRESHOLD":
            recommendations.append(
                "Model threshold sensitivity using observed score margins."
            )
        else:
            recommendations.append(
                "Expand qualification diagnostics before modifying behavior."
            )

        return tuple(recommendations)
