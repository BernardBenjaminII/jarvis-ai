from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any

def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None

def columns(conn: sqlite3.Connection, table: str) -> list[str]:
    if not table_exists(conn, table):
        return []
    return [str(row["name"]) for row in conn.execute(f"PRAGMA table_info({qident(table)})")]

def count_rows(conn: sqlite3.Connection, table: str) -> int:
    if not table_exists(conn, table):
        return 0
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {qident(table)}").fetchone()[0])
    except sqlite3.DatabaseError:
        return 0

def distinct_count(conn: sqlite3.Connection, table: str, column: str) -> int:
    if column not in columns(conn, table):
        return 0
    try:
        return int(conn.execute(
            f"SELECT COUNT(DISTINCT {qident(column)}) FROM {qident(table)} "
            f"WHERE {qident(column)} IS NOT NULL AND TRIM(CAST({qident(column)} AS TEXT)) <> ''"
        ).fetchone()[0])
    except sqlite3.DatabaseError:
        return 0

def populated_count(conn: sqlite3.Connection, table: str, column: str) -> int:
    if column not in columns(conn, table):
        return 0
    try:
        return int(conn.execute(
            f"SELECT COUNT(*) FROM {qident(table)} "
            f"WHERE {qident(column)} IS NOT NULL AND TRIM(CAST({qident(column)} AS TEXT)) <> ''"
        ).fetchone()[0])
    except sqlite3.DatabaseError:
        return 0

def schema_signature(conn: sqlite3.Connection) -> tuple[str, ...]:
    rows = conn.execute(
        "SELECT type,name,tbl_name,COALESCE(sql,'') AS sql "
        "FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
    ).fetchall()
    return tuple(f"{r['type']}|{r['name']}|{r['tbl_name']}|{r['sql']}" for r in rows)

def file_identity_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    preferred = (
        "path", "file_path", "document_path", "source_path", "relative_path",
        "object_path", "local_path", "sha256", "content_sha256", "document_id", "id",
    )
    available = set(columns(conn, table))
    return [item for item in preferred if item in available]

def sample_values(conn: sqlite3.Connection, table: str, column: str, limit: int = 5) -> list[Any]:
    if column not in columns(conn, table):
        return []
    try:
        return [
            row[0] for row in conn.execute(
                f"SELECT {qident(column)} FROM {qident(table)} "
                f"WHERE {qident(column)} IS NOT NULL AND TRIM(CAST({qident(column)} AS TEXT)) <> '' "
                f"LIMIT ?",
                (limit,),
            ).fetchall()
        ]
    except sqlite3.DatabaseError:
        return []
