class PageStore:
    def __init__(self, db):
        self.db = db

    def replace_pages(self, document_path: str, pages: list[dict]) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "DELETE FROM document_pages WHERE document_path = ?",
                (document_path,),
            )
            conn.execute(
                "DELETE FROM document_pages_fts WHERE document_path = ?",
                (document_path,),
            )

            for page in pages:
                conn.execute(
                    """
                    INSERT INTO document_pages (
                        document_path,
                        page_number,
                        text
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        document_path,
                        page["page_number"],
                        page["text"],
                    ),
                )

                conn.execute(
                    """
                    INSERT INTO document_pages_fts (
                        document_path,
                        page_number,
                        text
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        document_path,
                        page["page_number"],
                        page["text"],
                    ),
                )

    def search(self, query: str, limit: int = 8) -> list[dict]:
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    document_path,
                    page_number,
                    snippet(document_pages_fts, 2, '[', ']', '...', 32)
                FROM document_pages_fts
                WHERE document_pages_fts MATCH ?
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()

        return [
            {
                "document_path": row[0],
                "page_number": row[1],
                "snippet": row[2],
            }
            for row in rows
        ]
