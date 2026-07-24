from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.knowledge_catalog.classifiers.subject_assignment import assign_subject
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB, DEFAULT_KNOWLEDGE_ROOT
from core.knowledge_catalog.database import connect, migrate


SUPPORTED = {
    ".pdf", ".txt", ".md", ".json", ".xml", ".html", ".htm", ".epub", ".zim"
}


def main() -> None:
    migrate(DEFAULT_CATALOG_DB)

    inserted_subjects = 0
    inserted_concepts = 0
    skipped = 0

    with connect(DEFAULT_CATALOG_DB) as conn:
        for file in DEFAULT_KNOWLEDGE_ROOT.rglob("*"):
            if not file.is_file():
                continue

            if file.suffix.lower() not in SUPPORTED:
                continue

            result = assign_subject(file)
            subject = result.get("subject")

            if not subject or subject == "unknown":
                skipped += 1
                continue

            now = datetime.utcnow().isoformat()

            conn.execute(
                """
                INSERT OR REPLACE INTO document_subjects
                (file_path, subject, confidence, assigned_by, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(file),
                    subject,
                    result.get("confidence", 1.0),
                    result.get("method", "semantic_rules"),
                    now,
                ),
            )
            inserted_subjects += 1

            for concept in result.get("concepts", []):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO document_concepts
                    (file_path, concept, confidence, assigned_by, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(file),
                        concept,
                        result.get("confidence", 1.0),
                        result.get("method", "semantic_rules"),
                        now,
                    ),
                )
                inserted_concepts += 1

        conn.commit()

    print("[OK] Semantic backfill complete")
    print(f"Subjects inserted : {inserted_subjects}")
    print(f"Concepts inserted : {inserted_concepts}")
    print(f"Skipped           : {skipped}")


if __name__ == "__main__":
    main()
