"""C-5 Executive Knowledge Awareness and Evidence Reasoning service."""
from __future__ import annotations
from core.conversation.grounding import GroundingResult, ObjectiveGrounding
from core.reasoning.enums import EvidenceKind, EvidenceStance
from core.reasoning.generation import DeterministicHypothesisGenerator
from core.reasoning.models import EvidenceItem, ReasoningRequest, canonical_fingerprint
from core.reasoning.service import ReasoningEngine
from core.knowledge_awareness.contracts import (
    EvidenceAssessment, ExecutiveKnowledgeState, KnowledgeCoverage,
    ResearchRecommendation,
)

class ExecutiveKnowledgeAwarenessService:
    """Convert catalog grounding into an auditable executive knowledge state."""
    def __init__(self, *, engine: ReasoningEngine | None = None,
                 generator: DeterministicHypothesisGenerator | None = None) -> None:
        self.engine = engine or ReasoningEngine()
        self.generator = generator or DeterministicHypothesisGenerator()

    def assess(self, grounding: GroundingResult) -> ExecutiveKnowledgeState:
        coverage=[]; assessments=[]; research=[]; all_sources=set(); total_evidence=0; contradictions=0
        for objective in grounding.objectives:
            evidence=self._evidence(objective)
            total_evidence += len(evidence)
            all_sources.update(item.source_ref for item in evidence)
            avg=sum(item.weight for item in evidence)/len(evidence) if evidence else 0.0
            score=min(1.0, (len(evidence)/4.0)*0.65 + avg*0.35)
            maturity=self._maturity(score)
            answerability=self._answerability(score)
            gaps=() if evidence else ((objective.gap.reason if objective.gap else "No admissible evidence was found."),)
            coverage.append(KnowledgeCoverage(
                objective_id=objective.objective_id, query=objective.query,
                evidence_count=len(evidence), source_count=len({x.source_ref for x in evidence}),
                average_weight=round(avg,6), coverage=round(score,6), maturity=maturity,
                answerability=answerability, gaps=gaps,
            ))
            if not evidence:
                assessments.append(EvidenceAssessment(
                    objective_id=objective.objective_id, status="insufficient",
                    selected_hypothesis_id=None, confidence=0.0, contradiction_count=0,
                    missing_information=gaps, reasoning_fingerprint=None,
                ))
                research.append(ResearchRecommendation(
                    objective_id=objective.objective_id, query=objective.query,
                    priority="high", reason=gaps[0],
                    recommended_action=(objective.gap.recommended_action if objective.gap else "Queue targeted acquisition and assimilation."),
                ))
                continue
            generated=self.generator.generate(objective.query, evidence)
            request=ReasoningRequest(
                request_id=f"c5_{canonical_fingerprint({'objective':objective.objective_id,'query':objective.query})[:16]}",
                goal=objective.query, evidence=evidence, hypotheses=generated.hypotheses,
                context={"objective_id":objective.objective_id,"convergence":"C-5"},
            )
            result=self.engine.reason(request)
            selected=next((x for x in result.assessments if x.hypothesis_id==result.selected_hypothesis_id), None)
            confidence=selected.confidence if selected else 0.0
            contradictions += len(result.contradictions)
            assessments.append(EvidenceAssessment(
                objective_id=objective.objective_id, status=result.status.value,
                selected_hypothesis_id=result.selected_hypothesis_id,
                confidence=round(confidence,6), contradiction_count=len(result.contradictions),
                missing_information=tuple(result.missing_information),
                reasoning_fingerprint=result.fingerprint,
            ))
            if score < 0.5 or result.contradictions:
                research.append(ResearchRecommendation(
                    objective_id=objective.objective_id, query=objective.query,
                    priority="medium", reason="Coverage or reasoning completeness is below the executive threshold.",
                    recommended_action="Acquire authoritative sources, assimilate them, and reassess this objective.",
                ))
        overall=sum(x.coverage for x in coverage)/len(coverage) if coverage else 0.0
        answerability=self._answerability(overall)
        status="ready" if answerability=="answerable" and contradictions==0 else ("limited" if total_evidence else "unknown")
        return ExecutiveKnowledgeState(
            status=status, answerability=answerability, confidence=round(overall,6),
            coverage=tuple(coverage), assessments=tuple(assessments), research_queue=tuple(research),
            evidence_count=total_evidence, source_count=len(all_sources), contradiction_count=contradictions,
        )

    @staticmethod
    def _evidence(objective: ObjectiveGrounding) -> tuple[EvidenceItem, ...]:
        return tuple(EvidenceItem(
            evidence_id=item.evidence_id,
            proposition=item.subject or item.query,
            stance=EvidenceStance.SUPPORTS,
            source_ref=item.source_path,
            kind=EvidenceKind.DOCUMENT,
            reliability=max(0.0,min(1.0,float(item.confidence))),
            confidence=max(0.0,min(1.0,float(item.confidence))),
            metadata={"assigned_by":item.assigned_by,"objective_id":item.objective_id,"query":item.query},
        ) for item in objective.evidence)

    @staticmethod
    def _maturity(score: float) -> str:
        return "mature" if score >= .75 else "developing" if score >= .45 else "sparse" if score > 0 else "unknown"
    @staticmethod
    def _answerability(score: float) -> str:
        return "answerable" if score >= .65 else "conditional" if score >= .30 else "insufficient"
