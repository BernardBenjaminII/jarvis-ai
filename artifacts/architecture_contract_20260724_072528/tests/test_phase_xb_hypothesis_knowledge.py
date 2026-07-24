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
