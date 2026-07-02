#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path

from core.knowledge_mapper.mapper import map_path

DEFAULT_DB = Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/librarian.sqlite")


def main() -> None:
    inserted = 0
    skipped = 0

    with sqlite3.connect(DEFAULT_DB) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT file_path, sha256
            FROM documents
            WHERE verification_status IS NULL
               OR verification_status = 'verified'
            """
        ).fetchall()

        for row in rows:
            file_path = row["file_path"]
            sha256 = row["sha256"]

            mapping = map_path(file_path)
            subject = mapping.get("subject", "unknown")

            if subject == "unknown":
                skipped += 1
                continue

            conn.execute(
                """
                INSERT OR IGNORE INTO document_subjects (
                    file_path, sha256, subject, confidence, assigned_by
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (file_path, sha256, subject, 0.95, "folder_rule"),
            )
            inserted += 1

        conn.commit()

    print(f"[OK] Subject backfill complete")
    print(f"Inserted/checked: {inserted}")
    print(f"Unknown/skipped:  {skipped}")


if __name__ == "__main__":
    main()
