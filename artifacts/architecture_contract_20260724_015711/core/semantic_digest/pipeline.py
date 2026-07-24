from __future__ import annotations

from pathlib import Path

from core.knowledge_catalog.digest import sha256_file
from core.semantic_digest.analyzer import analyze_semantics
from core.semantic_digest.inspector import inspect_document
from core.semantic_digest.readers import read_document


def process_document(path: Path) -> dict:
    path = Path(path)
    inspection = inspect_document(path)
    content = read_document(path)
    semantic = analyze_semantics(path, content)

    return {
        "file_path": str(path),
        "sha256": sha256_file(path),
        "title": path.stem.replace("_", " ").replace("-", " ").strip(),
        "file_type": path.suffix.lower().lstrip("."),
        "detected_type": inspection.detected_type,
        "inspection_reason": inspection.reason,
        "readable": inspection.readable,
        "size_bytes": path.stat().st_size,
        "subject": semantic.get("subject"),
        "concepts": semantic.get("concepts", []),
        "keywords": semantic.get("keywords", []),
        "headings": semantic.get("headings", []),
        "terms": semantic.get("terms", []),
        "confidence": semantic.get("confidence", 0.0),
        "assigned_by": semantic.get("assigned_by", "semantic_extraction"),
        "content_chars": semantic.get("content_chars", 0),
    }
