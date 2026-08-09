from __future__ import annotations
from dataclasses import dataclass
from .lexical import analyze_lexical

@dataclass(frozen=True, slots=True)
class SubjectAnalysis:
    score: float
    query_subject: str
    candidate_subject: str

def analyze_subject(query: str, candidate_subject: str, candidate_title: str = "") -> SubjectAnalysis:
    combined = " ".join(x for x in (candidate_subject, candidate_title) if x)
    return SubjectAnalysis(analyze_lexical(query, combined).score, query, combined)
