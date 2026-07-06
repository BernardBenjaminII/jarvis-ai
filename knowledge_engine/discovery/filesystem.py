from __future__ import annotations

import hashlib
import mimetypes
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "site-packages",
    "build",
    "dist",
    ".tox",
    ".cache",
}

IGNORE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".class",
    ".o",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".tmp",
    ".part",
    ".log",
}

DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".epub",
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".docx",
    ".odt",
    ".rtf",
    ".csv",
    ".json",
    ".xml",
    ".zim",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".js",
    ".ts",
    ".sh",
    ".sql",
    ".rs",
    ".go",
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".svg",
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".flac",
}

ARCHIVE_EXTENSIONS = {
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
}


@dataclass(frozen=True)
class DiscoveredFile:
    file_path: str
    root_path: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    sha256: str
    mime_type: str | None
    category: str
    status: str


def should_skip_dir(path: Path) -> bool:
    return path.name in IGNORE_DIRS


def classify(path: Path) -> tuple[str, str]:
    ext = path.suffix.lower()

    if ext in IGNORE_EXTENSIONS:
        return "ignored", "ignored"

    parts = set(path.parts)
    if parts & IGNORE_DIRS:
        return "ignored", "ignored"

    if ext in DOCUMENT_EXTENSIONS:
        return "document", "ready"

    if ext in SOURCE_EXTENSIONS:
        return "source_code", "review"

    if ext in IMAGE_EXTENSIONS:
        return "image", "review"

    if ext in AUDIO_EXTENSIONS:
        return "audio", "review"

    if ext in ARCHIVE_EXTENSIONS:
        return "archive", "review"

    return "unknown", "review"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    for current_root, dirs, files in os.walk(root):
        current = Path(current_root)

        dirs[:] = [d for d in dirs if not should_skip_dir(current / d)]

        for filename in files:
            yield current / filename


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS discovered_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL UNIQUE,
            root_path TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT,
            size_bytes INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            mime_type TEXT,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_discovered_files_sha256
        ON discovered_files(sha256)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_discovered_files_category
        ON discovered_files(category)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_discovered_files_status
        ON discovered_files(status)
        """
    )

    conn.commit()


def discover_file(path: Path, root: Path) -> DiscoveredFile:
    stat = path.stat()
    category, status = classify(path)
    mime_type, _ = mimetypes.guess_type(path)

    return DiscoveredFile(
        file_path=str(path),
        root_path=str(root),
        relative_path=str(path.relative_to(root)),
        filename=path.name,
        extension=path.suffix.lower(),
        size_bytes=stat.st_size,
        sha256=sha256_file(path),
        mime_type=mime_type,
        category=category,
        status=status,
    )


def save_file(conn: sqlite3.Connection, item: DiscoveredFile) -> None:
    conn.execute(
        """
        INSERT INTO discovered_files (
            file_path,
            root_path,
            relative_path,
            filename,
            extension,
            size_bytes,
            sha256,
            mime_type,
            category,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            size_bytes = excluded.size_bytes,
            sha256 = excluded.sha256,
            mime_type = excluded.mime_type,
            category = excluded.category,
            status = excluded.status,
            discovered_at = CURRENT_TIMESTAMP
        """,
        (
            item.file_path,
            item.root_path,
            item.relative_path,
            item.filename,
            item.extension,
            item.size_bytes,
            item.sha256,
            item.mime_type,
            item.category,
            item.status,
        ),
    )


def discover(root_path: str, db_path: str, limit: int | None = None) -> dict[str, int]:
    root = Path(root_path).expanduser().resolve()
    db = Path(db_path).expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Discovery root does not exist: {root}")

    db.parent.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {
        "seen": 0,
        "saved": 0,
        "errors": 0,
    }

    with sqlite3.connect(db) as conn:
        init_db(conn)

        for path in iter_files(root):
            if limit is not None and counts["seen"] >= limit:
                break

            counts["seen"] += 1

            try:
                item = discover_file(path, root)
                save_file(conn, item)
                counts["saved"] += 1
                counts[item.category] = counts.get(item.category, 0) + 1
            except Exception as exc:
                counts["errors"] += 1
                print(f"[WARN] Skipped {path}: {exc}")

            if counts["seen"] % 500 == 0:
                conn.commit()
                print(f"[INFO] scanned={counts['seen']} saved={counts['saved']} errors={counts['errors']}")

        conn.commit()

    return counts
