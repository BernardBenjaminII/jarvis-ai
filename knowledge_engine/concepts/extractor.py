from __future__ import annotations

import re
from dataclasses import dataclass

from knowledge_engine.concepts.rules import CONCEPT_RULES


@dataclass(frozen=True)
class ExtractedConcept:
    concept: str
    concept_type: str
    domain: str
    confidence: float
    evidence: str


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_concepts(text: str) -> list[ExtractedConcept]:
    haystack = normalize(text)
    results: list[ExtractedConcept] = []

    for domain, type_rules in CONCEPT_RULES.items():
        for concept_type, terms in type_rules.items():
            for term in terms:
                term_norm = term.lower()

                if term_norm in haystack:
                    evidence = _evidence_window(haystack, term_norm)

                    confidence = 0.75
                    if len(term_norm) >= 8:
                        confidence += 0.10
                    if haystack.count(term_norm) > 1:
                        confidence += 0.10

                    results.append(
                        ExtractedConcept(
                            concept=term,
                            concept_type=concept_type,
                            domain=domain,
                            confidence=min(confidence, 0.95),
                            evidence=evidence,
                        )
                    )

    return _dedupe(results)


def _evidence_window(text: str, term: str, radius: int = 90) -> str:
    index = text.find(term)

    if index < 0:
        return ""

    start = max(0, index - radius)
    end = min(len(text), index + len(term) + radius)

    return text[start:end]


def _dedupe(items: list[ExtractedConcept]) -> list[ExtractedConcept]:
    seen = set()
    deduped = []

    for item in items:
        key = (
            item.concept.lower(),
            item.concept_type,
            item.domain,
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

    return deduped
