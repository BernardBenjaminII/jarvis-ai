from __future__ import annotations

import contextlib
import io
from pathlib import Path

from core.semantic_digest.inspector import inspect_document


MAX_CHARS = 120_000


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:MAX_CHARS]
    except Exception:
        return ""


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader

        # Suppress noisy malformed-PDF warnings from pypdf.
        with contextlib.redirect_stderr(io.StringIO()):
            reader = PdfReader(str(path))
            chunks = []

            for page in reader.pages[:40]:
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""

                if text:
                    chunks.append(text)

                if sum(len(x) for x in chunks) >= MAX_CHARS:
                    break

        return "\n".join(chunks)[:MAX_CHARS]
    except Exception:
        return ""


def read_document(path: Path) -> str:
    inspection = inspect_document(path)

    if not inspection.readable:
        return ""

    if inspection.detected_type == "pdf":
        return read_pdf(path)

    if inspection.detected_type in {"txt", "md", "csv", "json", "xml", "html", "htm"}:
        return read_text_file(path)

    return ""
