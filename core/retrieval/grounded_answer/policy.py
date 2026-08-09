from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class GroundedAnswerPolicy:
    max_evidence: int = 6
    max_citations: int = 6
    known_confidence: float = 0.70
    partial_confidence: float = 0.35
    conflict_overlap: float = 0.40
