from __future__ import annotations

from pathlib import Path
import re
import yaml

from core.semantic_digest.structural import extract_structure


RULE_FILE = Path("knowledge/ontology/keyword_rules.yaml")


def load_rules() -> dict:
    if not RULE_FILE.exists():
        return {}
    data = yaml.safe_load(RULE_FILE.read_text(encoding="utf-8")) or {}
    return data.get("rules", {})


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[_/\\-]+", " ", text)
    text = re.sub(r"[^a-z0-9+.# ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def analyze_semantics(path: Path, content: str) -> dict:
    structure = extract_structure(path, content)

    haystack = normalize(
        " ".join(
            [
                str(path),
                path.name,
                path.stem,
                str(path.parent),
                content,
                " ".join(structure["headings"]),
                " ".join(structure["terms"]),
            ]
        )
    )

    subject_scores: dict[str, int] = {}
    concept_scores: dict[str, int] = {}
    keyword_scores: dict[str, int] = {}

    for _, rule in load_rules().items():
        subject = rule.get("subject")
        concepts = rule.get("concepts", [])
        keywords = rule.get("keywords", [])

        hits = 0
        for keyword in keywords:
            kw = normalize(keyword)
            if kw and kw in haystack:
                hits += 1
                keyword_scores[kw] = keyword_scores.get(kw, 0) + 1

        if hits and subject:
            subject_scores[subject] = subject_scores.get(subject, 0) + hits
            for concept in concepts:
                concept_scores[concept] = concept_scores.get(concept, 0) + hits

    best_subject = None
    confidence = 0.0

    if subject_scores:
        best_subject, best_hits = max(subject_scores.items(), key=lambda x: x[1])
        confidence = min(0.45 + best_hits * 0.08, 1.0)

    concepts = [x[0] for x in sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)[:40]]
    keywords = [x[0] for x in sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:80]]

    # Add frequent extracted terms as low-level keywords.
    for term in structure["terms"][:30]:
        if term not in keywords:
            keywords.append(term)

    return {
        "subject": best_subject,
        "concepts": concepts,
        "keywords": keywords,
        "headings": structure["headings"],
        "terms": structure["terms"],
        "confidence": confidence,
        "assigned_by": "semantic_extraction",
        "content_chars": structure["content_chars"],
    }
