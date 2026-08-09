from __future__ import annotations
import re
from .models import QueryAnalysis

QUOTED_RE = re.compile(r'"([^"]+)"')
TOKEN_RE = re.compile(r"[A-Za-z0-9_\-\u0600-\u06ff]{2,}")
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9\-]{2,}\b")

def analyze_query(query: str) -> QueryAnalysis:
    raw = query.strip()
    phrases = tuple(x.strip() for x in QUOTED_RE.findall(raw) if x.strip())
    terms = tuple(TOKEN_RE.findall(raw))
    entities = list(ACRONYM_RE.findall(raw))

    # Capitalized leading tokens and multiword proper-like phrases are weak entity hints.
    words = raw.split()
    for w in words:
        clean = re.sub(r"[^A-Za-z0-9\-]", "", w)
        if len(clean) >= 3 and clean[:1].isupper() and clean.upper() != clean:
            entities.append(clean)

    seen = set()
    unique_entities = []
    for e in entities:
        k = e.casefold()
        if k not in seen:
            seen.add(k)
            unique_entities.append(e)

    normalized = " ".join(terms)
    return QueryAnalysis(
        raw=raw,
        terms=terms,
        quoted_phrases=phrases,
        entities=tuple(unique_entities),
        normalized=normalized,
    )
