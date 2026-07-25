from __future__ import annotations

from typing import Sequence
from core.cognition.reasoner import ExecutiveReasoningResult, ReasoningDisposition
from .enums import DecisionDisposition, DecisionStatus
from .errors import InvalidDecisionInputError
from .models import (
    DecisionAlternative, DecisionConstraint, DecisionRecord,
    DecisionRisk, DecisionSynthesisPolicy, derive_decision_identity,
)

class DeterministicDecisionSynthesizer:
    def synthesize(
        self,
        *,
        reasoning: ExecutiveReasoningResult,
        alternatives: Sequence[DecisionAlternative],
        risks: Sequence[DecisionRisk] = (),
        constraints: Sequence[DecisionConstraint] = (),
        policy: DecisionSynthesisPolicy | None = None,
    ) -> DecisionRecord:
        if not isinstance(reasoning, ExecutiveReasoningResult):
            raise TypeError("reasoning must be ExecutiveReasoningResult")
        alternatives = tuple(alternatives)
        risks = tuple(risks)
        constraints = tuple(constraints)
        if not alternatives:
            raise InvalidDecisionInputError("at least one alternative is required")
        policy = policy or DecisionSynthesisPolicy()

        ranked = sorted(
            alternatives,
            key=lambda a: (a.expected_utility * a.confidence, a.alternative_id),
            reverse=True,
        )
        top = ranked[0]
        max_exposure = max((risk.exposure for risk in risks), default=0.0)
        mandatory_constraints = [c for c in constraints if c.mandatory]

        if policy.require_selected_hypothesis and reasoning.disposition is not ReasoningDisposition.SELECTED:
            disposition = DecisionDisposition.DEFERRED
            selected = None
            rationale = "Decision deferred because reasoning did not select a hypothesis."
        elif reasoning.confidence < policy.minimum_reasoning_confidence:
            disposition = DecisionDisposition.DEFERRED
            selected = None
            rationale = "Decision deferred because reasoning confidence is below policy."
        elif max_exposure > policy.maximum_risk_exposure:
            disposition = DecisionDisposition.ESCALATION_REQUIRED
            selected = None
            rationale = "Decision requires escalation because risk exposure exceeds policy."
        elif top.expected_utility * top.confidence < policy.minimum_utility:
            disposition = DecisionDisposition.REJECTED
            selected = None
            rationale = "No alternative satisfies the minimum utility threshold."
        else:
            disposition = DecisionDisposition.RECOMMENDED
            selected = top.alternative_id
            rationale = "The recommended alternative has the highest policy-compliant expected utility."

        decision_id = derive_decision_identity(reasoning, alternatives, risks, constraints, policy)
        return DecisionRecord(
            decision_id=decision_id,
            reasoning_id=reasoning.reasoning_id,
            situation_id=reasoning.situation_id,
            status=DecisionStatus.COMPLETE,
            disposition=disposition,
            selected_alternative_id=selected,
            alternatives=alternatives,
            risks=risks,
            constraints=constraints,
            confidence=reasoning.confidence * top.confidence,
            rationale=rationale,
            required_approvals=tuple(
                f"Approval required for constraint: {c.description}"
                for c in mandatory_constraints
            ),
            rollback_criteria=tuple(
                f"Risk exposure becomes unacceptable: {r.description}"
                for r in risks
            ),
            expected_outcomes=(top.title,),
        )
