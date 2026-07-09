from __future__ import annotations

import hashlib
from pathlib import Path

from knowledge_engine.processors.registry import default_registry


def checksum_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def extract_text(path: Path) -> tuple[str, str, str, str | None]:
    processor = default_registry().get(path)

    if processor is None:
        return "", "no_processor", "failed", f"no processor for {path.suffix or path.name}"

    result = processor.process(path)
    return result.text, result.processor, result.status, result.error
