from __future__ import annotations
from typing import Any, Sequence
from .enums import CourseOfActionKind, CourseOfActionStatus, GenerationDisposition
from .errors import AlternativeGenerationError
from .models import AlternativeGenerationPolicy, AlternativeGenerationResult, CourseOfAction, CourseOfActionTemplate


def _first(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        value = getattr(obj, name, None)
        if value is not None:
            return value
    return default

class DeterministicCourseOfActionGenerator:
    """Generate bounded, deterministic COAs from a certified reasoning result."""

    def generate(self, reasoning_result: Any, templates: Sequence[CourseOfActionTemplate], policy: AlternativeGenerationPolicy | None = None) -> AlternativeGenerationResult:
        if reasoning_result is None:
            raise AlternativeGenerationError("reasoning_result is required")
        policy = policy or AlternativeGenerationPolicy()
        reasoning_id = str(_first(reasoning_result, "reasoning_id", "result_id", "id", default="")).strip()
        if not reasoning_id:
            raise AlternativeGenerationError("reasoning_result must expose reasoning_id, result_id, or id")
        selected = _first(reasoning_result, "selected_hypothesis_id", "selected_hypothesis", "hypothesis_id")
        if selected is not None and not isinstance(selected, str):
            selected = str(_first(selected, "hypothesis_id", "id", default=""))
        selected = (selected or "").strip()
        confidence = float(_first(reasoning_result, "confidence", "reasoning_confidence", "selected_confidence", default=0.0))
        if not selected:
            return AlternativeGenerationResult.derive(reasoning_id, GenerationDisposition.DEFERRED, (), ("no selected hypothesis",))
        if confidence < policy.minimum_reasoning_confidence:
            return AlternativeGenerationResult.derive(reasoning_id, GenerationDisposition.DEFERRED, (), ("reasoning confidence below policy threshold",))

        normalized = {t.template_id: t for t in templates}
        candidate_templates = list(normalized.values())
        kinds = {t.kind for t in candidate_templates}
        if policy.require_hold_alternative and CourseOfActionKind.HOLD not in kinds:
            candidate_templates.append(default_hold_template())
        if policy.require_contingency_alternative and CourseOfActionKind.CONTINGENCY not in kinds:
            candidate_templates.append(default_contingency_template())

        generated = []
        for template in sorted(candidate_templates, key=lambda t: (t.kind.value, t.template_id)):
            title = template.title_pattern.format(hypothesis_id=selected, reasoning_id=reasoning_id)
            description = template.description_pattern.format(hypothesis_id=selected, reasoning_id=reasoning_id)
            utility = max(0.0, min(1.0, template.base_utility))
            coa_confidence = max(0.0, min(1.0, template.base_confidence * confidence))
            rank_score = policy.utility_weight * utility + policy.confidence_weight * coa_confidence
            generated.append(CourseOfAction.derive(
                reasoning_id=reasoning_id,
                selected_hypothesis_id=selected,
                kind=template.kind,
                status=CourseOfActionStatus.CANDIDATE,
                title=title,
                description=description,
                objectives=template.objectives or (f"Address hypothesis {selected}",),
                proposed_tasks=template.proposed_tasks,
                required_resources=template.required_resources,
                risks=template.risks,
                constraints=template.constraints,
                expected_outcomes=template.expected_outcomes or (f"Produce a measurable response to {selected}",),
                utility=utility,
                confidence=coa_confidence,
                rank_score=rank_score,
                provenance=(reasoning_id, selected, template.template_id),
                metadata={"template_id": template.template_id},
            ))
        ranked = tuple(sorted(generated, key=lambda c: (-c.rank_score, c.coa_id))[:policy.maximum_candidates])
        return AlternativeGenerationResult.derive(reasoning_id, GenerationDisposition.GENERATED, ranked)

def default_hold_template() -> CourseOfActionTemplate:
    return CourseOfActionTemplate(template_id="constitutional-hold", kind=CourseOfActionKind.HOLD, title_pattern="Hold pending additional evidence", description_pattern="Preserve the current state while gathering evidence for {hypothesis_id}.", base_utility=0.35, base_confidence=0.9, objectives=("Prevent premature commitment",), proposed_tasks=("Collect additional evidence",), risks=("Opportunity cost",), expected_outcomes=("Decision uncertainty reduced",), tags=("mandatory", "hold"))

def default_contingency_template() -> CourseOfActionTemplate:
    return CourseOfActionTemplate(template_id="constitutional-contingency", kind=CourseOfActionKind.CONTINGENCY, title_pattern="Prepare contingency for {hypothesis_id}", description_pattern="Prepare a reversible response if {hypothesis_id} is confirmed.", base_utility=0.55, base_confidence=0.7, objectives=("Maintain response readiness",), proposed_tasks=("Define trigger", "Prepare reversible response"), risks=("Preparation cost",), expected_outcomes=("Reduced response latency",), tags=("mandatory", "contingency"))

__all__ = ["DeterministicCourseOfActionGenerator", "default_hold_template", "default_contingency_template"]
