from __future__ import annotations

import sqlite3

from knowledge_engine.resources.book import BookDetector
from knowledge_engine.resources.codebase import CodebaseDetector
from knowledge_engine.resources.fallback import FallbackDetector
from knowledge_engine.resources.image import ImageDetector
from knowledge_engine.resources.models import ResourceGuess
from knowledge_engine.resources.website import WebsiteDetector


class ResourceDetectorFactory:
    def __init__(self) -> None:
        self.detectors = [
            WebsiteDetector(),
            BookDetector(),
            CodebaseDetector(),
            ImageDetector(),
            FallbackDetector(),
        ]

    def detect(self, row: sqlite3.Row) -> ResourceGuess:
        for detector in self.detectors:
            result = detector.detect(row)
            if result is not None:
                return result

        raise RuntimeError(f"No resource detector handled {row['file_path']}")
