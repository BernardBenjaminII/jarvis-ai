from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .confidence import normalize_retrieval_score
from .contracts import (
    EvidenceCandidate,
    QualificationResult,
    QualificationScore,
    QualifiedEvidence,
)
from .enums import QualificationDecision
from .lexical import analyze_lexical
from .phrase import analyze_phrases
from .subject import analyze_subject
from .thresholds import QualificationThresholds


def _unit_score(value: Any) -> float:
    """
    Convert a persisted retrieval signal into a finite [0, 1] score.

    Invalid, missing, non-numeric, NaN, and infinite values fail closed
    to zero.
    """

    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    if score != score:
        return 0.0

    if score in (float("inf"), float("-inf")):
        return 0.0

    return max(0.0, min(1.0, score))


def _raw_row(candidate: EvidenceCandidate) -> Mapping[str, Any]:
    """
    Return the original retrieval row carried by qualified_search.

    EvidenceCandidate intentionally remains backend-neutral. Modern
    retrieval-specific diagnostics stay inside metadata["raw_row"].
    """

    metadata = candidate.metadata

    if not isinstance(metadata, Mapping):
        return {}

    raw = metadata.get("raw_row")

    if not isinstance(raw, Mapping):
        return {}

    return raw


def _semantic_score(candidate: EvidenceCandidate) -> float:
    """
    Recover an independently persisted semantic relevance signal.

    Preference order:

      1. semantic_score from the original modern retrieval row;
      2. zero when no explicit semantic signal exists.

    We deliberately do NOT substitute candidate.retrieval_score here.
    That field represents the selected retrieval confidence and may be
    a hybrid score, lexical score, or legacy backend score.

    This keeps semantic relevance and retrieval confidence independent
    inside qualification.
    """

    raw = _raw_row(candidate)

    if "semantic_score" not in raw:
        return 0.0

    return _unit_score(raw.get("semantic_score"))


@dataclass(frozen=True, slots=True)
class QualificationEngine:
    thresholds: QualificationThresholds = QualificationThresholds()

    def evaluate(
        self,
        query: str,
        candidates: Iterable[EvidenceCandidate],
    ) -> QualificationResult:

        accepted: list[QualifiedEvidence] = []
        rejected: list[QualifiedEvidence] = []

        items = tuple(candidates)

        for candidate in items:
            item = self.evaluate_candidate(query, candidate)

            if item.accepted:
                accepted.append(item)
            else:
                rejected.append(item)

        return QualificationResult(
            tuple(accepted),
            tuple(rejected),
            self.thresholds.accept,
            {
                "query": query,
                "candidate_count": len(items),
                "accepted_count": len(accepted),
                "rejected_count": len(rejected),
                "empty_result": not items,
            },
        )

    def evaluate_candidate(
        self,
        query: str,
        candidate: EvidenceCandidate,
    ) -> QualifiedEvidence:

        # A shared storage path is provenance, not topical evidence.
        # Including it in lexical analysis allowed every file below a
        # common knowledge root to match queries about that path.
        text = " ".join(
            x
            for x in (
                candidate.title,
                candidate.subject,
                candidate.excerpt,
            )
            if x
        )

        lexical = analyze_lexical(query, text)
        phrase = analyze_phrases(query, text)
        subject = analyze_subject(
            query,
            candidate.subject,
            candidate.title,
        )

        # Retrieval confidence remains the normalized score selected by
        # the retrieval adapter. For modern runtime retrieval this is
        # normally the hybrid score.
        confidence = normalize_retrieval_score(
            candidate.retrieval_score,
            backend=candidate.backend,
        )

        # Semantic relevance is independent from retrieval confidence.
        # It is populated only when the retrieval row explicitly carries
        # a validated semantic score.
        semantic = _semantic_score(candidate)

        provenance = 1.0 if candidate.source_path else 0.0

        # Until a dedicated entity analyzer exists, entity relevance
        # derives from substantive lexical evidence. This intentionally
        # preserves the existing deterministic lexical safety behavior.
        entity = lexical.score

        # GENESIS semantic-aware qualification R1
        #
        # Semantic evidence receives a bounded 10% contribution while
        # deterministic lexical relevance remains dominant and remains
        # a mandatory decision gate in _decide().
        #
        # Total = 1.00
        #
        # lexical     0.30
        # semantic    0.10
        # phrase      0.15
        # subject     0.20
        # entity      0.10
        # confidence  0.10
        # provenance  0.05
        final = (
            0.30 * lexical.score
            + 0.10 * semantic
            + 0.15 * phrase.score
            + 0.20 * subject.score
            + 0.10 * entity
            + 0.10 * confidence
            + 0.05 * provenance
        )

        score = QualificationScore(
            lexical=lexical.score,
            semantic=semantic,
            phrase=phrase.score,
            entity=entity,
            subject=subject.score,
            provenance=provenance,
            final=final,
        )

        decision, explanation = self._decide(
            lexical.score,
            phrase.score,
            subject.score,
            confidence,
            final,
        )

        return QualifiedEvidence(
            candidate,
            score,
            decision,
            explanation,
        )

    def _decide(
        self,
        lexical: float,
        phrase: float,
        subject: float,
        confidence: float,
        final: float,
    ) -> tuple[QualificationDecision, str]:

        t = self.thresholds

        if confidence < t.minimum_confidence:
            return (
                QualificationDecision.REJECTED_LOW_CONFIDENCE,
                (
                    f"confidence {confidence:.3f} below "
                    f"{t.minimum_confidence:.3f}"
                ),
            )

        # Substantive lexical relevance remains a mandatory
        # qualification gate. Semantic similarity may strengthen
        # relevant evidence but cannot override lexical mismatch.
        if lexical < t.minimum_lexical:
            return (
                QualificationDecision.REJECTED_LOW_RELEVANCE,
                (
                    f"lexical {lexical:.3f} below "
                    f"{t.minimum_lexical:.3f}"
                ),
            )

        if (
            phrase >= t.strong_phrase_override
            and final >= t.accept
        ):
            return (
                QualificationDecision.ACCEPTED,
                (
                    "accepted by strong phrase match "
                    "with lexical support"
                ),
            )

        if subject < t.minimum_subject:
            return (
                QualificationDecision.REJECTED_SUBJECT_MISMATCH,
                (
                    f"subject {subject:.3f} below "
                    f"{t.minimum_subject:.3f}"
                ),
            )

        if phrase < t.minimum_phrase:
            return (
                QualificationDecision.REJECTED_ENTITY_MISMATCH,
                (
                    f"phrase {phrase:.3f} below "
                    f"{t.minimum_phrase:.3f}"
                ),
            )

        if final < t.accept:
            return (
                QualificationDecision.REJECTED_LOW_RELEVANCE,
                (
                    f"final {final:.3f} below "
                    f"{t.accept:.3f}"
                ),
            )

        return (
            QualificationDecision.ACCEPTED,
            f"final {final:.3f} meets {t.accept:.3f}",
        )
