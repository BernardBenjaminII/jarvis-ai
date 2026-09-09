from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .confidence import normalize_retrieval_score
from .contracts import EvidenceCandidate, QualificationResult, QualificationScore, QualifiedEvidence
from .enums import QualificationDecision
from .lexical import analyze_lexical
from .phrase import analyze_phrases
from .subject import analyze_subject
from .thresholds import QualificationThresholds

@dataclass(frozen=True, slots=True)
class QualificationEngine:
    thresholds: QualificationThresholds = QualificationThresholds()

    def evaluate(self, query: str, candidates: Iterable[EvidenceCandidate]) -> QualificationResult:
        accepted, rejected = [], []
        items = tuple(candidates)
        for candidate in items:
            item = self.evaluate_candidate(query, candidate)
            (accepted if item.accepted else rejected).append(item)
        return QualificationResult(
            tuple(accepted), tuple(rejected), self.thresholds.accept,
            {"query":query,"candidate_count":len(items),"accepted_count":len(accepted),
             "rejected_count":len(rejected),"empty_result":not items},
        )

    def evaluate_candidate(self, query: str, candidate: EvidenceCandidate) -> QualifiedEvidence:
        # A shared storage path is provenance, not topical evidence.  Including
        # it here allowed every file below JARVISDATA/Knowledge to match queries
        # about JARVISDATA or the knowledge catalog regardless of its content.
        text = " ".join(x for x in (candidate.title,candidate.subject,candidate.excerpt) if x)
        lexical = analyze_lexical(query, text)
        phrase = analyze_phrases(query, text)
        subject = analyze_subject(query, candidate.subject, candidate.title)
        confidence = normalize_retrieval_score(candidate.retrieval_score, backend=candidate.backend)
        provenance = 1.0 if candidate.source_path else 0.0
        # Until a dedicated entity analyzer exists, entity relevance must
        # derive from substantive lexical evidence.  Reusing phrase.score here
        # double-counted phrase relevance and could legitimize unrelated text.
        entity = lexical.score
        final = 0.35*lexical.score + 0.20*phrase.score + 0.20*subject.score + 0.10*entity + 0.10*confidence + 0.05*provenance
        score = QualificationScore(lexical.score,0.0,phrase.score,entity,subject.score,provenance,final)
        decision, explanation = self._decide(lexical.score,phrase.score,subject.score,confidence,final)
        return QualifiedEvidence(candidate, score, decision, explanation)

    def _decide(self, lexical, phrase, subject, confidence, final):
        t = self.thresholds
        if confidence < t.minimum_confidence:
            return QualificationDecision.REJECTED_LOW_CONFIDENCE, f"confidence {confidence:.3f} below {t.minimum_confidence:.3f}"

        # Substantive lexical relevance is a mandatory qualification gate.
        # A phrase match may strengthen relevant evidence, but it must never
        # override complete lexical mismatch.
        if lexical < t.minimum_lexical:
            return QualificationDecision.REJECTED_LOW_RELEVANCE, f"lexical {lexical:.3f} below {t.minimum_lexical:.3f}"

        if phrase >= t.strong_phrase_override and final >= t.accept:
            return QualificationDecision.ACCEPTED, "accepted by strong phrase match with lexical support"
        if subject < t.minimum_subject:
            return QualificationDecision.REJECTED_SUBJECT_MISMATCH, f"subject {subject:.3f} below {t.minimum_subject:.3f}"
        if phrase < t.minimum_phrase:
            return QualificationDecision.REJECTED_ENTITY_MISMATCH, f"phrase {phrase:.3f} below {t.minimum_phrase:.3f}"
        if final < t.accept:
            return QualificationDecision.REJECTED_LOW_RELEVANCE, f"final {final:.3f} below {t.accept:.3f}"
        return QualificationDecision.ACCEPTED, f"final {final:.3f} meets {t.accept:.3f}"
