from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .normalization import normalize_subject


DEFAULT_ALIASES = {
    "cybersecurity": {
        "cryptography",
        "security",
        "hashing",
        "sha256",
        "sha_256",
    },
    "cryptography": {
        "cybersecurity",
        "security",
        "hashing",
        "sha256",
        "sha_256",
    },
    "retrieval": {
        "full_text_search",
        "fts",
        "search",
        "information_retrieval",
    },
    "database": {
        "sqlite",
        "full_text_search",
        "fts",
        "data",
    },
    "programming": {
        "software",
        "software_engineering",
        "computer_programming",
        "c_programming",
    },
    "computer_science": {
        "computing",
        "programming",
        "computer_architecture",
        "software_engineering",
    },
    "computer_architecture": {
        "architecture",
        "computer_science",
        "hardware",
        "systems",
    },
    "executive": {
        "executive_director",
        "governance",
        "leadership",
        "organization",
    },
    "governance": {
        "executive",
        "executive_director",
        "organization",
        "management",
    },
    "jarvis": {
        "executive",
        "executive_director",
        "mission_control",
        "architecture",
    },
    "medicine": {
        "medical",
        "health",
        "vasculitis",
        "anca",
    },
    "health": {
        "medicine",
        "medical",
        "vasculitis",
        "anca",
    },
}


@dataclass(frozen=True, slots=True)
class TaxonomyMatch:
    exact_matches: tuple[str, ...]
    alias_matches: tuple[str, ...]
    aliases_considered: tuple[str, ...]
    overlap_score: float


def aliases_for(subjects: Iterable[str]) -> tuple[str, ...]:
    values = set()

    for subject in subjects:
        normalized = normalize_subject(subject)
        if not normalized:
            continue

        values.add(normalized)
        values.update(
            normalize_subject(item)
            for item in DEFAULT_ALIASES.get(normalized, ())
        )

    return tuple(sorted(item for item in values if item))


def compare_subjects(
    query_subjects: Iterable[str],
    candidate_subjects: Iterable[str],
) -> TaxonomyMatch:
    query = {
        normalize_subject(item)
        for item in query_subjects
        if normalize_subject(item)
    }
    candidate = {
        normalize_subject(item)
        for item in candidate_subjects
        if normalize_subject(item)
    }

    exact = tuple(sorted(query & candidate))
    query_aliases = set(aliases_for(query))
    candidate_aliases = set(aliases_for(candidate))
    alias = tuple(
        sorted(
            (query_aliases & candidate)
            | (candidate_aliases & query)
            | (query_aliases & candidate_aliases)
        )
    )
    aliases = tuple(sorted(query_aliases | candidate_aliases))

    denominator = max(1, len(query))
    overlap = min(
        1.0,
        (len(exact) + 0.5 * len(alias)) / denominator,
    )

    return TaxonomyMatch(
        exact_matches=exact,
        alias_matches=alias,
        aliases_considered=aliases,
        overlap_score=overlap,
    )
