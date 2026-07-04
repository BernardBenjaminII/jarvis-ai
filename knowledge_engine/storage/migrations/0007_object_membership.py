TABLES = ["knowledge_object_members"]


def up(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_object_members(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_uuid TEXT NOT NULL,
            file_path TEXT NOT NULL,
            member_role TEXT NOT NULL,
            member_type TEXT NOT NULL,
            processor_hint TEXT,
            importance INTEGER NOT NULL DEFAULT 50,
            reason TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(object_uuid, file_path)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_object_members_uuid
        ON knowledge_object_members(object_uuid)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_object_members_role
        ON knowledge_object_members(member_role)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_object_members_type
        ON knowledge_object_members(member_type)
        """
    )
