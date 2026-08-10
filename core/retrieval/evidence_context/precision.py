from __future__ import annotations


def passes_precision_gate(
    *,
    hybrid_score: float,
    semantic_score: float,
    lexical_score: float,
    title_score: float,
    minimum_hybrid: float = 0.42,
    minimum_semantic: float = 0.58,
    require_concept_signal: bool = True,
) -> bool:
    if hybrid_score < minimum_hybrid:
        return False
    if semantic_score < minimum_semantic:
        return False
    if require_concept_signal and lexical_score <= 0.0 and title_score <= 0.0:
        return False
    return True
