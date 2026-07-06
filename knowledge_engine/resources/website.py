from __future__ import annotations

import sqlite3
from pathlib import Path

from knowledge_engine.resources.base import ResourceDetector
from knowledge_engine.resources.models import ResourceGuess
from knowledge_engine.resources.utils import clean_object_name


WEB_EXTENSIONS = {
    ".html", ".htm", ".css", ".js", ".json", ".png", ".jpg",
    ".jpeg", ".gif", ".svg", ".webp", ".ico",
}


class WebsiteDetector(ResourceDetector):
    def detect(self, row: sqlite3.Row) -> ResourceGuess | None:
        file_path = Path(row["file_path"])
        ext = file_path.suffix.lower()

        if ext not in WEB_EXTENSIONS:
            return None

        bundle = self._find_enclosing_html_bundle(file_path)

        if bundle is None:
            return None

        primary = bundle / "index.html"

        return ResourceGuess(
            object_path=bundle,
            object_name=clean_object_name(bundle),
            object_type_hint="website_archive",
            primary_file_path=str(primary),
            confidence=0.99,
            reason="resource detector: enclosing website bundle directory",
        )

    def _find_enclosing_html_bundle(self, path: Path) -> Path | None:
        for parent in [path] + list(path.parents):
            name = parent.name.lower()

            if name.endswith((".html", ".htm")) and parent != path:
                return parent

        return None
