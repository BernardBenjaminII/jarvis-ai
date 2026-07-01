class StructureStore:
    def __init__(self, db):
        self.db = db

    def replace(self, document_path: str, nodes: list) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "DELETE FROM document_structure WHERE document_path = ?",
                (document_path,),
            )

            conn.executemany(
                """
                INSERT INTO document_structure (
                    document_path, title, level, page,
                    order_index, parent_title, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        node.document_path,
                        node.title,
                        node.level,
                        node.page,
                        node.order_index,
                        node.parent_title,
                        node.source,
                    )
                    for node in nodes
                ],
            )

    def summary(self):
        with self.db.connect() as conn:
            return conn.execute(
                """
                SELECT source, COUNT(*)
                FROM document_structure
                GROUP BY source
                ORDER BY COUNT(*) DESC
                """
            ).fetchall()
