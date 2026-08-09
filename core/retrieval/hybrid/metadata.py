from __future__ import annotations
from pathlib import Path
from .models import QueryAnalysis

AUTHORITY_HINTS = {
    "nist": 2.5,
    "cisa": 2.25,
    "fema": 2.0,
    "dod": 1.75,
    "army": 1.5,
    "marine": 1.5,
    "navy": 1.5,
    "air force": 1.5,
    "who": 1.5,
    "cdc": 1.5,
}

def metadata_score(analysis: QueryAnalysis, title: str, file_path: str) -> tuple[float, float]:
    title_l = (title or "").casefold()
    path_l = (file_path or "").casefold()
    score = 0.0
    authority = 0.0

    for term in analysis.terms:
        t = term.casefold()
        if t in title_l:
            score += 1.25
        if t in Path(file_path).name.casefold():
            score += 0.65
        if f"/{t}/" in path_l:
            score += 0.35

    for ent in analysis.entities:
        e = ent.casefold()
        if e in title_l:
            score += 2.5
        if e in path_l:
            score += 1.5

    raw_l = analysis.raw.casefold()
    for hint, weight in AUTHORITY_HINTS.items():
        if hint in raw_l and (hint in title_l or hint in path_l):
            authority += weight

    return score, authority
