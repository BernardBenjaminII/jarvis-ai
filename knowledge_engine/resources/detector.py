from __future__ import annotations

import sqlite3

from knowledge_engine.resources.factory import ResourceDetectorFactory
from knowledge_engine.resources.models import ResourceGuess


_factory = ResourceDetectorFactory()


def detect_resource(row: sqlite3.Row) -> ResourceGuess:
    return _factory.detect(row)
