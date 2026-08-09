from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any

def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def exists(conn, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None

def cols(conn, table: str) -> list[str]:
    if not exists(conn, table):
        return []
    return [str(r["name"]) for r in conn.execute(f"PRAGMA table_info({q(table)})")]

def rows(conn, table: str) -> list[dict[str, Any]]:
    if not exists(conn, table):
        return []
    return [dict(r) for r in conn.execute(f"SELECT * FROM {q(table)}")]

def count(conn, table: str) -> int:
    if not exists(conn, table):
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {q(table)}").fetchone()[0])
