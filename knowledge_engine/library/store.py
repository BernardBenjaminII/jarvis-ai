from knowledge_engine.library.models import LibraryRecord


class LibraryCatalogStore:

    def __init__(self, db):

        self.db = db

    def upsert(
        self,
        record: LibraryRecord,
    ):

        with self.db.connect() as conn:

            conn.execute(
                """
                INSERT INTO library_catalog(

                    document_path,

                    filename,

                    extension,

                    category,

                    provider,

                    title,

                    subtitle,

                    author,

                    publisher,

                    publication_year,

                    edition,

                    isbn,

                    subject,

                    keywords,

                    language,

                    pages,

                    fingerprint

                )

                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

                ON CONFLICT(document_path)

                DO UPDATE SET

                    filename=excluded.filename,

                    extension=excluded.extension,

                    category=excluded.category,

                    provider=excluded.provider,

                    title=excluded.title,

                    subtitle=excluded.subtitle,

                    author=excluded.author,

                    publisher=excluded.publisher,

                    publication_year=excluded.publication_year,

                    edition=excluded.edition,

                    isbn=excluded.isbn,

                    subject=excluded.subject,

                    keywords=excluded.keywords,

                    language=excluded.language,

                    pages=excluded.pages,

                    fingerprint=excluded.fingerprint,

                    cataloged_at=CURRENT_TIMESTAMP
                """,

                (

                    record.document_path,

                    record.filename,

                    record.extension,

                    record.category,

                    record.provider,

                    record.title,

                    record.subtitle,

                    record.author,

                    record.publisher,

                    record.publication_year,

                    record.edition,

                    record.isbn,

                    record.subject,

                    record.keywords,

                    record.language,

                    record.pages,

                    record.fingerprint,

                ),
            )

    def summary(self):

        with self.db.connect() as conn:

            total = conn.execute(

                "SELECT COUNT(*) FROM library_catalog"

            ).fetchone()[0]

        return {

            "library_records": total

        }
