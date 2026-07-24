"""Deterministic hypothesis assessment for the JARVIS Reasoning Engine."""

from __future__ import annotations

from collections.abc import Mapping

from core.reasoning.confidence import (
    classify_disposition,
    hypothesis_confidence,
    total_weight,
)
from core.reasoning.models import (
    EvidenceItem,
    Hypothesis,
    HypothesisAssessment,
)


def assess_hypothesis(
    hypothesis: Hypothesis,
    evidence_by_id: Mapping[str, EvidenceItem],
) -> HypothesisAssessment:
    """Assess one hypothesis against explicitly referenced evidence."""

    supporting = tuple(
        evidence_by_id[evidence_id]
        for evidence_id in hypothesis.supporting_evidence_ids
    )
    contradicting = tuple(
        evidence_by_id[evidence_id]
        for evidence_id in hypothesis.contradicting_evidence_ids
    )

    support_score = total_weight(supporting)
    contradiction_score = total_weight(contradicting)
    confidence = hypothesis_confidence(
        support_score=support_score,
        contradiction_score=contradiction_score,
        assumption_count=len(hypothesis.assumptions),
    )
    disposition = classify_disposition(
        support_score=support_score,
        contradiction_score=contradiction_score,
        confidence=confidence,
    )

    rationale = (
        f"Weighted support score: {support_score:.6f}.",
        f"Weighted contradiction score: {contradiction_score:.6f}.",
        f"Unresolved assumptions: {len(hypothesis.assumptions)}.",
        f"Resulting confidence: {confidence:.6f}.",
        f"Disposition: {disposition.value}.",
    )

    return HypothesisAssessment(
        hypothesis_id=hypothesis.hypothesis_id,
        statement=hypothesis.statement,
        support_score=support_score,
        contradiction_score=contradiction_score,
        confidence=confidence,
        disposition=disposition,
        supporting_evidence_ids=hypothesis.supporting_evidence_ids,
        contradicting_evidence_ids=hypothesis.contradicting_evidence_ids,
        assumptions=hypothesis.assumptions,
        rationale=rationale,
    )
