from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from core.knowledge_catalog.classifiers.subject_assignment import assign_subject


RULE_FILE = Path("knowledge/ontology/keyword_rules.yaml")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_keyword_rules() -> dict:
    if not RULE_FILE.exists():
        return {}
    data = yaml.safe_load(RULE_FILE.read_text(encoding="utf-8")) or {}
    return data.get("rules", {})


def normalize_text(path: Path) -> str:
    return " ".join(
        [
            str(path).lower(),
            path.name.lower(),
            path.stem.lower().replace("_", " ").replace("-", " "),
            str(path.parent).lower().replace("_", " ").replace("-", " "),
        ]
    )


def digest_path(path: Path) -> dict:
    text = normalize_text(path)
    rules = load_keyword_rules()

    subject_result = assign_subject(path)
    subject = subject_result.get("subject")
    concepts = set(subject_result.get("concepts", []))
    keywords = set()

    best_keyword_subject = None
    best_hits = 0
    best_rule = None

    for _, rule in rules.items():
        hits = 0

        for kw in rule.get("keywords", []):
            if kw.lower() in text:
                hits += 1
                keywords.add(kw.lower())

        if hits > best_hits:
            best_hits = hits
            best_keyword_subject = rule.get("subject")
            best_rule = rule

    if best_keyword_subject and (not subject or subject == "unknown"):
        subject = best_keyword_subject

    if best_rule:
        for concept in best_rule.get("concepts", []):
            concepts.add(concept)

    confidence = subject_result.get("confidence", 0.0)

    if best_hits:
        confidence = max(confidence, min(0.50 + best_hits * 0.15, 1.0))

    return {
        "file_path": str(path),
        "sha256": sha256_file(path),
        "title": path.stem.replace("_", " ").replace("-", " ").strip(),
        "file_type": path.suffix.lower().lstrip("."),
        "size_bytes": path.stat().st_size,
        "subject": subject if subject and subject != "unknown" else None,
        "concepts": sorted(concepts),
        "keywords": sorted(keywords),
        "confidence": confidence,
        "assigned_by": "folder_rules+keyword_rules" if best_hits else subject_result.get("method", "folder_rules"),
    }
