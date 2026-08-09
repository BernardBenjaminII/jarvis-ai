from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


KEY_TOKENS = (
    "id",
    "document_id",
    "source_id",
    "chunk_id",
    "path",
    "file_path",
    "document_path",
    "relative_path",
    "source_path",
    "local_path",
    "hash",
    "sha256",
)

CATEGORY_TOKENS = (
    "category",
    "domain",
    "subject",
    "topic",
    "classification",
)


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def open_ro(path: Path):
    return sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )


def scalar(connection, sql: str, params=()):
    try:
        row = connection.execute(sql, params).fetchone()
        return None if row is None else row[0]
    except Exception:
        return None


def examples(connection, table: str, column: str, limit: int = 5) -> list[Any]:
    sql = (
        f"SELECT {qident(column)} "
        f"FROM {qident(table)} "
        f"WHERE {qident(column)} IS NOT NULL "
        f"AND TRIM(CAST({qident(column)} AS TEXT)) <> '' "
        f"GROUP BY {qident(column)} "
        f"ORDER BY COUNT(*) DESC "
        f"LIMIT ?"
    )

    try:
        return [
            row[0]
            for row in connection.execute(sql, (limit,)).fetchall()
        ]
    except Exception:
        return []


def profile_column(
    connection,
    table: str,
    column: str,
    row_count: int,
) -> dict[str, Any]:
    present = int(
        scalar(
            connection,
            (
                f"SELECT COUNT(*) FROM {qident(table)} "
                f"WHERE {qident(column)} IS NOT NULL "
                f"AND TRIM(CAST({qident(column)} AS TEXT)) <> ''"
            ),
        )
        or 0
    )
    distinct = int(
        scalar(
            connection,
            (
                f"SELECT COUNT(DISTINCT {qident(column)}) "
                f"FROM {qident(table)} "
                f"WHERE {qident(column)} IS NOT NULL "
                f"AND TRIM(CAST({qident(column)} AS TEXT)) <> ''"
            ),
        )
        or 0
    )

    return {
        "name": column,
        "present_count": present,
        "coverage": 0.0 if row_count == 0 else present / row_count,
        "distinct_count": distinct,
        "uniqueness": 0.0 if present == 0 else distinct / present,
        "examples": examples(connection, table, column),
        "key_like": any(
            token == column.casefold()
            or token in column.casefold()
            for token in KEY_TOKENS
        ),
        "category_like": any(
            token in column.casefold()
            for token in CATEGORY_TOKENS
        ),
    }


def profile_database(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    database = {
        "path": str(path.resolve()),
        "name": path.name,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "errors": [],
    }
    profiles: list[dict[str, Any]] = []

    if not path.is_file():
        database["errors"].append("missing")
        return database, profiles

    try:
        connection = open_ro(path)
    except Exception as exc:
        database["errors"].append(f"{type(exc).__name__}: {exc}")
        return database, profiles

    try:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """
        ).fetchall()

        for (table_name,) in tables:
            columns_info = connection.execute(
                f"PRAGMA table_info({qident(table_name)})"
            ).fetchall()
            columns = [str(row[1]) for row in columns_info]
            row_count = int(
                scalar(
                    connection,
                    f"SELECT COUNT(*) FROM {qident(table_name)}",
                )
                or 0
            )
            profiled = [
                profile_column(
                    connection,
                    table_name,
                    column,
                    row_count,
                )
                for column in columns
                if any(
                    token == column.casefold()
                    or token in column.casefold()
                    for token in (*KEY_TOKENS, *CATEGORY_TOKENS)
                )
            ]

            profiles.append(
                {
                    "database": path.name,
                    "database_path": str(path.resolve()),
                    "table": table_name,
                    "row_count": row_count,
                    "columns": columns,
                    "profiled_columns": profiled,
                }
            )
    finally:
        connection.close()

    return database, profiles
