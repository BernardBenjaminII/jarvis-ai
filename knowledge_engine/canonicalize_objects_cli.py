from __future__ import annotations

import argparse

from knowledge_engine.ontology.object_classifier import classify_object
from knowledge_engine.storage.database import KnowledgeDatabase


def ensure_columns(conn) -> None:
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(knowledge_objects)")
    }

    if "canonical_type" not in existing:
        conn.execute("ALTER TABLE knowledge_objects ADD COLUMN canonical_type TEXT")

    if "canonical_confidence" not in existing:
        conn.execute("ALTER TABLE knowledge_objects ADD COLUMN canonical_confidence REAL")

    if "canonical_reason" not in existing:
        conn.execute("ALTER TABLE knowledge_objects ADD COLUMN canonical_reason TEXT")

    existing_registry = {
        row[1]
        for row in conn.execute("PRAGMA table_info(knowledge_registry)")
    }

    if "canonical_type" not in existing_registry:
        conn.execute("ALTER TABLE knowledge_registry ADD COLUMN canonical_type TEXT")

    if "canonical_confidence" not in existing_registry:
        conn.execute("ALTER TABLE knowledge_registry ADD COLUMN canonical_confidence REAL")

    if "canonical_reason" not in existing_registry:
        conn.execute("ALTER TABLE knowledge_registry ADD COLUMN canonical_reason TEXT")


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonicalize Knowledge Object types")
    parser.add_argument("--db", required=True)
    parser.add_argument("--root-filter", default=None)
    parser.add_argument("--limit", type=int, default=None)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)

    params = []
    sql = """
        SELECT object_uuid, object_path, object_type
        FROM knowledge_objects
    """

    if args.root_filter:
        sql += " WHERE object_path LIKE ?"
        params.append(f"%{args.root_filter}%")

    sql += " ORDER BY object_path"

    if args.limit:
        sql += " LIMIT ?"
        params.append(args.limit)

    counts: dict[str, int] = {}
    updated = 0

    with db.connect() as conn:
        ensure_columns(conn)
        rows = conn.execute(sql, params).fetchall()

        for row in rows:
            canonical_type, confidence, reason = classify_object(
                row["object_path"],
                row["object_type"],
            )

            conn.execute(
                """
                UPDATE knowledge_objects
                SET canonical_type=?,
                    canonical_confidence=?,
                    canonical_reason=?
                WHERE object_uuid=?
                """,
                (
                    canonical_type,
                    confidence,
                    reason,
                    row["object_uuid"],
                ),
            )

            conn.execute(
                """
                UPDATE knowledge_registry
                SET canonical_type=?,
                    canonical_confidence=?,
                    canonical_reason=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE object_uuid=?
                """,
                (
                    canonical_type,
                    confidence,
                    reason,
                    row["object_uuid"],
                ),
            )

            counts[canonical_type] = counts.get(canonical_type, 0) + 1
            updated += 1

        conn.commit()

    print(f"canonicalized: {updated}")
    for key, value in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
