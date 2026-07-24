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
