from __future__ import annotations

from dataclasses import dataclass

from .models import ClaimRecord
from .normalize import jaccard, normalize_text, polarity


@dataclass(frozen=True)
class Detection:
    relationship_type: str
    score: float
    rationale: str


def detect_pair(left: ClaimRecord, right: ClaimRecord) -> Detection | None:
    if left.claim_id == right.claim_id:
        return None

    normalized_left = normalize_text(left.text)
    normalized_right = normalize_text(right.text)

    if normalized_left == normalized_right and normalized_left:
        return Detection("duplicates", 1.0, "Canonical normalized text is identical.")

    similarity = jaccard(left.text, right.text)
    same_domain = left.domain == right.domain
    opposite_polarity = polarity(left.text) != polarity(right.text)

    if similarity >= 0.72 and opposite_polarity:
        return Detection(
            "contradicts",
            round(similarity, 6),
            "Claims have high lexical overlap but opposite normative polarity.",
        )

    if similarity >= 0.88:
        return Detection(
            "duplicates",
            round(similarity, 6),
            "Claims exceed deterministic duplicate similarity threshold.",
        )

    if same_domain and similarity >= 0.68:
        if len(normalized_left.split()) != len(normalized_right.split()):
            return Detection(
                "refines",
                round(similarity, 6),
                "Claims share domain and substantial vocabulary; the longer statement is treated as refinement.",
            )
        return Detection(
            "supports",
            round(similarity, 6),
            "Claims share domain and substantial normative vocabulary.",
        )

    return None
