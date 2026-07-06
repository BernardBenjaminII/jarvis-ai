from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod

from knowledge_engine.resources.models import ResourceGuess


class ResourceDetector(ABC):
    @abstractmethod
    def detect(self, row: sqlite3.Row) -> ResourceGuess | None:
        ...
