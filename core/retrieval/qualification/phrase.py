from __future__ import annotations
import re
from dataclasses import dataclass

QUOTED_RE = re.compile(r'"([^"]+)"|\'([^\']+)\'')

@dataclass(frozen=True, slots=True)
class PhraseAnalysis:
    score: float
    phrases: tuple[str, ...]
    matched: tuple[str, ...]

def extract_phrases(query: str) -> tuple[str, ...]:
    phrases = []
    for m in QUOTED_RE.finditer(query or ""):
        value = next(g for g in m.groups() if g)
        phrases.append(value.strip())
    tokens = re.findall(r"[A-Za-z0-9]+", query or "")
    if len(tokens) >= 3:
        phrases.append(" ".join(tokens[-min(6,len(tokens)):]))
    return tuple(dict.fromkeys(x for x in phrases if x))

def analyze_phrases(query: str, candidate_text: str) -> PhraseAnalysis:
    phrases = extract_phrases(query)
    if not phrases:
        return PhraseAnalysis(0.5, (), ())
    haystack = (candidate_text or "").casefold()
    matched = tuple(p for p in phrases if p.casefold() in haystack)
    return PhraseAnalysis(len(matched)/len(phrases), phrases, matched)
