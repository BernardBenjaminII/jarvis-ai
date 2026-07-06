from __future__ import annotations

import argparse

from knowledge_engine.storage.database import KnowledgeDatabase
from knowledge_engine.queue.builder import ProcessingQueueBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Knowledge Object queue")
    parser.add_argument("--db", required=True)
    parser.add_argument("--root-filter", default=None)
    parser.add_argument("--limit", type=int, default=None)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)
    builder = ProcessingQueueBuilder()

    sql = """
        SELECT object_uuid, object_path, object_type, lifecycle_state
        FROM knowledge_registry
        WHERE lifecycle_state='validated'
          AND assimilation_state='not_queued'
    """
    params = []

    if args.root_filter:
        sql += " AND object_path LIKE ?"
        params.append(f"%{args.root_filter}%")

    sql += " ORDER BY object_path"

    if args.limit:
        sql += " LIMIT ?"
        params.append(args.limit)

    with db.connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        queue = builder.build_from_registry(rows)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_assimilation_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_uuid TEXT NOT NULL UNIQUE,
                object_path TEXT NOT NULL,
                object_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                queue_state TEXT NOT NULL,
                reason TEXT NOT NULL,
                queued_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        for item in queue:
            conn.execute(
                """
                INSERT INTO knowledge_assimilation_queue (
                    object_uuid,
                    object_path,
                    object_type,
                    priority,
                    queue_state,
                    reason
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(object_uuid) DO UPDATE SET
                    object_path=excluded.object_path,
                    object_type=excluded.object_type,
                    priority=excluded.priority,
                    queue_state=excluded.queue_state,
                    reason=excluded.reason,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    item.object_uuid,
                    item.object_path,
                    item.object_type,
                    item.priority,
                    "queued",
                    item.reason,
                ),
            )

            conn.execute(
                """
                UPDATE knowledge_registry
                SET assimilation_state='queued',
                    lifecycle_state='queued',
                    updated_at=CURRENT_TIMESTAMP
                WHERE object_uuid=?
                """,
                (item.object_uuid,),
            )

        conn.commit()

    print(f"queued: {len(queue)}")


if __name__ == "__main__":
    main()
