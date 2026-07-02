import json

from knowledge_engine.library.models import LibraryRecord


class LibraryCatalogBuilder:

    def __init__(

        self,

        db,

        store,

    ):

        self.db = db

        self.store = store

    def build(self):

        indexed = 0

        errors = []

        with self.db.connect() as conn:

            docs = conn.execute(

                """
                SELECT

                    path,

                    filename,

                    extension,

                    category,

                    sha256

                FROM documents

                ORDER BY filename
                """

            ).fetchall()

        for path, filename, extension, category, sha256 in docs:

            try:

                metadata = self._metadata(path)

                record = LibraryRecord(

                    document_path=path,

                    filename=filename,

                    extension=extension,

                    category=category,

                    provider=None,

                    title=metadata.get("title") or filename,

                    subtitle=metadata.get("subtitle"),

                    author=metadata.get("author"),

                    publisher=metadata.get("producer"),

                    publication_year=metadata.get("creationDate"),

                    edition=None,

                    isbn=None,

                    subject=metadata.get("subject"),

                    keywords=metadata.get("keywords"),

                    language=metadata.get("language"),

                    pages=metadata.get("pages"),

                    fingerprint=sha256,

                )

                self.store.upsert(record)

                indexed += 1

            except Exception as exc:

                errors.append(

                    (

                        path,

                        str(exc),

                    )

                )

        return {

            "library_cataloged": indexed,

            "library_errors": errors,

        }

    def _metadata(

        self,

        path,

    ):

        with self.db.connect() as conn:

            row = conn.execute(

                """

                SELECT metadata_json

                FROM inspections

                WHERE document_path=?

                """,

                (

                    path,

                ),

            ).fetchone()

        if row is None:

            return {}

        if not row[0]:

            return {}

        try:

            return json.loads(row[0])

        except Exception:

            return {}
