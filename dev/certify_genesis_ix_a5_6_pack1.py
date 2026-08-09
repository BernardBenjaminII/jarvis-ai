from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from dev.metadata_lineage.audit import MetadataJoinLineageAudit


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        database = root / "catalog.sqlite"

        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE documents(path TEXT, category TEXT)"
        )
        connection.execute(
            "CREATE TABLE chunks(document_path TEXT, text TEXT)"
        )
        connection.executemany(
            "INSERT INTO documents VALUES (?, ?)",
            [
                ("/tmp/a.md", "programming"),
                ("/tmp/b.md", "medical"),
            ],
        )
        connection.executemany(
            "INSERT INTO chunks VALUES (?, ?)",
            [
                ("/tmp/a.md", "one"),
                ("/tmp/a.md", "two"),
                ("/tmp/b.md", "three"),
            ],
        )
        connection.commit()
        connection.close()

        before = database.read_bytes()
        report = MetadataJoinLineageAudit(
            project_root=root,
            knowledge_root=root,
        ).execute()
        after = database.read_bytes()

        checks = {
            "joins_found": (
                report.summary["join_candidate_count"] > 0
            ),
            "lineage_found": (
                report.summary["metadata_lineage_count"] > 0
            ),
            "propagation_found": (
                report.summary["propagation_path_count"] > 0
            ),
            "read_only": before == after,
            "serialization": (
                report.to_dict()["summary"][
                    "join_candidate_count"
                ]
                > 0
            ),
        }

    failed = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    print("=" * 76)
    print("GENESIS IX-A5.6 PACK 1 — METADATA JOIN AND LINEAGE AUDIT")
    print("=" * 76)
    print("Checks executed :", len(checks))
    print("Checks passed   :", len(checks) - len(failed))
    print("Checks failed   :", len(failed))
    print("Overall status  :", "EXCELLENT" if not failed else "FAILED")
    print("=" * 76)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
