from __future__ import annotations

from knowledge_engine.membership.classifier import classify_member


class KnowledgeMembershipBuilder:
    def __init__(self, db):
        self.db = db

    def build(self, root_filter: str | None = None, limit: int | None = None) -> dict:
        params = []

        sql = """
            SELECT kof.object_uuid,
                   kof.file_path,
                   kof.role
            FROM knowledge_object_files kof
            JOIN knowledge_objects ko
              ON ko.object_uuid = kof.object_uuid
        """

        if root_filter:
            sql += " WHERE kof.file_path LIKE ?"
            params.append(f"%{root_filter}%")

        sql += " ORDER BY kof.object_uuid, kof.file_path"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        counts: dict[str, int] = {}
        built = 0

        with self.db.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

            for row in rows:
                member_type, member_role, processor_hint, importance, reason = classify_member(
                    row["file_path"],
                    row["role"],
                )

                conn.execute(
                    """
                    INSERT INTO knowledge_object_members(
                        object_uuid,
                        file_path,
                        member_role,
                        member_type,
                        processor_hint,
                        importance,
                        reason
                    )
                    VALUES(?,?,?,?,?,?,?)
                    ON CONFLICT(object_uuid, file_path)
                    DO UPDATE SET
                        member_role=excluded.member_role,
                        member_type=excluded.member_type,
                        processor_hint=excluded.processor_hint,
                        importance=excluded.importance,
                        reason=excluded.reason
                    """,
                    (
                        row["object_uuid"],
                        row["file_path"],
                        member_role,
                        member_type,
                        processor_hint,
                        importance,
                        reason,
                    ),
                )

                counts[member_type] = counts.get(member_type, 0) + 1
                built += 1

            conn.commit()

        return {
            "members_built": built,
            "member_counts": counts,
        }
