from __future__ import annotations

from pathlib import Path
import yaml


RULE_FILE = Path("knowledge/ontology/keyword_rules.yaml")


def load_keyword_rules() -> dict:
    if not RULE_FILE.exists():
        return {}

    data = yaml.safe_load(RULE_FILE.read_text(encoding="utf-8")) or {}
    return data.get("rules", {})


def classify_text(text: str) -> dict:
    text_l = text.lower()
    rules = load_keyword_rules()

    best = {
        "subject": None,
        "concepts": [],
        "confidence": 0.0,
        "method": "keyword_rules",
    }

    best_hits = 0

    for _, rule in rules.items():
        hits = 0

        for keyword in rule.get("keywords", []):
            if keyword.lower() in text_l:
                hits += 1

        if hits > best_hits:
            best_hits = hits
            best = {
                "subject": rule.get("subject"),
                "concepts": rule.get("concepts", []),
                "confidence": min(0.50 + hits * 0.15, 1.0),
                "method": "keyword_rules",
            }

    return best
