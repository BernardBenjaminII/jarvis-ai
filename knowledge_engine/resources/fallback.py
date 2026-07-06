from __future__ import annotations

import sqlite3
from pathlib import Path

from knowledge_engine.resources.base import ResourceDetector
from knowledge_engine.resources.models import ResourceGuess
from knowledge_engine.resources.utils import clean_object_name


class FallbackDetector(ResourceDetector):
    def detect(self, row: sqlite3.Row) -> ResourceGuess:
        file_path = Path(row["file_path"])
        relative = Path(row["relative_path"])

        if len(relative.parts) > 1:
            return ResourceGuess(
                object_path=file_path.parent,
                object_name=clean_object_name(file_path.parent),
                object_type_hint=None,
                primary_file_path=None,
                confidence=0.60,
                reason="fallback: grouped by parent folder",
            )

        return ResourceGuess(
            object_path=file_path,
            object_name=clean_object_name(file_path),
            object_type_hint=None,
            primary_file_path=str(file_path),
            confidence=0.50,
            reason="fallback: single loose file",
        )
