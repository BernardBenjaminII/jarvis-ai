from __future__ import annotations

import re

STOP = {
    "a","an","and","are","as","at","be","by","do","does","for","from","how",
    "i","in","is","it","of","on","or","that","the","this","to","what","when",
    "where","which","who","why","with","work","works",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9_+#.-]+")


def analyze_query(query: str) -> tuple[str, ...]:
    terms = []
    seen = set()

    for raw in TOKEN_RE.findall(query):
        t = raw.strip("._-").casefold()
        if not t or t in STOP or len(t) < 2:
            continue
        if t not in seen:
            seen.add(t)
            terms.append(t)

    return tuple(terms)
