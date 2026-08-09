from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class QualificationThresholds:
    accept: float = 0.35
    minimum_lexical: float = 0.20
    minimum_subject: float = 0.10
    minimum_phrase: float = 0.0
    minimum_confidence: float = 0.05
    strong_phrase_override: float = 0.85
