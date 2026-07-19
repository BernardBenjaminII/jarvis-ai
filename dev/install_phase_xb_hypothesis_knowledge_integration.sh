#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${1:-$(pwd)}"
cd "$PROJECT_ROOT"

if [[ ! -d .git ]]; then
    echo "ERROR: Run from the JARVIS repository root or pass its path."
    exit 1
fi
if [[ ! -f core/reasoning/service.py ]] || [[ ! -f tests/test_phase_x_reasoning_foundation.py ]]; then
    echo "ERROR: Phase X Reasoning Engine foundation is not installed."
    exit 1
fi

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE X-B HYPOTHESIS + KNOWLEDGE INTEGRATION"
echo "======================================================================"
mkdir -p core/reasoning tests dev/verification docs/architecture

cat > core/reasoning/knowledge.py <<'JARVIS_XB_CORE_REASONING_KNOWLEDGE_PY'
"""Normalize Knowledge Engine results into reasoning evidence."""

from __future__ import annotations
import hashlib
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any
from core.reasoning.enums import EvidenceKind, EvidenceStance
from core.reasoning.models import EvidenceItem


class KnowledgeEvidenceAdapterError(ValueError):
    """Raised when knowledge output cannot be adapted."""


@dataclass(frozen=True, slots=True)
class AdaptedEvidenceBatch:
    query: str
    evidence: tuple[EvidenceItem, ...]
    rejected_count: int
    source_count: int


def _get(value: Any, names: tuple[str, ...], default: Any = None) -> Any:
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default


