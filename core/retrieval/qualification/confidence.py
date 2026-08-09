from __future__ import annotations

def normalize_retrieval_score(value: float, *, backend: str = "") -> float:
    score = max(0.0, float(value))
    if score <= 1.0:
        return min(1.0, score)
    if (backend or "").casefold() in {"fts","runtime_fts","sqlite_fts"}:
        return score / (score + 10.0)
    return score / (score + 1.0)
