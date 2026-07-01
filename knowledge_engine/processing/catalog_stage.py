from pathlib import Path

from knowledge_engine.document import DocumentRecord
from knowledge_engine.discovery.scanner import discover_files
from knowledge_engine.metadata.fingerprints import sha256_file


def category_from_path(root: Path, path: Path) -> str | None:
    relative = path.relative_to(root)
    return relative.parts[0] if len(relative.parts) > 1 else None


def build_record(root: Path, path: Path) -> DocumentRecord:
    stat = path.stat()

    return DocumentRecord(
        path=path.resolve(),
        root=root.resolve(),
        filename=path.name,
        extension=path.suffix.lower() or "[none]",
        size_bytes=stat.st_size,
        modified_time=stat.st_mtime,
        sha256=sha256_file(path),
        category=category_from_path(root, path),
    )


class CatalogStage:
    def __init__(self, catalog_store):
        self.catalog_store = catalog_store

    def run(self, root: Path) -> dict:
        scanned = 0
        errors = []
        paths = []

        for path in discover_files(root):
            try:
                record = build_record(root, path)
                self.catalog_store.upsert_document(record)
                scanned += 1
                paths.append(path)
            except Exception as exc:
                errors.append((str(path), str(exc)))

        return {
            "paths": paths,
            "scanned": scanned,
            "errors": errors,
        }
