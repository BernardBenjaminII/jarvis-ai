from __future__ import annotations

import sqlite3
from pathlib import Path

from knowledge_engine.resources.base import ResourceDetector
from knowledge_engine.resources.models import ResourceGuess
from knowledge_engine.resources.utils import clean_object_name


SOURCE_EXTENSIONS = {
    ".py", ".c", ".cpp", ".h", ".hpp", ".java", ".js", ".ts",
    ".rs", ".go", ".sh", ".sql", ".yml", ".yaml", ".json",
}

PROJECT_MARKERS = {
    ".git", "pyproject.toml", "setup.py", "requirements.txt",
    "package.json", "Cargo.toml", "CMakeLists.txt", "Makefile",
    "pom.xml", "build.gradle",
}


class CodebaseDetector:
    def detect(self, row: sqlite3.Row) -> ResourceGuess | None:
        file_path = Path(row["file_path"])
        relative = Path(row["relative_path"])
        ext = file_path.suffix.lower()

        project_root = self._find_project_root_from_path(file_path)

        if project_root is not None:
            return ResourceGuess(
                object_path=project_root,
                object_name=clean_object_name(project_root),
                object_type_hint="codebase",
                primary_file_path=None,
                confidence=0.85,
                reason="resource detector: project marker in path",
            )

        if ext in SOURCE_EXTENSIONS and len(relative.parts) > 1:
            return ResourceGuess(
                object_path=file_path.parent,
                object_name=clean_object_name(file_path.parent),
                object_type_hint="source_collection",
                primary_file_path=None,
                confidence=0.70,
                reason="resource detector: source file grouped by parent folder",
            )

        return None

    def _find_project_root_from_path(self, path: Path) -> Path | None:
        parts = tuple(str(part) for part in path.parts)

        for marker in PROJECT_MARKERS:
            if marker in parts:
                idx = parts.index(marker)
                return Path(*parts[:idx]) if idx > 0 else None

        return None
