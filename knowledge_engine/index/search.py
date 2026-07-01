class KnowledgeIndexSearch:
    def __init__(self, db):
        self.db = db

    def search(self, query: str, limit: int = 10) -> list[dict]:
        like = f"%{query.lower()}%"

        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    document_path,
                    title,
                    category,
                    extension,
                    pages,
                    toc_entries
                FROM knowledge_index
                WHERE
                    lower(filename) LIKE ?
                    OR lower(title) LIKE ?
                    OR lower(category) LIKE ?
                    OR lower(structure_terms) LIKE ?
                    OR lower(keywords) LIKE ?
                    OR lower(subject) LIKE ?
                ORDER BY toc_entries DESC, pages DESC
                LIMIT ?
                """,
                (like, like, like, like, like, like, limit),
            ).fetchall()

        return [
            {
                "document_path": row[0],
                "title": row[1],
                "category": row[2],
                "extension": row[3],
                "pages": row[4],
                "toc_entries": row[5],
            }
            for row in rows
        ]
