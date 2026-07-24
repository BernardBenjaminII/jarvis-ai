from __future__ import annotations

from pathlib import Path

from core.knowledge_catalog.registrar import register_file, register_tree
from core.knowledge_catalog.paths import CATALOG_DB


def register(path: str | Path) -> dict:
    path = Path(path)

    if path.is_dir():
        return register_tree(path, db_path=CATALOG_DB)

    return register_file(path, db_path=CATALOG_DB)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="JARVIS Librarian → Knowledge Catalog bridge")
    parser.add_argument("path", help="File or directory to register into Knowledge Catalog")
    args = parser.parse_args()

    result = register(args.path)
    print(result)
