from __future__ import annotations

import argparse
import importlib
import pkgutil

from knowledge_engine.storage.database import KnowledgeDatabase


MIGRATION_PACKAGE = "knowledge_engine.storage.migrations"


def ensure_schema_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations(
            version TEXT PRIMARY KEY,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def applied(conn):
    return {
        row[0]
        for row in conn.execute(
            "SELECT version FROM schema_migrations"
        )
    }


def discover():
    package = importlib.import_module(MIGRATION_PACKAGE)

    migrations = []

    for module in pkgutil.iter_modules(package.__path__):
        name = module.name

        if name[:4].isdigit():
            migrations.append(name)

    return sorted(migrations)


def already_exists(conn, migration_module):
    """
    Optional helper.

    A migration may define:

        TABLES = [
            "document_text",
            "knowledge_registry",
            ...
        ]

    If every listed table already exists,
    the migration is recorded as applied
    without running it.
    """

    if not hasattr(migration_module, "TABLES"):
        return False

    existing = {
        row[0]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        )
    }

    return all(
        table in existing
        for table in migration_module.TABLES
    )


def migrate(db_path):

    db = KnowledgeDatabase(db_path)

    with db.connect() as conn:

        ensure_schema_table(conn)

        complete = applied(conn)

        for version in discover():

            if version in complete:
                continue

            module = importlib.import_module(
                f"{MIGRATION_PACKAGE}.{version}"
            )

            if already_exists(conn, module):

                print(
                    f"Adopting existing schema for {version}"
                )

            else:

                print(
                    f"Applying {version}"
                )

                module.up(conn)

            conn.execute(
                """
                INSERT INTO schema_migrations(version)
                VALUES(?)
                """,
                (version,),
            )

        conn.commit()


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db",
        required=True,
    )

    args = parser.parse_args()

    migrate(args.db)


if __name__ == "__main__":
    main()
