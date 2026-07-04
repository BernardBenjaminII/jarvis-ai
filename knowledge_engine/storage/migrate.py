from __future__ import annotations

import importlib
import pkgutil

from knowledge_engine.storage.database import KnowledgeDatabase


def ensure_migration_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations(
            version TEXT PRIMARY KEY,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def applied_versions(conn):
    return {
        row[0]
        for row in conn.execute(
            "SELECT version FROM schema_migrations"
        )
    }


def discover_migrations():
    import knowledge_engine.storage.migrations as migrations

    modules = []

    for info in pkgutil.iter_modules(migrations.__path__):
        if info.name[0].isdigit():
            modules.append(info.name)

    return sorted(modules)


def migrate(db_path):
    db = KnowledgeDatabase(db_path)

    with db.connect() as conn:

        ensure_migration_table(conn)

        applied = applied_versions(conn)

        for module_name in discover_migrations():

            if module_name in applied:
                continue

            module = importlib.import_module(
                f"knowledge_engine.storage.migrations.{module_name}"
            )

            print(f"Applying {module_name}")

            module.up(conn)

            conn.execute(
                """
                INSERT INTO schema_migrations(version)
                VALUES(?)
                """,
                (module_name,),
            )

        conn.commit()


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db",
        required=True,
    )

    args = parser.parse_args()

    migrate(args.db)
