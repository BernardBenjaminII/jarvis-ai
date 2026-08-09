from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any

from .contracts import Candidate


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".md",
    ".txt",
    ".html",
    ".htm",
    ".docx",
    ".epub",
    ".json",
    ".csv",
    ".xml",
}


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _open_ro(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    return connection


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    if not _table_exists(connection, table):
        return set()
    return {
        str(row["name"])
        for row in connection.execute(
            f"PRAGMA table_info({_q(table)})"
        )
    }


def _resolve_path(row: dict[str, Any], knowledge_root: Path) -> Path | None:
    for key in (
        "file_path",
        "document_path",
        "path",
        "source_path",
        "local_path",
        "relative_path",
    ):
        value = row.get(key)
        if not value:
            continue
        path = Path(str(value)).expanduser()
        if not path.is_absolute():
            path = knowledge_root / path
        return path
    return None


def _candidate_id(row: dict[str, Any], path: Path) -> str:
    for key in ("id", "classification_id", "document_id", "source_id"):
        value = row.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()
    return f"path:{digest}"


def _runtime_paths(runtime_catalog: Path) -> set[str]:
    connection = _open_ro(runtime_catalog)
    try:
        if not _table_exists(connection, "runtime_documents"):
            return set()
        columns = _columns(connection, "runtime_documents")
        key = "file_path" if "file_path" in columns else None
        if key is None:
            return set()
        return {
            str(row[key])
            for row in connection.execute(
                f"""
                SELECT {_q(key)}
                FROM runtime_documents
                WHERE {_q(key)} IS NOT NULL
                """
            )
        }
    finally:
        connection.close()


def discover_candidates(
    *,
    runtime_catalog: Path,
    inventory_catalog: Path,
    knowledge_root: Path,
) -> tuple[Candidate, ...]:
    runtime_existing = _runtime_paths(runtime_catalog)
    runtime = _open_ro(runtime_catalog)
    inventory = _open_ro(inventory_catalog)

    try:
        source_connection = runtime
        source_table = "knowledge_classifications"

        if not _table_exists(runtime, source_table):
            source_connection = inventory
            for table in ("documents", "knowledge_index", "library_catalog"):
                if _table_exists(inventory, table):
                    source_table = table
                    break
            else:
                return ()

        rows = [
            dict(row)
            for row in source_connection.execute(
                f"SELECT * FROM {_q(source_table)}"
            )
        ]

        candidates = []

        for row in rows:
            path = _resolve_path(row, knowledge_root)
            if path is None:
                continue
            path_string = str(path)
            extension = path.suffix.casefold()

            if path_string in runtime_existing:
                continue
            if extension not in SUPPORTED_EXTENSIONS:
                continue
            if not path.is_file():
                continue
            try:
                if path.stat().st_size <= 0:
                    continue
            except OSError:
                continue

            candidates.append(
                Candidate(
                    candidate_id=_candidate_id(row, path),
                    path=path_string,
                    extension=extension,
                    sha256=(
                        str(row.get("sha256"))
                        if row.get("sha256")
                        else None
                    ),
                    title=(
                        str(row.get("title"))
                        if row.get("title")
                        else path.name
                    ),
                    category=(
                        str(
                            row.get("category")
                            or row.get("domain")
                            or row.get("subject")
                            or ""
                        )
                        or None
                    ),
                    source_row=row,
                )
            )

        candidates.sort(
            key=lambda item: (
                item.extension,
                item.path.casefold(),
                item.candidate_id,
            )
        )
        return tuple(candidates)
    finally:
        runtime.close()
        inventory.close()
