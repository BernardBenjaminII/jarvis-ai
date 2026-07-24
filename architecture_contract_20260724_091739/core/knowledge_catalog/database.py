"""Knowledge Catalog database lifecycle and schema compatibility."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog import schema as catalog_schema


OPTIONAL_ALTERS = [
    "ALTER TABLE catalog_documents ADD COLUMN detected_type TEXT",
    "ALTER TABLE catalog_documents ADD COLUMN inspection_reason TEXT",
    "ALTER TABLE catalog_documents ADD COLUMN readable INTEGER DEFAULT 0",
    "ALTER TABLE catalog_documents ADD COLUMN content_chars INTEGER DEFAULT 0",
]


def _schema_script(name: str) -> str:
    """Return a schema script when exported by the installed catalog generation.

    Knowledge Catalog deployments created at different Genesis stages do not
    all export the same optional schema constants. Required scripts remain
    mandatory; optional scripts resolve to an empty string instead of causing
    catalog import failure.
    """
    value = getattr(catalog_schema, name, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a SQL string")
    return value


def connect(db_path: Path = DEFAULT_CATALOG_DB) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(db_path: Path = DEFAULT_CATALOG_DB) -> None:
    """Apply the canonical schema without requiring obsolete optional exports."""
    required_scripts = (
        "SCHEMA_SQL",
        "COLLECTIONS_SQL",
        "CONCEPTS_SQL",
        "INGESTION_SQL",
    )

    with connect(Path(db_path)) as conn:
        for name in required_scripts:
            script = _schema_script(name)
            if not script.strip():
                raise RuntimeError(f"Required Knowledge Catalog schema missing: {name}")
            conn.executescript(script)

        # STRUCTURE_SQL existed in some catalog generations but not others.
        # Execute it only when the active schema exports it.
        structure_sql = _schema_script("STRUCTURE_SQL")
        if structure_sql.strip():
            conn.executescript(structure_sql)

        for statement in OPTIONAL_ALTERS:
            try:
                conn.execute(statement)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
