import json

from knowledge_engine.index.models import IndexRecord


class KnowledgeIndexBuilder:
    def __init__(self, db, index_store):
        self.db = db
        self.index_store = index_store

    def build(self) -> dict:
        indexed = 0
        errors = []

        with self.db.connect() as conn:
            documents = conn.execute(
                """
                SELECT path, filename, extension, category, sha256
                FROM documents
                ORDER BY path
                """
            ).fetchall()

        for path, filename, extension, category, sha256 in documents:
            try:
                metadata = self._metadata(path)
                structure = self._structure(path)

                record = IndexRecord(
                    document_path=path,
                    filename=filename,
                    extension=extension,
                    category=category,
                    title=metadata.get("title") or filename,
                    author=metadata.get("author"),
                    subject=metadata.get("subject"),
                    keywords=metadata.get("keywords"),
                    pages=metadata.get("pages"),
                    toc_entries=structure["toc_entries"],
                    structure_terms=structure["terms"],
                    language=metadata.get("language"),
                    fingerprint=sha256,
                )

                self.index_store.upsert(record)
                indexed += 1

            except Exception as exc:
                errors.append((path, str(exc)))

        return {
            "indexed": indexed,
            "index_errors": errors,
        }

    def _metadata(self, document_path: str) -> dict:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT metadata_json
                FROM inspections
                WHERE document_path = ?
                """,
                (document_path,),
            ).fetchone()

        if not row or not row[0]:
            return {}

        try:
            data = json.loads(row[0])
        except Exception:
            return {}

        return data if isinstance(data, dict) else {}

    def _structure(self, document_path: str) -> dict:
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT title
                FROM document_structure
                WHERE document_path = ?
                ORDER BY order_index
                """,
                (document_path,),
            ).fetchall()

        titles = [row[0] for row in rows if row[0]]

        return {
            "toc_entries": len(titles),
            "terms": " | ".join(titles) if titles else None,
        }
