from __future__ import annotations

import re

from .contracts import ClaimModality, ConstitutionalDomain

_MODALITY_RULES: tuple[tuple[ClaimModality, re.Pattern[str]], ...] = (
    (ClaimModality.MUST_NOT, re.compile(r"\bmust\s+not\b", re.I)),
    (ClaimModality.SHALL_NOT, re.compile(r"\bshall\s+not\b", re.I)),
    (ClaimModality.SHOULD_NOT, re.compile(r"\bshould\s+not\b", re.I)),
    (ClaimModality.MUST, re.compile(r"\bmust\b", re.I)),
    (ClaimModality.SHALL, re.compile(r"\bshall\b", re.I)),
    (ClaimModality.SHOULD, re.compile(r"\bshould\b", re.I)),
    (ClaimModality.MAY, re.compile(r"\bmay\b", re.I)),
)

_PRINCIPLE = re.compile(
    r"^(?:principle|rule|requirement|policy|doctrine|invariant|prohibition)\s*[:—-]",
    re.I,
)

_DOMAIN_KEYWORDS: tuple[tuple[ConstitutionalDomain, tuple[str, ...]], ...] = (
    (ConstitutionalDomain.KNOWLEDGE, ("knowledge", "catalog", "source", "provenance", "assimilation", "retrieval")),
    (ConstitutionalDomain.REASONING, ("reasoning", "inference", "hypothesis", "confidence", "cognition")),
    (ConstitutionalDomain.MEMORY, ("memory", "remember", "retention", "checkpoint")),
    (ConstitutionalDomain.PLANNING, ("plan", "planning", "objective", "mission design")),
    (ConstitutionalDomain.EXECUTION, ("execution", "execute", "action", "orchestration")),
    (ConstitutionalDomain.EXPERIENCE, ("experience", "learning", "lesson")),
    (ConstitutionalDomain.ENGINEERING, ("engineering", "software", "code", "test", "verification", "release")),
    (ConstitutionalDomain.GOVERNANCE, ("governance", "constitution", "ratification", "authority", "audit", "compliance")),
    (ConstitutionalDomain.SAFETY, ("safety", "harm", "hazard", "protected")),
    (ConstitutionalDomain.SECURITY, ("security", "permission", "authorization", "threat", "access control")),
    (ConstitutionalDomain.EVIDENCE, ("evidence", "observation", "traceability", "citation")),
    (ConstitutionalDomain.ORGANIZATION, ("organization", "directorate", "department", "office", "role")),
    (ConstitutionalDomain.INTERFACE, ("interface", "ui", "operator", "commander", "projection")),
    (ConstitutionalDomain.EXECUTIVE, ("executive", "decision", "commander", "mission")),
)


def detect_modality(text: str) -> ClaimModality | None:
    for modality, pattern in _MODALITY_RULES:
        if pattern.search(text):
            return modality
    if _PRINCIPLE.search(text.strip()):
        return ClaimModality.PRINCIPLE
    return None


def infer_domain(text: str, section_path: tuple[str, ...], path: str) -> tuple[ConstitutionalDomain, tuple[str, ...]]:
    haystack = " ".join((path, *section_path, text)).lower()
    scores: list[tuple[int, int, ConstitutionalDomain, tuple[str, ...]]] = []
    for order, (domain, keywords) in enumerate(_DOMAIN_KEYWORDS):
        matched = tuple(keyword for keyword in keywords if keyword in haystack)
        if matched:
            scores.append((len(matched), -order, domain, matched))
    if not scores:
        return ConstitutionalDomain.GENERAL, ("no domain keyword matched",)
    _, _, domain, matched = max(scores)
    return domain, tuple(f"keyword:{item}" for item in matched)
