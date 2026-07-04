def up(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_info(
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
