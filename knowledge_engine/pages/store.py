class PageStore:

    def __init__(self, db):
        self.db = db

    def replace_pages(
        self,
        document_path,
        pages,
    ):

        with self.db.connect() as conn:

            conn.execute(

                """
                DELETE
                FROM document_pages
                WHERE document_path=?
                """,

                (document_path,),
            )

            conn.executemany(

                """
                INSERT INTO document_pages(

                    document_path,

                    page_number,

                    text

                )

                VALUES(?,?,?)
                """,

                pages,
            )
