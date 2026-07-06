from __future__ import annotations

import hashlib
from pathlib import Path


def read_text(path: Path) -> str:
    ext = path.suffix.lower()

    if ext in {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    if ext == ".pdf":
        try:
            from knowledge_engine.extraction.extractors.pdf import PDFExtractor

            pages = PDFExtractor().extract(path)
            if isinstance(pages, list):
                return "\n\n".join(str(p) for p in pages)
            return str(pages)
        except Exception as exc:
            raise RuntimeError(f"PDF extraction failed for {path}: {exc}") from exc

    raise RuntimeError(f"Unsupported single_document extension: {ext}")


def checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(0, end - overlap)

    return chunks
