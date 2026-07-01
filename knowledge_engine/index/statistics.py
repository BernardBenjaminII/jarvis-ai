class KnowledgeIndexStatistics:
    def __init__(self, db):
        self.db = db

    def top_categories(self, limit: int = 20):
        with self.db.connect() as conn:
            return conn.execute(
                """
                SELECT COALESCE(category, 'uncategorized'), COUNT(*)
                FROM knowledge_index
                GROUP BY category
                ORDER BY COUNT(*) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
