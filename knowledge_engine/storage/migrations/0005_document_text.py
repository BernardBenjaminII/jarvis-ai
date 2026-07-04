def up(conn):

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS document_text (

            file_path TEXT PRIMARY KEY,

            text TEXT,

            extractor TEXT NOT NULL,

            content_chars INTEGER DEFAULT 0,

            checksum TEXT,

            status TEXT NOT NULL,

            error TEXT,

            extracted_at TEXT NOT NULL

        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_text_status
        ON document_text(status)
        """
    )
