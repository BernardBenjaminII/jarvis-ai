from __future__ import annotations

from pathlib import Path

from core.knowledge_mapper.mapper import map_path
from core.knowledge_catalog.classifiers.keyword_classifier import classify_text


def assign_subject(path: Path) -> dict:
    folder_result = map_path(str(path))
    folder_subject = folder_result.get("subject")

    if folder_subject and folder_subject != "unknown":
        return {
            "subject": folder_subject,
            "concepts": [],
            "confidence": 0.95,
            "method": "folder_rules",
        }

    keyword_result = classify_text(str(path))

    if keyword_result.get("subject"):
        return keyword_result

    return {
        "subject": "unknown",
        "concepts": [],
        "confidence": 0.0,
        "method": "unclassified",
    }
