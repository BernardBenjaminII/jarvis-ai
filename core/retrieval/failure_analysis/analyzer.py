from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

def as_map(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}

class CertificationFailureAnalyzer:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def analyze(self) -> dict[str, Any]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != "genesis_ix_a4_3_v1":
            raise ValueError(f"Unsupported schema: {data.get('schema_version')!r}")

        failed = [x for x in data.get("checks", []) if str(x.get("status")).upper() == "FAIL"]
        analyses = [self._classify(item, data) for item in failed]
        counts = Counter(x["classification"] for x in analyses)
        blocking = sum(bool(x["blocking"]) for x in analyses)

        return {
            "schema_version": "genesis_ix_a4_3a_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_certification": str(self.path),
            "source_status": data.get("status", "UNKNOWN"),
            "failed_check_count": len(failed),
            "status": "EXCELLENT" if not failed else "ANALYZED",
            "analyses": analyses,
            "summary": {
                "classification_counts": dict(sorted(counts.items())),
                "blocking_failures": blocking,
                "non_blocking_failures": len(analyses) - blocking,
                "recommended_next_action": self._next_action(analyses),
            },
        }

    def _classify(self, failure: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        code = str(failure.get("code") or "UNKNOWN")
        label = str(failure.get("label") or code)
        detail = str(failure.get("detail") or "")
        expected = failure.get("expected")
        actual = failure.get("actual")

        known = as_map(data.get("known_trace"))
        gap = as_map(data.get("gap_trace"))
        runtime = as_map(data.get("runtime_snapshot"))

        if code in {"KNOWN-EVIDENCE", "KNOWN-STATUS", "KNOWN-SOURCE"}:
            query = str(known.get("query") or "")
            prompt = str(known.get("prompt") or "")
            grounding = as_map(known.get("grounding"))
            metadata = as_map(known.get("metadata"))
            status = grounding.get("status") or metadata.get("grounding_status")
            count = grounding.get("evidence_count") or metadata.get("evidence_count") or 0
            has_grounding = "JARVIS KNOWLEDGE GROUNDING:" in prompt
            has_retrieved = "Retrieved catalog evidence:" in prompt

            if query.casefold() in {"sha256","metadata","document","file_path","confidence"}:
                return self._result(
                    code, label, "DATA_QUALITY", 0.97, False,
                    f"The automatically selected known query {query!r} is metadata-like rather than semantic.",
                    [
                        f"Known query: {query!r}",
                        f"Grounding status: {status!r}",
                        f"Evidence count: {count!r}",
                        f"Grounding marker: {has_grounding}",
                        f"Retrieved marker: {has_retrieved}",
                    ],
                    "Replace token-only query discovery with phrase selection from subject, title, or runtime chunk text, and reject metadata vocabulary.",
                    "certification query selection",
                )

            if has_grounding and has_retrieved:
                return self._result(
                    code, label, "METADATA_MISMATCH", 0.92, False,
                    "The prompt contains retrieved evidence, but the certifier did not find the expected structured metadata fields.",
                    [f"Status field: {status!r}", f"Evidence count: {count!r}"],
                    "Normalize the grounding metadata contract or update the certifier's nested lookup.",
                    "certification metadata adapter",
                )

            if has_grounding:
                return self._result(
                    code, label, "DATA_QUALITY", 0.89, False,
                    "The retrieval path executed, but the selected known query did not produce usable evidence.",
                    [f"Known query: {query!r}", f"Status: {status!r}", f"Evidence count: {count!r}"],
                    "Select a stronger known query from populated runtime chunks before changing retrieval.",
                    "certification fixture selection",
                )

            return self._result(
                code, label, "RUNTIME_BUG", 0.91, True,
                "Known-query evidence did not reach the grounded synthesis prompt.",
                [f"Expected: {expected!r}", f"Actual: {actual!r}", detail],
                "Trace search_catalog through GroundingResult.synthesis_input and repair the first missing edge.",
                "runtime retrieval-to-grounding path",
            )

        if code.startswith("GAP-"):
            prompt = str(gap.get("prompt") or "")
            grounding = as_map(gap.get("grounding"))
            metadata = as_map(gap.get("metadata"))
            status = grounding.get("status") or metadata.get("grounding_status")
            count = grounding.get("gap_count") or metadata.get("gap_count") or 0

            if "Knowledge gaps:" in prompt or "No catalog evidence was retrieved." in prompt:
                return self._result(
                    code, label, "METADATA_MISMATCH", 0.94, False,
                    "The prompt explicitly contains gap handling, but the certifier did not resolve the structured gap fields.",
                    [f"Status: {status!r}", f"Gap count: {count!r}"],
                    "Normalize KnowledgeGap serialization or update the certifier's nested metadata lookup.",
                    "gap metadata adapter",
                )

            return self._result(
                code, label, "RUNTIME_BUG", 0.93, True,
                "Unknown material did not produce an explicit KnowledgeGap.",
                [f"Status: {status!r}", f"Gap count: {count!r}", detail],
                "Repair CatalogGroundingService gap creation and prompt propagation.",
                "runtime gap handling",
            )

        if code.startswith("RUNTIME-"):
            return self._result(
                code, label, "RUNTIME_BUG", 0.99, True,
                "A required live runtime object or dependency is missing or noncanonical.",
                [f"Expected: {expected!r}", f"Actual: {actual!r}", f"Runtime keys: {sorted(runtime)}"],
                "Restore canonical dependency injection and rerun Pack 3A.",
                "runtime dependency injection",
            )

        if code.startswith("SOURCE-"):
            return self._result(
                code, label, "RUNTIME_BUG", 0.99, True,
                "A required source-level execution contract is absent.",
                [f"Expected: {expected!r}", f"Actual: {actual!r}", detail],
                "Restore the missing source contract and rerun IX-A4.3.",
                "canonical source implementation",
            )

        return self._result(
            code, label, "UNKNOWN", 0.35, True,
            "No deterministic analyzer rule covers this check.",
            [f"Expected: {expected!r}", f"Actual: {actual!r}", detail],
            "Inspect the failed check and corresponding trace manually.",
            "manual diagnosis",
        )

    @staticmethod
    def _result(code, label, classification, confidence, blocking, reason, evidence, repair, scope):
        return {
            "check_code": code,
            "label": label,
            "classification": classification,
            "confidence": confidence,
            "blocking": blocking,
            "reason": reason,
            "evidence": list(evidence),
            "recommended_repair": repair,
            "repair_scope": scope,
        }

    @staticmethod
    def _next_action(analyses):
        if not analyses:
            return "No repair required."
        if any(x["blocking"] for x in analyses):
            return "Repair blocking runtime failures before changing certification thresholds."
        classes = {x["classification"] for x in analyses}
        if classes <= {"DATA_QUALITY","CERTIFICATION_BUG","METADATA_MISMATCH"}:
            return "Repair the certification query selector and metadata adapter; do not modify the retrieval runtime."
        return "Apply the smallest scoped repair supported by the evidence."
