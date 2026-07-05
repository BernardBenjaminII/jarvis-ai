from __future__ import annotations

import json

from knowledge_engine.resource_inspection.inspectors import inspect_resource, to_metadata_json
from knowledge_engine.resource_inspection.models import ResourceInspection
from knowledge_engine.resource_inspection.store import ResourceInspectionStore, init_resource_inspection


class ResourceInspectionBuilder:
    def __init__(self, db):
        self.db = db
        self.store = ResourceInspectionStore(db)

    def inspect(self, limit: int | None = None, root_filter: str | None = None) -> dict:
        inspected = 0
        errors: list[tuple[str, str]] = []

        sql = """
            SELECT
                object_uuid,
                root_path,
                object_path,
                object_name,
                object_type,
                primary_file_path,
                file_count,
                total_size_bytes,
                reason
            FROM knowledge_objects
            WHERE 1=1
        """

        params: list[object] = []

        if root_filter:
            sql += " AND object_path LIKE ?"
            params.append(f"%{root_filter}%")

        sql += " ORDER BY object_path"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        with self.db.connect() as conn:
            init_resource_inspection(conn)
            rows = conn.execute(sql, params).fetchall()

            for row in rows:
                try:
                    data = inspect_resource(row, conn)

                    inspection = ResourceInspection(
                        object_uuid=row["object_uuid"],
                        object_path=row["object_path"],
                        object_type=row["object_type"],
                        title=data.get("title"),
                        description=data.get("description"),
                        language=data.get("language"),
                        primary_subject=data.get("primary_subject"),
                        keywords=data.get("keywords"),
                        metadata_json=to_metadata_json(data),
                        status="inspected",
                        error=None,
                    )

                    self.store.upsert(inspection)
                    inspected += 1

                except Exception as exc:
                    errors.append((row["object_path"], str(exc)))

                    failure = ResourceInspection(
                        object_uuid=row["object_uuid"],
                        object_path=row["object_path"],
                        object_type=row["object_type"],
                        title=row["object_name"],
                        description=None,
                        language=None,
                        primary_subject=None,
                        keywords=None,
                        metadata_json=json.dumps({}),
                        status="failed",
                        error=str(exc),
                    )
                    self.store.upsert(failure)

        return {
            "resources_inspected": inspected,
            "inspection_errors": errors,
        }
