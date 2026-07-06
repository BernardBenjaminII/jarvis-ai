from __future__ import annotations

import sqlite3
from pathlib import Path

from knowledge_engine.resources.base import ResourceDetector
from knowledge_engine.resources.models import ResourceGuess
from knowledge_engine.resources.utils import clean_object_name


DOCUMENT_EXTENSIONS = {
    ".pdf", ".epub", ".doc", ".docx", ".txt", ".md", ".rtf",
    ".odt", ".ods", ".odp", ".ppt", ".pptx", ".xls", ".xlsx",
    ".csv", ".zim",
}


class BookDetector(ResourceDetector):
    def detect(self, row: sqlite3.Row) -> ResourceGuess | None:
        file_path = Path(row["file_path"])
        ext = file_path.suffix.lower()

        if ext not in DOCUMENT_EXTENSIONS:
            return None

        return ResourceGuess(
            object_path=file_path,
            object_name=clean_object_name(file_path),
            object_type_hint="single_document",
            primary_file_path=str(file_path),
            confidence=0.90,
            reason=f"resource detector: standalone document {ext}",
        )
