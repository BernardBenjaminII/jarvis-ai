from __future__ import annotations
import re
from dataclasses import dataclass
from itertools import combinations
from typing import Callable
from core.retrieval.qualification import QualificationResult
from .contracts import AnswerCitation, AnswerConflict, GroundedAnswer, GroundedAnswerPlan, RankedEvidence
from .enums import AnswerKnowledgeState, ConflictSeverity
from .policy import GroundedAnswerPolicy

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
CONTRADICTIONS = (
    ("is", "is not"), ("can", "cannot"), ("present", "absent"),
    ("enabled", "disabled"), ("true", "false"), ("higher", "lower"),
)

def _tokens(value: str) -> set[str]:
    return {x.casefold() for x in TOKEN_RE.findall(value or "") if len(x) >= 3}

@dataclass(frozen=True, slots=True)
class GroundedAnswerEngine:
    policy: GroundedAnswerPolicy = GroundedAnswerPolicy()

    def plan(self, query: str, qualification: QualificationResult) -> GroundedAnswerPlan:
        ranked = self._rank(qualification)
        citations = tuple(
            AnswerCitation(
                citation_id=f"C{index}",
                evidence_id=item.evidence_id,
                source_id=item.source_id,
                source_path=item.source_path,
                title=item.title,
                excerpt=item.excerpt,
                rank=index,
            )
            for index, item in enumerate(ranked[:self.policy.max_citations], start=1)
        )
        conflicts = self._conflicts(ranked)
        confidence = self._confidence(ranked, conflicts)
        state = self._state(confidence, len(ranked), len(conflicts))
        uncertainty = self._uncertainty(state, confidence, len(ranked), len(conflicts))
        action = (
            "Acquire and assimilate authoritative sources, then retry."
            if state is AnswerKnowledgeState.UNKNOWN
            else "Review conflicting sources before relying on this answer."
            if state is AnswerKnowledgeState.CONFLICTED
            else None
        )
        prompt = self._prompt(query, state, confidence, ranked, citations, conflicts, uncertainty)
        return GroundedAnswerPlan(
            query=query, state=state, confidence=confidence,
            ranked_evidence=ranked, citations=citations, conflicts=conflicts,
            synthesis_prompt=prompt, uncertainty_note=uncertainty,
            recommended_action=action,
        )

    def answer(self, query: str, qualification: QualificationResult, synthesis_handler: Callable[[str], str]) -> GroundedAnswer:
        plan = self.plan(query, qualification)
        text = str(synthesis_handler(plan.synthesis_prompt)).strip() or self.deterministic_answer(plan)
        return GroundedAnswer(
            answer=text, state=plan.state, confidence=plan.confidence,
            citations=plan.citations, conflicts=plan.conflicts,
            uncertainty_note=plan.uncertainty_note,
            recommended_action=plan.recommended_action,
        )

    def deterministic_answer(self, plan: GroundedAnswerPlan) -> str:
        if plan.state is AnswerKnowledgeState.UNKNOWN:
            return "JARVIS does not have qualified evidence sufficient to answer this question."
        lines = [f"Knowledge state: {plan.state.value}.", f"Confidence: {plan.confidence:.3f}."]
        for item, citation in zip(plan.ranked_evidence, plan.citations):
            lines.append(f"- [{citation.citation_id}] {item.excerpt.strip()}")
        if plan.conflicts:
            lines.append("Conflicting evidence was detected.")
        lines.append(plan.uncertainty_note)
        return "\n".join(lines)

    def _rank(self, qualification: QualificationResult) -> tuple[RankedEvidence, ...]:
        values = []
        for index, item in enumerate(qualification.accepted, start=1):
            c = item.candidate
            relevance = item.score.final
            score = 0.65 * relevance + 0.25 * c.retrieval_score + 0.10 * bool(c.source_path)
            values.append(RankedEvidence(
                evidence_id=f"evidence-{index}", source_id=c.source_id,
                source_path=c.source_path, title=c.title, subject=c.subject,
                excerpt=c.excerpt, relevance=relevance,
                retrieval_score=c.retrieval_score, rank_score=score,
            ))
        values.sort(key=lambda x: (-x.rank_score, x.source_path, x.source_id))
        return tuple(values[:self.policy.max_evidence])

    def _conflicts(self, evidence: tuple[RankedEvidence, ...]) -> tuple[AnswerConflict, ...]:
        results = []
        for index, (left, right) in enumerate(combinations(evidence, 2), start=1):
            a, b = _tokens(left.excerpt), _tokens(right.excerpt)
            overlap = len(a & b) / max(1, len(a | b))
            if overlap < self.policy.conflict_overlap:
                continue
            reasons = []
            lt, rt = left.excerpt.casefold(), right.excerpt.casefold()
            for positive, negative in CONTRADICTIONS:
                if (positive in lt and negative in rt) or (negative in lt and positive in rt):
                    reasons.append(f"{positive!r} versus {negative!r}")
            if reasons:
                results.append(AnswerConflict(
                    conflict_id=f"conflict-{index}",
                    left_evidence_id=left.evidence_id,
                    right_evidence_id=right.evidence_id,
                    severity=ConflictSeverity.HIGH if len(reasons) > 1 else ConflictSeverity.MODERATE,
                    reason="Potential contradiction: " + ", ".join(reasons),
                ))
        return tuple(results)

    def _confidence(self, ranked, conflicts) -> float:
        if not ranked:
            return 0.0
        weights = [1 / (i + 1) for i in range(len(ranked))]
        base = sum(x.rank_score * w for x, w in zip(ranked, weights)) / sum(weights)
        diversity = min(1.0, len({x.source_id for x in ranked}) / 3)
        return max(0.0, min(1.0, 0.85 * base + 0.15 * diversity - min(0.45, 0.15 * len(conflicts))))

    def _state(self, confidence, evidence_count, conflict_count):
        if evidence_count == 0:
            return AnswerKnowledgeState.UNKNOWN
        if conflict_count:
            return AnswerKnowledgeState.CONFLICTED
        if confidence >= self.policy.known_confidence:
            return AnswerKnowledgeState.KNOWN
        if confidence >= self.policy.partial_confidence:
            return AnswerKnowledgeState.PARTIAL
        return AnswerKnowledgeState.UNKNOWN

    @staticmethod
    def _uncertainty(state, confidence, evidence_count, conflict_count):
        if state is AnswerKnowledgeState.KNOWN:
            return f"Supported by {evidence_count} qualified item(s); confidence {confidence:.3f}."
        if state is AnswerKnowledgeState.PARTIAL:
            return "Evidence is relevant but incomplete."
        if state is AnswerKnowledgeState.CONFLICTED:
            return f"{conflict_count} potential conflict(s) require review."
        return "No qualified evidence is available for a reliable answer."

    @staticmethod
    def _prompt(query, state, confidence, ranked, citations, conflicts, uncertainty):
        lines = [
            query.strip(), "", "JARVIS GROUNDED ANSWER CONTRACT:",
            f"Knowledge state: {state.value}",
            f"Calibrated confidence: {confidence:.3f}",
            f"Uncertainty: {uncertainty}", "", "QUALIFIED EVIDENCE:",
        ]
        if ranked:
            for item, citation in zip(ranked, citations):
                lines.append(f"[{citation.citation_id}] title={item.title!r}; source={item.source_path!r}; rank_score={item.rank_score:.3f}")
                lines.append(item.excerpt.strip())
        else:
            lines.append("- No qualified evidence.")
        lines.extend(["", "CONFLICTS:"])
        if conflicts:
            lines.extend(f"- {x.conflict_id}: {x.reason}" for x in conflicts)
        else:
            lines.append("- None detected.")
        lines.extend([
            "", "INSTRUCTIONS:",
            "- Answer only from the qualified evidence above.",
            "- Cite supporting claims using [C#] markers.",
            "- State uncertainty explicitly.",
            "- Do not invent missing facts.",
            "- Describe conflicts rather than silently choosing one.",
        ])
        return "\n".join(lines)
