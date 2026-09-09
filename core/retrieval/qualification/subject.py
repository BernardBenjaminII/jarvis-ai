from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .lexical import analyze_lexical


@dataclass(frozen=True, slots=True)
class SubjectAnalysis:
    score: float
    query_subject: str
    candidate_subject: str


_FILENAME_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".html", ".htm",
    ".doc", ".docx", ".odt", ".rtf",
    ".epub", ".mobi",
}


def _normalize_subject_text(value: str) -> str:
    """
    Normalize filename-like subject/title metadata for qualification.

    This normalization is intentionally local to subject analysis.  It does
    not alter global lexical tokenization or the original evidence metadata.
    """
    text = str(value or "").strip()

    if not text:
        return ""

    # Remove a common document extension when the subject/title is carrying
    # a filename rather than a semantic label.
    suffix = Path(text).suffix.lower()

    if suffix in _FILENAME_EXTENSIONS:
        text = text[: -len(suffix)]

    # Filename separators should form lexical token boundaries.
    text = text.replace("_", " ")

    # Hyphens between alphanumeric components are also common filename
    # separators.  Qualification needs those components independently
    # searchable (e.g. NIST-SP-800-61r3-Incident-Response).
    text = re.sub(r"(?<=\w)-(?=\w)", " ", text)

    # Collapse separator/whitespace artifacts without otherwise rewriting
    # the semantic content.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def analyze_subject(
    query: str,
    candidate_subject: str,
    candidate_title: str = "",
) -> SubjectAnalysis:
    normalized_subject = _normalize_subject_text(candidate_subject)
    normalized_title = _normalize_subject_text(candidate_title)

    combined = " ".join(
        x for x in (normalized_subject, normalized_title) if x
    )

    return SubjectAnalysis(
        analyze_lexical(query, combined).score,
        query,
        combined,
    )
