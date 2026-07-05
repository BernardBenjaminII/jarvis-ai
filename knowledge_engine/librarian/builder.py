from __future__ import annotations

import hashlib

from knowledge_engine.librarian.classifier import classify_subject
from knowledge_engine.librarian.normalization import canonical_key, normalize_title
from knowledge_engine.librarian.quality import catalog_quality_score
from knowledge_engine.librarian.store import init_librarian, upsert_catalog_entry


def stable_group(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:16]


class LibrarianBuilder:
    def __init__(self, db):
        self.db = db

    def build(self, root_filter: str | None = None, limit: int | None = None) -> dict:
        cataloged = 0
        errors: list[tuple[str, str]] = []

        sql = """
            SELECT
                ko.object_uuid,
                ko.object_path,
                ko.object_name,
                ko.object_type,
                ko.file_count,
                ko.total_size_bytes,
                ko.reason,
                ri.title,
                ri.description,
                ri.language,
                ri.primary_subject,
                ri.keywords,
                ri.metadata_json
            FROM knowledge_objects ko
            LEFT JOIN resource_inspections ri
              ON ri.object_uuid = ko.object_uuid
            WHERE 1=1
        """

        params: list[object] = []

        if root_filter:
            sql += " AND ko.object_path LIKE ?"
            params.append(f"%{root_filter}%")

        sql += " ORDER BY ko.object_path"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        with self.db.connect() as conn:
            init_librarian(conn)
            rows = conn.execute(sql, params).fetchall()

            for row in rows:
                try:
                    display_title = row["title"] or row["object_name"]
                    canonical_title = normalize_title(display_title)

                    subject = row["primary_subject"]
                    subject_confidence = 0.75 if subject else 0.0
                    subject_reason = "from resource inspection" if subject else ""

                    if not subject:
                        subject, subject_confidence, subject_reason = classify_subject(
                            row["object_path"],
                            row["object_name"],
                            row["title"],
                            row["description"],
                            row["keywords"],
                            row["metadata_json"],
                        )

                    work_key = canonical_key(
                        display_title,
                        subject,
                        row["object_type"],
                    )

                    duplicate_group = stable_group(work_key) if canonical_title else None

                    quality_score = catalog_quality_score(
                        title=display_title,
                        subject=subject,
                        resource_type=row["object_type"],
                        keywords=row["keywords"],
                        metadata_json=row["metadata_json"],
                    )

                    upsert_catalog_entry(
                        conn,
                        object_uuid=row["object_uuid"],
                        object_path=row["object_path"],
                        object_type=row["object_type"],
                        canonical_title=canonical_title,
                        display_title=display_title,
                        subject=subject,
                        subject_confidence=subject_confidence,
                        subject_reason=subject_reason,
                        keywords=row["keywords"],
                        language=row["language"],
                        description=row["description"],
                        quality_score=quality_score,
                        work_key=work_key,
                        duplicate_group=duplicate_group,
                        metadata_json=row["metadata_json"] or "{}",
                    )

                    cataloged += 1

                except Exception as exc:
                    errors.append((row["object_path"], str(exc)))

            conn.commit()

        return {
            "resources_cataloged": cataloged,
            "librarian_errors": errors,
        }
