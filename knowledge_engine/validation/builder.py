from __future__ import annotations

from knowledge_engine.validation.store import init_validation


class KnowledgeValidationBuilder:
    def __init__(self, db):
        self.db = db

    def build(self, root_filter: str | None = None) -> dict:
        params: list[str] = []

        sql = """
            SELECT
                object_uuid,
                object_path,
                object_type,
                file_count,
                total_size_bytes,
                confidence
            FROM knowledge_objects
        """

        if root_filter:
            sql += " WHERE object_path LIKE ?"
            params.append(f"%{root_filter}%")

        validated = 0
        review = 0
        errors = []

        with self.db.connect() as conn:
            init_validation(conn)
            rows = conn.execute(sql, params).fetchall()

            for row in rows:
                try:
                    state, score, reason = self._validate(row)

                    conn.execute(
                        """
                        INSERT INTO knowledge_validation (
                            object_uuid,
                            object_path,
                            object_type,
                            validation_state,
                            score,
                            reason
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(object_uuid) DO UPDATE SET
                            object_path = excluded.object_path,
                            object_type = excluded.object_type,
                            validation_state = excluded.validation_state,
                            score = excluded.score,
                            reason = excluded.reason,
                            validated_at = CURRENT_TIMESTAMP
                        """,
                        (
                            row["object_uuid"],
                            row["object_path"],
                            row["object_type"],
                            state,
                            score,
                            reason,
                        ),
                    )

                    conn.execute(
                        """
                        UPDATE knowledge_registry
                        SET validation_state = ?,
                            lifecycle_state = CASE
                                WHEN ? = 'validated' THEN 'validated'
                                ELSE lifecycle_state
                            END,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE object_uuid = ?
                        """,
                        (
                            state,
                            state,
                            row["object_uuid"],
                        ),
                    )

                    if state == "validated":
                        validated += 1
                    else:
                        review += 1

                except Exception as exc:
                    errors.append((row["object_path"], str(exc)))

            conn.commit()

        return {
            "validated": validated,
            "review": review,
            "validation_errors": errors,
        }

    def _validate(self, row) -> tuple[str, float, str]:
        object_type = row["object_type"]
        file_count = int(row["file_count"])
        total_size = int(row["total_size_bytes"])
        confidence = float(row["confidence"])

        if file_count <= 0:
            return "review", 0.0, "object has no files"

        if total_size <= 0:
            return "review", 0.1, "object has zero total size"

        if object_type in {"single_file", "folder_collection"}:
            return "review", 0.5, f"{object_type} requires human review"

        if confidence < 0.65:
            return "review", confidence, "low object confidence"

        return "validated", min(1.0, confidence), "basic structural validation passed"
