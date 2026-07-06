from __future__ import annotations

from pathlib import Path


class DuplicateDetector:
    def __init__(self, db):
        self.db = db

    def find_existing_destination(self, destination_path: str) -> str | None:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT destination_path
                FROM promotion_history
                WHERE destination_path=?
                LIMIT 1
                """,
                (destination_path,),
            ).fetchone()

        return row["destination_path"] if row else None

    def find_same_title_subject(
        self,
        *,
        object_uuid: str,
        title: str,
        subject: str | None,
        object_type: str,
    ) -> list[dict]:
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    object_uuid,
                    display_title,
                    subject,
                    object_type,
                    object_path,
                    quality_score
                FROM librarian_catalog
                WHERE object_uuid != ?
                  AND lower(display_title) = lower(?)
                  AND COALESCE(lower(subject), '') = COALESCE(lower(?), '')
                  AND object_type = ?
                ORDER BY quality_score DESC
                """,
                (
                    object_uuid,
                    title,
                    subject,
                    object_type,
                ),
            ).fetchall()

        return [dict(row) for row in rows]

    def classify_duplicate_risk(
        self,
        *,
        object_uuid: str,
        title: str,
        subject: str | None,
        object_type: str,
        destination_path: str,
    ) -> tuple[str, str]:
        if Path(destination_path).exists():
            return "duplicate_destination", "destination path already exists"

        existing = self.find_existing_destination(destination_path)
        if existing:
            return "duplicate_destination", "destination already recorded in promotion history"

        matches = self.find_same_title_subject(
            object_uuid=object_uuid,
            title=title,
            subject=subject,
            object_type=object_type,
        )

        if matches:
            return "possible_duplicate", f"{len(matches)} same-title catalog match(es)"

        return "unique", "no duplicate indicators found"
