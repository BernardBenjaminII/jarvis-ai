from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SubjectProbe:
    probe_id: str
    query: str
    expected_subjects: tuple[str, ...]
    expectation: str


def canonical_subject_probes() -> tuple[SubjectProbe, ...]:
    return (
        SubjectProbe(
            "SUBJECT-SHA256",
            "SHA-256",
            ("cybersecurity", "cryptography"),
            "known",
        ),
        SubjectProbe(
            "SUBJECT-FTS",
            "full text search",
            ("retrieval", "database", "programming"),
            "known",
        ),
        SubjectProbe(
            "SUBJECT-C",
            "professional C programming",
            ("programming", "computer_science"),
            "known",
        ),
        SubjectProbe(
            "SUBJECT-COMPUTER-ARCH",
            "computer architecture",
            ("computer_architecture", "computer_science"),
            "known",
        ),
        SubjectProbe(
            "SUBJECT-EXECUTIVE-DIRECTOR",
            "Executive Director",
            ("executive", "governance", "jarvis"),
            "known",
        ),
        SubjectProbe(
            "SUBJECT-ANCA",
            "ANCA vasculitis",
            ("medicine", "health"),
            "possible",
        ),
    )
