"""JARVIS Arsenal R3.2: metadata-only SQLite catalog."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import uuid
from pathlib import Path

from core.security.external_arsenal import LIBRARIES

DEFAULT_ROOT = Path("/mnt/jarvis_arsenal")
EXPECTED_UUID = "eb913241-2f20-4521-ae06-0c83f3552a3b"


def verify_storage(root: Path = DEFAULT_ROOT) -> bool:
    root = Path(root)

    try:
        result = subprocess.run(
            [
                "findmnt", "-n", "-T", str(root),
                "-t", "ext4", "-o", "UUID",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    return (
        result.returncode == 0
        and result.stdout.strip() == EXPECTED_UUID
    )


def build_catalog(
    root: Path = DEFAULT_ROOT,
    database: Path | None = None,
) -> dict:
    root = Path(root)

    if not verify_storage(root):
        raise RuntimeError(
            "Expected JARVIS Arsenal SSD is not mounted"
        )

    if database is None:
        database = (
            root / "jarvis_index/catalog/arsenal.sqlite3"
        )

    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)

    temporary = database.with_name(
        database.name + ".tmp-" + uuid.uuid4().hex
    )

    counts = {}

    try:
        with sqlite3.connect(temporary) as connection:
            connection.execute("""
                CREATE TABLE resources (
                    library TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    PRIMARY KEY (library, relative_path)
                )
            """)

            for library, relative in LIBRARIES.items():
                base = root / relative

                if not base.is_dir():
                    raise RuntimeError(
                        f"Missing arsenal library: {library}"
                    )

                count = 0

                for directory, dirs, files in os.walk(
                    base, followlinks=False
                ):
                    dirs[:] = sorted(
                        name for name in dirs
                        if name != ".git"
                        and not (
                            Path(directory) / name
                        ).is_symlink()
                    )

                    for filename in sorted(files):
                        path = Path(directory) / filename

                        if path.is_symlink() or not path.is_file():
                            continue

                        try:
                            size = path.stat().st_size
                        except OSError as exc:
                            raise RuntimeError(
                                f"Cannot inspect {path}"
                            ) from exc

                        relative_path = (
                            path.relative_to(base).as_posix()
                        )

                        connection.execute(
                            """
                            INSERT INTO resources
                            (library, relative_path,
                             filename, size_bytes)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                library,
                                relative_path,
                                filename,
                                size,
                            ),
                        )
                        count += 1

                counts[library] = count

            connection.commit()

        if not verify_storage(root):
            raise RuntimeError(
                "Arsenal SSD identity changed during indexing"
            )

        os.replace(temporary, database)

        return {
            "state": "ready",
            "database": str(database),
            "libraries": counts,
            "total_resources": sum(counts.values()),
            "execution_authorized": False,
        }

    finally:
        if temporary.exists():
            temporary.unlink()


def search_catalog(
    query: str,
    database: Path = (
        DEFAULT_ROOT
        / "jarvis_index/catalog/arsenal.sqlite3"
    ),
    limit: int = 30,
) -> list[dict]:
    query = query.strip()

    if not query or len(query) > 100:
        raise ValueError("Query must contain 1-100 characters")

    limit = max(1, min(int(limit), 50))

    with sqlite3.connect(
        database.as_uri() + "?mode=ro",
        uri=True,
    ) as connection:
        rows = connection.execute(
            """
            SELECT library, relative_path,
                   filename, size_bytes
            FROM resources
            WHERE instr(
                lower(relative_path), lower(?)
            ) > 0
            ORDER BY library, relative_path
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()

    return [
        {
            "library": row[0],
            "path": row[1],
            "name": row[2],
            "size_bytes": row[3],
        }
        for row in rows
    ]
