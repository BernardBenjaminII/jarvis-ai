"""Deterministic hypothesis generation for Genesis IV-A3."""

from __future__ import annotations

from typing import Sequence

from core.cognition.situation import SituationSnapshot

from .enums import HypothesisStatus
from .errors import InvalidHypothesisError
from .models import (
    Hypothesis,
    HypothesisProposal,
    derive_hypothesis_identity,
)


class ExecutiveHypothesisGenerator:
    """Generate immutable candidate explanations from a situation."""

    def generate(
        self,
        *,
        situation: SituationSnapshot,
        proposals: Sequence[HypothesisProposal],
    ) -> tuple[Hypothesis, ...]:
        """Generate deterministic candidate hypotheses."""

        if not isinstance(situation, SituationSnapshot):
            raise TypeError("situation must be SituationSnapshot")

        normalized = tuple(proposals)
        if not normalized:
            raise InvalidHypothesisError(
                "at least one hypothesis proposal is required"
            )

        valid_observation_ids = set(situation.observation_ids)
        generated: list[Hypothesis] = []

        for proposal in normalized:
            if not isinstance(proposal, HypothesisProposal):
                raise TypeError(
                    "proposals must contain HypothesisProposal objects"
                )

            referenced = (
                set(proposal.supporting_observation_ids)
                | set(proposal.contradicting_observation_ids)
            )
            unknown = referenced - valid_observation_ids
            if unknown:
                raise InvalidHypothesisError(
                    "hypothesis references observations outside its "
                    f"situation: {sorted(unknown)}"
                )

            hypothesis_id = derive_hypothesis_identity(
                situation=situation,
                proposal=proposal,
            )

            generated.append(
                Hypothesis(
                    hypothesis_id=hypothesis_id,
                    situation_id=situation.situation_id,
                    statement=proposal.statement,
                    kind=proposal.kind,
                    status=HypothesisStatus.PROPOSED,
                    confidence=proposal.confidence,
                    supporting_observation_ids=(
                        proposal.supporting_observation_ids
                    ),
                    contradicting_observation_ids=(
                        proposal.contradicting_observation_ids
                    ),
                    assumptions=proposal.assumptions,
                    unresolved_questions=(
                        proposal.unresolved_questions
                    ),
                    rationale=proposal.rationale,
                    labels=proposal.labels,
                )
            )

        return tuple(
            sorted(generated, key=lambda item: item.hypothesis_id)
        )
