from __future__ import annotations

import sqlite3
import tempfile

from pathlib import Path

from dev.as1.global_identity_resolver import (
    REL_AMBIGUOUS,
    REL_EXACT_SHA,
    REL_NORMALIZED_CONTENT,
    ensure_schema,
    load_fingerprints,
    resolve,
)


def build_state(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    conn.execute(
        """
        CREATE TABLE runtime_fingerprints (
            runtime_document_id INTEGER PRIMARY KEY,
            sha256 TEXT,
            content_fp TEXT NOT NULL,
            structural_fp TEXT,
            char_count INTEGER,
            token_count INTEGER
        )
        """
    )

    rows = [
        # Exact raw duplicate
        (1, "sha-a", "content-a", "struct-a", 1000, 200),
        (2, "sha-a", "content-a", "struct-a", 1000, 200),

        # Same normalized content, different raw SHA
        (3, "sha-b", "content-b", "struct-b", 2000, 400),
        (4, "sha-c", "content-b", "struct-b", 2000, 400),

        # Structural duplicate
        (5, "sha-d", "content-c", "struct-c", 3000, 600),
        (6, "sha-e", "content-d", "struct-c", 2990, 598),

        # Ambiguous structural candidate
        (7, "sha-f", "content-e", "struct-d", 4000, 800),
        (8, "sha-g", "content-f", "struct-d", 3650, 730),

        # Distinct singleton
        (9, "sha-h", "content-g", "struct-e", 5000, 1000),
    ]

    conn.executemany(
        """
        INSERT INTO runtime_fingerprints (
            runtime_document_id,
            sha256,
            content_fp,
            structural_fp,
            char_count,
            token_count
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    ensure_schema(conn)
    conn.commit()

    return conn


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "state.sqlite"

        conn = build_state(db)

        fingerprints = load_fingerprints(conn)

        assert len(fingerprints) == 9

        stats = resolve(
            fingerprints,
            conn,
        )

        assert stats["fingerprints_examined"] == 9
        assert stats["exact_groups"] >= 1
        assert stats["content_groups"] >= 1
        assert stats["structural_edges"] >= 1
        assert stats["ambiguous_edges"] >= 1

        exact = conn.execute(
            """
            SELECT COUNT(*)
            FROM as1_identity_edges
            WHERE relationship=?
            """,
            (REL_EXACT_SHA,),
        ).fetchone()[0]

        content = conn.execute(
            """
            SELECT COUNT(*)
            FROM as1_identity_edges
            WHERE relationship=?
            """,
            (REL_NORMALIZED_CONTENT,),
        ).fetchone()[0]

        ambiguous = conn.execute(
            """
            SELECT COUNT(*)
            FROM as1_identity_edges
            WHERE relationship=?
            """,
            (REL_AMBIGUOUS,),
        ).fetchone()[0]

        assert exact >= 1
        assert content >= 1
        assert ambiguous >= 1

        # Every input record must receive durable membership.
        member_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM as1_identity_members
            """
        ).fetchone()[0]

        assert member_count == 9

        # Exact duplicates must share a canonical id.
        rows = conn.execute(
            """
            SELECT
                runtime_document_id,
                canonical_runtime_document_id
            FROM as1_identity_members
            WHERE runtime_document_id IN (1, 2)
            ORDER BY runtime_document_id
            """
        ).fetchall()

        assert len(rows) == 2
        assert rows[0][1] == rows[1][1] == 1

        # Normalized-content duplicates must share canonical id.
        rows = conn.execute(
            """
            SELECT
                runtime_document_id,
                canonical_runtime_document_id
            FROM as1_identity_members
            WHERE runtime_document_id IN (3, 4)
            ORDER BY runtime_document_id
            """
        ).fetchall()

        assert len(rows) == 2
        assert rows[0][1] == rows[1][1] == 3

        # Re-run must remain stable.
        stats2 = resolve(
            fingerprints,
            conn,
        )

        member_count2 = conn.execute(
            """
            SELECT COUNT(*)
            FROM as1_identity_members
            """
        ).fetchone()[0]

        assert member_count2 == 9
        assert stats2["components"] == stats["components"]

        integrity = conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        assert integrity == "ok"

        conn.close()

    print(
        "GENESIS AS1 PACK 3B GLOBAL IDENTITY TESTS: PASS"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
