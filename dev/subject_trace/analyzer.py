from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

from .contracts import (
    CandidateSubjectTrace,
    ProbeSubjectTrace,
    SubjectTraceReport,
)
from .extract import (
    candidate_data,
    candidate_domain,
    candidate_subjects,
    mapping,
    number,
    score_component,
)
from .normalization import normalize_text, tokens
from .probes import SubjectProbe, canonical_subject_probes
from .provider import LiveSubjectTraceProvider
from .taxonomy import compare_subjects


class SubjectQualificationTrace:
    def __init__(
        self,
        *,
        database_path: Path,
        provider=None,
        probes: Iterable[SubjectProbe] | None = None,
        limit: int = 10,
    ) -> None:
        self.database_path = database_path
        self.provider = provider or LiveSubjectTraceProvider()
        self.probes = tuple(
            probes or canonical_subject_probes()
        )
        self.limit = limit

    def execute(self) -> SubjectTraceReport:
        probe_results = tuple(
            self._run_probe(probe)
            for probe in self.probes
        )

        diagnoses = Counter(
            candidate.diagnosis
            for probe in probe_results
            for candidate in probe.candidates
        )
        missing = sum(
            candidate.missing_metadata
            for probe in probe_results
            for candidate in probe.candidates
        )
        mismatches = sum(
            candidate.taxonomy_mismatch
            for probe in probe_results
            for candidate in probe.candidates
        )
        total_candidates = sum(
            len(probe.candidates)
            for probe in probe_results
        )
        zero_subject_scores = sum(
            candidate.subject_score == 0.0
            for probe in probe_results
            for candidate in probe.candidates
            if candidate.subject_score is not None
        )

        heatmap = {}

        for probe in probe_results:
            key = (
                probe.detected_subjects[0]
                if probe.detected_subjects
                else "undetected"
            )
            bucket = heatmap.setdefault(
                key,
                {
                    "candidates": 0,
                    "exact_matches": 0,
                    "alias_matches": 0,
                    "missing_metadata": 0,
                    "taxonomy_mismatches": 0,
                    "accepted": 0,
                    "subject_score_total": 0.0,
                    "subject_score_count": 0,
                },
            )

            for candidate in probe.candidates:
                bucket["candidates"] += 1
                bucket["exact_matches"] += len(
                    candidate.exact_matches
                )
                bucket["alias_matches"] += len(
                    candidate.alias_matches
                )
                bucket["missing_metadata"] += int(
                    candidate.missing_metadata
                )
                bucket["taxonomy_mismatches"] += int(
                    candidate.taxonomy_mismatch
                )
                bucket["accepted"] += int(
                    candidate.decision.casefold().startswith(
                        "accept"
                    )
                )

                if candidate.subject_score is not None:
                    bucket["subject_score_total"] += (
                        candidate.subject_score
                    )
                    bucket["subject_score_count"] += 1

        for bucket in heatmap.values():
            count = bucket["subject_score_count"]
            bucket["average_subject_score"] = (
                0.0
                if count == 0
                else bucket["subject_score_total"] / count
            )
            candidates = bucket["candidates"]
            bucket["acceptance_rate"] = (
                0.0
                if candidates == 0
                else bucket["accepted"] / candidates
            )
            del bucket["subject_score_total"]
            del bucket["subject_score_count"]

        summary = {
            "probe_count": len(probe_results),
            "candidate_count": total_candidates,
            "missing_subject_metadata": missing,
            "taxonomy_mismatches": mismatches,
            "zero_subject_scores": zero_subject_scores,
            "diagnoses": dict(sorted(diagnoses.items())),
            "top_diagnosis": (
                diagnoses.most_common(1)[0][0]
                if diagnoses
                else None
            ),
            "heatmap": heatmap,
        }

        classification = self._classify(summary)
        status = (
            "EXCELLENT"
            if classification
            == "SUBJECT_QUALIFICATION_TRACE_HEALTHY"
            else "FAILED"
        )

        return SubjectTraceReport(
            status=status,
            classification=classification,
            probes=probe_results,
            summary=summary,
            recommendations=self._recommendations(
                summary
            ),
        )

    def _run_probe(
        self,
        probe: SubjectProbe,
    ) -> ProbeSubjectTrace:
        raw_rows = self.provider.raw_search(
            probe.query,
            database_path=self.database_path,
            limit=self.limit,
        )
        qualified_rows = self.provider.qualified_search(
            probe.query,
            database_path=self.database_path,
            limit=self.limit,
        )

        trace = mapping(self.provider.last_trace())
        result = mapping(self.provider.last_result())

        diagnostics = trace.get("diagnostics")
        if not isinstance(diagnostics, (list, tuple)):
            diagnostics = result.get("diagnostics")
        if not isinstance(diagnostics, (list, tuple)):
            diagnostics = ()

        threshold = number(trace.get("threshold"))
        if threshold is None:
            threshold = number(result.get("threshold"))

        source_rows = list(diagnostics) or list(qualified_rows) or list(raw_rows)

        normalized_query = normalize_text(probe.query)
        query_tokens = tokens(probe.query)
        detected_subjects = probe.expected_subjects

        candidates = tuple(
            self._candidate_trace(
                row,
                index=index,
                query_subjects=detected_subjects,
                threshold=threshold,
            )
            for index, row in enumerate(
                source_rows,
                start=1,
            )
        )

        diagnoses = Counter(
            item.diagnosis
            for item in candidates
        )

        return ProbeSubjectTrace(
            probe_id=probe.probe_id,
            query=probe.query,
            expected_subjects=probe.expected_subjects,
            normalized_query=normalized_query,
            query_tokens=query_tokens,
            detected_subjects=detected_subjects,
            raw_count=len(raw_rows),
            qualified_count=len(qualified_rows),
            candidates=candidates,
            dominant_diagnosis=(
                diagnoses.most_common(1)[0][0]
                if diagnoses
                else None
            ),
        )

    @staticmethod
    def _candidate_trace(
        value,
        *,
        index: int,
        query_subjects: tuple[str, ...],
        threshold: float | None,
    ) -> CandidateSubjectTrace:
        data = candidate_data(value)
        subjects = candidate_subjects(data)
        domain = candidate_domain(data)
        match = compare_subjects(
            query_subjects,
            subjects,
        )

        subject_score = score_component(
            data,
            "subject",
            "subject_score",
        )
        final_score = score_component(
            data,
            "final",
            "final_score",
            "qualification_score",
        )
        decision = str(
            data.get("qualification_decision")
            or data.get("decision")
            or data.get("status")
            or "UNKNOWN"
        )
        missing_metadata = not subjects
        taxonomy_mismatch = (
            bool(subjects)
            and not match.exact_matches
            and not match.alias_matches
        )

        if missing_metadata:
            diagnosis = "MISSING_SUBJECT_METADATA"
        elif taxonomy_mismatch:
            diagnosis = "TAXONOMY_OR_ALIAS_MISMATCH"
        elif (
            subject_score == 0.0
            and (
                match.exact_matches
                or match.alias_matches
            )
        ):
            diagnosis = "SUBJECT_SCORING_DEFECT"
        elif (
            subject_score is None
            and (
                match.exact_matches
                or match.alias_matches
            )
        ):
            diagnosis = "SUBJECT_SCORE_NOT_EXPOSED"
        elif decision.casefold().startswith("accept"):
            diagnosis = "SUBJECT_MATCH_ACCEPTED"
        else:
            diagnosis = "SUBJECT_MATCH_PARTIAL_OR_REJECTED"

        return CandidateSubjectTrace(
            candidate_id=str(
                data.get("source_id")
                or data.get("chunk_id")
                or data.get("document_id")
                or data.get("id")
                or f"candidate-{index}"
            ),
            title=str(
                data.get("title")
                or data.get("document_title")
                or data.get("source_id")
                or f"candidate-{index}"
            ),
            source_path=str(
                data.get("source_path")
                or data.get("file_path")
                or data.get("path")
                or ""
            ),
            query_subjects=tuple(
                query_subjects
            ),
            candidate_subjects=subjects,
            candidate_domain=domain,
            aliases_considered=match.aliases_considered,
            exact_matches=match.exact_matches,
            alias_matches=match.alias_matches,
            overlap_score=match.overlap_score,
            subject_score=subject_score,
            final_score=final_score,
            threshold=threshold,
            decision=decision,
            diagnosis=diagnosis,
            missing_metadata=missing_metadata,
            taxonomy_mismatch=taxonomy_mismatch,
            metadata={
                "available_keys": sorted(
                    str(key)
                    for key in data
                ),
            },
        )

    @staticmethod
    def _classify(
        summary: dict,
    ) -> str:
        candidates = summary["candidate_count"]

        if candidates == 0:
            return "NO_SUBJECT_CANDIDATES_OBSERVED"

        missing_rate = (
            summary["missing_subject_metadata"]
            / candidates
        )
        mismatch_rate = (
            summary["taxonomy_mismatches"]
            / candidates
        )

        if missing_rate >= 0.5:
            return "SUBJECT_METADATA_MISSING_CRITICAL"
        if mismatch_rate >= 0.5:
            return "SUBJECT_TAXONOMY_MISMATCH_CRITICAL"
        if summary["zero_subject_scores"] >= candidates * 0.5:
            return "SUBJECT_SCORING_ZERO_COLLAPSE"

        return "SUBJECT_QUALIFICATION_TRACE_HEALTHY"

    @staticmethod
    def _recommendations(
        summary: dict,
    ) -> tuple[str, ...]:
        top = summary.get("top_diagnosis")

        mapping = {
            "MISSING_SUBJECT_METADATA": (
                "Run a catalog subject-metadata backfill before changing qualification weights.",
                "Measure metadata coverage by table and source collection.",
            ),
            "TAXONOMY_OR_ALIAS_MISMATCH": (
                "Audit stored subject vocabulary against the active taxonomy.",
                "Add deterministic aliases only after recording unmatched labels.",
            ),
            "SUBJECT_SCORING_DEFECT": (
                "Inspect the subject scoring function with exact and alias matches.",
                "Do not lower the final threshold to conceal a zero subject score.",
            ),
            "SUBJECT_SCORE_NOT_EXPOSED": (
                "Expose the canonical subject component in qualification diagnostics.",
            ),
        }

        return tuple(
            mapping.get(
                top,
                (
                    "Review the subject heatmap and candidate-level traces.",
                    "Apply only the repair supported by the dominant diagnosis.",
                ),
            )
        )
