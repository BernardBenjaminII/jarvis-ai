from __future__ import annotations

from knowledge_engine.registry.models import RegistryRecord
from knowledge_engine.registry.store import KnowledgeRegistryStore


class KnowledgeRegistryBuilder:
    def __init__(self, db):
        self.db = db
        self.store = KnowledgeRegistryStore(db)

    def build(self, root_filter: str | None = None) -> dict:
        self.store.initialize()

        params: list[str] = []

        sql = """
            SELECT
                object_uuid,
                object_path,
                object_name,
                object_type,
                status,
                reason
            FROM knowledge_objects
        """

        if root_filter:
            sql += " WHERE object_path LIKE ?"
            params.append(f"%{root_filter}%")

        sql += " ORDER BY object_path"

        built = 0
        errors: list[tuple[str, str]] = []

        with self.db.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        for row in rows:
            try:
                record = RegistryRecord(
                    object_uuid=row["object_uuid"],
                    object_path=row["object_path"],
                    object_type=row["object_type"],
                    title=row["object_name"],
                    status="active",
                    lifecycle_state="registered",
                    validation_state="unvalidated",
                    assimilation_state="not_queued",
                    source="knowledge_objects",
                    trust_level="local",
                    duplicate_of=None,
                    notes=row["reason"],
                )

                self.store.upsert(record)
                built += 1

            except Exception as exc:
                errors.append((row["object_path"], str(exc)))

        return {
            "registry_records_built": built,
            "registry_errors": errors,
        }
