from __future__ import annotations

import hashlib
import sqlite3
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


OBJECT_MARKERS = {
    "git_repository": [".git"],
    "python_project": ["pyproject.toml", "setup.py", "requirements.txt"],
    "node_project": ["package.json"],
    "epub_extracted_book": ["content.opf", "toc.ncx"],
    "website_archive": ["index.html", "index.htm"],
    "academic_project": ["Code Files", "Screenshots", "Report.pdf", "README.md"],
}


@dataclass(frozen=True)
class KnowledgeObject:
    object_uuid: str
    root_path: str
    object_path: str
    object_name: str
    object_type: str
    primary_file_path: str | None
    file_count: int
    total_size_bytes: int
    content_fingerprint: str
    status: str
    confidence: float
    reason: str


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_uuid TEXT NOT NULL UNIQUE,
            root_path TEXT NOT NULL,
            object_path TEXT NOT NULL UNIQUE,
            object_name TEXT NOT NULL,
            object_type TEXT NOT NULL,
            primary_file_path TEXT,
            file_count INTEGER NOT NULL,
            total_size_bytes INTEGER NOT NULL,
            content_fingerprint TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence REAL NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_object_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_uuid TEXT NOT NULL,
            discovered_file_id INTEGER NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL,
            FOREIGN KEY(object_uuid) REFERENCES knowledge_objects(object_uuid),
            FOREIGN KEY(discovered_file_id) REFERENCES discovered_files(id)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_objects_type
        ON knowledge_objects(object_type)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_objects_status
        ON knowledge_objects(status)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_object_files_object_uuid
        ON knowledge_object_files(object_uuid)
        """
    )

    conn.commit()


def stable_uuid(object_path: str, fingerprint: str) -> str:
    seed = f"{object_path}|{fingerprint}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def fingerprint_files(files: list[sqlite3.Row]) -> str:
    digest = hashlib.sha256()

    for row in sorted(files, key=lambda r: r["relative_path"]):
        digest.update(str(row["relative_path"]).encode("utf-8", errors="ignore"))
        digest.update(str(row["sha256"]).encode("utf-8", errors="ignore"))

    return digest.hexdigest()


def path_has_ignored_parts(path: Path) -> bool:
    ignored = {
        ".git",
        ".venv",
        "venv",
        "site-packages",
        "__pycache__",
        ".idea",
        ".vscode",
        "node_modules",
    }
    return bool(set(path.parts) & ignored)


def detect_object_type(object_path: Path, files: list[sqlite3.Row]) -> tuple[str, float, str, str | None]:
    names = {Path(row["file_path"]).name for row in files}
    suffixes = {Path(row["file_path"]).suffix.lower() for row in files}
    parts = set(object_path.parts)

    if ".git" in names or ".git" in parts:
        return "git_repository", 0.98, "contains .git marker", None

    if {"pyproject.toml", "setup.py", "requirements.txt"} & names:
        return "python_project", 0.92, "contains Python project marker", None

    if "package.json" in names:
        return "node_project", 0.90, "contains Node project marker", None

    if {"content.opf", "toc.ncx"} & names:
        primary = next((row["file_path"] for row in files if Path(row["file_path"]).name == "content.opf"), None)
        return "epub_extracted_book", 0.95, "contains EPUB metadata marker", primary

    if {"index.html", "index.htm"} & names and ({".css", ".js"} & suffixes):
        primary = next(
            (row["file_path"] for row in files if Path(row["file_path"]).name in {"index.html", "index.htm"}),
            None,
        )
        return "website_archive", 0.90, "contains index page plus web assets", primary

    if any("Project" in part or "project" in part for part in object_path.parts):
        return "academic_or_code_project", 0.70, "path name suggests project", None

    if len(files) == 1:
        row = files[0]
        ext = Path(row["file_path"]).suffix.lower()

        if ext in {".pdf", ".epub", ".docx", ".txt", ".md", ".zim"}:
            return "single_document", 0.80, f"single supported document {ext}", row["file_path"]

        if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            return "single_image", 0.70, f"single image {ext}", row["file_path"]

        return "single_file", 0.50, "single loose file", row["file_path"]

    if suffixes <= {".html", ".htm", ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".json"}:
        return "web_or_html_collection", 0.75, "directory contains mostly web assets", None

    return "folder_collection", 0.60, "directory grouped as folder collection", None


def choose_group_key(row: sqlite3.Row, root: Path) -> Path:
    file_path = Path(row["file_path"])
    relative = Path(row["relative_path"])
    parent = file_path.parent

    # Single real book/document files should usually be objects themselves.
    ext = file_path.suffix.lower()
    if ext in {".pdf", ".epub", ".docx", ".zim"}:
        return file_path

    # HTML trees, source projects, extracted folders, and mixed directories should group by parent.
    if len(relative.parts) > 1:
        return parent

    return file_path


def load_discovered_files(
    conn: sqlite3.Connection,
    root_filter: str | None,
) -> list[sqlite3.Row]:
    sql = """
        SELECT
            id,
            file_path,
            root_path,
            relative_path,
            filename,
            extension,
            size_bytes,
            sha256,
            category,
            status
        FROM discovered_files
    """
    params: list[str] = []

    if root_filter:
        sql += " WHERE file_path LIKE ?"
        params.append(f"%{root_filter}%")

    sql += " ORDER BY file_path"

    return list(conn.execute(sql, params))


def build_objects(
    db_path: str,
    root_filter: str | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    db = Path(db_path).expanduser().resolve()

    counts: dict[str, int] = {
        "files_seen": 0,
        "files_grouped": 0,
        "objects_built": 0,
        "ignored_files": 0,
        "errors": 0,
    }

    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        init_db(conn)

        rows = load_discovered_files(conn, root_filter)
        counts["files_seen"] = len(rows)

        grouped: dict[Path, list[sqlite3.Row]] = defaultdict(list)

        for row in rows:
            path = Path(row["file_path"])

            if row["status"] == "ignored" or path_has_ignored_parts(path):
                counts["ignored_files"] += 1
                continue

            try:
                root = Path(row["root_path"])
                key = choose_group_key(row, root)
                grouped[key].append(row)
                counts["files_grouped"] += 1
            except Exception as exc:
                counts["errors"] += 1
                print(f"[WARN] Failed grouping {row['file_path']}: {exc}")

        if dry_run:
            print(f"[DRY-RUN] Would build {len(grouped)} knowledge objects.")
            counts["objects_built"] = len(grouped)
            return counts

        for object_path, files in grouped.items():
            try:
                root_path = files[0]["root_path"]
                total_size = sum(int(row["size_bytes"]) for row in files)
                fingerprint = fingerprint_files(files)
                object_uuid = stable_uuid(str(object_path), fingerprint)

                object_type, confidence, reason, primary_file = detect_object_type(object_path, files)

                obj = KnowledgeObject(
                    object_uuid=object_uuid,
                    root_path=root_path,
                    object_path=str(object_path),
                    object_name=object_path.name,
                    object_type=object_type,
                    primary_file_path=primary_file,
                    file_count=len(files),
                    total_size_bytes=total_size,
                    content_fingerprint=fingerprint,
                    status="registered",
                    confidence=confidence,
                    reason=reason,
                )

                conn.execute(
                    """
                    INSERT INTO knowledge_objects (
                        object_uuid,
                        root_path,
                        object_path,
                        object_name,
                        object_type,
                        primary_file_path,
                        file_count,
                        total_size_bytes,
                        content_fingerprint,
                        status,
                        confidence,
                        reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(object_path) DO UPDATE SET
                        object_uuid = excluded.object_uuid,
                        object_name = excluded.object_name,
                        object_type = excluded.object_type,
                        primary_file_path = excluded.primary_file_path,
                        file_count = excluded.file_count,
                        total_size_bytes = excluded.total_size_bytes,
                        content_fingerprint = excluded.content_fingerprint,
                        status = excluded.status,
                        confidence = excluded.confidence,
                        reason = excluded.reason,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        obj.object_uuid,
                        obj.root_path,
                        obj.object_path,
                        obj.object_name,
                        obj.object_type,
                        obj.primary_file_path,
                        obj.file_count,
                        obj.total_size_bytes,
                        obj.content_fingerprint,
                        obj.status,
                        obj.confidence,
                        obj.reason,
                    ),
                )

                for row in files:
                    role = "primary" if row["file_path"] == primary_file else "member"

                    conn.execute(
                        """
                        INSERT INTO knowledge_object_files (
                            object_uuid,
                            discovered_file_id,
                            file_path,
                            role
                        )
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(file_path) DO UPDATE SET
                            object_uuid = excluded.object_uuid,
                            discovered_file_id = excluded.discovered_file_id,
                            role = excluded.role
                        """,
                        (
                            obj.object_uuid,
                            row["id"],
                            row["file_path"],
                            role,
                        ),
                    )

                counts["objects_built"] += 1
                counts[obj.object_type] = counts.get(obj.object_type, 0) + 1

                if counts["objects_built"] % 500 == 0:
                    conn.commit()
                    print(f"[INFO] objects_built={counts['objects_built']}")

            except Exception as exc:
                counts["errors"] += 1
                print(f"[WARN] Failed object build for {object_path}: {exc}")

        conn.commit()

    return counts
