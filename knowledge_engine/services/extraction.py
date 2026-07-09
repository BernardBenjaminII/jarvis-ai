from __future__ import annotations

from pathlib import Path

from knowledge_engine.worker.extraction import extract_text


class ExtractionService:
    """
    Canonical extraction service.

    Workflows, CLI tools, Doctor, Librarian, and future agents
    should use this service instead of calling worker.extract_text()
    directly.
    """

    @staticmethod
    def extract(path: Path):

        return extract_text(path)