def _probability(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if 1.0 < number <= 100.0:
        number /= 100.0
    return max(0.0, min(1.0, number))


def _quality(result: Any) -> float:
    value = _get(result, ("quality_score", "quality"), 1.0)
    if hasattr(value, "score"):
        value = value.score
    elif isinstance(value, Mapping):
        value = value.get("score", 1.0)
    return _probability(value, 1.0)


def _ranking(result: Any) -> dict[str, Any]:
    value = _get(result, ("ranking", "breakdown"), {})
    if hasattr(value, "as_dict"):
        return dict(value.as_dict())
    return dict(value) if isinstance(value, Mapping) else {}


def _evidence_id(source: str, chunk: int | None, text: str) -> str:
    digest = hashlib.sha256(
        f"{source}\x1f{chunk}\x1f{text}".encode("utf-8")
    ).hexdigest()[:20]
    return f"knowledge_{digest}"


def _proposition(text: str) -> str:
    for candidate in re.split(r"(?<=[.!?])\s+", text):
        candidate = " ".join(candidate.split())
        if len(candidate) >= 12:
            return candidate[:500]
    return text[:500]


class KnowledgeEvidenceAdapter:
    """Accept production SearchResult objects or ranked dictionaries."""

    def adapt(
        self,
        query: str,
        results: Iterable[Any],
        *,
        stance: EvidenceStance = EvidenceStance.SUPPORTS,
        minimum_text_length: int = 12,
    ) -> AdaptedEvidenceBatch:
        query = " ".join(query.split())
        if not query:
            raise KnowledgeEvidenceAdapterError("query cannot be empty")

        evidence: list[EvidenceItem] = []
        rejected = 0
        sources: set[str] = set()

        for result in results:
            text = " ".join(str(_get(
                result, ("text", "content", "text_preview", "snippet"), ""
            ) or "").split())
            source = str(_get(
                result, ("source", "file_path", "path", "document_path"), ""
            ) or "").strip()
            raw_chunk = _get(
                result, ("chunk_index", "chunk_number", "chunk_id"), None
            )
            try:
                chunk = int(raw_chunk) if raw_chunk not in (None, "") else None
            except (TypeError, ValueError):
                chunk = None

            if len(text) < minimum_text_length or not source:
                rejected += 1
                continue

            score = _probability(_get(
                result, ("ranking_score", "score", "semantic_score"), 0.5
            ), 0.5)
            quality = _quality(result)
            sources.add(source)
            evidence.append(EvidenceItem(
                evidence_id=_evidence_id(source, chunk, text),
                proposition=_proposition(text),
                stance=stance,
                source_ref=(
                    f"{source}#chunk={chunk}" if chunk is not None else source
                ),
                kind=EvidenceKind.DOCUMENT,
                reliability=quality,
                confidence=score,
                metadata={
                    "query": query,
                    "source": source,
                    "chunk_index": chunk,
                    "retrieval_score": score,
                    "quality_score": quality,
                    "ranking": _ranking(result),
                    "text": text,
                },
            ))

        evidence.sort(key=lambda item: item.evidence_id)
        return AdaptedEvidenceBatch(
            query=query,
            evidence=tuple(evidence),
            rejected_count=rejected,
            source_count=len(sources),
        )
JARVIS_XB_CORE_REASONING_KNOWLEDGE_PY

cat > core/reasoning/generation.py <<'JARVIS_XB_CORE_REASONING_GENERATION_PY'
"""Conservative deterministic hypothesis generation."""

from __future__ import annotations
import hashlib
from dataclasses import dataclass
from core.reasoning.enums import EvidenceStance
from core.reasoning.models import EvidenceItem, Hypothesis


@dataclass(frozen=True, slots=True)
class HypothesisGenerationResult:
    goal: str
    hypotheses: tuple[Hypothesis, ...]
    evidence_count: int
    strategy: str


def _identifier(prefix: str, statement: str) -> str:
    digest = hashlib.sha256(statement.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


class DeterministicHypothesisGenerator:
    """Generate bounded competing hypotheses without inventing facts."""

    strategy_name = "deterministic_evidence_synthesis_v1"

    def generate(
        self,
        goal: str,
        evidence: tuple[EvidenceItem, ...],
        *,
        max_evidence: int = 8,
    ) -> HypothesisGenerationResult:
        goal = " ".join(goal.split())
        if not goal:
            raise ValueError("goal cannot be empty")

        ranked = sorted(
            evidence,
            key=lambda item: (-item.weight, item.evidence_id),
        )[:max_evidence]
        supporting = tuple(
            item.evidence_id for item in ranked
            if item.stance is EvidenceStance.SUPPORTS
        )
        contradicting = tuple(
            item.evidence_id for item in ranked
            if item.stance is EvidenceStance.CONTRADICTS
        )

        hypotheses: list[Hypothesis] = []
        if supporting:
            statement = f"Available knowledge supports pursuing the goal: {goal}"
            hypotheses.append(Hypothesis(
                hypothesis_id=_identifier("hypothesis_supported", statement),
                statement=statement,
                supporting_evidence_ids=supporting,
                contradicting_evidence_ids=contradicting,
                assumptions=(
                    "Retrieved evidence is sufficiently representative",
                    "Knowledge source quality scores are trustworthy",
                ),
                proposed_actions=(
                    "Preserve evidence and provenance",
                    "Convert the conclusion into planning inputs",
                ),
                metadata={
                    "generator": self.strategy_name,
                    "kind": "evidence_synthesis",
                },
            ))

        statement = f"Available knowledge is insufficient to justify the goal: {goal}"
        hypotheses.append(Hypothesis(
            hypothesis_id=_identifier("hypothesis_insufficient", statement),
            statement=statement,
            supporting_evidence_ids=contradicting,
            contradicting_evidence_ids=supporting,
            proposed_actions=(
                "Request additional evidence",
                "Refine or broaden the knowledge search",
            ),
            metadata={
                "generator": self.strategy_name,
                "kind": "insufficiency",
            },
        ))

        if supporting and contradicting:
            statement = f"Knowledge contains unresolved conflict concerning: {goal}"
            hypotheses.append(Hypothesis(
                hypothesis_id=_identifier("hypothesis_conflict", statement),
                statement=statement,
                supporting_evidence_ids=contradicting,
                contradicting_evidence_ids=supporting,
                assumptions=("Conflicting evidence refers to the same context",),
                proposed_actions=(
                    "Investigate source and context differences",
                    "Do not authorize irreversible action",
                ),
                metadata={
                    "generator": self.strategy_name,
                    "kind": "conflict",
                },
            ))

        hypotheses.sort(key=lambda item: item.hypothesis_id)
        return HypothesisGenerationResult(
            goal=goal,
            hypotheses=tuple(hypotheses),
            evidence_count=len(evidence),
            strategy=self.strategy_name,
        )
JARVIS_XB_CORE_REASONING_GENERATION_PY

cat > core/reasoning/pipeline.py <<'JARVIS_XB_CORE_REASONING_PIPELINE_PY'
"""Knowledge-integrated reasoning pipeline."""

from __future__ import annotations
import hashlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any
from core.reasoning.generation import (
    DeterministicHypothesisGenerator,
    HypothesisGenerationResult,
)
from core.reasoning.knowledge import AdaptedEvidenceBatch, KnowledgeEvidenceAdapter
from core.reasoning.models import ReasoningRequest, ReasoningResult
from core.reasoning.service import ReasoningEngine

KnowledgeSearch = Callable[[str, int], Iterable[Any]]


@dataclass(frozen=True, slots=True)
class KnowledgeReasoningOutcome:
    evidence_batch: AdaptedEvidenceBatch
    generation: HypothesisGenerationResult
    reasoning: ReasoningResult


def _request_id(goal: str, query: str) -> str:
    digest = hashlib.sha256(
        f"{goal}\x1f{query}".encode("utf-8")
    ).hexdigest()[:16]
    return f"knowledge_reasoning_{digest}"


class KnowledgeReasoningPipeline:
    """Join an injected Knowledge search callable to reasoning."""

    def __init__(
        self,
        search: KnowledgeSearch,
        *,
        adapter: KnowledgeEvidenceAdapter | None = None,
        generator: DeterministicHypothesisGenerator | None = None,
        engine: ReasoningEngine | None = None,
    ) -> None:
        self._search = search
        self._adapter = adapter or KnowledgeEvidenceAdapter()
        self._generator = generator or DeterministicHypothesisGenerator()
        self._engine = engine or ReasoningEngine()

    def reason(
        self,
        *,
        goal: str,
        query: str | None = None,
        limit: int = 8,
        constraints: tuple[str, ...] = (),
        context: dict[str, Any] | None = None,
    ) -> KnowledgeReasoningOutcome:
        search_query = " ".join((query or goal).split())
        raw_results = tuple(self._search(search_query, limit))
        batch = self._adapter.adapt(search_query, raw_results)
        generation = self._generator.generate(goal, batch.evidence)
        request = ReasoningRequest(
            request_id=_request_id(goal, search_query),
            goal=goal,
            evidence=batch.evidence,
            hypotheses=generation.hypotheses,
            constraints=constraints,
            context={
                **(context or {}),
                "knowledge_query": search_query,
                "knowledge_result_count": len(raw_results),
                "adapted_evidence_count": len(batch.evidence),
                "rejected_result_count": batch.rejected_count,
                "hypothesis_generation_strategy": generation.strategy,
            },
        )
        return KnowledgeReasoningOutcome(
            evidence_batch=batch,
            generation=generation,
            reasoning=self._engine.reason(request),
        )
JARVIS_XB_CORE_REASONING_PIPELINE_PY

cat > core/reasoning/__init__.py <<'JARVIS_XB_CORE_REASONING___INIT___PY'
"""Public interface for the JARVIS Reasoning Engine."""

from core.reasoning.enums import (
    EvidenceKind,
    EvidenceStance,
    HypothesisDisposition,
    ReasoningStatus,
)
from core.reasoning.errors import (
    DuplicateReasoningElementError,
    InvalidReasoningRequestError,
    ReasoningError,
    UnknownEvidenceReferenceError,
)
from core.reasoning.generation import (
    DeterministicHypothesisGenerator,
    HypothesisGenerationResult,
)
from core.reasoning.knowledge import (
    AdaptedEvidenceBatch,
    KnowledgeEvidenceAdapter,
    KnowledgeEvidenceAdapterError,
)
from core.reasoning.models import (
    EvidenceItem,
    Hypothesis,
    HypothesisAssessment,
    PlanningRecommendation,
    ReasoningRequest,
    ReasoningResult,
    ReasoningTraceStep,
    canonical_fingerprint,
)
from core.reasoning.pipeline import (
    KnowledgeReasoningOutcome,
    KnowledgeReasoningPipeline,
    KnowledgeSearch,
)
from core.reasoning.service import ENGINE_VERSION, ReasoningEngine

__all__ = [
    "ENGINE_VERSION",
    "AdaptedEvidenceBatch",
    "DeterministicHypothesisGenerator",
    "DuplicateReasoningElementError",
    "EvidenceItem",
    "EvidenceKind",
    "EvidenceStance",
    "Hypothesis",
    "HypothesisAssessment",
    "HypothesisDisposition",
    "HypothesisGenerationResult",
    "InvalidReasoningRequestError",
    "KnowledgeEvidenceAdapter",
    "KnowledgeEvidenceAdapterError",
    "KnowledgeReasoningOutcome",
    "KnowledgeReasoningPipeline",
    "KnowledgeSearch",
    "PlanningRecommendation",
    "ReasoningEngine",
    "ReasoningError",
    "ReasoningRequest",
    "ReasoningResult",
    "ReasoningStatus",
    "ReasoningTraceStep",
    "UnknownEvidenceReferenceError",
    "canonical_fingerprint",
]
JARVIS_XB_CORE_REASONING___INIT___PY

cat > tests/test_phase_xb_hypothesis_knowledge.py <<'JARVIS_XB_TESTS_TEST_PHASE_XB_HYPOTHESIS_KNOWLEDGE_PY'
"""Tests for Phase X-B."""

from __future__ import annotations
import unittest
from dataclasses import dataclass
from core.reasoning import (
    DeterministicHypothesisGenerator,
    EvidenceStance,
    KnowledgeEvidenceAdapter,
    KnowledgeReasoningPipeline,
    ReasoningStatus,
)


@dataclass
class QualityReport:
    score: int


@dataclass
class SearchResultFixture:
    score: float
    file_path: str
    chunk_index: int
    text: str
    quality: QualityReport


def fixtures() -> tuple[SearchResultFixture, ...]:
    return (
        SearchResultFixture(
            0.92,
            "/docs/reference/reasoning.pdf",
            3,
            "Structured evidence makes reasoning auditable and reproducible.",
            QualityReport(96),
        ),
        SearchResultFixture(
            0.84,
            "/docs/reference/planning.pdf",
            7,
            "Reasoning should preserve assumptions, constraints, risks, and provenance.",
            QualityReport(91),
        ),
    )


class AdapterTests(unittest.TestCase):
    def test_production_shape(self) -> None:
        batch = KnowledgeEvidenceAdapter().adapt("reasoning", fixtures())
        self.assertEqual(len(batch.evidence), 2)
        self.assertEqual(batch.source_count, 2)
        self.assertEqual(batch.rejected_count, 0)
        self.assertEqual(batch.evidence[0].stance, EvidenceStance.SUPPORTS)

    def test_ranked_mapping_shape(self) -> None:
        batch = KnowledgeEvidenceAdapter().adapt("ranking", ({
            "source": "/docs/ranked.pdf",
            "chunk_index": 4,
            "text": "Ranked knowledge preserves an explainable score.",
            "ranking_score": 0.78,
            "quality": 94,
            "ranking": {"final_score": 0.78},
        },))
        item = batch.evidence[0]
        self.assertAlmostEqual(item.confidence, 0.78)
        self.assertAlmostEqual(item.reliability, 0.94)
        self.assertEqual(item.metadata["ranking"]["final_score"], 0.78)

    def test_rejects_unusable(self) -> None:
        batch = KnowledgeEvidenceAdapter().adapt("query", (
            {"text": "short", "source": "/docs/a"},
            {"text": "This result has no source path."},
        ))
        self.assertEqual(batch.evidence, ())
        self.assertEqual(batch.rejected_count, 2)


class GeneratorTests(unittest.TestCase):
    def test_competing_hypotheses(self) -> None:
        evidence = KnowledgeEvidenceAdapter().adapt("reasoning", fixtures()).evidence
        result = DeterministicHypothesisGenerator().generate(
            "Integrate knowledge with reasoning", evidence
        )
        self.assertEqual(len(result.hypotheses), 2)
        self.assertEqual(
            {item.metadata["kind"] for item in result.hypotheses},
            {"evidence_synthesis", "insufficiency"},
        )


class PipelineTests(unittest.TestCase):
    def test_complete_cycle(self) -> None:
        calls: list[tuple[str, int]] = []
        def search(query: str, limit: int):
            calls.append((query, limit))
            return fixtures()

        outcome = KnowledgeReasoningPipeline(search).reason(
            goal="Integrate knowledge with structured reasoning",
            limit=5,
            constraints=("Do not execute tools",),
        )
        self.assertEqual(
            calls, [("Integrate knowledge with structured reasoning", 5)]
        )
        self.assertEqual(outcome.reasoning.status, ReasoningStatus.COMPLETED)
        self.assertIsNotNone(outcome.reasoning.selected_hypothesis_id)
        self.assertIsNotNone(outcome.reasoning.planning_recommendation)

    def test_deterministic(self) -> None:
        pipeline = KnowledgeReasoningPipeline(lambda query, limit: fixtures())
        first = pipeline.reason(goal="Integrate knowledge")
        second = pipeline.reason(goal="Integrate knowledge")
        self.assertEqual(
            first.reasoning.fingerprint, second.reasoning.fingerprint
        )
        self.assertEqual(first.reasoning.to_dict(), second.reasoning.to_dict())


if __name__ == "__main__":
    unittest.main()
JARVIS_XB_TESTS_TEST_PHASE_XB_HYPOTHESIS_KNOWLEDGE_PY

cat > dev/verification/verify_phase_xb_hypothesis_knowledge.py <<'JARVIS_XB_DEV_VERIFICATION_VERIFY_PHASE_XB_HYPOTHESIS_KNOWLEDGE_PY'
#!/usr/bin/env python3
"""Structural verification for Phase X-B."""

from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "core/reasoning/knowledge.py",
    "core/reasoning/generation.py",
    "core/reasoning/pipeline.py",
    "tests/test_phase_xb_hypothesis_knowledge.py",
    "docs/architecture/reasoning_hypothesis_knowledge_integration.md",
)
FORBIDDEN = (
    "knowledge_engine.storage",
    "knowledge_engine.director",
    "knowledge_engine.search.service",
    "subprocess",
    "openai",
)

def main() -> int:
    failures: list[str] = []
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"Missing required file: {relative}")
            continue
        if path.suffix == ".py":
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError as exc:
                failures.append(f"Syntax error in {relative}: {exc}")
                continue
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(FORBIDDEN):
                            failures.append(
                                f"{relative} imports forbidden dependency {alias.name}"
                            )
                if module and module.startswith(FORBIDDEN):
                    failures.append(
                        f"{relative} imports forbidden dependency {module}"
                    )
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print("[PASS] Phase X-B structural boundaries are valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
JARVIS_XB_DEV_VERIFICATION_VERIFY_PHASE_XB_HYPOTHESIS_KNOWLEDGE_PY

cat > dev/verify_phase_xb.sh <<'JARVIS_XB_DEV_VERIFY_PHASE_XB_SH'
#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
LOG="/tmp/jarvis_phase_xb.log"
PASSED=0
FAILED=0
cd "$ROOT"

run_check() {
    local description="$1"
    shift
    if "$@" >"$LOG" 2>&1; then
        printf '[PASS] %s\n' "$description"
        PASSED=$((PASSED + 1))
    else
        printf '[FAIL] %s\n' "$description"
        cat "$LOG"
        FAILED=$((FAILED + 1))
    fi
}

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE X-B HYPOTHESIS + KNOWLEDGE INTEGRATION"
echo "======================================================================"

run_check "Phase X prerequisite"     "$PYTHON_BIN" -c 'from core.reasoning import ReasoningEngine; assert ReasoningEngine'
run_check "Reasoning integration compilation"     "$PYTHON_BIN" -m compileall -q core/reasoning
run_check "Phase X-B structural boundaries"     "$PYTHON_BIN" dev/verification/verify_phase_xb_hypothesis_knowledge.py
run_check "Phase X-B unit tests"     "$PYTHON_BIN" -m unittest -v tests.test_phase_xb_hypothesis_knowledge
run_check "Phase X regression tests"     "$PYTHON_BIN" -m unittest -v tests.test_phase_x_reasoning_foundation
run_check "Stable public integration imports"     "$PYTHON_BIN" -c 'from core.reasoning import KnowledgeEvidenceAdapter, DeterministicHypothesisGenerator, KnowledgeReasoningPipeline'
run_check "Deterministic knowledge reasoning smoke test"     "$PYTHON_BIN" -c '
from core.reasoning import KnowledgeReasoningPipeline
results = ({
    "source": "/docs/a.pdf",
    "chunk_index": 1,
    "text": "Structured evidence supports auditable reasoning.",
    "ranking_score": 0.91,
    "quality": 96,
},)
pipeline = KnowledgeReasoningPipeline(lambda query, limit: results)
first = pipeline.reason(goal="Integrate knowledge with reasoning")
second = pipeline.reason(goal="Integrate knowledge with reasoning")
assert first.reasoning.selected_hypothesis_id is not None
assert first.reasoning.fingerprint == second.reasoning.fingerprint
'

echo "----------------------------------------------------------------------"
printf 'Checks passed : %d\n' "$PASSED"
printf 'Checks failed : %d\n' "$FAILED"
if [ "$FAILED" -eq 0 ]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi
echo "Overall status: FAILED"
echo "======================================================================"
exit 1
JARVIS_XB_DEV_VERIFY_PHASE_XB_SH

cat > docs/architecture/reasoning_hypothesis_knowledge_integration.md <<'JARVIS_XB_DOCS_ARCHITECTURE_REASONING_HYPOTHESIS_KNOWLEDGE_INTEGRATION_MD'
# Phase X-B — Hypothesis Generation and Knowledge Evidence Integration

## Purpose

Phase X-B connects Knowledge Engine retrieval output to the deterministic
Reasoning Engine and introduces bounded competing-hypothesis generation.

## Pipeline

```text
Knowledge search callable
        |
        v
raw search or ranking results
        |
        v
KnowledgeEvidenceAdapter
        |
        +-- source and chunk provenance
        +-- retrieval/ranking score
        +-- quality score
        +-- ranking explanation
        +-- stable evidence identity
        |
        v
EvidenceItem[]
        |
        v
DeterministicHypothesisGenerator
        |
        +-- evidence-backed synthesis
        +-- competing insufficiency hypothesis
        +-- optional conflict hypothesis
        |
        v
ReasoningEngine
        |
        v
PlanningRecommendation
```

## Supported result contracts

Production search objects may expose:

- `score`
- `file_path`
- `chunk_index`
- `text`
- `quality`

Ranked mappings may expose:

- `ranking_score`
- `source`
- `chunk_index`
- `text`
- `quality`
- `ranking`

The adapter accepts attribute-based and mapping-based forms.

## Translation policy

Retrieval relevance becomes evidence confidence. Content quality becomes
evidence reliability. Source path and chunk index remain explicit provenance.
The adapter does not claim that relevance proves truth.

## Generation policy

The generator does not invent domain facts. It creates only bounded
hypotheses concerning whether the available evidence supports the stated goal,
is insufficient, or contains unresolved conflict.

## Dependency boundary

The pipeline receives an injected callable:

```python
search(query: str, limit: int) -> Iterable[result]
```

It does not construct the Knowledge database or import the Knowledge Director.
That keeps reasoning independent of runtime wiring.

## Safety boundary

Phase X-B does not execute tools, mutate knowledge, authorize a plan, create a
runtime mission, autonomously expand research, or call an LLM.

## Next phase

Phase X-C should extract explicit claims from retrieved text, relate evidence
to claims, and detect agreement or conflict across sources before hypothesis
assessment.
JARVIS_XB_DOCS_ARCHITECTURE_REASONING_HYPOTHESIS_KNOWLEDGE_INTEGRATION_MD

chmod +x dev/verify_phase_xb.sh
chmod +x dev/verification/verify_phase_xb_hypothesis_knowledge.py
echo
echo "Phase X-B installation complete."
