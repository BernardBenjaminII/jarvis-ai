from __future__ import annotations

from types import SimpleNamespace

from core.conversation.grounded_answer.integration import enforce_grounded_answer_output
from core.knowledge_catalog.qualified_search import _gate_repair_should_rescue
from core.retrieval.grounded_answer.engine import GroundedAnswerEngine
from core.retrieval.qualification import (
    EvidenceCandidate,
    QualificationDecision,
    QualificationResult,
    QualificationScore,
    QualifiedEvidence,
)


def test_unknown_plan_discards_model_answer_and_external_links():
    plan = GroundedAnswerEngine().plan("gardening advice", QualificationResult())
    orchestrator = SimpleNamespace(_last_grounded_answer_plan=plan)

    answer = enforce_grounded_answer_output(
        orchestrator,
        "Plant in spring [C1]. https://example.invalid/gardening",
    )

    assert answer == "JARVIS does not have qualified evidence sufficient to answer this question."
    assert "http" not in answer
    assert orchestrator._grounded_answer_output_fallback is True


def test_semantic_score_cannot_rescue_missing_gardening_terms():
    candidate = EvidenceCandidate(
        source_id="survival-manual",
        source_path="/Knowledge/survival/manual.pdf",
        title="Emergency Shelter",
        subject="survival",
        excerpt="Select a dry site and construct a wind-resistant shelter.",
        backend="hybrid",
        retrieval_score=0.99,
        metadata={"hybrid_score": 0.99, "semantic_score": 0.99},
    )
    rejected = QualifiedEvidence(
        candidate=candidate,
        score=QualificationScore(
            lexical=0.05,
            semantic=0.99,
            subject=0.05,
            provenance=1.0,
            final=0.99,
        ),
        decision=QualificationDecision.REJECTED_LOW_RELEVANCE,
    )

    rescued, reason = _gate_repair_should_rescue(
        "What should I do to start a garden?", rejected, threshold=0.50
    )

    assert rescued is False
    assert reason.startswith("missing_core_terms:")
    assert "garden" in reason


def test_grounded_answer_rejects_url_absent_from_evidence():
    candidate = EvidenceCandidate(
        source_id="garden-guide",
        source_path="/Knowledge/Agriculture/garden.pdf",
        title="Garden Guide",
        subject="gardening",
        excerpt="Add compost to improve garden soil before planting.",
        backend="runtime_fts",
        retrieval_score=0.95,
    )
    accepted = QualifiedEvidence(
        candidate=candidate,
        score=QualificationScore(
            lexical=0.95,
            semantic=0.90,
            subject=0.95,
            provenance=1.0,
            final=0.95,
        ),
        decision=QualificationDecision.ACCEPTED,
    )
    plan = GroundedAnswerEngine().plan(
        "How should I improve garden soil?",
        QualificationResult(accepted=(accepted,), threshold=0.50),
    )
    orchestrator = SimpleNamespace(_last_grounded_answer_plan=plan)

    answer = enforce_grounded_answer_output(
        orchestrator,
        "Add compost to improve garden soil [C1]. https://example.invalid/advice",
    )

    assert "example.invalid" not in answer
    assert "Add compost" in answer
